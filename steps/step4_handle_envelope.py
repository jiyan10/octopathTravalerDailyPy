"""
step4_handle_envelope.py — Step 4: 领取信封奖励
=====================================================
独立运行：python step4_handle_envelope.py
功能：菜单→信件→一键领取→确定
=====================================================
"""

import logging
import sys
import os
import time

# 添加父目录到路径，以便导入 config 和 core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core import MuMuController
import actions

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


def run_step4(c: MuMuController = None) -> bool:
    """
    领取信封奖励（简化版：菜单→信件→一键领取→确定）。

    流程：
      1. 确保在主菜单
      2. 点击菜单按钮
      3. 点击信件按钮
      4. 点击一键领取
      5. 点击确定
      6. 退出所有弹窗回到主菜单

    参数:
        c : MuMuController 实例（None 则自动创建）

    返回:
        True  = 领取成功
        False = 领取失败
    """
    log.info("=" * 50)
    log.info("Step 4: 领取信封奖励")
    log.info("=" * 50)

    # 创建控制器
    if c is None:
        c = MuMuController()

    # 确保在主菜单
    if not actions.is_in_main_menu(c):
        log.warning("当前不在主菜单，尝试退出弹窗...")
        c.normal_exit()
        if not actions.wait_for_main_menu(c, timeout=10):
            log.warning("⚠️ 无法确认是否在主菜单，继续执行")

    # 1. 点击菜单按钮
    log.info("点击菜单按钮...")
    if not c.find_and_tap_sure(c._pic("menu", "menu.png"), retry=3):
        log.warning("⚠️ 未找到菜单按钮，继续执行")
    time.sleep(1.0)

    # 2. 点击信件按钮
    log.info("点击信件按钮...")
    if not c.find_and_tap_sure(c._pic("menu", "envelop.png"), retry=3):
        log.warning("⚠️ 未找到信件按钮，继续执行")
    time.sleep(1.0)

    # 3. 处理信封1
    log.info("处理信封1...")
    if c.find_and_tap_sure(c._pic("menu", "envelope", "1.png"), retry=3):
        time.sleep(0.5)
        
        # 点击一键领取
        log.info("点击一键领取...")
        if c.find_and_tap_sure(c._pic("menu", "envelope", "get.png"), retry=3):
            time.sleep(0.5)
            
            # 点击确定（如果有）
            log.info("点击确定...")
            c.click_sure()
            
        # 点击空白处关闭弹窗
        log.info("点击空白处关闭弹窗...")
        for _ in range(3):
            c.tap_empty()
            time.sleep(0.5)

    # 4. 处理信封2
    log.info("处理信封2...")
    if c.find_and_tap_sure(c._pic("menu", "envelope", "2.png"), retry=3):
        time.sleep(0.5)
        
        # 点击一键领取
        log.info("点击一键领取...")
        if c.find_and_tap_sure(c._pic("menu", "envelope", "get.png"), retry=3):
            time.sleep(0.5)
            
            # 点击确定（如果有）
            log.info("点击确定...")
            c.click_sure()
            
        # 点击空白处关闭弹窗
        log.info("点击空白处关闭弹窗...")
        for _ in range(3):
            c.tap_empty()
            time.sleep(0.5)

    # 5. 退出所有弹窗回到主菜单
    log.info("退出弹窗回到主菜单...")
    c.normal_exit()

    log.info("✅ Step 4 执行完成")
    return True


if __name__ == "__main__":
    ok = run_step4()
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)