"""
step1_start_emulator.py — Step 1: 启动 MuMu 模拟器
=====================================================
独立运行：python step1_start_emulator.py
功能：启动 MuMu 模拟器（如果已在运行则跳过）
=====================================================
"""

import logging
import sys
import os

# 添加父目录到路径，以便导入 config 和 emulator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import emulator

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def run_step1() -> bool:
    """
    启动 MuMu 模拟器（如果已经在跑就跳过）。

    返回:
        True  = 成功就绪
        False = 失败
    """
    log.info("=" * 50)
    log.info("Step 1: 启动 MuMu 模拟器")
    log.info("=" * 50)

    # 先看一眼当前状态
    info = emulator.get_emulator_info()
    if info:
        log.info(f"当前模拟器状态: is_android_started={info.get('is_android_started')}")

    ok = emulator.launch_emulator(wait_ready=True, timeout=90)
    if not ok:
        log.error("❌ 模拟器启动失败，请检查：")
        log.error("   1. MuMu12 是否已正确安装")
        log.error("   2. 模拟器是否卡在 BIOS/启动画面")
        log.error(f"   3. config.VM_INDEX={config.VM_INDEX} 是否正确")
        return False

    log.info("✅ 模拟器已就绪")
    return True


if __name__ == "__main__":
    ok = run_step1()
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)