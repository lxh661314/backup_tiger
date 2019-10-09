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
from logger import log
logger = log().getLogger()
import pymysql
PROJ_CONFIG_OBJ = readConfig(PROJ_CONFIG_FILE)
PROJ_DB_CONFIG = PROJ_CONFIG_OBJ.read_config("db")

sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'webadmins.settings')
from django.conf import settings
POOL = settings.POOL



class duplicate_claen_tools:
    def __init__(self, p_id=None, t_id=None):
        # self.source_addr = source_addr
        # self.cmdb_host_info = self.__get_cmdb_host_info()
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


    def before_db_backup_status_add(self):
        db = dbControl(POOL)
        task_id = '-'.join([self.p_id, self.t_id, self.stat_time])
        data = {"stat_time": self.stat_time, "task_id": task_id, "source_addr": '127.0.0.1', "svc_type": "duplicate_clean",
                "createor": "sched", "task_status": 0}
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
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").\
                where({"task_id": task_id}).set(data).update()
        except Exception as e:
            logger.error(str(e))
        finally:
            db.close()

    def duplicate_clean_start(self):
        self.stat_time = str(int(time.time()))
        try:
            db = dbControl(POOL)
            sched_policy = db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_policy_manager").\
                select("*", final="dict")
        except Exception as e:
            logger.error(str(e))
            sys.stdout.write(str(e))
        else:
            self.before_db_backup_status_add()
            context = ""
            sshObj = ""
            if not sched_policy:
                data = {"message": "未发现定时任务调度的任务!", "task_status": 1}
            else:
                for j in sched_policy:
                    self.source_addr = j.get("source_addr", '')
                    self.cmdb_host_info = self.__get_cmdb_host_info()
                    backup_to_local_path = j.get("backup_to_local_path", '')
                    duplicate = int(j.get("copy_count", 20))
                    try:
                        sshObj = self.__get_sshConn()
                        result = sshObj.exeCommand("ls -t %s" % backup_to_local_path)["stdout"].decode(
                            encoding="utf-8").strip().splitlines()
                        delete_duplicate = result[duplicate::]
                    except Exception as e:
                        sys.stdout.write(str(e))
                        msg = "主机%s 清理副本失败! err: %s\n" % (self.source_addr, str(e))
                        context += msg
                    else:
                        if not delete_duplicate:
                            msg = "主机%s 副本数量未达到阈值!\n" %self.source_addr
                            context += msg
                        else:
                            msg = "主机:%s 清理副本:\n" % (self.source_addr)
                            for k in delete_duplicate:
                                cmd = "cd %s; rm -rf %s" % (backup_to_local_path, k)
                                sshObj.exeCommand(cmd)
                                t = "%s\n" % (os.path.join(backup_to_local_path, k))
                                msg += t
                            context += msg
                    finally:
                        if hasattr(sshObj, "close"):
                            sshObj.close()
                print(context)
                data = {"message": pymysql.escape_string(context), "task_status": 1}
            self.after_db_backup_status_update(data)
        finally:
            db.close()


        # timestamp = ControlTime.date_today(_format="%Y%m%d%H%M%S")[0]
        # backup_to_local_path = os.path.join(backup_to_local_path, timestamp)
        # self.before_db_backup_status_add(backup_to_local_path)
        # sshObj = ""
        # try:
        #     sshObj = self.__get_sshConn()
        # except Exception as e:
        #    pass
        # else:
        #    pass
        # finally:
        #     if hasattr(sshObj, "close"):
        #         sshObj.close()


if __name__ == "__main__":
    x = duplicate_claen_tools("1000", "2000")
    x.duplicate_clean_start()


