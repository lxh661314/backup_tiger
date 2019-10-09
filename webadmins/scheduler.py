#coding:utf8

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import os
import traceback
import sys, subprocess
os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'webadmins.settings')
from django.conf import settings
PROJ_DB_CONFIG = settings.PROJ_DB_CONFIG
sys.path.insert(0, settings.PROJ_LIB_DIR)
from dbControl import *
from logger import log
logger = log().getLogger()
POOL = settings.POOL
import time

from abc import ABCMeta, abstractmethod
import sched_task.sched_db_backup_tasks
import sched_task.sched_fs_backup_tasks
import sched_task.sched_clean_backup_duplicate


def f1(*args, **kwargs):
    print(args)
    print(kwargs)
    print(time.time())


class abstract_schedule(metaclass=ABCMeta):

    def __init__(self):
        self.sched = BlockingScheduler()

    def lstCronJob(self, job_id=None):
        result = {}
        if not job_id:
            jobs = self.sched.get_jobs()
            for j in jobs:
                result[j.id] = j
        else:
            jobs = self.sched.get_job(job_id)
            result[job_id] = jobs
        return result

    def delCronJob(self, job_id):
        jobs = self.lstCronJob(job_id)
        if not jobs:
            sys.stdout.write("Job %s not found" %job_id)
        else:
            self.sched.remove_job(job_id)
            sys.stdout.write("Job %s 删除成功!"%job_id)
            return True

    def addCronJob(self, job_id, func, policy, args):
        cron = CronTrigger(**policy)
        self.sched.add_job(func, cron, args=args, id=job_id)

    def start(self):
        print("123123")
        self.sched.add_job(self.autoAddJob, IntervalTrigger(seconds=5), id="autoAddJob")
        self.sched.start()

    def autoAddJob(self):
        history_jobs = self.lstCronJob()
        print(history_jobs, 'history_jobs')

        current_jobs = self.getBackupPolicy()
        print(current_jobs, 'current_jobs')

        only_current_jobs = set(current_jobs.keys()).difference(set(history_jobs.keys()))
        print(only_current_jobs, 'only_current_jobs')
        # 当前任务调度列表中有的 历史任务列表中没有的

        only_history_jobs = set(history_jobs.keys()).difference(set(current_jobs.keys()))
        print(only_history_jobs, 'only_history_jobs')
        #历史任务中有的当前任务列表中没有的任务
        #
        for j in only_history_jobs:
            if j == 'autoAddJob':
                continue
            self.delCronJob(job_id=j)

        for j in only_current_jobs:
            func = current_jobs[j].pop('func')
            args = current_jobs[j].pop('args')
            policy = current_jobs[j]
            self.addCronJob(job_id=j, func=func, policy=policy, args=args)

    @abstractmethod
    def getBackupPolicy(self):
        pass


class schedule(abstract_schedule):
    def getBackupPolicy(self):
        db = dbControl(POOL)
        result = {}
        try:
            res = db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_sched_task_manager").select('*', final="dict")
        except Exception as e:
            traceback.print_exc()
            logger.warn("调取器获取任务调度策略失败! err: %s"%(str(e)))
            raise ValueError("调度器获取任务调度策略失败! err: %s"%(str(e)))
        else:
            for j in res:
                t_id = str(j.get("t_id", 0))
                p_id = str(j.get("p_id", 0))
                day_of_week = {"day_of_week": j.get("day_of_week", None)} if j.get("day_of_week", None) else {}
                hour = {"hour": j.get('sched_hour', None)} if j.get('sched_hour', None) else {}
                minute = {"minute": j.get("sched_minute", None)} if j.get("sched_minute", None) else {}

                source_addr = j.get("source_addr")
                svc_type = j.get("svc_type")
                backup_to_local_path = j.get("backup_to_local_path")
                backup_path = j.get("backup_path")

                if svc_type == "db":
                    func = sched_task.sched_db_backup_tasks.db_backup_tools(source_addr, p_id, t_id)
                    result[t_id] = {"func": func.db_backup_start, "args": [backup_to_local_path, ]}
                elif svc_type == "fs":
                    func = sched_task.sched_fs_backup_tasks.fs_backup_tools(source_addr, p_id, t_id)
                    result[t_id] = {"func": func.fs_backup_start, "args": [backup_path, backup_to_local_path]}

                if t_id == "1000000001": ##副本自动清理任务脚本
                    func = sched_task.sched_clean_backup_duplicate.duplicate_claen_tools(p_id, t_id)
                    result[t_id] = {"func": func.duplicate_clean_start, "args": []}

                result[t_id].update(day_of_week)
                result[t_id].update(hour)
                result[t_id].update(minute)
                print(result)

            return result


if __name__ == '__main__':
    s = schedule()
    s.start()