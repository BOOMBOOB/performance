from utils.Prometheus import Prometheus
from lib.logee import logger
from lib.SSHRemoteOperation import SSHRemoteOperation
from bin import project_path
from config import NODE_CONFIG, WORKLOAD_RUN_CONFIG, WORKLOAD_FIO_TEMPLATE, WORKLOAD_VDBENCH_TEMPLATE

import os

CLIENTS = NODE_CONFIG.get("clients")
CLIENT_FILE_PREFIX = "socket_client"
SOCK_SERVER_IP = NODE_CONFIG.get("sock_server").get("ip")


class WorkLoad(object):

    @staticmethod
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

    @staticmethod
    def package_record(workload_type):
        records = Prometheus.analyse_prometheus_records()
        template = None
        if workload_type == "fio":
            template = WORKLOAD_FIO_TEMPLATE.get("fio")
        if workload_type == "vdbench":
            template = WORKLOAD_VDBENCH_TEMPLATE.get("vdbench")
        index_list = []
        for record in records:
            if template.get(record):
                index_list.append(("{}".format(record), int("{}".format(template.get(record)))))
        return index_list

    @staticmethod
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
        file = template_file if template_file else "{}/config/socket_performance_client.py".format(project_path)
        # 为配置中的每个客户端写一个可执行的socket_client_xxx.py文件
        for i in range(len(CLIENTS)):
            read_file = open(file, 'r', encoding='utf-8')
            client_port = CLIENTS[i].get("client").get("port")
            client_work_dir = CLIENTS[i].get("client").get("work_dir")
            record_indexes = WorkLoad.package_record(workload_type)

            file_name = "{}_{}.py".format(CLIENT_FILE_PREFIX, CLIENTS[i].get("client").get("hostname"))
            file_path = os.path.join(project_path, "temp", file_name)
            if os.path.isfile(file_path):
                os.unlink(file_path)
            write_file = open(file_path, 'w', encoding='utf-8')
            logger.info("读取客户端执行文件模板 socket_performance_client.py， 生成第 {} 个客户端执行文件".format(i))
            for line in read_file:
                write_file.write(line.
                                 # 替换socket通信的端口
                                 replace('ip_port = (("10.0.5.63", 9999))', 'ip_port = (("{}", {}))'.
                                         format(SOCK_SERVER_IP, client_port)).
                                 # 替换测试负载类型
                                 replace('workload_type = "fio"', 'workload_type = "{}"'.format(workload_type)).
                                 # 替换测试负载配置文件
                                 replace('workload = "sequential_write_512k_2thread.fio"',
                                         'workload = "{}"'.format(workload)).
                                 # 替换要监控的指标
                                 replace('record_indexes = []', 'record_indexes = {}'.format(record_indexes)).
                                 replace('work_dir = ""', 'work_dir = "{}"'.format(client_work_dir)))
            read_file.close()
            write_file.close()

    @staticmethod
    def distribute_exec_file(workload, workload_type):
        """
        向nodes.yml配置中的所有客户端下发指定的测试工作负载
        :param workload_type: 负载类型： fio、 vdbench ....
        :param workload: 负载文件
        :return:
        """
        logger.info("分发生成的客户端可执行Python脚本")
        # 根据config中的客户端与服务端执行文件模板生成每个客户端执行的文件
        WorkLoad.generate_client_exec(workload, workload_type)
        # 分发执行文件到每个客户端
        client_ips = list(map(lambda x: x.get('client').get('ip'), CLIENTS))
        client_hostnames = list(map(lambda x: x.get('client').get('hostname'), CLIENTS))
        client_remote_dir = list(map(lambda x: x.get('client').get('work_dir'), CLIENTS))
        for idx, ip in enumerate(client_ips):
            logger.info("分发到客户端 {}".format(ip))
            ssh = SSHRemoteOperation(ip)
            # 上传性能客户端python执行文件到配置的工作目录
            py_file_path = os.path.join(project_path, "temp",
                                        "{}_{}.py".format(CLIENT_FILE_PREFIX, client_hostnames[idx]))
            ssh.upload_file(py_file_path, "{}/{}_{}.py".format(client_remote_dir[idx], CLIENT_FILE_PREFIX,
                                                               client_hostnames[idx]))
            # 上传性能客户端workload负载文件到配置的工作目录
            workload_file_path = os.path.join(project_path, "workloads", workload)
            ssh.upload_file(workload_file_path, "{}/{}".format(client_remote_dir[idx], workload))
