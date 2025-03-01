#!/usr/bin/env python3
import os
import subprocess
import logging
import signal
import sys
from contextlib import contextmanager
from dependency_parser import get_directory_build_info, extract_build_rules
import time

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("SDCBuilder")

def validate_build_rule(build_rules):
    if not isinstance(build_rules, list) or len(build_rules) == 0:
        return False, "构建规则必须是非空列表"
    for rule in build_rules:
        if not isinstance(rule, str) or not rule.startswith('make '):
            return False, f"无效规则 '{rule}' - 必须是非空字符串且以'make'开头"
    return True, ""

@contextmanager
def safe_subprocess(command: list[str], cwd: str, timeout: int = 300):
    proc = None
    logger = logging.getLogger("SDCBuilder")
    try:
        proc = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid
        )
        logger.debug("🔄 启动进程 (PID: %d): %s", proc.pid, ' '.join(command))
        yield proc
    except Exception as e:
        logger.error("🚨 进程启动失败: %s", str(e))
        raise
    finally:
        if proc and proc.poll() is None:
            logger.warning("🛑 终止未结束的进程 (PID: %d)", proc.pid)
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                logger.error("💀 强制杀死顽固进程 (PID: %d)", proc.pid)
            proc.stdout.close()

def main():
    # 获取当前 main.py 所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取上两层目录
    parent_dir = os.path.dirname(current_dir)
    # 构造 config 目录下 sdc_build_config.yaml 的路径
    file_path = os.path.join(parent_dir, "config", "sdc_build_config.yaml")
    
    # 获取目录和对应的构建规则
    directory_info = get_directory_build_info(file_path)
    # 获取所有构建规则
    all_build_rules = extract_build_rules(file_path)
    
    logger.info("从 sdc_build_config.yaml 中提取的目录信息：")
    for info in directory_info:
        logger.info(f"目录: {info['name']}, 使用规则: {info['rule']}")
    
    logger.info("可用的构建规则：")
    for rule_name, rules in all_build_rules.items():
        logger.info(f"{rule_name}: {rules}")

    # 验证所有构建规则
    for rule_name, rules in all_build_rules.items():
        is_valid, error_msg = validate_build_rule(rules)
        if not is_valid:
            logger.error(f"错误：无效的构建规则 {rule_name} - {error_msg}")
            return

    # 验证所有目录是否存在
    for info in directory_info:
        directory = info['name']
        # 看下目录是否合法 
        full_path = os.path.join(os.path.dirname(parent_dir), directory)
        if not os.path.exists(full_path):
            logger.error(f"错误：目录 {full_path} 不存在 exit")
            sys.exit(1)
        if not os.path.isdir(full_path):
            logger.error(f"错误：{full_path} 不是有效的目录")
            sys.exit(1)

    # 处理每个目录
    for info in directory_info:
        directory = info['name']
        rule_name = info['rule']
        
        # 获取对应的构建规则
        if rule_name not in all_build_rules:
            logger.error(f"错误：找不到构建规则 '{rule_name}' 用于目录 '{directory}'")
            continue
        
        build_rule = all_build_rules[rule_name]
        
        # 构造完整路径
        full_path = os.path.join(os.path.dirname(parent_dir), directory)
        try:
            logger.info(f"\n{'='*30}\n▶ 开始构建目录: {directory} (使用规则: {rule_name})\n{'='*30}")
            total_start = time.time()
            
            for idx, rule in enumerate(build_rule, 1):
                step_start = time.time()
                logger.info("🚀 [%s] 步骤 %d/%d: %s", directory, idx, len(build_rule), rule)
                
                try:
                    with safe_subprocess(rule.split(), cwd=full_path, timeout=180) as proc:
                        for line in proc.stdout:
                            logger.info(f"[{directory}] {line.strip()}")
                        proc.wait()
                        if proc.returncode != 0:
                            raise subprocess.CalledProcessError(proc.returncode, proc.args)
                except subprocess.CalledProcessError as e:
                    logger.error("❌ 步骤失败 [退出码%d] - 命令: %s", e.returncode, e.cmd)
                    logger.error("⚠️ 跳过剩余步骤，继续下一个目录")
                    sys.exit(e.returncode)
                except subprocess.TimeoutExpired:
                    logger.error("⏰ 进程超时: %s", ' '.join(proc.args))
                    sys.exit(1)
                finally:
                    elapsed = time.time() - step_start
                    logger.debug("⏱️ 步骤耗时: %.2fs", elapsed)

            total_duration = time.time() - total_start
            logger.info(f"\n🎉 目录 {directory} 构建成功！总耗时: {total_duration:.1f}s")
            
        except subprocess.CalledProcessError:
            logger.error(f"\n⛔ 构建中止：{directory} 存在失败步骤")
        except Exception as e:
            logger.error(f"\n⚠️ 未捕获异常：{str(e)}")
            
        total_duration = time.time() - total_start
        logger.info(f"🌟 目录 {directory} 构建完成 (总耗时: {total_duration:.2f}秒)")

if __name__ == '__main__':
    main()
