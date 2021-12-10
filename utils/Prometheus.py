import time
from prometheus_client import Gauge

from lib.logee import logger
from config import WORKLOAD_RUN_CONFIG, NODE_CONFIG


def get_clients():
    return list(map(lambda x: x.get("client").get("hostname"), NODE_CONFIG.get("clients")))


class Prometheus(object):

    def __init__(self):
        names = self.__dict__
        names["clients"] = get_clients()
        names["timer"] = 0
        records = Prometheus.analyse_prometheus_records()
        for record in records:
            names[record] = float(0)

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
        for record, prometheus_record in prometheus_records:
            # get()必须给default值，否则set()会报错
            if "lat" in record and client == "total":
                continue
            prometheus_record.labels(client).set(msg.get(record, "0"))

    @staticmethod
    def counter_reset(counter, data):
        for r in data.keys():
            counter[r] = float(0)

    @staticmethod
    def count_total_for_prometheus(counter, data: dict, f_time):
        """
        获取并处理各个数据来源（客户端、...）的同类型数据
        :param counter:
        :param f_time: 数据传入时间（ 0.1秒级误差 ）
        :param data: 性能数据   dict
        :return: total_read_bw ...
        """
        if counter["timer"] == f_time:
            for key, value in data.items():
                if "lat" in key:
                    continue
                counter[key] += float(value)
        else:
            print("计数器判定timer不满足，重置...")
            print("counter: ", counter)
            Prometheus.counter_reset(counter, data)
            counter["timer"] = f_time

            for key, value in data.items():
                if "lat" in key:
                    continue
                counter[key] += float(value)
        pass


if __name__ == '__main__':
    p = Prometheus.prometheus_declare()
    print(p)
