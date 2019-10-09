#coding:utf8
import os, sys
from lib.util import readConfig, os_system
import subprocess
from abc import ABCMeta, abstractmethod

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_CONFIG_DIR = os.path.join(BASE_DIR, 'config')
PROJ_CONFIG_FILE = os.path.join(PROJ_CONFIG_DIR, "config.cfg")
CONFIG_OBJ = readConfig(PROJ_CONFIG_FILE)

REDIS_CONFIG = CONFIG_OBJ.read_config("redis") #{}
BASE_CONFIG = CONFIG_OBJ.read_config("base")
UWSGI_CONFIG = CONFIG_OBJ.read_config("uwsgi")
NGINX_CONFIG= CONFIG_OBJ.read_config("nginx")
CELERY_CONFIG = CONFIG_OBJ.read_config("celery")


class process_control(metaclass=ABCMeta):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def status(self):
        pass

    @abstractmethod
    def stop(self):
        pass

class nginx_process_control(process_control):
    nginx_process = os.path.join(NGINX_CONFIG["home"], 'sbin/nginx')

    def start(self):
        status, output = subprocess.getstatusoutput(self.nginx_process)
        if status != 0:
            s = 'Nginx启动失败! 进程:%s err:%s\n' % (self.nginx_process, output)
            print(s)
        else:
            s = "Nginx启动成功! 进程:%s" %self.nginx_process
            print(s)

    def stop(self):
        cmd = "kill -TERM `ps -ef | grep -v grep  | grep %s | awk -F ' ' '{print $2}' | xargs`" %self.nginx_process
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            s = 'Nginx停止失败! 进程:%s err:%s\n' % (self.nginx_process, output)
            print(s)
        else:
            s = 'Nginx停止成功! 进程:%s' %self.nginx_process
            print(s)

    def status(self):
        cmd = 'ps -ef | grep -v grep | grep %s' %self.nginx_process
        output = subprocess.getoutput(cmd)
        result = """Nginx进程如下:

        %s
        """ % output
        print(result)

class redis_process_control(process_control):
    redis_process =  os.path.join(REDIS_CONFIG["home"], 'bin/redis-server')
    def start(self):
        redis_conf = REDIS_CONFIG["config"]
        cmd = "%s %s" % (self.redis_process, redis_conf)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            s = "Redis启动失败! 进程:%s err: %s\n" %(self.redis_process, output)
            print(s)
        else:
            print('Redis启动成功! 进程:%s' %self.redis_process)


    def stop(self):
        cmd = "kill -9 `ps -ef | grep %s | grep -v grep  | awk -F ' ' '{print $2}' | xargs`" %self.redis_process
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            s = 'Redis停止失败! 进程: %s err: %s\n' %(self.redis_process, output)
            print(s)
        else:
            s = '''Redis停止成功! 进程: %s''' %self.redis_process
            print(s)

    def status(self):
        cmd = 'ps -ef | grep -v grep | grep %s' %self.redis_process
        output = subprocess.getoutput(cmd)
        result = """Redis进程如下:

        %s
        """ % output
        print(result)

class uwsgi_process_control(process_control):
    uwsgi_process =  os.path.join(BASE_CONFIG["python_home"], 'bin/uwsgi')
    uwsgi_config_file = os.path.join(PROJ_CONFIG_DIR, 'uwsgi.ini')
    uwsgi_sock = os.path.join(BASE_CONFIG["proj_home"], 'uwsgi.sock')
    uwsgi_pid =  os.path.join(BASE_CONFIG["proj_home"], 'uwsgi.pid')

    def start(self):
        pass

    def mk_uwsgi_config(self):
        try:
            uwsgi_template = os.path.join(PROJ_CONFIG_DIR, 'uwsgi.template')
            uwsgi_config_str = open(uwsgi_template).read(). \
                format(proj_home=BASE_CONFIG["proj_home"],
                       python_home=BASE_CONFIG["python_home"],
                       proj_name=BASE_CONFIG["proj_home"].split('/')[-1],
                       address=UWSGI_CONFIG["address"],
                       uwsgi_port=UWSGI_CONFIG["port"],
                       proj_log_dir=os.path.join(BASE_DIR, 'log')
                       )
        except Exception as e:
            s = "生成uwsgi配置文件失败! err: %s" % (str(e))
            print(s)
        else:
            with open(os.path.join(PROJ_CONFIG_DIR, 'uwsgi.ini'), 'w') as f:
                f.write(uwsgi_config_str)
            print("生成uwsgi配置文件成功!")

    def stop(self):
        cmd = "kill -9 `ps -ef | grep -v grep | grep %s | awk -F ' ' '{print $2}' | xargs`" %self.uwsgi_process
        #cmd = "kill -9 `ps -ef | grep -v grep | grep %s | awk -F ' ' '{print $2}' | xargs`; rm -rf %s %s" %(self.uwsgi_process, self.uwsgi_sock, self.uwsgi_pid)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            s = 'uwsgi进程停止失败! 进程:%s err:%s\n' %(self.uwsgi_process, output)
            print(s)
        else:
            cmd = 'rm -rf %s %s'%(self.uwsgi_sock, self.uwsgi_pid)
            os.system(cmd)
            s = 'uwsgi进程停止成功! 进程:%s\n' %self.uwsgi_process
            print(s)

    def status(self):
        cmd = 'ps -ef | grep -v grep | grep %s' %self.uwsgi_process
        output = subprocess.getoutput(cmd)
        result = """uwsgi进程如下:

        %s
        """ % output
        print(result)

class celery_process_control(process_control):
    django_entry = os.path.join(BASE_CONFIG["proj_home"], 'manage.py')
    python_env = os.path.join(os.path.join(BASE_CONFIG["python_home"], 'bin'), 'python')
    loglevel = CELERY_CONFIG["loglevel"]
    logfile = CELERY_CONFIG["logfile"]
    def start(self):
        pass

    def stop(self):
        p_name = '{python_env} {django_entry} celery worker -c 4 --loglevel={loglevel} --logfile={logfile}'.format(
            python_env=self.python_env, django_entry=self.django_entry, loglevel=self.loglevel, logfile=self.logfile)
        cmd = "kill -9 `ps -ef | grep -v grep | grep celery | grep %s | awk -F ' ' '{print $2}' | xargs`" % (
            self.django_entry)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            s = 'celery进程停止失败! 进程:%s err:%s\n' % (p_name, output)
            print(s)
        else:
            s = 'celery进程停止成功! 进程:%s' % p_name
            print(s)

    def status(self):
        cmd = 'ps -ef | grep -v grep | grep celery | grep %s ' % (self.django_entry)
        output = subprocess.getoutput(cmd)
        result = """celery进程如下:

                  %s
                  """ % output
        print(result)

class apscheduler_process_control(process_control):
    apscheduler_entry = os.path.join(BASE_CONFIG["proj_home"], 'scheduler.py')

    def start(self):
        pass

    def stop(self):
        cmd = "kill -9 `ps -ef | grep -v grep | grep %s | awk -F ' ' '{print $2}' | xargs`" % (
            self.apscheduler_entry)

        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            s = 'apscheduler进程停止失败! 进程:%s err:%s\n' % (self.apscheduler_entry, output)
            print(s)
        else:
            s = 'apscheduler进程停止成功! 进程:%s' %self.apscheduler_entry
            print(s)

    def status(self):
        cmd = 'ps -ef | grep -v grep  | grep %s ' % (self.apscheduler_entry)
        output = subprocess.getoutput(cmd)
        result = """apscheduler进程如下:

                         %s
                         """ % output
        print(result)

class supervisord_process_control(process_control):
    django_entry = os.path.join(BASE_CONFIG["proj_home"], 'manage.py')
    scheduler_entry = os.path.join(BASE_CONFIG["proj_home"], 'scheduler.py')
    python_env = os.path.join(os.path.join(BASE_CONFIG["python_home"], 'bin'), 'python')
    supervisord_env = os.path.join(os.path.join(BASE_CONFIG["python_home"], 'bin'), 'supervisord')
    supervisord_config_file = os.path.join(PROJ_CONFIG_DIR, 'supervisord.ini')
    supervisord_sock = os.path.join(BASE_CONFIG["proj_home"], 'supervisord.sock')
    supervisord_pid =  os.path.join(BASE_CONFIG["proj_home"], 'supervisord.pid')
    uwsgi_process = os.path.join(BASE_CONFIG["python_home"], 'bin/uwsgi')
    uwsgi_config_file = os.path.join(PROJ_CONFIG_DIR, 'uwsgi.ini')

    def start(self):
        cmd = '{supervisord_env} -c {supervisord_conf}'.format(supervisord_env=self.supervisord_env, supervisord_conf=self.supervisord_config_file)
        exit_code = os.system(cmd)
        if exit_code != 0:
            s = 'supervisord启动失败! 进程:%s' %cmd
            print(s)
        else:
            s = "supervisord启动成功! 进程:%s" %cmd
            print(s)

    def stop(self):
        p_name = '{supervisord_env}'.format(supervisord_env=self.supervisord_env)
        cmd = "kill -9 `ps -ef | grep -v grep | grep %s | awk -F ' ' '{print $2}' | xargs`"%p_name
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            s = 'supervisord进程停止失败! 进程:%s err:%s\n' % (p_name, output)
            print(s)
        else:
            cmd = "rm -rf %s %s" %(self.supervisord_sock, self.supervisord_pid)
            os.system(cmd)
            s = 'supervisord进程停止成功! 进程:%s\n' % p_name
            print(s)

    def status(self):
        p_name = '{supervisord_env}'.format(supervisord_env=self.supervisord_env)
        cmd = 'ps -ef | grep -v grep | grep %s '%p_name
        output = subprocess.getoutput(cmd)
        result = """supervisord进程如下:

                  %s
                  """ %output
        print(result)

    def mk_supervisord_config(self):
        try:
            supervisord_template = os.path.join(PROJ_CONFIG_DIR, 'supervisord.template')
            uwsgi_config_str = open(supervisord_template).read(). \
                format(proj_home=BASE_CONFIG["proj_home"],
                       proj_log_dir=os.path.join(BASE_DIR, 'log'),
                       python_env=self.python_env,
                       scheduler_entry=self.scheduler_entry,
                       django_entry=self.django_entry,
                       uwsgi_process=self.uwsgi_process,
                       uwsgi_config_file=self.uwsgi_config_file,
                       )
        except Exception as e:
            s = "生成supervisord配置文件失败! err: %s" % (str(e))
            print(s)
        else:
            with open(os.path.join(PROJ_CONFIG_DIR, 'supervisord.ini'), 'w') as f:
                f.write(uwsgi_config_str)
            print("生成supervisord配置文件成功!")

def help():
    s = """使用方法:
python %s start|restart|status|stop"""%(sys.argv[0])
    print(s)

def start(kwargs):
    kwargs["uwsgi"].mk_uwsgi_config()
    kwargs["supervisord"].mk_supervisord_config()
    kwargs['nginx'].start()
    kwargs['redis'].start()
    kwargs["supervisord"].start()

def stop(kwargs):
    kwargs['nginx'].stop()
    kwargs['redis'].stop()
    kwargs["supervisord"].stop()
    kwargs["celery"].stop()
    kwargs["apscheduler"].stop()
    kwargs['uwsgi'].stop()

def status(kwargs):
    kwargs["nginx"].status()
    kwargs["redis"].status()
    kwargs["supervisord"].status()
    kwargs["uwsgi"].status()
    kwargs["celery"].status()
    kwargs["apscheduler"].status()

def restart(kwargs):
    stop(kwargs)
    start(kwargs)

def main():
    nginx = nginx_process_control()
    redis = redis_process_control()
    supervisord = supervisord_process_control()
    uwsgi = uwsgi_process_control()
    celery = celery_process_control()
    apscheduler = apscheduler_process_control()

    process_obj = {"nginx": nginx, 'uwsgi': uwsgi, 'redis': redis, 'supervisord': supervisord,
                   "celery": celery, "apscheduler": apscheduler
                   }

    result = {"status": status, "start": start, "stop": stop, 'restart': restart}
    if len(sys.argv) != 2:
        help()
    elif sys.argv[1] not in result:
        help()
    else:
        result[sys.argv[1]](process_obj)
        #result["status"](process_obj)

if __name__ == '__main__':
    main()
    #x = celery_process_control()
    #x.start()
    #x.stop()
    #x.status()
    # s = supervisord_process_control()
    # s.mk_supervisord_conf()


