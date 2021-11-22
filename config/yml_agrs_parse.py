import yaml
import os
from bin import project_path


class Args:

    def get_yml_data(self, yaml_file):
        """
        解析yml配置文件为json格式
        :param yaml_file: config目录下的yml配置文件
        :return:
        """
        # 判断传参yaml_file是否在config目录下存在且为文件
        yaml_file_path = os.path.join(project_path, "config", yaml_file)
        if not os.path.isfile(yaml_file_path):
            print("配置文件不存在")
            return

        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            data = f.read()
        f.close()

        data_dict = yaml.load(data)
        return data_dict


if __name__ == '__main__':
    args = Args()
    res = args.get_yml_data("workload_run.yml")
    # load_run = list(filter(lambda x: x.get("workload").get("run") is True, res.get("workloads")))
    # load_run = list(map(lambda x: x.get("workload").get("record"),
    #                     list(filter(lambda x: x.get("workload").get("run") is True, res.get("workloads")))))
    # load_run = list(map(lambda x: x.get("workload").get("record"), res.get("workloads")))
    # records = []
    # for item in load_run:
    #     records = list(set(records).union(set(item)))
    # print(load_run)
    # print(records)