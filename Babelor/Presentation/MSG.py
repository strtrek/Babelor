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

# System Required
from datetime import datetime
import base64
# Outer Required
# Inner Required
from Babelor.Tools import dict2json, json2dict, dict2xml, xml2dict
from Babelor.Config import GLOBAL_CFG
from Babelor.Presentation import URL, CASE
# Global Parameters
DatetimeFmt = GLOBAL_CFG["DatetimeFormat"]
PortFmt = GLOBAL_CFG["PortFormat"]
CODING = GLOBAL_CFG["CODING"]
MSG_TYPE = GLOBAL_CFG["MSG_TYPE"]


def current_datetime() -> str:
    return datetime.now().strftime(DatetimeFmt)


def null_keep(item: object, item_type: classmethod = str) -> object:
    if item is None:
        return None
    elif isinstance(item, item_type):
        return item
    else:
        return item_type(item)


class MSG:
    def __init__(self, msg=None):
        self.timestamp = current_datetime()     # 时间戳        -   Time Stamp
        self.origination = None                 # 来源节点      -   Source Node
        self.destination = None                 # 目标节点      -   Target Node
        self.case = None                        # 实例          -   Instance
        self.activity = None                    # 步骤          -   Step in Instance
        self.treatment = None                   # 计算节点      -   Computing Node
        self.encryption = None                  # 加/解密节点   -   Encrypted Node
        self.nums = 0                           # 参数个数      -   Number of Arguments
        self.coding = None                      # 文字编码      -   Character Coding
        self.dtype = None                       # 数据编码      -   Data Encoding
        self.stream = None                      # 数据流        -   Data Stream
        self.path = None                        # 路径          -   Path
        if isinstance(msg, str):
            if MSG_TYPE in ["json"]:
                self.from_json(msg)
            elif MSG_TYPE in ["xml"]:
                self.from_xml(msg)
            else:
                raise NotImplementedError("仅支持 xml 和 json 类消息")
        if isinstance(msg, dict):
            self.from_dict(msg)

    def __str__(self):
        return self.to_string()

    __repr__ = __str__

    def __setattr__(self, key, value):
        self.__dict__[key] = value
        keys = ["coding", "dtype", "path", "stream"]
        is_keys_init = len([False for k in keys if k not in list(self.__dict__.keys())]) == 0
        if key in ["nums"]:
            if value == 0 and is_keys_init:
                for k in keys:
                    self.__dict__[k] = None
        if key in keys and is_keys_init:
            if isinstance(value, list) and self.__dict__["nums"] == 1:
                self.__dict__[key] = value[0]
            # print([False for k in keys if self.__dict__[k] is None])
        if key not in ["timestamp"]:
            self.__dict__["timestamp"] = current_datetime()

    def to_dict(self):
        return {
            "head": {
                "timestamp": self.timestamp,        # 时间戳        -   Time Stamp
                "origination": self.origination,    # 来源节点      -   Source Node
                "destination": self.destination,    # 目标节点      -   Target Node
                "treatment": self.treatment,        # 计算节点      -   Computing Node
                "encryption": self.encryption,      # 加/解密节点   -   Encrypted Node
                "case": self.case,                  # 实例          -   Instance
                "activity": self.activity,          # 步骤          -   Step in Instance
            },
            "body": {
                "nums": self.nums,                  # 参数个数      -   Number of Arguments
                "coding": self.coding,              # 文字编码      -   Character Coding
                "dtype": self.dtype,                # 数据编码      -   Data Encoding
                "path": self.path,                  # 路径          -   Path
                "stream": self.stream,              # 数据流        -   Data Stream
            },
        }

    def to_serialize(self):
        return {
            "head": {
                "timestamp": null_keep(self.timestamp),
                "origination": null_keep(self.origination),
                "destination": null_keep(self.destination),
                "treatment": null_keep(self.treatment),
                "encryption": null_keep(self.encryption),
                "case": null_keep(self.case),
                "activity": null_keep(self.activity),
            },
            "body": {
                "nums": self.nums,
                "coding": self.coding,
                "dtype": self.dtype,
                "path": self.path,
                "stream": self.stream,
            },
        }

    def to_string(self):
        if MSG_TYPE is "json":
            return self.to_json()
        elif MSG_TYPE is "xml":
            return self.to_xml()
        else:
            raise NotImplementedError("Support xml and json pattern only.")

    def to_json(self):
        return dict2json(self.to_serialize())

    def to_xml(self):
        return dict2xml(self.to_serialize())

    def from_dict(self, msg: dict):
        def _value_check(key: str, item: dict, datum_type: classmethod = str):
            if key in item.keys():
                self.__dict__[key] = null_keep(item[key], datum_type)
            else:
                self.__dict__[key] = None
        if not isinstance(msg, dict):
            raise AttributeError("{0} is not dict type.".format(str(msg)))
        if "head" in msg.keys():
            # set timestamp from msg
            _value_check("timestamp", msg["head"])
            if self.__dict__["timestamp"] is None:
                self.__dict__["timestamp"] = current_datetime()
            # set origination from msg
            _value_check("origination", msg["head"], URL)
            # set destination from msg
            _value_check("destination", msg["head"], URL)
            # set treatment from msg
            _value_check("treatment", msg["head"], URL)
            # set encryption from msg
            _value_check("encryption", msg["head"], URL)
            # set case from msg
            _value_check("case", msg["head"], CASE)
            # set activity from msg
            _value_check("activity", msg["head"])
        else:
            self.__dict__["timestamp"] = current_datetime()
            self.__dict__["origination"] = None
            self.__dict__["destination"] = None
            self.__dict__["treatment"] = None
            self.__dict__["encryption"] = None
            self.__dict__["case"] = None
            self.__dict__["activity"] = None
        if "body" in msg.keys():
            # set nums from msg
            _value_check("nums", msg["body"], int)
            # set coding from msg
            self.__dict__["coding"] = msg["body"]["coding"]
            # set path from msg
            self.__dict__["path"] = msg["body"]["path"]
            # set dtype from msg
            self.__dict__["dtype"] = msg["body"]["dtype"]
            # set stream from msg
            self.__dict__["stream"] = msg["body"]["stream"]
        else:
            self.__dict__["nums"] = 0
            self.__dict__["coding"] = None
            self.__dict__["path"] = None
            self.__dict__["dtype"] = None
            self.__dict__["stream"] = None

    def from_json(self, msg: str):
        self.from_dict(json2dict(msg))

    def from_xml(self, msg: str):
        self.from_dict(xml2dict(msg))

    def swap(self):
        origination = self.origination
        self.origination = self.destination
        self.destination = origination
        return self

    def forward(self, destination: URL):
        self.origination = self.destination
        self.destination = destination
        return self

    def add_datum(self, datum, path=None):
        stream, coding, dtype = datum_to_stream(datum)
        path = null_keep(path)
        if self.__dict__["nums"] == 0:
            self.__dict__["stream"] = stream
            self.__dict__["coding"] = coding
            self.__dict__["path"] = path
            self.__dict__["dtype"] = dtype
        if self.__dict__["nums"] == 1:
            self.__dict__["stream"] = [self.__dict__["stream"], stream]
            self.__dict__["coding"] = [self.__dict__["coding"], coding]
            self.__dict__["path"] = [self.__dict__["path"], path]
            self.__dict__["dtype"] = [self.__dict__["dtype"], dtype]
        if self.__dict__["nums"] > 1:
            self.__dict__["stream"] = self.__dict__["stream"] + [stream]
            self.__dict__["coding"] = self.__dict__["coding"] + [coding]
            self.__dict__["path"] = self.__dict__["path"] + [path]
            self.__dict__["dtype"] = self.__dict__["dtype"] + [dtype]
        self.__dict__["nums"] = self.__dict__["nums"] + 1
        return self

    def read_datum(self, num: int):
        if self.__dict__["nums"] == 0:
            return {"stream": None, "path": None}
        elif num > self.__dict__["nums"]:
            return {"stream": None, "path": None}
        elif self.__dict__["nums"] == 1:
            return {
                "stream": stream_to_datum(self.__dict__["stream"], self.__dict__["coding"], self.__dict__["dtype"]),
                "path": self.__dict__["path"],
            }
        else:
            return {
                "stream": stream_to_datum(self.__dict__["stream"][num - 1], self.__dict__["coding"][num - 1],
                                          self.__dict__["dtype"][num - 1]),
                "path": self.__dict__["path"][num - 1],
            }

    def delete_datum(self, num: int):
        if self.__dict__["nums"] == 0:
            pass
        elif self.__dict__["nums"] == 1:
            self.nums = 0
        else:
            del self.__dict__["stream"][num]
            del self.__dict__["coding"][num]
            del self.__dict__["path"][num]
            del self.__dict__["dtype"][num]
            self.nums = self.__dict__["nums"] - 1   # Out of list by __setattr__
            self.stream = self.__dict__["stream"]
            self.coding = self.__dict__["coding"]
            self.path = self.__dict__["path"]
            self.dtype = self.__dict__["dtype"]


def datum_to_stream(datum=None):
    if datum is None:
        return None, None, None
    elif isinstance(datum, str):
        return datum, CODING, "str"
    else:
        return base64.b64encode(datum).decode(CODING), CODING, "base64"


def stream_to_datum(stream, coding=None, dtype=None):
    if stream is None and coding is None and dtype is None:
        return None
    if stream is None or coding is None or dtype is None:
        raise ValueError
    if isinstance(stream, str):
        if dtype in ["base64"]:
            return base64.b64decode(stream.encode(coding))
        elif dtype in ["str"]:
            return stream
        else:
            raise NotImplementedError("Not support type:{0}".format(dtype))
