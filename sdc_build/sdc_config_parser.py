#!/usr/bin/env python3
import os
import yaml

def extract_list_from_file(file_path):
    with open(file_path) as f:
        config = yaml.safe_load(f)
    return config.get('directories', [])

def extract_build_rules(file_path):
    """
    从配置文件中提取所有构建规则
    返回一个字典，键为规则名称，值为规则列表
    """
    with open(file_path) as f:
        config = yaml.safe_load(f)
    
    # 创建一个包含所有构建规则的字典
    rules = {}
    
    # 添加所有包含 "rule" 的配置项
    for key in config:
        if 'rule' in key.lower() and isinstance(config[key], list):
            rules[key] = config[key]
    
    return rules

def get_directory_build_info(file_path):
    """
    从配置文件中提取目录和对应的构建规则
    返回一个列表，每个元素是包含目录名和规则名的字典
    """
    with open(file_path) as f:
        config = yaml.safe_load(f)
    
    directories = config.get('directories', [])
    result = []
    
    for directory in directories:
        if isinstance(directory, dict) and 'name' in directory:
            result.append({
                'name': directory['name'],
                'rule': directory.get('rule', 'build_rule')  # 默认使用build_rule
            })
    
    return result

# 如果直接运行此模块，可以进行简单测试
if __name__ == "__main__":
    # 自动计算 config 目录中 sdc_build_config.yaml 的路径（假设 config 在上一级目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    config_dir = os.path.join(parent_dir, "config")
    file_path = os.path.join(config_dir, "sdc_build_config.yaml")
    
    result = get_directory_build_info(file_path)
    print("提取的目录和规则：")
    print(result)
    
    rules = extract_build_rules(file_path)
    print("提取的构建规则：")
    print(rules)
