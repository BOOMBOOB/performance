# coding: utf-8

import socket
import subprocess
import json
import os


client = socket.socket(type=socket.SOCK_DGRAM)
ip_port = (("10.0.5.63", 20023))


def send_data_format(data_line=None):
    """
    格式化客户端向服务端发送的数据格式（json）
    :param data_line: 每次打印的数据行
    :return:
    """
    data = {}
    record_indexes = [('write_clat_avg', 56), ('write_bw', 47), ('write_iops', 48), ('read_bw', 6), ('read_iops', 7), ('read_clat_avg', 15)]
    if data_line is not None:
        split = data_line.split(";")
        for record_index in record_indexes:
            record, index = record_index
            data.update({record: split[index]})
        return data
    else:
        for record_index in record_indexes:
            record, _ = record_index
            data.update({record: '0'})
        return data


def sh(command, send_msg=True):
    """
    执行客户端shell命令
    :param command: shell命令
    :param send_msg: 是否向服务端发送shell命令执行过程
    :return:
    """
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = []
    for line in iter(p.stdout.readline, b''):
        line = line.rstrip().decode('utf8')
        if send_msg:
            content = send_data_format(line)
            content = json.dumps(content).encode('utf-8')
            client.sendto(content, ip_port)

    if p.poll() == 0:
        # fio负载执行结束，发送 0 值使监控得知结束
        content = send_data_format()
        content = json.dumps(content).encode('utf-8')
        client.sendto(content, ip_port)
        # 发送结束讯号，关闭对应的socket服务端
        stop_signal = "exit"
        stop_signal = stop_signal.encode("utf-8")
        client.sendto(stop_signal, ip_port)


def trash_del(file_name):
    """
    删除指定文件（此处用于删除上传的负载文件）
    :param file_name: 文件路径
    :return:
    """
    os.remove(file_name)


workload_type = "fio"
workload = "sequential_read_512k_2thread.fio"
exec_cmd = ""
if workload_type == "fio":
    exec_cmd = "fio {} --output-format=terse --terse-version=3 --eta=never --status-interval=1".format(workload)
if workload_type == "vdbench":
    exec_cmd = "./vdbench {}".format(workload)


sh(exec_cmd)
trash_del(workload)
