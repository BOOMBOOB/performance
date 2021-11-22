import time

from bin import project_path
from config.yml_agrs_parse import Args
from lib.logee import logger
from lib.SSHRemoteOperation import SSHRemoteOperation
import os
import re
import sys


NODE_CONFIG = Args().get_yml_data("nodes.yml")
WORKLOAD_RUN_CONFIG = Args().get_yml_data("workload_run.yml")
SOCK_SERVER_IP = NODE_CONFIG.get("sock_server").get("ip")
CLIENTS = NODE_CONFIG.get("clients")
CLIENT_FILE_PREFIX = "socket_client"


def prepare_write(file_path):
    """
    删除指定路径文件已存在的文件
    :param file_path: 文件路径
    :return:
    """
    if os.path.isfile(file_path):
        os.unlink(file_path)


def traversal_run_workloads():
    """
    遍历负载配置文件，获取标记 run 为 True 的工作负载
    :return: list: [tuple: (type, workload_file)]
    """
    load_run = list(filter(lambda x: x.get("workload").get("run") is True, WORKLOAD_RUN_CONFIG.get("workloads")))
    load_list = []
    for load in load_run:
        for load_file in load.get("workload").get("workload_files"):
            load_list.append((load.get("workload").get("type"), load_file))
    return load_list

# ret = traversal_run_workloads()
# print(ret)


def analyse_prometheus_records():
    load_run = list(map(lambda x: x.get("workload").get("record"),
                        list(filter(lambda x: x.get("workload").get("run") is True,
                                    WORKLOAD_RUN_CONFIG.get("workloads")))))
    records = []
    for item in load_run:
        records = list(set(records).union(set(item)))
    return records


def package_record(workload_type):
    records = analyse_prometheus_records()
    template = None
    if workload_type == "fio":
        template = Args().get_yml_data("fio_terse3.yml").get("fio")
    if workload_type == "vdbench":
        template = Args().get_yml_data("vdbench_out.yml").get("vdbench")
    index_list = []
    for record in records:
        if template.get(record):
            index_list.append(("{}".format(record), int("{}".format(template.get(record)))))
    return index_list


def generate_client_exec(workload, workload_type, template_file=None):
    """
    根据config目录下的socket_client.py或者自己指定的模板生成对应客户端对应负载的可执行python文件
    :param workload_type: 负载类型： fio、 vdbench ....
    :param workload: 指定负载文件
    :param template_file: 客户端可执行python模板文件
    :return:
    """
    logger.info("生成客户端执行Python脚本文件")
    # 读取socket_client.py模板文件
    file = template_file if template_file else "{}/config/socket_client.py".format(project_path)
    # 为配置中的每个客户端写一个可执行的socket_client_xxx.py文件
    for i in range(len(CLIENTS)):
        read_file = open(file, 'r', encoding='utf-8')
        client_port = CLIENTS[i].get("client").get("port")
        file_name = "{}_{}.py".format(CLIENT_FILE_PREFIX, CLIENTS[i].get("client").get("hostname"))
        file_path = os.path.join(project_path, "temp", file_name)
        prepare_write(file_path)
        write_file = open(file_path, 'w', encoding='utf-8')
        logger.info("读取客户端执行文件模板 socket_client.py， 生成第 {} 个客户端执行文件".format(i))
        for line in read_file:
            # 替换服务端IP与配置的客户端通信socket_port； 替换负载类型； 替换指定的要执行的负载； 替换要监控的指标；
            write_file.write(line.
                             replace('ip_port = (("10.0.5.63", 9999))', 'ip_port = (("{}", {}))'.
                                     format(SOCK_SERVER_IP, client_port)).
                             replace('workload_type = "fio"', 'workload_type = "{}"'.format(workload_type)).
                             replace('workload = "sequential_write_512k_2thread.fio"',
                                     'workload = "{}"'.format(workload)).
                             replace('record_indexes = []', 'record_indexes = {}'.format(package_record(workload_type))))
        read_file.close()
        write_file.close()


def distribute_exec_file(workload, workload_type):
    """
    向nodes.yml配置中的所有客户端下发指定的测试工作负载
    :param workload_type: 负载类型： fio、 vdbench ....
    :param workload: 负载文件
    :return:
    """
    logger.info("分发生成的客户端可执行Python脚本")
    # 根据config中的客户端与服务端执行文件模板生成每个客户端执行的文件
    generate_client_exec(workload, workload_type)
    # 分发执行文件到每个客户端
    client_ips = list(map(lambda x: x.get('client').get('ip'), CLIENTS))
    client_hostnames = list(map(lambda x: x.get('client').get('hostname'), CLIENTS))
    for idx, ip in enumerate(client_ips):
        logger.info("分发到客户端 {}".format(ip))
        ssh = SSHRemoteOperation(ip)
        # 上传性能客户端python执行文件
        py_file_path = os.path.join(project_path, "temp", "{}_{}.py".format(CLIENT_FILE_PREFIX, client_hostnames[idx]))
        ssh.upload_file(py_file_path, "{}_{}.py".format(CLIENT_FILE_PREFIX, client_hostnames[idx]))
        # 上传性能客户端workload负载文件
        fio_file_path = os.path.join(project_path, "workloads", workload)
        ssh.upload_file(fio_file_path, workload)


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
                    logger.info("Total OSD: {}, Up OSD: {}, In OSD: {}".format(osd_total_num, osd_up_num, osd_in_num))
                    if osd_total_num == osd_up_num == osd_in_num:
                        return True
                except:
                    continue
        time.sleep(5)
    return False


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


# workload = "sequential_read_512k_2thread.fio"
# distribute_exec_file(workload)
# check_ceph_health_status()
# check_ceph_osd_status()
