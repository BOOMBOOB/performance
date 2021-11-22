import time

from lib.MyThreadWithResult import ParallelOperation
from lib.SSHRemoteOperation import SSHRemoteOperation
from config.yml_agrs_parse import Args
from config.socket_server import socket_server, prometheus_declare
from bin.functions import CLIENT_FILE_PREFIX, distribute_exec_file, check_ceph_health_status, check_ceph_osd_status, \
    traversal_run_workloads
from lib.logee import logger

NODE_CONFIG = Args().get_yml_data("nodes.yml")
WORKLOAD_RUN_CONFIG = Args().get_yml_data("workload_run.yml")


tp = ParallelOperation()


def start_server_service(workloads):
    """
    启动nodes.yml中配置的所有客户端对应的服务端socket监听
    :return:
    """
    prometheus_records = prometheus_declare()
    logger.info("启动服务端SOCKET SERVER监听")
    # 默认服务端为本机时的启动方式
    for node in NODE_CONFIG.get("clients"):
        node = node.get("client")
        client = node.get("hostname")
        port = node.get("port")
        tp.add(socket_server, args=(client, port, prometheus_records))
    tp.start()
    tp.clear()
    pass


def start_client_service():
    """
    所有nodes.yml中配置的客户端执行测试负载
    :return:
    """
    logger.info("启动客户端工作")
    # 并发执行ssh命令运行socket_client_xxx.py脚本
    for node in NODE_CONFIG.get("clients"):
        node = node.get("client")
        client_ip = node.get("ip")
        client_name = node.get("hostname")
        client_work_dir = node.get("work_dir")
        ssh = SSHRemoteOperation(client_ip)
        run_cmd = "nohup python {}/{}_{}.py".format(client_work_dir, CLIENT_FILE_PREFIX, client_name)
        tp.add(ssh.ssh_connect, cmd=run_cmd)
    tp.start()
    tp.join()
    pass


def workflow():
    """
    定义工作流程
    :return:
    """
    workloads = traversal_run_workloads()

    start_server_service(workloads)
    time.sleep(10)

    check = NODE_CONFIG.get("ceph").get("level")
    for work_type, work in workloads:
        if "none" not in check:
            if "health" in check:
                logger.info("检查 Ceph 状态....")
                check_ceph_health_status()
            if "osd" in check:
                logger.info("检查 OSD 状态....")
                check_ceph_osd_status()
            if "ops" in check:
                pass
        logger.info("分发 {} 工作： {}".format(work_type, work))
        distribute_exec_file(work, work_type)
        start_client_service()


if __name__ == '__main__':

    workflow()
