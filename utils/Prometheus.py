from prometheus_client import Gauge

from lib.logee import logger
from config import WORKLOAD_RUN_CONFIG


class Prometheus(object):

    @staticmethod
    def analyse_prometheus_records():
        # 从负载配置文件获取所有 【run】标记为 True，即要运行负载的record s
        load_run = list(map(lambda x: x.get("workload").get("record"),
                            list(filter(lambda x: x.get("workload").get("run") is True,
                                        WORKLOAD_RUN_CONFIG.get("workloads")))))
        records = []
        for item in load_run:
            records = list(set(records).union(set(item)))
        logger.info("由配置可得，监控指标为： {}".format(records))
        return records

    @staticmethod
    def prometheus_declare():
        """
        声明Prometheus数据项，  每次程序启动该方法只能执行一次
        :return:
        """
        records = Prometheus.analyse_prometheus_records()
        prometheus_records = []
        for record in records:
            prometheus_record = Gauge("{}".format(record), "fio {}".format(record.replace("_", " ")), ['client'])
            prometheus_records.append((record, prometheus_record))
        return prometheus_records

    @staticmethod
    def push_data_to_prometheus(msg, client, prometheus_records):
        """
        发送数据到Prometheus
        :param prometheus_records: 声明的Prometheus指标
        :param msg: 要发送的信息
        :param client: 发出信息的客户端
        :return:
        """
        prometheus_records = prometheus_records
        for record, prometheus_record in prometheus_records:
            # get()必须给default值，否则set()会报错
            prometheus_record.labels(client).set(msg.get(record, "0"))
