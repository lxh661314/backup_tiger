#!/usr/bin/python
#coding:utf8
from abc import ABCMeta, abstractmethod
import time, subprocess, socket, os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ_CONFIG_FILE = os.path.join(os.path.join(BASE_DIR, 'config'), 'config.cfg')
PROJ_LIB_DIR = os.path.join(BASE_DIR, 'lib')
sys.path.insert(0, PROJ_LIB_DIR)
from util import *
from sshConn import *
from dbControl import *
from db_backup_tools import *
from fs_backup_tools import *
import pymysql

PROJ_CONFIG_OBJ = readConfig(PROJ_CONFIG_FILE)
PROJ_DB_CONFIG = PROJ_CONFIG_OBJ.read_config("db")

sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'webadmins.settings')
from django.conf import settings
POOL = settings.POOL



class fs_backup_tools:
    def __init__(self, source_addr, p_id, t_id):
        self.source_addr = source_addr
        self.cmdb_host_info = self.__get_cmdb_host_info()
        self.p_id = p_id
        self.t_id = t_id

    def __get_cmdb_host_info(self):
        db = dbControl(POOL)
        result = select_database_info(db, PROJ_DB_CONFIG["database"], "cmdb_host_information",
                                      source_addr=self.source_addr)
        db.close()
        return result

    def __get_sshConn(self):
        result = controlHost(self.source_addr, self.cmdb_host_info["host_user"], self.cmdb_host_info["host_passwd"], self.cmdb_host_info["host_port"])
        return result

    def before_db_backup_status_add(self, backup_path, backup_to_local_path):
        db = dbControl(POOL)
        task_id = '-'.join([self.p_id, self.t_id, self.stat_time])
        data = {"stat_time": self.stat_time, "task_id": task_id, "source_addr": self.source_addr, "svc_type": "fs_full_backup",
                "createor": "sched", "task_status": 0, "backup_to_local_path": backup_to_local_path,
                "backup_path": backup_path
                }
        print(data)
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").add([data])
        except Exception as e:
            logger.error(str(e))
        finally:
            db.close()

    def after_db_backup_status_update(self, data):
        task_id = '-'.join([self.p_id, self.t_id, self.stat_time])
        db = dbControl(POOL)
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").where({"task_id": task_id}).set(data).update()
        except Exception as e:
            logger.error(str(e))
        finally:
            db.close()


    def fs_backup_start(self, backup_path, backup_to_local_path):
        timestamp = ControlTime.date_today(_format="%Y%m%d%H%M%S")[0]
        self.stat_time = str(ControlTime.date_today(_format="%Y%m%d%H%M%S")[1])
        backup_to_local_path = os.path.join(backup_to_local_path, timestamp)
        self.before_db_backup_status_add(backup_path, backup_to_local_path)
        sshObj = ""
        try:
            sshObj = self.__get_sshConn()
            d = distribute_filesystem_backup(sshObj, self.source_addr)
            result = d.fs_full_backup(backup_path, backup_to_local_path)
        except Exception as e:
            data = {"message": pymysql.escape_string(str(e))}
            self.after_db_backup_status_update(data)
        else:
            data = {"task_status": 1, "message": pymysql.escape_string(result)}
            self.after_db_backup_status_update(data)
        finally:
            if hasattr(sshObj, "close"):
                sshObj.close()


if __name__ == "__main__":
    from dbControl import *
    POOL = dbPool(PROJ_DB_CONFIG)
    db = dbControl(POOL)
    print(db)
    x = fs_backup_tools('172.16.70.221', '2000', '3000')
    x.fs_backup_start("/mnt/nfs/031551540182823/backup_filesystem/172.16.70.221/etc/sysconfig/network-scripts",
                      '/mnt/nfs/031551540182823/backup_filesystem/172.16.70.221/filesystem_full_backup/etc/sysconfig/network-scripts')
