from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
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


def login_home_page(request):
    if request.method == "GET":
        return HttpResponseRedirect("/static/login.html")


def account_login(request):
    if request.method == "POST":
        result = {}
        db = request.META.get("db")
        um_account = request.POST.get("um_account", '').strip()
        um_passwd = request.POST.get('um_passwd', '').strip()
        if not um_account or not um_passwd:
            result["code"] = 404
            result["message"] = u"缺少必须填写的登录信息!"
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            try:
                user_info = db.select_database(PROJ_DB_CONFIG["database"]).select_table("account_user").\
                    where({"um_account": um_account , "um_passwd": um_passwd, "account_status": 1}).select("*", final="dict")
            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                if not user_info:
                    result["code"] = 404
                    result["message"] = u"账号或密码不存在或账号已被禁用!"
                    return HttpResponse(status=404, content=json.dumps(result))
                else:
                    request.session["um_account"] = um_account
                    print(request.session.get("um_account"), 'dfdf')
                    request.session["last_login_time"] = user_info[0].get("last_login_time", 'error')
                    stat_time = int(time.time())
                    try:
                        db.select_database(PROJ_DB_CONFIG["database"]).select_table("account_user").where(
                            {"um_account": um_account}).set({"last_login_time": stat_time}).select("*")
                    except Exception as e:
                        result["code"] = 404
                        result["message"] = str(e)
                        return HttpResponse(status=404, content=json.dumps(result))
                    else:
                        result["code"] = 200
                        result["message"] = "登录成功!"
                        resp = HttpResponse(json.dumps(result))
                        resp.set_cookie('login', 'true')
                        return resp


def account_logout(request):
    result = {}
    um_account = request.session.get("um_account", '')
    try:
        del request.session["um_account"]
    except:
        pass
    finally:
        result["code"] = 200
        result["message"] = um_account
        resp = HttpResponse(json.dumps(result))
        resp.set_cookie("login", 'false')
        return resp


class account_login_info(View):
    def get(self, request):
        result = {}
        um_account = request.GET.get("um_account", "").strip()
        db = request.META.get("db")
        try:
            if not um_account:
                msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("account_user").\
                    select('*', final="dict")
            else:
                msg = db.select_database(PROJ_DB_CONFIG["database"]).select_table("account_user").\
                           where({"um_account": um_account}).select('*', final="dict")
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            request.session["account_login_info"] = msg[0]
            result["code"] = 200
            result["message"] = msg
            return HttpResponse(json.dumps(result))

    def post(self, request):
        result = {}
        db = request.META.get("db")
        um_account = request.POST.get("um_account", "").strip()
        um_passwd = request.POST.get("um_passwd", "").strip()
        create_time = int(time.time())
        um_role = request.POST.get("um_role", '').strip()
        mobile = request.POST.get("mobile", '').strip()
        e_mail = request.POST.get("e_mail", '').strip()
        context = request.POST.get("context", '').strip()
        try:
            um_exist = db.select_database(PROJ_DB_CONFIG["database"]).select_table("account_user").\
                where({"um_account": um_account}).select("*")
            if um_exist:
                result["code"] = 404
                result["message"] = "账号:%s 已存在!" %um_account
                return HttpResponse(status=404, content=json.dumps(result))
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            data = {
                "um_account": um_account, "um_passwd": um_passwd, "create_time": create_time,
                "um_role": um_role, "mobile": mobile, "e_mail": e_mail, "context": context
            }
            try:
                db.select_database(PROJ_DB_CONFIG["database"]).select_table("account_user").add([data])
            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                result["code"] = 200
                result["message"] = "账号:%s创建成功!"%(um_account)
                return HttpResponse(json.dumps(result))

    def put(self, request):
        result = {}
        httpPut = QueryDict(request.body)
        db = request.META.get("db")
        um_account = httpPut.get("um_account", '').strip()
        action = httpPut.get('action', '').strip()
        if action == "start":
            data = {"account_status": 1}
            alert_msg = u"启动"
        elif action == "stop":
            data = {"account_status": 0}
            alert_msg = u"禁用"
        else:
            data = {}
            alert_msg = u"未知"
        try:
            db.select_database(PROJ_DB_CONFIG["database"]).select_table("account_user").\
                where({"um_account": um_account}).set(data).update()
        except Exception as e:
            result["code"] = 404
            result["message"] = str(e)
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            result["code"] = 200
            result["message"] = "账号:%s%s"%(um_account, alert_msg)
            return HttpResponse(json.dumps(result))

    def delete(self, request):
        result = {}
        httpDel = QueryDict(request.body)
        db = request.META.get("db")
        um_account = httpDel.get("um_account", '').strip()
        if um_account == "admin":
            result["code"] = 404
            result["message"] = "Admin超级管理员账号不可删除!"
            return HttpResponse(status=404, content=json.dumps(result))
        else:
            try:
                db.select_database(PROJ_DB_CONFIG["database"]).select_table("account_user").\
                    where({"um_account": um_account}).delete()
            except Exception as e:
                result["code"] = 404
                result["message"] = str(e)
                return HttpResponse(status=404, content=json.dumps(result))
            else:
                result["code"] = 200
                result["message"] = "账号:%s 删除成功!"%(um_account)
                return HttpResponse(json.dumps(result))

class account_current_user(View):
    def get(self, request):
        result = {}
        um_account = request.session.get("um_account", 'unknown')
        result["code"] = 200
        result["message"] = um_account
        return HttpResponse(json.dumps(result))





# Create your views here.
