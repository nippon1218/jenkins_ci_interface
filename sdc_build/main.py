#!/usr/bin/env python3
import os
import subprocess
import logging
import signal
from contextlib import contextmanager
from dependency_parser import extract_list_from_file, extract_build_rule
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
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    # 构造 config 目录下 sdc_build_config.yaml 的路径
    file_path = os.path.join(current_dir, "../config", "sdc_build_config.yaml")
    
    sdc_list = extract_list_from_file(file_path)
    build_rule = extract_build_rule(file_path)
    logger.info("从 sdc_build_config.yaml 中提取的列表：")
    logger.info(sdc_list)
    logger.info(f"构建规则: {build_rule}")

    # 验证构建规则
    is_valid, error_msg = validate_build_rule(build_rule)
    if not is_valid:
        logger.error(f"错误：无效的构建规则 - {error_msg}")
        return

    for directory in sdc_list:
        # 构造完整路径
        full_path = os.path.join(parent_dir, directory)
        try:
            if not os.path.exists(full_path):
                logger.error(f"错误：目录 {full_path} 不存在")
                continue
            if not os.path.isdir(full_path):
                logger.error(f"错误：{full_path} 不是有效的目录")
                continue
            logger.info(f"\n{'='*30}\n▶ 开始构建目录: {directory}\n{'='*30}")
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
                    raise
                except subprocess.TimeoutExpired:
                    logger.error("⏰ 进程超时: %s", ' '.join(proc.args))
                    raise
                finally:
                    elapsed = time.time() - step_start
                    logger.debug("⏱️ 步骤耗时: %.2fs", elapsed)

            total_duration = time.time() - total_start
            logger.info(f"\n🎉 目录 {directory} 构建成功！总耗时: {total_duration:.1f}s")
            
        except subprocess.CalledProcessError:
            logger.error(f"\n⛔ 构建中止：{directory} 存在失败步骤")
        except Exception as e:
            logger.error(f"\n⚠️ 未捕获异常：{str(e)}")

if __name__ == '__main__':
    main()
