import os, sys, time
from django.conf import settings
import time
PROJ_LIB_DIR = settings.PROJ_LIB_DIR
sys.path.insert(0, PROJ_LIB_DIR)
from sshConn import *
from db_backup_tools import *
from backup_agent_install import *
from dbControl import *
from util import *
app = settings.CELERY
logger = settings.LOGGER
PROJ_DB_CONFIG = settings.PROJ_DB_CONFIG
POOL = settings.POOL

import pymysql
import traceback
from fs_backup_tools import *


class MyTask(app.Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        db = dbControl(POOL)
        # print('{0!r} failed: {1!r}'.format(task_id, exc))
        # print(args,  'args')
        # print(kwargs, 'kwargs')
        # print(einfo, 'einfo', type(einfo))
        # print(str(einfo), type(einfo))
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").set({"message": pymysql.escape_string(str(einfo))}).\
                where({"task_id": task_id}).update()
        except Exception as e:
            logger.warn(str(e))
        finally:
            db.close()

    def on_success(self, retval, task_id, args, kwargs):
        db = dbControl(POOL)
        # print(retval, 'retval')
        # print(task_id, 'taskid')
        # print(args, 'args')
        # print(kwargs, 'kwargs', type(kwargs))
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").where({"task_id": task_id}).\
                set({"task_status": 1, "message": pymysql.escape_string(str(retval)[-5000])}).update()
        except Exception as e:
            traceback.print_exc()
            logger.warn(str(e))
        finally:
            db.close()

@app.task(base=MyTask)
def celery_database_full_backup(cmdb_host_info, db_conn_info, backup_to_local_path, timestamp):
    sshObj = controlHost(cmdb_host_info["source_addr"], cmdb_host_info["host_user"],
                         cmdb_host_info["host_passwd"], cmdb_host_info["host_port"])
    db_info = {}
    db_info.update(db_conn_info)
    db_info["my_files"] = db_conn_info["db_conf"]
    db_info["db_host"] = db_conn_info["source_addr"]
    x = db_xtrabackup(sshObj, db_info)
    result = x.xtrabackup_full_backup(backup_to_local_path, timestamp)  ##此处备份失败会raise一个错误出来!
    sshObj.close()
    return result

@app.task(base=MyTask)
def celery_filesystem_agent_install(cmdb_host_info, svc_type):
    result = ''
    db = dbControl(POOL)
    sshObj = controlHost(cmdb_host_info["source_addr"], cmdb_host_info["host_user"],
                         cmdb_host_info["host_passwd"], cmdb_host_info["host_port"],
                         )
    if svc_type == 'fs':
        data = {"rsync_status": 1, "sersync_status": 1}
        fs_agent_install = backup_agent_install(sshObj)  ##celery
        x = fs_agent_install.fs_backup_agent()
        result += x["msg"]

    elif svc_type == 'db':
        data = {"xtrabackup_status": 1}
        db_agent_install = backup_agent_install(sshObj)   ##celery
        x = db_agent_install.db_backup_agent()
        result += x["msg"]

    elif svc_type == "all":
        data = {"rsync_status": 1, "sersync_status": 1, "xtrabackup_status": 1}
        fs_agent_install = backup_agent_install(sshObj)   ##celery
        x = fs_agent_install.fs_backup_agent()
        db_agent_install = backup_agent_install(sshObj)  ##celery
        y = db_agent_install.db_backup_agent()
        result += x["msg"]
        result += y["msg"]
    else:
        data = {}
    try:
        db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_host_manager").where(
            {"source_addr": cmdb_host_info["source_addr"]}).set(data).update()
    except Exception as e:
        logger.warn(str(e))
    finally:
        if hasattr(sshObj, "close"):
            sshObj.close()
    return result

@app.task(base=MyTask)
def celery_filesystem_full_backup(cmdb_host_info, backup_path, backup_to_local_path, action):
    result = ''
    db = dbControl(POOL)
    sshObj = controlHost(cmdb_host_info["source_addr"], cmdb_host_info["host_user"],
                         cmdb_host_info["host_passwd"], cmdb_host_info["host_port"],
                         )
    d = distribute_filesystem_backup(sshObj, cmdb_host_info["source_addr"], backup_path, backup_to_local_path)
    if action == "start":
        data = {"backup_status": 2}  # 修改启动状态为启动中
        db.select_database(PROJ_DB_CONFIG["database"]).select_table("filesystem_backup_task"). \
                where({"source_addr": cmdb_host_info["source_addr"], "backup_path": backup_path,
                       "backup_to_local_path": backup_to_local_path}).set(data).update()
        result = d.fs_backup_start()  # 执行celery任务
        data = {"backup_status": 1}  # 修改启动状态为已启动
        db.select_database(PROJ_DB_CONFIG["database"]).select_table("filesystem_backup_task"). \
                where({"source_addr": cmdb_host_info["source_addr"], "backup_path": backup_path,
                       "backup_to_local_path": backup_to_local_path}).set(data).update()

    elif action == "stop":
        result = d.fs_backup_stop()
        data = {"backup_status": 0}
        db.select_database(PROJ_DB_CONFIG["database"]).select_table("filesystem_backup_task"). \
                where({"source_addr": cmdb_host_info["source_addr"], "backup_path": backup_path,
                       "backup_to_local_path": backup_to_local_path}).set(data).update()

    elif action == "fs_full_backup":
        today = ControlTime.date_today(_format="%Y%m%d%H%M%S")[0]
        fs_full_backup_path = list(backup_to_local_path.partition(cmdb_host_info["source_addr"]))
        fs_full_backup_path[1] = os.path.join(fs_full_backup_path[1], 'filesystem_full_backup')
        fs_full_backup_path.append('/%s' % today)
        fs_full_backup_path = ''.join(fs_full_backup_path)
        task_id = celery_filesystem_full_backup.request.id
        db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").where({"task_id": task_id}). \
            set({"backup_path": backup_to_local_path, "backup_to_local_path": fs_full_backup_path}).update()

        result = d.fs_full_backup(backup_to_local_path, fs_full_backup_path)  ##celery

    if hasattr(sshObj, "close"):
        sshObj.close()
    return result

