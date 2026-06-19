"""
step10_get_honor.py — Step 10: 领取荣耀
=====================================================
独立运行：python step10_get_honor.py
功能：主菜单→菜单→荣耀→一键领取→攻击→领取→返回主菜单
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


def run_step10(c: MuMuController = None) -> bool:
    """
    领取荣耀。

    流程：
      1. 确保在主菜单
      2. 点击菜单按钮
      3. 点击荣耀按钮
      4. 点击一键领取
      5. 点击确定
      6. 点击攻击
      7. 点击一键领取
      8. 点击确定
      9. 退出回到主菜单

    参数:
        c : MuMuController 实例（None 则自动创建）

    返回:
        True  = 操作成功
        False = 操作失败
    """
    log.info("=" * 50)
    log.info("Step 10: 领取荣耀")
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

    # 2. 点击荣耀按钮
    log.info("点击荣耀按钮...")
    if not c.find_and_tap_sure(c._pic("menu", "honor.png"), retry=3):
        log.warning("⚠️ 未找到荣耀按钮，继续执行")
    time.sleep(1.0)

    # 3. 点击一键领取
    log.info("点击一键领取...")
    if not c.find_and_tap_sure(c._pic("menu", "honor", "yijianhuode.png"), retry=3):
        log.warning("⚠️ 未找到一键领取按钮，继续执行")
    time.sleep(1.0)

    # 4. 点击确定
    log.info("点击确定...")
    if not c.click_sure():
        log.warning("⚠️ 未找到确定按钮，继续执行")
    time.sleep(1.0)

    # 5. 点击攻击
    log.info("点击攻击...")
    if not c.find_and_tap_sure(c._pic("menu", "honor", "gongji.png"), retry=3):
        log.warning("⚠️ 未找到攻击按钮，继续执行")
    time.sleep(1.0)

    # 6. 点击一键领取
    log.info("点击一键领取...")
    if not c.find_and_tap_sure(c._pic("menu", "honor", "yijianhuode.png"), retry=3):
        log.warning("⚠️ 未找到一键领取按钮，继续执行")
    time.sleep(1.0)

    # 7. 点击确定
    log.info("点击确定...")
    if not c.click_sure():
        log.warning("⚠️ 未找到确定按钮，继续执行")
    time.sleep(1.0)

    # 8. 退出回到主菜单
    log.info("退出弹窗回到主菜单...")
    c.normal_exit()

    log.info("✅ Step 10 执行完成")
    return True


if __name__ == "__main__":
    ok = run_step10()
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)