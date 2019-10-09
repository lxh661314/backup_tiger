#coding:utf8

from abc import ABCMeta, abstractmethod
from util import *
from sshConn import *
from logger import log
import subprocess

logger = log().getLogger()


class NfsMountError(Exception):
    pass


class storage_nfs_mount(metaclass=ABCMeta):
    base_dir = '/mnt/nfs'
    def __init__(self, source_addr, storage_mount_path, local_path=None):
        if not local_path:
            self.local_path = os.path.join(storage_nfs_mount.base_dir, create_jid(15))
        else:
            self.local_path = local_path
        self.source_addr = source_addr
        self.storage_mount_path = storage_mount_path

    @abstractmethod
    def check_nfs_install(self):
        pass

    @abstractmethod
    def mk_local_dir(self):
        pass

    @abstractmethod
    def cg_local_fstab(self):
        pass

    @abstractmethod
    def mnt_local_dir(self):
        pass

    @abstractmethod
    def rm_local_dir(self):
        pass

    @abstractmethod
    def rm_local_fstab(self):
        pass

    @abstractmethod
    def umnt_local_dir(self):
        pass

    def umount_nfs(self):
        if all([self.rm_local_fstab(), self.umnt_local_dir(), self.rm_local_dir()]):
            return True
        else:
            return False

    def mount_nfs(self):
        if all([self.check_nfs_install(), self.mk_local_dir(), self.cg_local_fstab(), self.mnt_local_dir()]):
            return True
        else:
            self.rm_local_fstab()
            self.umnt_local_dir()
            self.rm_local_dir()
            return False

class local_nfs_mount(storage_nfs_mount):

    def check_nfs_install(self):
        cmd = 'rpm -q nfs-utils'
        status, output = subprocess.getstatusoutput(cmd)
        if status == 0:
            return True
        else:
            logger.warn("nfs-utils客户端未安装!")
            return False

    def mk_local_dir(self):
        try:
            if not os.path.exists(self.local_path):
                os.makedirs(self.local_path)
        except Exception as e:
            logger.warn("创建NFS挂载目录%s失败!err:%s"%self.local_path, str(e))
            raise NfsMountError("目录%s创建失败! err: %s"%(self.local_path, str(e)))
        else:
            logger.info("创建NFS挂载目录%s成功" %self.local_path)
            return True

    def cg_local_fstab(self):
        mount_point = '{source_addr}:{storage_mount_path}'.format(source_addr=self.source_addr,
                                                                  storage_mount_path=self.storage_mount_path)
        current_rules = [ j.decode(encoding='utf-8') for j in os_system("cat /etc/fstab").splitlines()]
        for j in current_rules:
            if j.startswith("#"):
                continue
            elif not j:
                continue
            sp = j.split()
            if len(sp) < 2: #不正确的行
                continue
            elif any([sp[0].strip() == mount_point, sp[1].strip() == self.local_path]):
                raise NfsMountError("挂载点%s或本地路径%s已存在!"%(mount_point, self.local_path))
        rules = '{mount_point} {local_path} nfs defaults 0 0'.format(mount_point=mount_point, local_path=self.local_path)

        cmd = 'echo "{rules}" >> /etc/fstab'.format(rules=rules)
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            logger.warn("规则%s添加至fstab失败! err:%s"%(cmd, output))
            raise NfsMountError("规则%s添加至fstab失败! err:%s"%(cmd, output))
        else:
            logger.warn("规则%s添加至fstab成功!"%cmd)
            return True

    def mnt_local_dir(self):
        cmd = 'sh -c "mount -a"'
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            logger.warn("mount -a挂载NFS共享失败!")
            raise NfsMountError("挂载%s失败!err:%s" %(cmd, output))
        else:
            logger.info("mount -a挂载NFS共享成功!")
            return True

    def rm_local_dir(self):
        cmd = 'rm -rf %s'%self.local_path
        #print(cmd, 'cmd')
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            logger.error("删除本地目录%s失败!err: %s" %(self.local_path, output))
            raise NfsMountError("删除本地目录%s失败!err: %s" %(self.local_path, output))
        else:
            logger.info("删除本地目录%s成功!"%self.local_path)
            return True

    def rm_local_fstab(self):
        cmd = 'sed -i /%s:%s/d /etc/fstab'%(self.source_addr, self.storage_mount_path.replace('/', '\\\\/'))
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            logger.warn("删除挂载点%s:%s fstab配置失败!err:%s"%(self.source_addr, self.storage_mount_path, output))
            raise NfsMountError("删除挂载点%s:%s fstab配置失败!err:%s"%(self.source_addr, self.storage_mount_path, output))
        else:
            logger.info("创建挂载点%s:%s fstab配置成功!"%(self.source_addr, self.storage_mount_path))
            return True

    def umnt_local_dir(self):
        cmd = 'sh -c "umount %s"'%self.local_path
        status, output = subprocess.getstatusoutput(cmd)
        if status != 0:
            logger.warn("卸载挂载路径%s失败!err:%s"%(self.local_path, output))
            #raise NfsMountError("卸载挂载路径%s失败!err:%s"%(self.local_path, output))
        else:
            logger.info("卸载挂载路径%s成功!"%self.local_path)
        return True

class remote_nfs_mount(storage_nfs_mount):
    def __init__(self, source_addr, storage_mount_path, sshObj=None,  local_path=None):
        storage_nfs_mount.__init__(self, source_addr, storage_mount_path, local_path)
        self.sshObj = sshObj
        # self.local_path = os.path.join(storage_nfs_mount.base_dir, create_jid(15))

    def check_nfs_install(self):
        cmd = 'rpm -q nfs-utils'
        output = self.sshObj.exeCommand(cmd, timeout=5)
        print(output)
        status = output["exit_code"]
        if status == 0:
            return True
        else:
            logger.warn("主机%s nfs-utils未安装!"%self.source_addr)
            return False

    def mk_local_dir(self):
        try:
            self.sshObj.exeCommand("mkdir -p %s"%self.local_path)
        except Exception as e:
            logger.warn("主机%s创建目录%s创建失败! err: %s"%(self.sshObj.host, self.local_path, str(e)))
            raise NfsMountError("主机%s创建目录%s创建失败! err: %s"%(self.sshObj.host, self.local_path, str(e)))
        else:
            logger.info("主机%s创建目录%s成功!"%(self.sshObj.host, self.local_path))
            return True

    def cg_local_fstab(self):
        mount_point = '{source_addr}:{storage_mount_path}'.format(source_addr=self.source_addr,
                                                                  storage_mount_path=self.storage_mount_path)
        current_rules = [j.decode(encoding="utf-8") for j in self.sshObj.exeCommand("cat /etc/fstab").get("stdout", '').splitlines()]
        for j in current_rules:
            if j.startswith("#"):
                continue
            elif not j:
                continue
            sp = j.split()
            print(sp[0].strip(), mount_point, sp[1].strip(), self.local_path, 'xwew')
            if len(sp) < 2: #不正确的行
                continue
            elif any([sp[0].strip() == mount_point, sp[1].strip() == self.local_path]):
                raise NfsMountError("挂载点%s或本地路径%s已存在!"%(mount_point, self.local_path))
        rules = '{mount_point} {local_path} nfs defaults 0 0'.format(mount_point=mount_point, local_path=self.local_path)

        cmd = 'echo "{rules}" >> /etc/fstab'.format(rules=rules)
        try:
            self.sshObj.exeCommand(cmd, timeout=5)
        except Exception as e:
            logger.warn("主机%s规则%s添加至fstab失败! err:%s"%(self.sshObj.host, cmd, str(e)))
            raise NfsMountError("主机%s规则%s添加至fstab失败! err:%s"%(self.sshObj.host, cmd, str(e)))
        else:
            logger.info("主机%s规则%s添加至fstab成功!"%(self.sshObj.host, cmd))
            return True

    def mnt_local_dir(self):
        cmd = 'sh -c "mount -a"'
        try:
            self.sshObj.exeCommand(cmd, timeout=5)
        except Exception as e:
            logger.warn("主机%s挂载%s失败!err:%s" % (self.sshObj.host, cmd, str(e)))
            raise NfsMountError("主机%s挂载%s失败!err:%s" % (self.sshObj.host, cmd, str(e)))
        else:
            logger.info("主机%s挂载%s成功!"%(self.sshObj.host, cmd))
            return True

    def rm_local_dir(self):
        try:
            cmd = 'rm -rf %s' % self.local_path
            self.sshObj.exeCommand(cmd, timeout=5)
        except:
            logger.warn("主机%s删除本地目录%s失败!err: %s" % (self.sshObj.host, self.local_path, str(e)))
            raise NfsMountError("主机%s删除本地目录%s失败!err: %s" % (self.sshObj.host, self.local_path, str(e)))
        else:
            logger.info("主机%s删除本地目录%s成功!"%(self.sshObj.host, self.local_path))
            return True

    def rm_local_fstab(self):
        cmd = 'sed -i /%s:%s/d /etc/fstab' % (self.source_addr, self.storage_mount_path.replace('/', '\\\\/'))
        try:
            self.sshObj.exeCommand(cmd, timeout=5)
        except Exception as e:
            logger.warn("主机%s删除挂载点%s:%s fstab配置失败!err:%s" % (self.sshObj.host, self.source_addr,
                                                                     self.storage_mount_path, str(e)))
            raise NfsMountError("主机%s删除挂载点%s:%s fstab配置失败!err:%s" % (self.sshObj.host, self.source_addr,
                                                                     self.storage_mount_path, str(e)))
        else:
            logger.info("主机%s删除挂载点%s:%s fstab配置成功!" %(self.sshObj.host, self.source_addr, self.storage_mount_path))
            return True

    def umnt_local_dir(self):
        cmd = 'sh -c "umount %s"' % self.local_path
        try:
            self.sshObj.exeCommand(cmd, timeout=5)
        except Exception as e:
            logger.warn("主机%s卸载挂载路径%s失败!err:%s" % (self.sshObj.host, self.local_path, str(e)))
            raise NfsMountError("主机%s卸载挂载路径%s失败!err:%s" % (self.sshObj.host, self.local_path, str(e)))
        else:
            logger.info("主机%s卸载挂载路径%s成功!"%(self.sshObj.host, self.local_path))
            return True


if __name__ == '__main__':
    # nfs_mount = local_nfs_mount("172.16.70.233", '/opt/nfs_test', '/mnt/nfs/343284705541386')
    # #x = nfs_mount.mount_nfs()
    # x = nfs_mount.umount_nfs()
    # print(x)


    sshObj = controlHost('172.16.70.221', 'root', 'meizu.com', 22)
    nfs_mount = remote_nfs_mount('172.16.70.233', '/opt/nfs_test', sshObj)
    nfs_mount.check_nfs_install()
    #x = nfs_mount.mount_nfs()
    #x = nfs_mount.umount_nfs()
    #print(x)

