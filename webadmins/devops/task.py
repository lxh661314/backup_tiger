import os, sys
from django.conf import settings
import time
PROJ_LIB_DIR = settings.PROJ_LIB_DIR
sys.path.insert(0, PROJ_LIB_DIR)
from sshConn import *
from db_backup_tools import *
from dbControl import *
app = settings.CELERY
logger = settings.LOGGER
PROJ_DB_CONFIG = settings.PROJ_DB_CONFIG
POOL = settings.POOL
db = dbControl(POOL)



class celery_ssh_check_task(app.Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('{0!r} failed: {1!r}'.format(task_id, exc))
        print(args,  'args')
        print(kwargs, 'kwargs')
        print(einfo, 'einfo')
    #

    def on_success(self, retval, task_id, args, kwargs):
        print(retval, 'retval')
        print(task_id, 'taskid')
        print(args, 'args')
        print(kwargs, 'kwargs')


@app.task(base=celery_ssh_check_task)
def celery_ssh_connect_check(cmdb_host_info):
    sshObj = ' '
    try:
        sshObj = controlHost(cmdb_host_info["source_addr"], cmdb_host_info["host_user"],
                         cmdb_host_info["host_passwd"], cmdb_host_info["host_port"])
    except:
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_host_information"). \
                where({"source_addr": cmdb_host_info["source_addr"]}).set({"ssh_conn": 0}).update()
        except Exception as e:
            logger.warn("修改主机%sSSH连接状态为0失败! err:%s"%(cmdb_host_info["source_addr"], str(e)))
        else:
            logger.info("修改主机%sSSH连接状态为0成功!"%cmdb_host_info["source_addr"])
    else:
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_host_information").\
                where({"source_addr": cmdb_host_info["source_addr"]}).set({"ssh_conn": 1}).update()
        except Exception as e:
            logger.warn("修改主机%sSSH连接状态为1失败! err:%s"%(cmdb_host_info["source_addr"], str(e)))
        else:
            logger.info("修改主机%sSSH连接状态为1成功!"%cmdb_host_info["source_addr"])
    finally:
        if hasattr(sshObj, "close"):
            sshObj.close()
