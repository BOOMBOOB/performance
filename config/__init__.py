from utils.Yml import Args


NODE_CONFIG = Args("nodes.yml").get_yml_data()
LOG_CONFIG = Args("log.yml").get_yml_data()
WORKLOAD_RUN_CONFIG = Args("workload_run.yml").get_yml_data()
WORKLOAD_FIO_TEMPLATE = Args("fio_terse3.yml").get_yml_data()
WORKLOAD_VDBENCH_TEMPLATE = Args("vdbench_out.yml").get_yml_data()
