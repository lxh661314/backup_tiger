from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View
import json, time
from django.conf import settings
from django.http import QueryDict
import traceback
PROJ_LIB_DIR = settings.PROJ_LIB_DIR
PROJ_DB_CONFIG = settings.PROJ_DB_CONFIG
import sys
sys.path.insert(0, PROJ_LIB_DIR)
from util import *
from sshConn import *
from backup_agent_install import *
from db_backup_tools import *
import pymysql
from backupPlatform.task import celery_database_full_backup, celery_filesystem_agent_install,  celery_filesystem_full_backup


def api_test(request):
    return HttpResponse("API OK!")


class backup_host_manager(View):
    def get(self, request):
        result = {}
        db = request.META.get("db")
        svc_type = request.GET.get("svc_type", '')
        try:
            if not svc_type:
                context = db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_host_manager"). \
                order(order=["stat_time"]).select('*', final="dict")
            else:
                context = db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_host_manager"). \
                    order(order=["stat_time"]).where({"svc_type": "%s;all"%svc_type}).select('*', final="dict")
        except Exception as e:
            result["code"] = 404
            result["message"] = "数据库查询失败! err: %s"%(str(e))
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = context
            return HttpResponse(status=200, content=json.dumps(result))

    def post(self, request):
        result = {}
        db = request.META.get("db")
        stat_time = int(time.time())
        createor = request.session.get("um_account", 'unknown').strip()
        source_addr = request.POST.get("source_addr", '').strip()
        svc_type = request.POST.get("svc_type", '').strip()
        # storage_source = request.POST.get('storage_source', '').strip()
        db_user = request.POST.get("db_user", '').strip()
        db_passwd = request.POST.get("db_passwd", '').strip()
        db_port = request.POST.get("db_port", 3306)
        db_conf = request.POST.get("db_conf", "/etc/my.cnf").strip()

        if svc_type == "fs":
            if any([not source_addr]):
                result["code"] = 404
                reuslt["message"] = "缺少必要的信息!"
                return HttpResponse(status=404, content=json.dumps(result))
        elif svc_type == 'db' or svc_type == "all":
            if any([not source_addr, not db_user, not db_passwd, not db_port, not db_conf]):
                result["code"] = 404
                result["message"] = "缺少必要的信息!"
                return HttpResponse(status=404, content=json.dumps(result))

        try:
            context = db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_host_information").\
                where({"source_addr": source_addr}).select("*")
            if not context:
                result["code"] = 404
                result["message"] = '主机%s账号密码未托管!'%source_addr
                return HttpResponse(status=404, content=json.dumps(result))
        except Exception as e:
            result["code"] = 404
            result["message"] = "数据库查询失败! err: %s"%(str(e))
            return HttpResponse(status=404, content=json.dumps(result))

        host_manager_info = {
            "source_addr": source_addr, "svc_type": svc_type, "stat_time": stat_time, "createor": createor,
            "db_user": db_user, "db_passwd": db_passwd, "db_conf": db_conf,
            "db_port": db_port}

        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_host_manager").add([host_manager_info])
        except Exception as e:
            result["code"] = 404
            result["message"] = "添加备份源主机信息失败! err: %s" %(str(e))
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = "备份源主机%s添加成功!"%source_addr
            return HttpResponse(json.dumps(result))

    def delete(self, request):
        result = {}
        httpDel = QueryDict(request.body)
        source_addr = httpDel.get("source_addr", '').strip()
        db = request.META.get("db")

        try:
            has_fs_bk_task = db.select_database(PROJ_DB_CONFIG["database"]).select_table(
                "filesystem_backup_task").where({"source_addr": source_addr}).select('*')
            has_db_bk_task = db.select_database(PROJ_DB_CONFIG["database"]).select_table(
                "database_backup_task").where({"source_addr": source_addr}).select('*')
            # print(has_db_bk_task)
            # print(has_fs_bk_task)
            if any([has_db_bk_task, has_fs_bk_task]):
                result["code"] = 404
                result["message"] = u'备份源主机%s中存在托管的备份任务, 无法删除!' %source_addr
                return HttpResponse(status=404, content=json.dumps(result))
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))


        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_host_manager").where(
            {"source_addr": source_addr}).delete()
        except Exception as e:
            result["code"] = 404
            result["message"] = u"%s备份源主机删除失败! err:%s"%(source_addr, str(e))
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = u"%s备份源主机删除成功!" %source_addr
            return HttpResponse(status=200, content=json.dumps(result))

    def put(self, request):
        """
        部署备份代理agent
        """

        result = {}
        httpPut = QueryDict(request.body)
        source_addr = httpPut.get('source_addr', '').strip()
        svc_type = httpPut.get("svc_type", '').strip()
        db = request.META.get("db")
        createor = request.session.get("um_account", 'unknown')
        cmdb_host_info = select_database_info(db, PROJ_DB_CONFIG["database"],
                                              "cmdb_host_information", source_addr=source_addr)
        if not cmdb_host_info:
            result["code"] = 404
            result["message"] = "%s主机信息没找到!" % source_addr
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            stat_time = int(time.time())
            r = celery_filesystem_agent_install.delay(cmdb_host_info=cmdb_host_info, svc_type=svc_type)
            t_id = r.id
            data = {"stat_time": stat_time, "task_id": t_id, "source_addr": source_addr,
                    "svc_type": "agent_install", "createor": createor,
                    "task_status": 0}
            try:
                db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").add([data])
            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                result["code"] = 200
                result["message"] = u"备份源主机%s备份类型%s代理安装已发送至后台执行!" % (source_addr, svc_type)
                return HttpResponse(json.dumps(result))


class backup_database_manager(View):
    def get(self, request):
        result = {}
        db = request.META.get("db")
        source_addr = request.GET.get("source_addr", '')
        try:
            if not source_addr:
                msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("database_backup_task"). \
                    order(order=["stat_time"]).select("*", final="dict")
            else:
                msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("database_backup_task").\
                    where({"source_addr": source_addr}).order(order=["stat_time"]).select("*", final="dict")
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = msg
            return HttpResponse(status=200, content=json.dumps(result))

    def post(self, request):
        result = {}
        db = request.META.get("db")
        stat_time = int(time.time())
        source_addr = request.POST.get("source_addr", '').strip()
        backup_to_local_path = request.POST.get("backup_to_local_path", '').strip()
        createor = request.session.get("um_account", 'unknown')


        try:
            db_bk_task = db.select_database(PROJ_DB_CONFIG["database"]).select_table("database_backup_task").\
                where({"source_addr": source_addr, "backup_to_local_path": os.path.join(backup_to_local_path, 'backup_mysql')}).select("*")
            if db_bk_task:
                result["code"] = 404
                result["message"] = "主机%s数据库备份任务%s已存在!"%(source_addr, backup_to_local_path)
                return HttpResponse(status=404, content=json.dumps(result))
        except Exception as e:
            result['code'] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))


        db_backup_info = {
            "stat_time": stat_time, "source_addr": source_addr, "createor": createor,
            "backup_to_local_path": os.path.join(backup_to_local_path, 'backup_mysql')
        }
        print(db_backup_info)
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("database_backup_task").add([db_backup_info])
        except Exception as e:
            result["message"] = str(e)
            result["code"] = 404
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = "主机%s数据库备份任务添加成功!"%source_addr
            return HttpResponse(json.dumps(result))

    def delete(self, request):
        result = {}
        httpDel = QueryDict(request.body)
        source_addr = httpDel.get("source_addr")
        backup_to_local_path = httpDel.get("backup_to_local_path")
        db = request.META.get("db")
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("database_backup_task").where(
            {"source_addr": source_addr, "backup_to_local_path": backup_to_local_path}).delete()
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = u"数据库备份源主机%s删除成功!" %source_addr
            return HttpResponse(status=200, content=json.dumps(result))

    def put(self, request):
        """
        开始备份
        """
        result = {}
        httpPut = QueryDict(request.body)
        source_addr = httpPut.get('source_addr', '').strip()
        backup_to_local_path = httpPut.get('backup_to_local_path', '').strip()
        createor = request.session.get("um_account", "unknown")
        db = request.META.get("db")
        cmdb_host_info = select_database_info(db, PROJ_DB_CONFIG["database"],
                                              "cmdb_host_information", source_addr=source_addr)

        db_conn_info = select_database_info(db, PROJ_DB_CONFIG["database"],
                                            "backup_host_manager", source_addr=source_addr
                                            )
        # print(cmdb_host_info)
        # print(db_conn_info)
        if not cmdb_host_info:
            result["code"] = 404
            result["message"] = "%s主机信息没找到!" % source_addr
            return HttpResponse(status=404, content=json.dumps(result))

        if not db_conn_info:
            result["code"] = 404
            result["message"] = "%s主机数据库连接信息未找到!"%source_addr
            return HttpResponse(status=404, content=json.dumps(result))

        today = ControlTime.date_today(_format="%Y%m%d%H%M%S")
        timestamp = today[0]
        stat_time = today[1]
        t = celery_database_full_backup.delay(cmdb_host_info=cmdb_host_info, db_conn_info=db_conn_info, backup_to_local_path=backup_to_local_path, timestamp=timestamp)
        t_id = t.id
        data = {"stat_time": stat_time, "task_id": t_id, "source_addr": source_addr,
                "svc_type": "db", "backup_to_local_path": os.path.join(backup_to_local_path, timestamp), "backup_path": "", "createor": createor,
                "task_status": 0}
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").add([data])
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = "数据库备份任务已发送到后台异步执行!"
            return HttpResponse(json.dumps(result))


class backup_fs_manager(View):
    def get(self, request):
        result = {}
        db = request.META.get("db")
        source_addr = request.GET.get("source_addr", '').strip()
        backup_path = request.GET.get("backup_path", '').strip()
        try:
            if any([source_addr, backup_path]):
                msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("filesystem_backup_task").where({"source_addr": source_addr, "backup_path": backup_path}).\
                    order(order=["stat_time"]).select("*", final="dict")
            else:
                msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("filesystem_backup_task"). \
                        order(order=["stat_time"]).select("*", final="dict")

        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = msg
            return HttpResponse(status=200, content=json.dumps(result))

    def post(self, request):
        result = {}
        db = request.META.get("db")
        stat_time = int(time.time())
        source_addr = request.POST.get("source_addr", '').strip()
        backup_to_local_path = request.POST.get("backup_to_local_path", '').strip()
        backup_path = request.POST.get("backup_path", '').strip()
        backup_method = request.POST.get("backup_method", '').strip()
        createor = request.session.get("um_account", 'unknown')
        print(backup_to_local_path)
        backup_to_local_path = os.path.join(os.path.join(os.path.join(backup_to_local_path, 'backup_filesystem'), source_addr), backup_path.lstrip('/'))
        print(backup_to_local_path)

        db_backup_info = {
            "stat_time": stat_time, "source_addr": source_addr, "createor": createor,
            "backup_to_local_path": backup_to_local_path,
            "backup_path": backup_path, "backup_method": backup_method,
        }
        print(db_backup_info)
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("filesystem_backup_task").\
                add([db_backup_info])
        except Exception as e:
            result["message"] = str(e)
            result["code"] = 404
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = "主机%s文件系统备份任务%s添加成功!" %(source_addr, backup_path)
            return HttpResponse(json.dumps(result))

    def delete(self, request):
        result = {}
        httpDel = QueryDict(request.body)
        source_addr = httpDel.get("source_addr", '').strip()
        backup_path = httpDel.get("backup_path", '').strip()
        db = request.META.get("db")

        try:
            res = db.select_database(PROJ_DB_CONFIG["database"]).select_table("filesystem_backup_task").\
                where({"source_addr": source_addr,"backup_path": backup_path}).select('backup_status', final="dict")

            if not res:
                result["code"] = 404
                result["message"] = "主机%s备份任务%s不存在!"%(source_addr, backup_path)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                backup_status = res[0].get("backup_status")
                if backup_status == 1:
                    result["code"] = 404
                    result["message"] = "任务删除前需先将备份任务关闭!"
                    return HttpResponse(status=404, content=json.dumps(result))
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            try:
                db.select_database(PROJ_DB_CONFIG["database"]).select_table("filesystem_backup_task").where(
                    {"source_addr": source_addr, "backup_path": backup_path}).delete()
            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                result["code"] = 200
                result['message'] = u'主机%s备份任务%s删除成功!'%(source_addr, backup_path)
                return HttpResponse(content=json.dumps(result))

    def put(self, request):
        result = {}
        httpPut = QueryDict(request.body)
        source_addr = httpPut.get('source_addr', '').strip()
        backup_path = httpPut.get("backup_path", '').strip()
        backup_to_local_path = httpPut.get('backup_to_local_path', '').strip()
        action = httpPut.get('action', '').strip()
        db = request.META.get("db")
        createor = request.session.get("um_account", 'unknown')
        cmdb_host_info = select_database_info(db, PROJ_DB_CONFIG["database"],
                                              "cmdb_host_information", source_addr=source_addr)
        print(cmdb_host_info)

        if not cmdb_host_info:
            result["code"] = 404
            result["message"] = "%s主机信息没找到!" % source_addr
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            r = celery_filesystem_full_backup.delay(cmdb_host_info=cmdb_host_info, backup_path=backup_path,
                                                    backup_to_local_path=backup_to_local_path, action=action)
            t_id = r.id
            stat_time = int(time.time())
            try:
                if action == "fs_full_backup":
                    try:
                        res = db.select_database(PROJ_DB_CONFIG["database"]).select_table(
                            "filesystem_backup_task"
                        ).where({
                            "source_addr": source_addr,
                            "backup_path": backup_path,
                            "backup_to_local_path": backup_to_local_path,
                            "backup_status": 1
                        }).select("*")
                        if not res:
                            result["code"] = 404
                            result["message"] = "全量备份之前请先将备份任务启动!"
                            return HttpResponse(status=404, content=json.dumps(result))
                    except Exception as e:
                        result["code"] = 404
                        result["message"] = str(e)
                        return HttpResponse(status=404, content=json.dumps(result))
                    else:
                        data = {"stat_time": stat_time, "task_id": t_id, "source_addr": source_addr, "svc_type": action,
                                "backup_path": "", "backup_to_local_path": "", "task_status": 0, "createor": createor}
                        db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").add([data])

                else:
                    data = {"stat_time": stat_time, "task_id": t_id, "source_addr": source_addr, "svc_type": action,
                        "backup_path": backup_path, "backup_to_local_path": backup_to_local_path, "task_status": 0,
                        "createor": createor}
                    db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").add([data])

            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                result["code"] = 200
                result["message"] = "文件系统备份任务已发送至后台执行!"
                return HttpResponse(json.dumps(result))


class backup_history_list(View):
    def get(self, request):
        result = {}
        db = request.META.get("db")
        now_page = int(request.GET.get("now_page", 1))
        t_id = request.GET.get("t_id", '').strip()
        action = request.GET.get("action", "").strip()

        if action == "calc_sum":
            try:
                res = db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").\
                    select("count(*)")
            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                result["code"] = 200
                result["message"] = 0 if not res else res[0][0]
                return HttpResponse(json.dumps(result))

        try:
            if t_id:
                res = db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").order(order=["stat_time"]).where({"task_id": t_id}).select("message", final="dict")
            else:
                res = db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_task_history").limit(start=(now_page-1)*20, limit=20).order(order=["stat_time"]).\
                        select(["stat_time", "task_id", "source_addr", "svc_type", "backup_path", "backup_to_local_path", "task_status", "createor"], final="dict")

        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))

        else:
            result["code"] = 200
            result["message"] = res
            return HttpResponse(json.dumps(result))


class backup_policy_manager(View):
    def get(self, request):
        result = {}
        db = request.META.get("db")
        try:
            msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_policy_manager").\
                order(order=["stat_time"]).select("*", final="dict")
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = msg
            return HttpResponse(json.dumps(result))

    def post(self, request):
        result = {}
        db = request.META.get("db")
        source_addr = request.POST.get("source_addr", '')
        svc_type = request.POST.get("svc_type", '')
        backup_to_local_path = request.POST.get("backup_to_local_path", '')
        backup_path = request.POST.get("backup_path", '')
        day_of_week = request.POST.get("day_of_week", '')
        copy_count = request.POST.get("copy_count", '')
        backup_times = request.POST.get("backup_times", json.dumps({}))
        print(source_addr, svc_type, backup_to_local_path, day_of_week, copy_count, backup_times)
        stat_time = int(time.time())
        createor = request.session.get("um_account", "unknown")

        if svc_type == "fs":
            backup_to_local_path = list(backup_path.partition(source_addr))
            backup_to_local_path[1] = os.path.join(backup_to_local_path[1], 'filesystem_full_backup')
            backup_to_local_path = ''.join(backup_to_local_path)


        p_id = create_jid()
        data = {"source_addr": source_addr, "stat_time": stat_time, "svc_type": svc_type,
             "backup_path": backup_path, "backup_to_local_path": backup_to_local_path, 'createor': createor,
             "copy_count": copy_count, "p_id": p_id
             }

        tasks = []
        backup_times_json = json.loads(backup_times)
        for j in backup_times_json:
            t_id = create_jid()
            t = {"p_id": p_id, "t_id": t_id, "day_of_week": day_of_week,
                 "sched_hour": j["hour"], "sched_minute": j["minute"], "backup_path": backup_path,
                 "backup_to_local_path": backup_to_local_path, "svc_type": svc_type, "source_addr": source_addr}
            tasks.append(t)

        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_sched_task_manager").add(tasks)
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))


        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_policy_manager").add([data])
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = "任务定时备份策略添加成功!"
            return HttpResponse(json.dumps(result))

    def delete(self, request):
        result = {}
        db = request.META.get("db")
        httpDel = QueryDict(request.body)
        p_id = httpDel.get("p_id", '')
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_policy_manager").\
                where({"p_id": p_id}).delete()
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            try:
                db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_sched_task_manager").\
                    where({"p_id": p_id}).delete()
            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                result['code'] = 200
                result["message"] = "策略ID:%s 删除成功!"%p_id
                return HttpResponse(json.dumps(result))


class backup_policy_sched_manager(View):
    def get(self, request):
        result = {}
        db = request.META.get("db")
        p_id = request.GET.get("p_id", '')
        try:
            msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_sched_task_manager").\
                    where({"p_id": p_id}).select("*", final="dict")
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = msg
            return HttpResponse(json.dumps(result))


    def delete(self, request):
        result = {}
        db = request.META.get("db")
        httpDel = QueryDict(request.body)
        t_id = httpDel.get("t_id", '')
        p_id = httpDel.get('p_id', '')
        try:
            task_info = db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_sched_task_manager"). \
                            where({"p_id": p_id}).select("*")

            if len(task_info) == 1:
                db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_policy_manager"). \
                    where({"p_id": p_id}).delete()

            db.select_database(PROJ_DB_CONFIG["database"]).select_table("backup_sched_task_manager").\
                where({"t_id": t_id, "p_id": p_id}).delete()
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = "任务ID:%s删除成功!"%t_id
            return HttpResponse(json.dumps(result))




# Create your views here.
