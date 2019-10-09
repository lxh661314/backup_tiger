#coding:utf8

import subprocess
import time
import datetime
import configparser as ConfigParser
import traceback
import random






def select_database_info(db, database, table ,**kwargs):
    try:
        result = db.select_database(database).select_table(table).\
                     where(kwargs).select('*', final="dict")
    except:
        traceback.print_exc()
        return None
    else:
        if not result:
            return []
        else:
            return result[0]


class TimeoutError(Exception):
    pass

def os_system(cmd, timeout=3):
    """
    执行命令的超时时间
    """
    beg_time = int(time.time())
    s = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while 1:
        stop = s.poll()
        if stop is not None:
            break
        end_time = int(time.time())
        if (end_time - beg_time) >= timeout:
            s.terminate()
            raise TimeoutError("cmd exe expired!")
        time.sleep(0.1)
    result = s.stdout.read()
    return result

class ControlTime:
    @staticmethod
    def date_today(_format='%Y%m%d'):
        a = time.strftime(_format, time.localtime())
        return a, int(time.mktime(time.strptime(a, _format)))

    @staticmethod
    def int_conv_str(seconds, _format='%Y-%m-%d %H:%M:%S'):
        return time.strftime(_format, time.localtime(int(seconds)))

    @staticmethod
    def str_conv_int(string, _format='%Y%m%d'):
        return int(time.mktime(time.strptime(str(string), _format)))

class readConfig:
    def __init__(self, path='', section=None):
        self.section = section
        self.config = ConfigParser.ConfigParser()
        self.config.read(path)

    def getSections(self):
        return self.config.sections()

    def read_config(self, section):
        result = {}
        try:
            configArgs = self.config.items(section)
            #print(configArgs)
        except Exception as e:
            traceback.print_exc()
            return {}
        else:
            for (k, v) in configArgs:
                result[k] = v
        return result

def create_jid(length=10):
    result = []
    for _ in range(length):
        x = random.randint(0, 9)
        result.append(str(x))
    return ''.join(result)


def get_folder_size(mnt_path):
    result = [0, 0]
    output = os_system("df | grep %s" %mnt_path).split()
    if len(output) < 3:
        return result
    total = int(output[1]) if output[1].isdigit() else 0
    free = int(output[2]) if output[2].isdigit() else 0
    result[0] = total
    result[1] = free
    return result


if __name__ == '__main__':
    x = get_folder_size('/mnt/nfs/671071324918648')
    print(x)




if  __name__ == '__main__':
    f = '/app_shell/backup-platform/webadmins/config/config.cfg'
    x = readConfig(f)
    print(x.read_config("uwsgi"))