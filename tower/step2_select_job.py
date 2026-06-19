"""
step2_select_job.py — Step 2: 选择职业
=====================================================
功能：在试炼之塔中选择职业
流程：
  1. 查找并点击职业按钮
  2. 如果找不到，执行滑动后重试
  3. 点击"进入试炼之塔"按钮
=====================================================
"""

import logging
import time
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
from core import MuMuController

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def adb_swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
    """使用 ADB 执行滑动操作"""
    cmd = [
        config.MUMU_CLI,
        "adb",
        "--vmindex", str(config.VM_INDEX),
        "--cmd", "shell", "input", "swipe",
        str(x1), str(y1), str(x2), str(y2), str(duration_ms)
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.returncode == 0
    except Exception as e:
        log.warning(f"ADB 滑动失败: {e}")
        return False


def find_and_click_job(c: MuMuController, job: str, retry: int = 3) -> bool:
    """
    查找职业按钮并点击，找不到则下滑重试。

    参数:
        c     : MuMuController 实例
        job   : 职业名称
        retry : 最大重试次数

    返回:
        True  = 成功找到并点击
        False = 失败
    """
    job_path = c._pic("menu", "zhiyeta", f"{job}.png")
    enter_path = c._pic("menu", "zhiyeta", "jinrushilianzhita.png")

    for attempt in range(retry):
        log.info(f"查找职业 {job}，第 {attempt + 1} 次...")

        # 尝试点击职业按钮
        if c.find_and_tap(job_path, threshold=0.9):
            log.info(f"成功点击 {job}")
            time.sleep(0.3)

            # 点击"进入试炼之塔"
            if c.find_and_tap_sure(enter_path, retry=2):
                return True

        # 如果找不到，执行下滑操作
        if attempt < retry - 1:
            log.info(f"未找到 {job}，执行下滑...")
            adb_swipe(200, 700, 200, 300)  # 从下往上滑
            time.sleep(1)

    log.warning(f"经过 {retry} 次尝试，仍未找到 {job}")
    return False


def run_step2(c: MuMuController, job: str) -> bool:
    """
    选择职业。

    参数:
        c    : MuMuController 实例
        job  : 职业名称 (lieren, xingguan, xuezhe, youxia, yaoshi, jianshi, shangren, wuzhe)

    返回:
        True  = 成功选择职业
        False = 失败
    """
    log.info("=" * 50)
    log.info(f"Step 2: 选择职业 {job}")
    log.info("=" * 50)

    if not find_and_click_job(c, job, retry=3):
        return False

    log.info("✅ 职业选择完成")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", default="lieren", help="职业名称")
    args = parser.parse_args()

    c = MuMuController()
    ok = run_step2(c, args.job)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    sys.exit(0 if ok else 1)
