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
from mnt_nfs import *
from devops.task import celery_ssh_connect_check


class cmdb_host_information(View):

    def get(self, request):
        """
        获取所有主机的账号密码信息
        """
        result = {}
        db = request.META.get("db")
        source_addr = request.GET.get("source_addr", '')
        try:
            if source_addr:
                msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_host_information").\
                    where({"source_addr": source_addr}).order(order=["stat_time"]).select('*')
            else:
                msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_host_information").\
                    order(order=["stat_time"]).select('*', final="dict")
            result["code"] = 200
            result["message"] = msg
            return HttpResponse(status=200, content=json.dumps(result))
        except Exception as e:
            result["code"] = 404
            result["message"] = u'获取主机%s账号密码信息失败! err: %s' %(source_addr, str(e))
            return HttpResponse(status=404, content=json.dumps(result))

    def post(self, request):
        """
        添加主机账号密码信息
        """
        result = {}
        db = request.META.get("db")
        stat_time = int(time.time())
        source_addr = request.POST.get("source_addr", '').strip()
        host_user = request.POST.get("host_user", '').strip()
        host_passwd = request.POST.get("host_passwd", '').strip()
        host_port = request.POST.get("host_port", 22)
        createor = request.session.get("um_account", 'unknown')
        action = request.POST.get("action", '').strip()

        if any([not source_addr, not host_user, not host_passwd]):
            result["code"] = 404
            result["message"] = u"请求缺少必要的参数!"
            return HttpResponse(status=404, content=json.dumps(result))


        if action == "edit":
            try:
                db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_host_information").\
                    where({"source_addr": source_addr, "host_user": host_user}).set({"host_passwd": host_passwd}).update()
            except Exception as e:
                result["code"] = 404
                result["message"] = u"修改主机%s失败! err: %s" % (source_addr, str(e))
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                result["code"] = 200
                result["message"] = u"%s主机信息修改成功!" % source_addr
                return HttpResponse(status=200, content=json.dumps(result))



        cmdb_host_info = select_database_info(db, PROJ_DB_CONFIG["database"],
                                              "cmdb_host_information",
                                              source_addr=source_addr)
        if not cmdb_host_info:
            try:
                host_information = {"stat_time": stat_time, "host_user": host_user, "host_passwd": host_passwd,
                                    "host_port": host_port, "source_addr": source_addr, "createor": createor
                                    }
                db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_host_information").\
                    add([host_information])
            except Exception as e:
                result["code"] = 404
                result["message"] = u"添加主机%s失败! err: %s"%(source_addr, str(e))
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                result["code"] = 200
                result["message"] = u"%s主机信息添加成功!" %source_addr
                return HttpResponse(status=200, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = u"主机%s已经存在!"%source_addr
            return HttpResponse(content=json.dumps(result))

    def put(self, request):
        """
        检查ssh连通性
        """
        result = {}
        httpPut = QueryDict(request.body)
        host_id = httpPut.get('host_id', '').strip()
        db = request.META.get("db")
        cmdb_host_info = select_database_info(db, PROJ_DB_CONFIG["database"],
                                              "cmdb_host_information", id=host_id)
        if not cmdb_host_info:
            result["code"] = 404
            result["message"] = "主机ID:%s信息没找到!"%host_id
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            celery_ssh_connect_check.delay(cmdb_host_info=cmdb_host_info)
            result["code"] = 200
            result["message"] = "主机%sSSH连通性检查任务已发送至后台异步执行!"%cmdb_host_info["source_addr"]
            return HttpResponse(json.dumps(result))

    def delete(self, request):
        """
        删除主机信息
        """
        result = {}
        httpDel = QueryDict(request.body)
        host_id = httpDel.get("host_id", '').strip()
        source_addr = httpDel.get("source_addr", '').strip()
        db = request.META.get("db")

        backup_host_manager = select_database_info(db, PROJ_DB_CONFIG["database"],
                                                   "backup_host_manager", source_addr=source_addr
                                                   )
        print(backup_host_manager)

        if backup_host_manager:
            result["code"] = 404
            result['message'] = "删除主机之前请确保其没有任何备份任务在运行!"
            return HttpResponse(status=404, content=json.dumps(result))

        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_host_information").\
                where({"id": host_id}).delete()
        except Exception as e:
            result["code"] = 404
            result["message"] = u'删除主机ID:%s信息失败! err: %s' %(host_id, str(e))
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = u"删除主机ID:%s成功!" %host_id
            return HttpResponse(status=200, content=json.dumps(result))


class cmdb_storage_information(View):
    def get(self, request):
        result = {}
        db = request.META.get("db")
        source_addr = request.GET.get("source_addr", '')
        try:
            if source_addr:
                msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_storage_information"). \
                    where({"mount_addr": source_addr}).order(order=["stat_time"]).select('*', final="dict")
            else:
                msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_storage_information").\
                    order(order=["stat_time"]).select('*', final="dict")
        except Exception as e:
            result["code"] = 404
            result["message"] =u'获取NFS共享存储信息失败! err: %s'%(str(e))
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = msg
            return HttpResponse(status=200, content=json.dumps(result))

    def post(self, request):
        result = {}
        db = request.META.get("db")
        stat_time = int(time.time())
        source_addr = request.POST.get("source_addr", '')
        storage_mount_path = request.POST.get("storage_mount_path", '')
        mount_addr = request.POST.get("mount_addr", '').strip()
        createor =request.session.get("um_account", 'unknown')

        if mount_addr != "127.0.0.1":
            try:
                local_mount = select_database_info(db, PROJ_DB_CONFIG["database"], "cmdb_storage_information",
                                                source_addr=source_addr, storage_mount_path=storage_mount_path,
                                                mount_addr="127.0.0.1")
            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                if not local_mount:
                    result["code"] = 404
                    result["message"] = u"存储挂载至远程主机之前需先将其挂载至备份平台!"
                    return HttpResponse(status=404, content=json.dumps(result))



        if any([not source_addr, not storage_mount_path, not mount_addr]):
            result["code"] = 404
            result["message"] = u'缺少必要的参数!'
            return HttpResponse(status=404, content=json.dumps(result))

        try:
            mount_info = db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_storage_information").\
                where({"source_addr": source_addr, "storage_mount_path": storage_mount_path, "mount_addr": mount_addr}).select('*')
        except Exception as e:
            result["code"] = 404
            result["message"] = u"数据库查询失败! err: %s"%(str(e))
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            if mount_info:
                result["code"] = 404
                result["message"] = u"存储服务器%s共享目录%s已挂载至主机%s!"%(source_addr, storage_mount_path, mount_addr)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                if mount_addr == "127.0.0.1":
                    mnt_nfs = local_nfs_mount(source_addr, storage_mount_path)
                else:
                    mnt_nfs = remote_nfs_mount(source_addr, storage_mount_path)
                    
                storage_information = {"stat_time": stat_time, "source_addr": source_addr,
                                       "storage_mount_path": storage_mount_path, "createor": createor,
                                       "local_path": mnt_nfs.local_path, "storage_status": 0, "mount_addr": mount_addr
                                       }
                try:
                    db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_storage_information"). \
                        add([storage_information])
                except Exception as e:
                    result["code"] = 404
                    result["mesage"] = u'NFS服务区%s共享存储%s信息添加失败! err: %s'%(source_addr, storage_mount_path, str(e))
                    return HttpResponse(status=404, content=json.dumps(result))
                else:
                    result["code"] = 200
                    result["message"] = u"NFS服务器%s共享存储%s添加成功!" %(source_addr, storage_mount_path)
                    return HttpResponse(status=200, content=json.dumps(result))

    def put(self, request):
        """
        获取每个共享存储的磁盘空间大小
        """
        result = {}
        httpPut = QueryDict(request.body)
        source_addr = httpPut.get("source_addr", '').strip()
        storage_mount_path = httpPut.get("storage_mount_path", '').strip()
        local_path = httpPut.get("local_path", '').strip()
        mount_addr = httpPut.get("mount_addr", '').strip()
        action = httpPut.get("action", '').strip()
        db = request.META.get("db")
        print(source_addr, storage_mount_path, local_path, mount_addr, action, 'dfsdf')
        if action == 'storage_mount':
            try:
                if mount_addr == '127.0.0.1':
                    print('sdfsdfwww')
                    mnt_nfs = local_nfs_mount(source_addr, storage_mount_path, local_path)
                else:
                    print("sdfsdf1")
                    cmdb_host_info = select_database_info(db, PROJ_DB_CONFIG["database"],
                                                          "cmdb_host_information", source_addr=mount_addr)
                    print(cmdb_host_info)
                    if not cmdb_host_info:
                        result["code"] = 404
                        result["message"] = "%s主机信息没找到!" % mount_addr
                        return HttpResponse(status=404, content=json.dumps(result))
                    else:
                        sshObj = ''
                        try:
                            sshObj = controlHost(mount_addr, cmdb_host_info["host_user"],
                                                 cmdb_host_info["host_passwd"], cmdb_host_info["host_port"],
                                                 )
                        except Exception as e:
                            result["code"] = 404
                            result["message"] = "主机%sSSH连接失败! err:%s" % (mount_addr, str(e))
                            return HttpResponse(status=404, content=json.dumps(result))
                        else:
                            mnt_nfs = remote_nfs_mount(source_addr, storage_mount_path, sshObj, local_path)

                mnt_status = mnt_nfs.mount_nfs()
            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                if mnt_status:
                    try:
                        db.select_database(PROJ_DB_CONFIG["database"]).select_table('cmdb_storage_information').\
                        set({"storage_status": 1}).where({"source_addr": source_addr, "storage_mount_path": storage_mount_path,
                                                          "local_path": local_path
                                                          }).update()
                    except Exception as e:
                        result["code"] = 404
                        result["message"] = u"在数据库中修改存储状态失败! err: %s"%(str(e))
                        return HttpResponse(status=404, content=json.dumps(result))
                    else:
                        result["code"] = 200
                        result["message"] = u"主机:%s 存储:%s 挂载成功!"%(source_addr, storage_mount_path)
                        return HttpResponse(status=200, content=json.dumps(result))
                else:
                    result["code"] = 404
                    result["message"] = u"存储挂载挂载失败, 发生未知错误详情查看项目日志!"
                    return HttpResponse(status=404, content=json.dumps(result))

        elif action == 'check_size':
            result = {}
            val = get_folder_size(local_path)
            result["storage_size"] = val[0]
            result["storage_used"] = val[1]
            try:
                db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_storage_information").\
                    where({"source_addr": source_addr,  "storage_mount_path": storage_mount_path}).\
                    set(result).update()
            except Exception as e:
                msg = u'本地路径%s容量刷新失败! err: %s\n'%(mount_path, str(e))
                result["code"] = 404
                result["message"] = msg
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                result["code"] = 200
                result["message"] = '获取共享存储%s 空间成功! total: %s, used:%s'%(storage_mount_path, val[0], val[1])
                return HttpResponse(json.dumps(result))

    def delete(self, request):
        result = {}
        db = request.META.get("db")
        httpDel = QueryDict(request.body)
        source_addr = httpDel.get("source_addr", '').strip()
        storage_mount_path = httpDel.get("storage_mount_path", '').strip()
        mount_addr = httpDel.get("mount_addr", ''.strip())
        local_path = httpDel.get("local_path", '').strip()


        try:
            has_fs_bk_task = db.select_database(PROJ_DB_CONFIG["database"]).select_table("filesystem_backup_task").where({"backup_to_local_path": local_path}, vague=['backup_to_local_path']).select('*')
            has_db_bk_task = db.select_database(PROJ_DB_CONFIG["database"]).select_table("database_backup_task").where({"backup_to_local_path": local_path}, vague=['backup_to_local_path']).select('*')
            # print(has_db_bk_task)
            # print(has_fs_bk_task)
            if any([has_db_bk_task, has_fs_bk_task]):
                result["code"] = 404
                result["message"] = u'共享存储%s正在使用中!' % local_path
                return HttpResponse(status=404, content=json.dumps(result))
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))

        if any([not source_addr, not storage_mount_path, not local_path]):
            result["code"] = 404
            result["message"] = u"缺少必要的参数!!!"
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            try:
                if mount_addr == "127.0.0.1":
                    try:
                        res = db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_storage_information").where({"source_addr": source_addr,
                                                               "storage_mount_path": storage_mount_path,
                                                               "mount_addr": mount_addr
                                                               }, unlike=["mount_addr"]).select('*')
                        if res:
                            result["code"] = 404
                            result["message"] = "删除本地挂载存储之前需先在所有远程主机上将其删除后方可执行!"
                            return HttpResponse(status=404, content=json.dumps(result))
                        else:
                            mnt_nfs = local_nfs_mount(source_addr, storage_mount_path, local_path)
                    except Exception as e:
                        result["code"] = 404
                        result["message"] = str(e)
                        return HttpResponse(status=404, content=json.dumps(result))
                else:
                    print("sdfsdf1")
                    cmdb_host_info = select_database_info(db, PROJ_DB_CONFIG["database"],
                                                          "cmdb_host_information", source_addr=mount_addr)
                    print(cmdb_host_info)
                    if not cmdb_host_info:
                        result["code"] = 404
                        result["message"] = "%s主机信息没找到!" % mount_addr
                        return HttpResponse(status=404, content=json.dumps(result))
                    else:
                        sshObj = ''
                        try:
                            sshObj = controlHost(mount_addr, cmdb_host_info["host_user"],
                                                 cmdb_host_info["host_passwd"], cmdb_host_info["host_port"],
                                                 )
                        except Exception as e:
                            result["code"] = 404
                            result["message"] = "主机%sSSH连接失败! err:%s" % (mount_addr, str(e))
                            return HttpResponse(status=404, content=json.dumps(result))
                        else:
                            mnt_nfs = remote_nfs_mount(source_addr, storage_mount_path, sshObj, local_path)

                mnt_nfs.umount_nfs()
            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                try:
                    db.select_database(PROJ_DB_CONFIG["database"]).select_table("cmdb_storage_information").\
                        where({"source_addr": source_addr, "storage_mount_path": storage_mount_path, "mount_addr": mount_addr}).delete()
                except Exception as e:
                    result["code"] = 404
                    result['message'] = u'数据库操作失败! err: %s' %(str(e))
                    return HttpResponse(status=404, content=json.dumps(result))
                else:
                    result["code"] = 200
                    result["message"] = u"主机%s共享存储存储%s删除成功!" %(source_addr, storage_mount_path)
                    return HttpResponse(status=200, content=json.dumps(result))








# Create your views here.
