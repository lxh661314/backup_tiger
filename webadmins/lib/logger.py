#coding:utf8


import logging
from multiprocessing import Lock
import os
from functools import wraps
from logging.handlers import TimedRotatingFileHandler
import threading

lock = Lock()

def locker(locker):
    def _locker(func):
        @wraps(func)
        def __locker(i, s):
            locker.acquire()
            func(i, s)
            locker.release()
        return __locker
    return _locker


class log(object):
    _instance_lock = threading.Lock()
    proj_log_file = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log'), 'webadmins.log')
    def __new__(cls, *args, **kwargs):
        if not hasattr(log, "_instance"):
            with log._instance_lock:
                if not hasattr(log, "_instance"):
                    log._instance = object.__new__(cls)
        return log._instance

    def __init__(self, logFile=None, console=False):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level=logging.INFO)
        self.format = logging.Formatter(datefmt='%Z %z %A %Y-%m-%d %X', fmt='%(asctime)s|%(levelname)s|%(filename)s|%(funcName)s|%(message)s')

        if not logFile:
            self.logPath = self.__makeDir(log.proj_log_file)
            self.fileHander = log.__fileHandler(self.logger, log.proj_log_file, self.format)
        else:
            self.logPath = self.__makeDir(logFile)
            self.fileHander = log.__fileHandler(self.logger, logFile, self.format)

        if console:
            self.streamHandler = log.__streamHandler(self.logger, self.format)

    @staticmethod
    def __fileHandler(logObj, logFile, format):
        handler = TimedRotatingFileHandler(filename=logFile, when="D", interval=1, backupCount=7)
        handler.setLevel(logging.INFO)
        handler.setFormatter(format)
        logObj.addHandler(handler)


    @staticmethod
    def __streamHandler(logObj, format):
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(fmt=format)
        logObj.addHandler(console)


    @staticmethod
    def __makeDir(logFile):
        if '/' not in logFile:
            return
        logPath = logFile.rsplit('/', 1)[0]
        if not os.path.exists(logPath):
            os.makedirs(logPath)
        return 1


    def getLogger(self):
        return self.logger


if __name__ == '__main__':
    import multiprocessing
    logger = log().getLogger()
    def f1():
        logger.info("this is function f1")
    res = []
    for j in range(10):
        m = multiprocessing.Process(target=f1)
        res.append(m)

    for j in res:
        j.start()

    for j in res:
        j.join()
