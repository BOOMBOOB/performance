import socket
import time

from common.workloads import WorkLoad
from lib.logee import logger
from config import NODE_CONFIG
from utils.Prometheus import Prometheus


def socket_server(client, port, prometheus_records, counter, lock):
    """
    启动socket server服务端，接收客户端发送的实时数据
    :param prometheus_records: 声明的Prometheus监控指标
    :param client: 客户端
    :param port: 启动对应客户端socket监听的端口
    :return:
    """
    if isinstance(type(port), int):
        use_port = port
    else:
        use_port = int(port)

    server_ip = NODE_CONFIG.get("sock_server").get("ip")
    server = socket.socket(type=socket.SOCK_DGRAM)
    workload_nums = WorkLoad.traversal_run_workloads()
    try:
        server.bind(("{}".format(server_ip), use_port))
        logger.info("服务端开启，接收客户端 {} 消息中....".format(client))

        client_workload_runtimes = 0
        while True:
            msg, addr = server.recvfrom(1024)
            msg = msg.decode('utf-8')
            logger.info("客户端 {} 发送给服务端： {}".format(client, msg))

            if msg == "exit":
                client_workload_runtimes += 1
                if client_workload_runtimes < len(workload_nums):
                    logger.info("客户端 {} 第 {} 个工作负载执行完毕......".format(client, client_workload_runtimes))
                else:
                    logger.info("客户端 {} 执行完毕，等待服务端关闭！！".format(client))
                    break
            else:
                lock.acquire()
                Prometheus.count_total_for_prometheus(counter, eval(msg), int(time.time()))
                lock.release()
                Prometheus.push_data_to_prometheus(counter, "total", prometheus_records)
                # 将客户端发送到服务端的数据push到Prometheus
                Prometheus.push_data_to_prometheus(eval(msg), client, prometheus_records)

    except Exception as e:
        logger.info("开启服务端监听异常： ", e)
    finally:
        logger.info("服务端 SOCKET 关闭 ！！  PORT: {}".format(use_port))
        server.close()


if __name__ == '__main__':
    from prometheus_client import start_http_server
    start_http_server(9091)
    clients = NODE_CONFIG["clients"]
    ports = list(map(lambda x: x.get("client").get("port"), clients))
    print(ports, type(ports))
