# coding=utf-8
# Copyright 2019 StrTrek Team Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from urllib.parse import urlparse, unquote, urlunparse
from Tools.Conversion import dict2json, json2dict
from datetime import datetime
import re

DatetimeFmt = '%Y-%m-%d %H:%M:%S.%f'
CODING = 'utf-8'


def current_datetime():
    return datetime.now().strftime(DatetimeFmt)


class URL:
    def __new__(cls, *args, **kwargs):
        cls.scheme = None
        cls.username = None
        cls.password = None
        cls.hostname = None
        cls.port = None
        cls.netloc = None
        cls.path = None
        cls.params = None
        cls.query = None
        cls.fragment = None

    def __init__(self, url: str):
        # scheme://username:password@hostname:port/path;params?query#fragment
        url = urlparse(re.sub(r':port[^@]', "", url))
        self.scheme = url.scheme
        self.username = url.username
        self.password = url.password
        self.hostname = url.hostname
        self.port = url.port
        self.netloc = url.netloc
        self.path = re.sub(r'/$', "", url.path)
        self.params = url.params
        self.query = url.query
        try:
            self.fragment = URL(unquote(url.fragment))
        except RecursionError:
            self.fragment = url.fragment

    def __str__(self):
        return self.to_string()

    __repr__ = __str__

    def __setattr__(self, key, value):
        self.__dict__[key] = value                                  # source update
        if key in ["port", "hostname", "username", "password"]:     # relative update
            if self.password is None:
                if self.username is None:
                    user_info = None
                else:
                    user_info = self.username
            else:
                user_info = "{0}:{1}".format(self.username, self.password)
            if self.port is None:
                net_info = self.hostname
            else:
                net_info = "{0}:{1}".format(self.hostname, self.port)
            if user_info is None:
                self.__dict__["netloc"] = net_info
            else:
                self.__dict__["netloc"] = "{0}@{1}".format(user_info, net_info)

    def to_string(self, allow_path=True, allow_params=True, allow_query=True, allow_fragment=True):
        path, params, query, fragment = "", "", "", ""
        if allow_path:
            path = self.path
        if allow_params:
            params = self.params
        if allow_query:
            query = self.query
        if allow_fragment:
            if isinstance(self.fragment, URL):
                fragment = self.fragment.to_string()
            else:
                fragment = self.fragment
        return urlunparse((self.scheme, self.netloc, path, params, query, fragment))


EMPTY_URL = URL("scheme://username:password@hostname:port/path;params?query#fragment")


def check_url(*args):
    if len(args) > 1:
        raise AttributeError
    if isinstance(args[0], str):
        return URL(args[0])
    elif isinstance(args[0], URL):
        return args[0]
    else:
        raise ValueError


def null_value_check(msg_value, msg_value_type=str):
    if msg_value is None:
        return None
    else:
        return msg_value_type(msg_value)


class MSG:
    def __init__(self, json: str):
        msg = json2dict(json)
        self.timestamp = null_value_check(msg["head"]["timestamp"])
        self.origination = null_value_check(msg["head"]["origination"], URL)
        self.destination = null_value_check(msg["head"]["destination"], URL)
        self.case = null_value_check(msg["head"]["case"])
        self.activity = null_value_check(msg["head"]["activity"])
        self.treatment = null_value_check(msg["body"]["treatment"], URL)
        self.encryption = null_value_check(msg["body"]["encryption"], URL)
        self.data = null_value_check(msg["body"]["data"])

    def __str__(self):
        return self.to_string()

    __repr__ = __str__

    def to_string(self):
        return dict2json({
            "head": {
                "timestamp": self.timestamp,
                "origination": self.origination,
                "destination": self.destination,
                "case": self.case,
                "activity": self.activity,
            },
            "body": {
                "treatment": self.treatment,
                "encryption": self.encryption,
                "data": self.data,
            }
        })

    def swap(self):
        origination = self.origination
        self.origination = self.destination
        self.destination = origination
        return self

    def forward(self, destination: URL):
        self.origination = self.destination
        self.destination = destination
        return self

    def renew(self):
        self.timestamp = current_datetime()
        self.data = None
        return self

    def success_reply(self, state: bool):
        self.renew()
        self.swap()
        self.treatment = None
        self.encryption = None
        self.data = {"SUCCESS": state}
        return self


EMPTY_MSG = MSG('''
{
    "head": {
        "timestamp": null,
        "origination": null,
        "destination": null,
        "case": null,
        "activity": null
    },
    "body": {
        "treatment": null,
        "encryption": null,
        "data": null
    }
}
''')


def check_sql_url(url: URL, has_table=False):
    # conn = "oracle://username:password@hostname/service#table"
    # conn = "mysql://username:password@hostname/service#table"
    # conn = "oracle://username:password@hostname:port/service#table"
    # conn = "mysql://username:password@hostname:port/service#table"
    port = 0
    if url.scheme == "oracle":
        url.scheme = "oracle+cx_oracle"
        port = 1521
    if url.scheme == "mysql":
        url.scheme = "mysql+pymysql"
        port = 3306
    if url.port is None:
        url.port = port
        url.netloc = "{0}:{1}".format(url.netloc, port)
    # conn = "oracle+cx_oracle://username:password@hostname:1521/service#table"
    # conn = "mysql+pymysql://username:password@hostname:3306/service#table"
    if has_table:
        return url.to_string(True, False, False, True)
    else:
        return url.to_string(True, False, False, False)


def check_ftp_url(*args):
    # conn = "ftp://username:password@hostname:10001/path#PASV"
    url = URL(args[0])
    if url.scheme != "ftp":
        raise ValueError
    if url.port is None:
        url.port = 21
        url.netloc = "{0}:{1}".format(url.netloc, url.port)
    return url.to_string(True, False, False, True)


def check_success_reply(*args):
    # Function Input Check
    if len(args) > 1:
        raise AttributeError("输入参数过多")
    if isinstance(args[0], str):
        msg = MSG(args[0])
    elif isinstance(args[0], MSG):
        msg = args[0]
    else:
        raise ValueError("未知的数据类型")
    if isinstance(msg.data, dict):
        if msg.data.haskey("SUCCESS"):
            return msg.data["SUCCESS"]
        else:
            return False
    else:
        return False


def demo_tomail():
    conn = "{0}#{1}#{2}#{3}".format("tomail://receiver_mail_username@receive_mail_hostname",
                                    "smtp://sender_username:sender_password@sender_hostname:port",
                                    "tomail://sender_mail_username_2@senderhostname_2",
                                    "receiver_user")
    url = URL(conn)
    print("URL:", url)
    print("收件人:", url.netloc)
    print("收件人协议:", url.scheme)
    print("收件人用户名:", url.username)
    print("收件人名:", url.fragment.fragment.fragment)
    print("发件人：", "{0}@{1}".format(url.fragment.username, url.fragment.fragment.hostname))
    print("发件人协议:", url.fragment.fragment.scheme)
    print("发件人用户名:", url.fragment.username)
    print("发件人名:", url.fragment.fragment.username)
    print("服务协议:", url.fragment.scheme)
    print("服务用户:", url.fragment.username)
    print("服务密码:", url.fragment.password)
    print("服务地址", url.fragment.hostname)
    print("服务端口", url.fragment.port)


def demo_sql():
    conn = "oracle://username:password@hostname:port/service"
    url = URL(conn)
    print("URL:", url)
    print("服务协议:", url.scheme)
    print("服务用户:", url.username)
    print("服务密码:", url.password)
    print("服务地址", url.hostname)
    print("服务端口", url.port)
    print("数据服务", url.path)


def demo_ftp():
    conn = "ftp://username:password@hostname/path#PASV"
    url = URL(conn)
    print("URL:", url)
    print("服务协议:", url.scheme)
    print("服务用户:", url.username)
    print("服务密码:", url.password)
    print("服务地址", url.hostname)
    print("服务端口", url.port)
    print("服务路径", url.path)
    print("服务模式", url.fragment)


if __name__ == '__main__':
    # string = "oracle://username:password@hostname:port/service"
    # txt = re.sub(r':port\[\^@\]', "", string)
    ur = EMPTY_URL
    ur.port = 100
    print(ur)
