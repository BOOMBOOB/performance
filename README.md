### **说明：**

​	SOCKET服务端监听性能测试客户端传输的指定实时性能监控参数（UDP）

​	SOCKET服务端将监听接收到的指标在Prometheus注册并实时上传

手动搭建Prometheus和Grafana服务后配置好数据源及展示panel即可以实时图形化的方式查看实时的性能测试情况



### **工程目录结构：**

├─bin
│  │  functions.py								# 公用的方法
│  │  prometheus_bin.py						# 启动服务时启动Prometheus，可浏览器访问 IP:端口   查看
│  │  service_start.py							# 仅启动负载
│  │  __init__.py
│
├─config
│  │  fio_terse3.yml							# fio terse格式输出参数解析模板
│  │  log.yml									# 工程日志模块配置
│  │  nodes.yml								# 测试节点配置：socket服务端节点、存储节点、性能客户端节点
│  │  socket_client.py							# socket客户端执行文件模板
│  │  socket_server.py							# socket服务端
│  │  vdbench_out.yml							# vdbench输出参数解析模板
│  │  workload_run.yml						# 性能测试负载配置
│  │  yml_agrs_parse.py						# yml配置解析
│
├─lib
│  │  logee.py								# 工程日志
│  │  MyThreadWithResult.py					# 多线程
│  │  SSHRemoteOperation.py					# SSH远程
│  │  __init__.py
│
├─log										# 日志目录
│      log.txt
│
├─temp										# 程序运行时处理socket_client写到此处后分发到性能客户端
│      socket_client_node6.py
│      socket_client_node7.py
│      socket_client_node8.py
│
├─workloads								# 负载配置文件
│      sequential_read_512k.vdbench
│      sequential_read_512k_2thread.fio
│      sequential_write_512k.vdbench
│      sequential_write_512k_2thread.fio



### 暂未完成：

- vdbench部分
- 统计所有性能客户端同一时刻总的性能情况
- 监控存储节点的磁盘、内存、cpu情况，以及存储自身的性能统计（ceph情况下）
- 接入cosbench