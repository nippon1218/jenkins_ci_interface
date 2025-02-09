#!/usr/bin/env python3
import os
import yaml

def extract_list_from_file(file_path):
    with open(file_path) as f:
        config = yaml.safe_load(f)
    return config.get('directories', [])

def extract_build_rule(file_path):
    with open(file_path) as f:
        config = yaml.safe_load(f)
    return config.get('build_rule', 'make sdc')

# 如果直接运行此模块，可以进行简单测试
if __name__ == "__main__":
    # 自动计算 config 目录中 sdc_dependency.txt 的路径（假设 config 在上一级目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    config_dir = os.path.join(parent_dir, "config")
    file_path = os.path.join(config_dir, "sdc_dependency.txt")
    
    result = extract_list_from_file(file_path)
    print("提取的列表内容：")
    print(result)
