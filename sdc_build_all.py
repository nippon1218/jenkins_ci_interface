#!/usr/bin/env python3
"""
SDC构建工具 - 入口点
根据配置文件中指定的目录和构建规则执行构建过程
"""
import os
import sys
import logging

# 添加sdc_build目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'sdc_build'))

# 导入main模块
from main import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("SDCBuilder")
    logger.info("开始SDC构建流程")
    
    try:
        main()
        logger.info("SDC构建流程完成")
    except Exception as e:
        logger.error(f"SDC构建流程失败: {str(e)}")
        sys.exit(1)
