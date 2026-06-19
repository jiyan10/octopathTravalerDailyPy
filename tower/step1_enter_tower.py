"""
step1_enter_tower.py — Step 1+2: 进入试炼之塔并选择职业
=====================================================
功能：
  1. 确保在主菜单
  2. 点击"塔·游戏盘"按钮
  3. 点击"试炼之塔"按钮
  4. 查找并点击职业按钮（下滑重试）
  5. 点击"进入试炼之塔"按钮
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
import actions

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


def run_step1(c: MuMuController, job: str) -> bool:
    """
    进入试炼之塔并选择职业。

    参数:
        c    : MuMuController 实例
        job  : 职业名称

    返回:
        True  = 成功进入并选择职业
        False = 失败
    """
    log.info("=" * 50)
    log.info(f"Step 1+2: 进入试炼之塔并选择职业 {job}")
    log.info("=" * 50)

    # 确保在主菜单
    if not actions.is_in_main_menu(c):
        log.warning("当前不在主菜单，尝试退出弹窗...")
        c.normal_exit()
        if not actions.wait_for_main_menu(c, timeout=10):
            log.warning("⚠️ 无法确认是否在主菜单，继续执行")

    # 1. 点击"塔·游戏盘"按钮
    log.info("点击「塔·游戏盘」...")
    ta_path = c._pic("menu", "zhiyeta", "ta_youxipan.png")
    if not c.find_and_tap_sure(ta_path, retry=3):
        log.warning("⚠️ 未找到塔·游戏盘按钮")
        return False
    time.sleep(0.5)

    # 2. 点击"试炼之塔"按钮
    log.info("点击「试炼之塔」...")
    shilian_path = c._pic("menu", "zhiyeta", "shilianzhita.png")
    if not c.find_and_tap_sure(shilian_path, retry=3):
        log.warning("⚠️ 未找到试炼之塔按钮")
        return False
    time.sleep(2)

    # 3. 查找职业塔，找不到则下滑重试
    job_path = c._pic("menu", "zhiyeta", f"{job}.png")
    log.info(f"查找职业塔 {job}...")
    
    pos = None
    for attempt in range(5):
        pos = c.find_image(job_path, threshold=0.9)
        if pos:
            break
        log.info(f"第 {attempt + 1} 次未找到，下滑...")
        c.mumu_swipe(540, 800, 540, 400, duration_ms=300)
        time.sleep(0.5)
    
    if not pos:
        log.warning(f"⚠️ 未找到职业塔 {job}")
        return False
    
    log.info(f"长按职业塔 {job} 两次...")
    for attempt in range(2):
        log.info(f"第 {attempt + 1} 次长按职业塔 {job}: ({pos[0]}, {pos[1]})")
        c.long_press(pos[0], pos[1], duration_ms=1000)
        time.sleep(0.5)
    time.sleep(0.5)

    # 3.5 检查是否已通关（fivefive.png 表示已打过的职业塔）
    fivefive_path = c._pic("menu", "zhiyeta", "fivefive.png")
    if c.is_visible(fivefive_path, threshold=0.9):
        log.info(f"✅ 职业 {job} 已通关（发现 fivefive.png），跳过")
        return False
    time.sleep(0.5)

    # 3.6 检查是否出现"尚未开始"，如果是则跳过该职业
    shangwei_path = c._pic("menu", "zhiyeta", "shangweikaishi.png")
    if c.is_visible(shangwei_path):
        log.info(f"⚠️ {job} 尚未开始，跳过该职业")
        return False

    # 4. 点击"进入试炼之塔"按钮
    log.info("点击「进入试炼之塔」...")
    enter_path = c._pic("menu", "zhiyeta", "jinrushilianzhita.png")
    if not c.find_and_tap_sure(enter_path, retry=3):
        log.warning("⚠️ 未找到进入试炼之塔按钮")
        return False

    log.info("✅ 已进入试炼之塔并选择职业")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", default="lieren", help="职业名称")
    args = parser.parse_args()

    c = MuMuController()
    ok = run_step1(c, args.job)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    sys.exit(0 if ok else 1)
