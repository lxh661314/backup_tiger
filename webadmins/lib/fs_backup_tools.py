#!/usr/bin/python
#coding:utf8

from sshConn import *
from util import *
from abc import ABCMeta, abstractmethod
import time, subprocess, socket

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ_CONFIG_FILE = os.path.join(os.path.join(BASE_DIR, 'config'), 'config.cfg')
PROJ_CONFIG_OBJ = readConfig(PROJ_CONFIG_FILE)
BACKUP_SERVER_CONFIG = PROJ_CONFIG_OBJ.read_config("localhost")
BACKUP_AGENT_CONFIG = PROJ_CONFIG_OBJ.read_config("backup-agent")

from logger import log
logger = log().getLogger()


class filesystem_backup(metaclass=ABCMeta):
    rsync_config_dir = os.path.join(os.path.join("/usr/local", BACKUP_AGENT_CONFIG["rsync"]), 'config')
    rsync_config_file = os.path.join(rsync_config_dir, 'rsyncd.conf')  # rsync配置文件路径
    rsync_temp_file = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template'),
                                   'rsyncd.template')  ##rsync模板文件

    def __init__(self, sshObj, source_addr, backup_src_path=None, backup_dst_path=None):
        self.sshObj = sshObj
        self.source_addr = source_addr
        self.backup_src_path = backup_src_path
        self.backup_dst_path = backup_dst_path

    @abstractmethod
    def mk_rsync_config(self):
        """
        生成rsync配置文件
        """
        pass

    @abstractmethod
    def rm_rsync_config(self):
        pass

    @abstractmethod
    def rsync_start(self):
        pass

    @abstractmethod
    def mk_sersync_config(self):
        pass

    @abstractmethod
    def fs_full_backup(self):
        pass

    def sftp_sersync_config(self):
        sersync_pid = None
        sersync_config = self.mk_sersync_config()
        sftp_config_file = self.sshObj.sftpFile(sersync_config, "/usr/local/sersync/config/%s" %sersync_config.split('/')[-1], "push")
        try:
            self.sshObj.exeCommand("/usr/local/sersync/sersync2 -n 10 -d -o /usr/local/sersync/config/%s "
                               %sersync_config.split('/')[-1], timeout=2)
        except Exception as e:
            logger.warn("推送sersync配置文件或在远程主机%s拉起sersync进程失败! err:%s" %(self.sshObj.host, str(e)))
            return False
        else:
            output = self.sshObj.exeCommand("ps -ef | grep %s | grep -v grep | awk -F ' ' '{print $2}'" % (sersync_config.split('/')[-1]))
            print(output, 'output')
            sersync_pid = output["stdout"].strip()
            print(sersync_pid)
        finally:
            print(sftp_config_file, sersync_pid)
            if all([sftp_config_file["status"], sersync_pid]):
                logger.info("推送sersync配置文件并在远程主机%s拉起sersync进程成功!"%self.sshObj.host)
                return True
            else:
                logger.warn("推送sersync配置文件或在远程主机%s拉起sersync进程失败!" %(self.sshObj.host))
                return False

    @abstractmethod
    def fs_backup_start(self):
        pass

    def fs_backup_stop(self):
        title = self.source_addr.replace('.', '-') + self.backup_src_path.replace('/', '-')
        cmd = "kill -9 `ps -ef | grep sersync2 | grep -v grep | grep %s- | awk -F ' ' '{print $2}' | xargs`" %title
        kill_sersync = self.sshObj.exeCommand(cmd, timeout=5)
        remove_rsync_config = self.rm_rsync_config()
        if all([kill_sersync['status'], remove_rsync_config]):
            result = "文件系统备份任务终止成功!"
            return result
        else:
            raise ValueError("文件系统备份任务终止失败!")

# class centralize_filesystem_backup(filesystem_backup):
#
#     def mk_rsync_config(self):
#         """
#         在本地生成rsync配置
#         """
#         if not os.path.exists(self.rsync_config_dir):
#             os.makedirs(self.rsync_config_dir)
#         cmd = 'cp %s %s' %(self.rsync_temp_file, self.rsync_config_file)
#         os.system(cmd) #复制配置文件
#         title = self.source_addr.replace('.', '-') + self.backup_src_path.replace('/', '-')
#         string = """\n[{title}]\npath={backup_path}\ncomment={title}
#         """.format(title=title, backup_path=self.backup_dst_path)
#         exit_code = subprocess.call("echo '%s' >> %s" %(string, self.rsync_config_file), shell=True)
#         if exit_code == 0:
#             logger.info("在本地生成rsync配置成功!")
#             return True
#         else:
#             logger.warn("在本地生成rsync配置失败!")
#             return False
#
#     def rm_rsync_config(self):
#         title = self.source_addr.replace('.', '-') + self.backup_src_path.replace('/', '-')
#         string = """\n[{title}]\npath={backup_path}\ncomment={title}
#         """.format(title=title, backup_path=self.backup_dst_path)
#         try:
#             for j in string.splitlines():
#                 if j.isspace():
#                     continue
#                 cmd = "sed -i /%s/d %s" %(j.replace('[', '\\\\[').replace(']', '\\\\]').replace('/', '\\\\/'), self.rsync_config_file)
#                 subprocess.check_call(cmd, shell=True)
#         except Exception as e:
#             logger.warn("在本地删除rsync配置失败! err: %s" %(str(e)))
#             return False
#         else:
#             logger.info("在本地删除rsync配置成功!")
#             return True
#
#     def mk_sersync_config(self):
#         """
#         生成sersync配置文件
#         """
#         try:
#             timestamp = str(int(time.time()))
#             sersync_temp_file = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template'),
#                                              'sersync_config.template')
#             comment = self.source_addr.replace('.', '-') + self.backup_src_path.replace('/', '-')
#             xmlfile_name = '-'.join([comment, timestamp])
#
#             temp = open(sersync_temp_file, 'r')
#             strings = temp.read().format(source_path=self.backup_src_path,
#                                          backup_server=BACKUP_SERVER_CONFIG["address"],
#                                          server_comment=comment,
#                                          backup_user="root",
#                                          rsync_password_file="/etc/rsync.pass"
#                                          )
#             temp.close()
#             sersync_config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
#             sersync_conf_file = os.path.join(sersync_config_dir, '%s.xml'%(xmlfile_name))
#             sersyncConf = open(sersync_conf_file, 'w')
#             sersyncConf.write(strings)
#             sersyncConf.close()
#         except Exception as e:
#             logger.warn("在本地生成sersync配置文件失败! err: %s" %(str(e)))
#             return False
#         else:
#             logger.info("在本地生成sersync配置文件成功!")
#             return sersync_conf_file
#
#     def fs_backup_start(self):
#         if all([self.sftp_sersync_config(), self.mk_rsync_config()]):
#             return True
#         else:
#             return False
#


class distribute_filesystem_backup(filesystem_backup):

    def mk_rsync_config(self):
        """
        在远程主机生成rsync配置
        """
        self.sshObj.exeCommand("mkdir -p %s"%self.rsync_config_dir) ##创建配置文件目录
        self.sshObj.sftpFile(self.rsync_temp_file, self.rsync_config_file, 'push')  ##推送配置文件
        title = self.source_addr.replace('.', '-') + self.backup_src_path.replace('/', '-')
        string = """\n[{title}]\npath={backup_path}\ncomment={title}
              """.format(title=title, backup_path=self.backup_dst_path)
        output = self.sshObj.exeCommand("echo '%s' >> %s" %(string, self.rsync_config_file))
        if output['exit_code'] == 0:
            logger.info("在远程主机%s生成rsync配置成功!" %self.sshObj.host)
            return True
        else:
            logger.warn("在远程主机%s生成rsync配置失败!")%(self.sshObj.host)
            return False

    def rm_rsync_config(self):
        title = self.source_addr.replace('.', '-') + self.backup_src_path.replace('/', '-')
        string = """\n[{title}]\npath={backup_path}\ncomment={title}
        """.format(title=title, backup_path=self.backup_dst_path)
        try:
            for j in string.splitlines():
                if j.isspace():
                    continue
                cmd = "sed -i /%s/d %s" %(j.replace('[', '\\\\[').replace(']', '\\\\]').replace('/', '\\\\/'), self.rsync_config_file)
                self.sshObj.exeCommand(cmd)
        except Exception as e:
            logger.warn("在远程主机%s删除rsync配置失败! err: %s" %(str(e)))
            return False
        else:
            logger.info("在远程主机%s删除rsync配置成功!"%self.sshObj.host)
            return True

    def mk_sersync_config(self):
        """
        生成sersync配置文件
        """
        try:
            timestamp = str(int(time.time()))
            sersync_temp_file = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template'),
                                             'sersync_config.template')
            comment = self.source_addr.replace('.', '-') + self.backup_src_path.replace('/', '-')
            xmlfile_name = '-'.join([comment, timestamp])
            temp = open(sersync_temp_file, 'r')
            strings = temp.read().format(source_path=self.backup_src_path,
                                         backup_server = self.source_addr,
                                         server_comment = comment,
                                         backup_user = "root",
                                         rsync_password_file="/etc/rsync.pass"
                                        )
            temp.close()
            sersync_config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
            sersync_conf_file = os.path.join(sersync_config_dir, '%s.xml'%(xmlfile_name))
            sersyncConf = open(sersync_conf_file, 'w')
            sersyncConf.write(strings)
            sersyncConf.close()
        except Exception as e:
            logger.warn("在本地生成sersync配置文件失败! err: %s" %(str(e)))
            return False
        else:
            logger.info("在本地生成sersync配置文件成功!")
            return sersync_conf_file

    def fs_full_backup(self, backup_to_local_path=None, fs_full_backup_path=None):
        self.sshObj.exeCommand("mkdir -p %s"%fs_full_backup_path)
        try:
            cmd = '/usr/local/rsync -avc %s/* %s'%(backup_to_local_path, fs_full_backup_path)
            print(cmd)
            output = self.sshObj.exeCommand(cmd)
            msg = output["stdout"].decode(encoding="utf-8").strip()
            logger.info("主机%s全量备份%s至%s成功! \n%s"%(self.source_addr, backup_to_local_path, fs_full_backup_path, msg))
            return msg
        except Exception as e:
            logger.warn("主机%s全量备份%s至%s失败! err:%s"%(self.source_addr, backup_to_local_path, fs_full_backup_path, str(e)))
            raise ValueError("主机%s全量备份%s至%s失败! err:%s"%(self.source_addr, backup_to_local_path, fs_full_backup_path, str(e)))

    def rsync_start(self):
        rsync_pid = "ps -ef | grep /usr/local/rsync | grep -v grep | awk -F ' ' '{print $2}' | xargs"
        output = self.sshObj.exeCommand(rsync_pid, timeout=5)
        print(output)
        pid = output.get("stdout")
        print(pid, type(pid), bool(pid))
        if not pid:
            cmd = 'rm -f /var/run/rsyncd.pid; /usr/local/rsync  --daemon --config=%s'%self.rsync_config_file
            try:
                self.sshObj.exeCommand(cmd, timeout=5)
            except Exception as e:
                logger.warn("在远程主机%s启动rsync失败! err:%s" %(self.sshObj.host, str(e)))
                return False
            else:
                logger.info("在远程主机%s启动rsync成功!"%self.sshObj.host)
                return True
        else:
            logger.info("远程主机%srsync已启动!" % self.sshObj.host)
            return True

    def fs_backup_start(self):
        self.sshObj.exeCommand("mkdir -p %s"%self.backup_dst_path)
        title = self.source_addr.replace('.', '-') + self.backup_src_path.replace('/', '-')
        if all([self.sftp_sersync_config(), self.mk_rsync_config(), self.rsync_start()]):
            rsync_cmd = '/usr/local/rsync  -avc {backup_src_path}/* root@{source_addr}::{title} '.format(
                backup_src_path=self.backup_src_path, source_addr=self.source_addr, title=title)
            print(rsync_cmd)
            output = self.sshObj.exeCommand(rsync_cmd, timeout=86400)
            msg = output["stdout"].decode(encoding="utf-8").strip()
            logger.info("主机%s全量备份%s至%s成功! \n%s"%(self.source_addr, self.backup_src_path, self.backup_dst_path, msg))
            return msg
        else:
            logger.warn("主机%s全量备份%s至%s失败! err:%s" % (self.source_addr, self.backup_src_path, self.backup_dst_path, str(e)))
            raise ValueError("主机%s全量备份%s至%s失败! err:%s" % (self.source_addr, self.backup_src_path, self.backup_dst_path, str(e)))


if __name__ == '__main__':
    sshObj = controlHost('172.16.70.221', 'root', 'meizu.com', 22)
    d = distribute_filesystem_backup(sshObj, "172.16.70.221", '/etc/sysconfig/network-scripts',
                                     backup_dst_path='/mnt/nfs/031551540182823/backup_filesystem/172.16.70.221/etc/sysconfig/network-scripts')
    d.fs_full_backup()
    #d.mk_rsync_config()
    #d.rm_rsync_config()
    #d.mk_sersync_config()
    #d.sftp_sersync_config()
    #d.fs_backup_start()
    #d.fs_backup_stop()

    #time.sleep(1)

    #c = centralize_filesystem_backup(sshObj, '172.16.70.231', '/etc/sysconfig/network-scripts',
    #                                 backup_dst_path='/mnt/nfs/fs/etc/sysconfig/network-scripts')
    #c.mk_rsync_config()
    #c.rm_rsync_config()
    #c.mk_sersync_config()
    #c.sftp_sersync_config()
    #c.fs_backup_start()
    #c.fs_backup_stop()


