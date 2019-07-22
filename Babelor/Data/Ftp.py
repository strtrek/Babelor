# coding=utf-8
# Copyright 2018 StrTrek Team Authors.
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
import os
import ftplib
import logging
# Outer Required
import pandas as pd
import numpy as np
# Inner Required
from Babelor.Presentation import URL, MSG
from Babelor.Data.File import mkdir
# Global Parameters
from Babelor.Config import CONFIG


class FTP:
    def __init__(self, conn: URL):
        if isinstance(conn, str):
            self.conn = URL(conn)
        else:
            self.conn = conn
        if os.path.splitext(self.conn.path)[-1] in [""]:
            self.url_is_dir = True
        else:
            self.url_is_dir = False

    def read(self, msg: MSG):
        # logging.debug("FTP::{0}::READ msg:{1}".format(self.conn, msg))
        ftp = self.open()
        # -------------------------------------------------
        rm_idx = []
        for i in range(0, msg.args_count, 1):
            argument = msg.read_args(i)
            if self.url_is_dir:
                path = os.path.join(self.conn.path, argument["path"])
            else:
                path = self.conn.path
            suffix = os.path.splitext(path)[-1]
            # ----------------------------
            stream = bytes()
            ftp.retrbinary('RETR ' + path, stream, CONFIG.FTP_BUFFER)
            temp_path = "temp/temp" + suffix
            mkdir(os.path.split(temp_path)[0])
            # -------------------------------
            if suffix in [".xls", ".xlsx"]:
                with open(temp_path, "wb") as temp_file:
                    temp_file.write(stream)
                if self.url_is_dir:
                    stream = pd.read_excel(temp_path)
                else:
                    stream = pd.read_excel(temp_path, sheet_name=argument["path"])
                logging.info("FTP::EXCEL::{0}::READ successfully.".format(path))
            elif suffix in [".npy"]:
                with open(temp_path, "wb") as temp_file:
                    temp_file.write(stream)
                stream = np.load(temp_path)
                logging.info("FTP::NUMPY::{0}::READ successfully.".format(path))
            else:
                logging.info("FTP::{0}::READ successfully.".format(path))
            os.remove(temp_path)
            os.removedirs(os.path.split(temp_path)[0])
            del temp_path
            # -------------------------------
            msg.add_datum(datum=stream, path=argument["path"])
            rm_idx = [i] + rm_idx
        # -------------------------------------------------
        if CONFIG.IS_DATA_READ_START:
            for i in rm_idx:
                msg.remove_args(i)
        logging.info("FTP::{0}::READ successfully.".format(self.conn))
        return msg

    def write(self, msg: MSG):
        # logging.debug("FTP::{0}::WRITE msg:{1}".format(self.conn, msg))
        ftp = self.open()
        # -------------------------------------------------
        rm_idx = []
        for i in range(0, msg.dt_count, 1):
            dt = msg.read_datum(i)
            if self.url_is_dir:
                path = os.path.join(self.conn.path, dt["path"])
            else:
                path = self.conn.path
            # ----------------------------
            suffix = os.path.splitext(path)[-1]
            temp_path = "temp/temp" + suffix
            mkdir(temp_path)
            # ----------------------------
            if suffix in [".xls", ".xlsx"]:
                if isinstance(dt["stream"], pd.DataFrame):
                    dt["stream"].to_excel(temp_path, index=False)
                    with open(temp_path, "rb") as temp_file:
                        stream = temp_file.read()
                    logging_info = "::EXCEL"
                else:
                    stream = None
                    logging_info = "::EXCEL"
            elif suffix in [".npy"]:
                if isinstance(dt["stream"], np.ndarray):
                    np.save(temp_path, dt["stream"])
                    with open(temp_path, "rb") as temp_file:
                        stream = temp_file.read()
                    logging_info = "::NUMPY"
                else:
                    stream = None
                    logging_info = "::NUMPY"
            else:
                stream = dt["stream"]
                logging_info = ""
            # ----------------------------
            ftp.storbinary('STOR ' + path, stream, CONFIG.FTP_BUFFER)
            rm_idx = [i] + rm_idx
            logging.info("FTP{0}::{1}::WRITE successfully.".format(logging_info, self.conn))
        # -------------------------------------------------
        if CONFIG.IS_DATA_WRITE_END:
            for i in rm_idx:
                msg.remove_datum(i)
        ftp.close()

    def open(self):
        ftp = ftplib.FTP()
        ftp.connect(self.conn.hostname, self.conn.port)
        ftp.login(self.conn.username, self.conn.password)
        # ----------------------------------------------------- 被动模式 - PASV Model
        if isinstance(self.conn.fragment, URL):
            if isinstance(self.conn.fragment.query, dict):
                if self.conn.fragment.query["model"] in ["PASV"]:
                    ftp.set_pasv(True)
        return ftp
