import time

import paramiko
import os
from lib.logee import logger
from config import NODE_CONFIG


match_list = []


def traversal_match_node(info, node_ip):
    for k, v in info.items():
        if isinstance(v, dict):
            traversal_match_node(v, node_ip)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    traversal_match_node(item, node_ip)
                else:
                    continue
        else:
            if "ip" in info.keys():
                if info.get("ip") == node_ip:
                    match_list.append(info)
                    break
    return match_list


class SSHRemoteOperation:

    def __init__(self, ip):
        self.ip = ip
        match_config = traversal_match_node(NODE_CONFIG, ip)
        for match in match_config:
            self.username = match.get("username")
            self.password = match.get("password")

    def ssh_connect(self, cmd, print_out=True, exec_timeout=120):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try_frequency = 1
            max_try = 3
            while try_frequency <= max_try:
                try:
                    self.ssh.connect(hostname=self.ip,
                                     port=22,
                                     username=self.username,
                                     password=self.password,
                                     timeout=60,
                                     allow_agent=False,
                                     look_for_keys=False)
                    logger.info("ssh connect {} success at {} times".format(self.ip, try_frequency))
                    break
                except Exception as e:
                    if str(e).find("Authentication failed") >= 0:
                        raise Exception('ssh connect {} timeout, e.message=[{}]'.format(self.ip, str(e)))
                    if try_frequency == max_try:
                        raise Exception("ssh connect {} timeout".format(self.ip))
                    time.sleep(2)
                    try_frequency += 1
                    logger.info("try connect {} times".format(try_frequency))
                    continue
            logger.info("send command： 【" + cmd + " 】 to host [ {} ]\n".format(self.ip))
            stdin, stdout, stderr = self.ssh.exec_command(cmd, -1, exec_timeout)
            x = stdout.read().decode("utf-8")
            y = stderr.read().decode("utf-8")
            out = "".join(stdout.readlines())
            err = "".join(stderr.readlines())
            if out == "" and err == "":
                if not (x == "" and y == ""):
                    out = x.strip()
                    err = y.strip()
            out = out.strip()
            err = err.strip()
            if print_out:
                logger.info("out: {}".format(out))
                logger.info("err: {}".format(err))
            return out, err
        except Exception as e:
            logger.error(e)
            out = "execute command error! IPAddress: [ {} ] Command Line: [ {} ]".format(self.ip, cmd)
            return out, e

    def sftp_connect(self):

        for n in range(3):
            try:
                transport = paramiko.Transport(self.ip, 22)
                transport.connect(username=self.username, password=self.password)
                self.sftp = paramiko.SFTPClient.from_transport(transport)
                break
            except Exception as e:
                if n < 2:
                    print("Error： 第 {} 次失败".format(n), e)
                    logger.error("第 {} 次链接失败， 抛出异常： {}".format(n, e))
                else:
                    logger.error("SFTP 链接失败")
        return self.sftp

    def upload_file(self, file_path, file_name):
        self.sftp_connect()
        if not os.path.isfile(file_path):
            logger.error("文件 {} 不存在".format(file_path))
            return
        if self.sftp is None:
            logger.error("SFTP未连接")
            return
        try:
            self.sftp.put(file_path, file_name)
            logger.info("上传文件 {} 到 {} 成功".format(file_path, self.ip))
        except Exception as e:
            logger.error("上传文件 {} 到 {} 失败".format(file_path, self.ip))
        finally:
            self.sftp.close()


if __name__ == '__main__':
    # test = SSHRemoteOperation("10.0.9.89")
    # test.ssh_connect("ls ./")
    # test.sftp_connect()
    # file_path = os.path.join(project_path, "temp", "socket_client_node7.py")
    # test.upload_file(file_path, "socket_client_node7.py")
    ret = traversal_match_node(NODE_CONFIG, '10.0.9.91')
    print(ret)