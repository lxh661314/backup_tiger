#coding:utf8

import paramiko
import os
import traceback

class SshConnectError(Exception):
    pass

class controlHost:
    def __init__(self, host, username, password, port=22, key_file='/root/.ssh/id_rsa'):
        self.host = host
        self.pkey = paramiko.RSAKey.from_private_key_file(key_file)
        self.ssh = controlHost.__sshConn(self.host, username, password, self.pkey, int(port))
        self.sftp = self.__sftpConn()


    def close(self):
        if hasattr(self.ssh, "close"):
            self.ssh.close()

    @staticmethod
    def __sshConn(host, username, password, pkey, port):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(hostname=host, port=int(port), username=username, pkey=pkey)
        except:
            try:
                ssh.connect(hostname=host, port=int(port), username=username, password=password)
            except:
                raise SshConnectError("SSH Connect %s Error!" %host)
            else:
                return ssh
        else:
            return ssh

    def __sftpConn(self):
        transport = self.ssh.get_transport()
        sftp = paramiko.SFTPClient.from_transport(transport)
        return sftp

    def exeCommand(self, cmd, timeout=300):
        _, stdout, stderr = self.ssh.exec_command(cmd, timeout=timeout)
        try:
            channel = stdout.channel
            exit_code = channel.recv_exit_status()
            stdout = stdout.read().strip()
            stderr = stderr.read().strip()
            return {"status": 1, "stdout": stdout, "stderr": stderr, 'exit_code': exit_code}
        except:
            return {"status": 0, "stdout": stdout, "stderr": stderr, 'exit_code': 127}

    def sftpFile(self, localpath, remotepath, action):
        try:
            if action == 'push':
                dirname = os.path.dirname(remotepath)
                self.exeCommand("mkdir -p %s" % dirname)
                self.sftp.put(localpath, remotepath)
                return {"status": 1, "message": 'sftp %s %s success!' % (self.host, action)}
            elif action == "pull":
                dirname = os.path.dirname(localpath)
                if not os.path.exists(dirname):
                    os.makedirs(dirname)
                # if os.path.exists(localpath):
                #     os.remove(localpath)
                self.sftp.get(remotepath, localpath)
                return {"status": 1, "stdout": 'sftp %s %s success!' % (self.host, action), "stderr": ""}
        except Exception as e:
            return {"status": 0, "stderr": 'sftp %s %s failed %s' % (self.host, action, str(e)), "stdout": ""}

    @staticmethod
    def iter_local_path(abs_path):
        result = set([])
        for j in os.walk(abs_path):
            base_path = j[0]
            file_list = j[2]
            for k in file_list:
                p = os.path.join(base_path, k)
                result.add(p)
        return result

    def iter_remote_path(self, abs_path):
        result = set([])
        try:
            stat = str(self.sftp.lstat(abs_path))
        except FileNotFoundError:
            return result
        else:
            if stat.startswith("d"):
                file_list = self.exeCommand("ls %s" %abs_path)["stdout"].decode(encoding='utf-8').strip().splitlines()
                for j in file_list:
                    p = os.path.join(abs_path, j)
                    result.update(self.iter_remote_path(p))
            else:
                result.add(abs_path)
        return result


if __name__ == '__main__':
    x = controlHost("172.16.70.233", 'root', 'jiandanai123')

    w = x.iter_local_path("/app_shell/proj_b/webadmins/webadmins")
    print(w)

    y = x.iter_remote_path("/app_shell/123456")
    print(y)

    print(w == y)
    #y = x.exeCommand("uname -r")
    # w = x.sftpFile("/tmp/demo1.py", '/tmp/xyz.py', "push")
    # w = x.sftpFile('/tmp/aaaa.py', '/tmp/xyz.py', 'pull')
    # print(w)
