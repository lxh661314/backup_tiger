#coding:utf8


import sys
from sshConn import *
from util import *
from logger import log

logger = log().getLogger()

class DB_BACKUP_ERROR(Exception):
    pass



class db_xtrabackup:
    def __init__(self, sshObj, db_info):
        self.sshObj = sshObj
        self.db_info = db_info

    def xtrabackup_full_backup(self, backup_path, timestamp=None):
        # result = {}
        # job_id = create_jid(length=10)
        # result["job_id"] = job_id
        if not timestamp:
            timestamp = ControlTime.date_today(_format="%Y%m%d%H%M%S")[0]
        full_backup_path = os.path.join(os.path.join(backup_path, self.sshObj.host), timestamp)

        backup_cmd = '/usr/local/percona-xtrabackup/bin/innobackupex ' \
                     '--defaults-file={my_files} --no-timestamp --user={db_user} ' \
                     '--password={db_passwd} --port={db_port} --host={db_host} {full_backup_path}'.format(my_files=self.db_info["my_files"],
                                                                                                          db_user=self.db_info["db_user"],
                                                                                                          db_passwd=self.db_info["db_passwd"],
                                                                                                          db_port=self.db_info["db_port"],
                                                                                                          db_host=self.db_info["db_host"],
                                                                                                          full_backup_path=full_backup_path)
        try:
            output = self.sshObj.exeCommand(backup_cmd, timeout=86400)
        except Exception as e:
            """
            备份失败
            """
            # logger.warn("job_id %s| err: %s " %(job_id, str(e)))
            logger.warn(u"主机%s数据库备份失败! err:%s"%(self.sshObj.host, str(e)))
            sys.stdout.write(u"主机%s数据库备份失败! err:%s"%(self.sshObj.host, str(e)))
            # result["message"] = u"主机%s数据库备份失败!"%self.sshObj.host
            # return result
            raise DB_BACKUP_ERROR(u"主机%s数据库备份失败! err:%s"%(self.sshObj.host, str(e)))

        else:
            """
            备份成功
            """
            if output["stderr"].decode(encoding="utf-8").strip().endswith("completed OK!"):
                # logger.info("job_id %s| 主机%s数据库备份成功!"%(job_id, self.sshObj.host))
                # result["message"] = u'主机%s数据库备份成功!'%self.sshObj.host
                logger.info(u'主机%s数据库备份成功!'%self.sshObj.host)
                sys.stdout.write(u'主机%s数据库备份成功!'%self.sshObj.host)
                return output["stderr"].decode(encoding="utf-8").strip()
            else:
                # logger.warn("job_id %s| stderr: %s" %(job_id, output["stderr"]))
                # result["message"] = u"主机%s数据库备份失败!" % self.sshObj.host
                logger.info(u"主机%s数据库备份失败!" % self.sshObj.host)
                sys.stdout.write(u"主机%s数据库备份失败!" % self.sshObj.host)
                raise DB_BACKUP_ERROR(u"主机%s数据库备份失败! err:%s" % (self.sshObj.host, output["stderr"].decode(encoding="utf-8").strip()))
            #return result

if __name__ == '__main__':
    sshObj = controlHost('172.16.70.221', 'root', 'meizu.com', 22)
    db_info = {"my_files":'/etc/my.cnf', "db_user": "root", "db_passwd": 'P@ssw0rd',
               "db_port": 3306, "db_host": "172.16.70.221"}
    full_backup_path = '/data/backup/2'

    print(db_info)
    print(full_backup_path)

    x = db_xtrabackup(sshObj, db_info)
    res = x.xtrabackup_full_backup(full_backup_path)
    print(res)

