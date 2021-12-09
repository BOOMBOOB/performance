import yaml
import os
from bin import project_path


class Args:

    def __init__(self, yaml_file=None):
        self.yaml_file = yaml_file

    def get_yml_data(self):
        """
        解析yml配置文件为json格式
        :return:
        """
        # 判断传参yaml_file是否在config目录下存在且为文件
        yaml_file_path = os.path.join(project_path, "config", self.yaml_file)
        if not os.path.isfile(yaml_file_path):
            print("配置文件不存在")
            return

        with open(yaml_file_path, 'r', encoding='utf-8') as f:
            data = f.read()
        f.close()

        data_dict = yaml.load(data)
        return data_dict
