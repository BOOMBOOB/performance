# coding: utf-8

import socket
import subprocess
import json
import os


client = socket.socket(type=socket.SOCK_DGRAM)

# 分发客户端前需replace改写的相应配置
ip_port = (("10.0.5.63", 20022))
workload_type = "vdbench"
workload = "sequential_write_512k.vdbench"
work_dir = "/home"
record_indexes = [('write_bw', 12), ('read_bw', 11)]


def send_data_format(data_line=None):
    """
    格式化客户端向服务端发送的数据格式（json）
    :param data_line: 每次打印的数据行
    :return:
    """
    data = {}
    if data_line is not None:
        split = ""
        if workload_type == "fio":
            split = data_line.split(";")
        if workload_type == "vdbench":
            split = data_line.split(" ")
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
            if workload_type == "fio":
                content = send_data_format(line)
                content = json.dumps(content).encode('utf-8')
                client.sendto(content, ip_port)
            if workload_type == "vdbench":
                new_line = ' '.join(line.replace("NaN", "0.00").split())
                if len(new_line.split(" ")) != 27:
                    continue
                else:
                    content = send_data_format(new_line)
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
    abs_path = "{}/{}".format(work_dir, file_name)
    os.remove(abs_path)


exec_cmd = ""
if workload_type == "fio":
    exec_cmd = "fio {}/{} --output-format=terse --terse-version=3 --eta=never --status-interval=1".format(work_dir,
                                                                                                          workload)
if workload_type == "vdbench":
    # 查找/proc目录外的vdbench文件
    exec_cmd = "`find / -path /proc -prune -o -name vdbench -type f -print` -f {}/{} -i 1".format(work_dir, workload)


sh(exec_cmd)
trash_del(workload)
