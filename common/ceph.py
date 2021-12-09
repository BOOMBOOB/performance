from config import NODE_CONFIG
from lib.logee import logger
from lib.SSHRemoteOperation import SSHRemoteOperation
import re
import sys
import time


class Ceph(object):

    @staticmethod
    def check_ceph_health_status(ip=None):
        """
        根据集群pg状态检查集群是否健康
        :param ip: 执行检查命令的ceph存储节点
        :return:
        """
        ceph_node = NODE_CONFIG.get("ceph")
        ip = ip if ip else ceph_node.get("ip")
        ssh = SSHRemoteOperation(ip)
        time_start = int(time.time())
        while int(time.time()) - time_start < ceph_node.get("time_wait"):
            ret, err = ssh.ssh_connect(cmd="ceph -s")
            ret1, err1 = ssh.ssh_connect(cmd="infi version")
            infi_version = re.findall("Infinity (\d)", ret1)[0]
            print("infinity的版本为" + infi_version)
            if err:
                continue
            else:
                if ret != '':
                    try:
                        osd_slow_ops = re.findall('osd\.\d+', ret)  # 检查存在slow ops的osd
                        if infi_version == "3" or infi_version == "4":
                            total_pg = int(re.findall('pools, (.*?) pgs', ret)[0])
                            ok_pg = sum([int(item) for item in re.findall(r'(\d+)\s+active\+clean', ret)])
                        elif infi_version == "2":
                            total_pg = re.findall('(\d+) pgs', ret)[0]
                            ok_pg = re.findall('(\d+) active\+clean', ret)[0]
                        else:
                            logger.error("the func <{}> don't currently adapted, please check it at now!!!".format(
                                sys._getframe().f_code.co_name))
                        logger.info(
                            f'total_pg:{total_pg}, active+clean_pg:{ok_pg},slow ops osd:{",".join(osd_slow_ops)}')
                        if total_pg == ok_pg and len(osd_slow_ops) == 0:
                            return True
                        else:
                            break
                    except:
                        continue
            time.sleep(5)
        return False

    @staticmethod
    def check_ceph_osd_status(ip=None):
        """
        检查集群osd状态是否全部为UP & IN
        :param ip: 执行检查命令的ceph存储节点
        :return:
        """
        ceph_node = NODE_CONFIG.get("ceph")
        ip = ip if ip else ceph_node.get("ip")
        ssh = SSHRemoteOperation(ip)
        cmd_check_osd = "ceph osd stat"
        time_start = int(time.time())
        while int(time.time()) - time_start < ceph_node.get("time_wait"):
            out, err = ssh.ssh_connect(cmd_check_osd)
            if err:
                continue
            else:
                if out != "":
                    try:
                        osd_info = re.findall("(\d+)\s+osds.*?:\s+(\d+)\s+up.*?,\s+(\d+)\s+in.*?", out)
                        osd_total_num, osd_up_num, osd_in_num = osd_info[0]
                        logger.info(
                            "Total OSD: {}, Up OSD: {}, In OSD: {}".format(osd_total_num, osd_up_num, osd_in_num))
                        if osd_total_num == osd_up_num == osd_in_num:
                            return True
                    except:
                        continue
            time.sleep(5)
        return False

    @staticmethod
    def check_ceph_slow_ops(ip=None):
        """
        检查集群是否有慢IO
        :param ip: 执行检查命令的ceph存储节点
        :return:
        """
        ceph_node = NODE_CONFIG.get("ceph")
        ip = ip if ip else ceph_node.get("ip")
        ssh = SSHRemoteOperation(ip)
        cmd = "ceph health"
        time_start = int(time.time())
        while int(time.time()) - time_start < ceph_node.get("time_wait"):
            out, err = ssh.ssh_connect(cmd)
            if err:
                continue
            else:
                if out != "":
                    if "slow ops" not in out:
                        logger.info("检查无慢IO： {}".format(out))
                        return True
            time.sleep(5)
        return False
