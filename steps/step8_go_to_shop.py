"""
step8_go_to_shop.py — Step 8: 商店购买碎片
=====================================================
独立运行：python step8_go_to_shop.py
功能：主菜单→商店→道具商店→装备系→米奇碎片→购买
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


def run_step8(c: MuMuController = None) -> bool:
    """
    商店购买碎片。

    流程：
      1. 确保在主菜单
      2. 点击菜单按钮
      3. 点击商店按钮
      4. 点击道具商店
      5. 点击装备系
      6. 点击米奇碎片
      7. 循环购买直到 max 出现
      8. 退出回到主菜单

    参数:
        c : MuMuController 实例（None 则自动创建）

    返回:
        True  = 操作成功
        False = 操作失败
    """
    log.info("=" * 50)
    log.info("Step 8: 商店购买碎片")
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

    # 2. 点击商店按钮
    log.info("点击商店按钮...")
    if not c.find_and_tap_sure(c._pic("menu", "shop.png"), retry=3):
        log.warning("⚠️ 未找到商店按钮，继续执行")
    time.sleep(1.0)

    # 3. 点击亿道大碎片
    log.info("点击亿道大碎片...")
    if not c.find_and_tap_sure(c._pic("menu", "shop", "yidaodedaopian.png"), retry=3):
        log.warning("⚠️ 未找到亿道大碎片按钮，继续执行")
    time.sleep(1.0)

    # 4. 点击装备系
    log.info("点击装备系...")
    if not c.find_and_tap_sure(c._pic("menu", "shop", "zhuangbeixi.png"), retry=3):
        log.warning("⚠️ 未找到装备系按钮，继续执行")
    time.sleep(1.0)

    # 5. 点击米奇碎片
    log.info("点击米奇碎片...")
    if not c.find_and_tap_sure(c._pic("menu", "shop", "mijisuipian.png"), retry=3):
        log.warning("⚠️ 未找到米奇碎片按钮，继续执行")
    time.sleep(1.0)

    # 6. 点击获取碎片
    log.info("点击获取碎片...")
    if not c.find_and_tap_sure(c._pic("menu", "shop", "huodesuipian.png"), retry=3):
        log.warning("⚠️ 未找到获取碎片按钮，继续执行")
    time.sleep(1.0)

    # 7. 循环购买直到 max 出现（最多3次）
    log.info("开始循环购买...")
    max_count = 0
    while c.is_visible(c._pic("menu", "shop", "max.png")):
        if max_count >= 3:
            log.info("⚠️ 已达到最大购买次数（3次），停止购买")
            break

        max_count += 1
        log.info(f"第 {max_count} 次购买...")

        # 点击 max 按钮
        log.info("点击 max 按钮...")
        if not c.find_and_tap_sure(c._pic("menu", "shop", "max.png"), retry=3):
            log.warning("⚠️ 未找到 max 按钮，退出循环")
            break
        time.sleep(0.5)

        # 点击获取碎片1
        log.info("点击获取碎片1...")
        if not c.find_and_tap_sure(c._pic("menu", "shop", "huodesuipian1.png"), retry=3):
            log.warning("⚠️ 未找到获取碎片1按钮，退出循环")
            break
        time.sleep(0.5)

        # 点击购买坐标
        log.info("点击购买坐标 (1185, 934)...")
        c.tap(1185, 934)
        time.sleep(0.3)

        # 点击确定
        log.info("点击确定...")
        c.click_sure()
        time.sleep(0.5)

    # 7. 退出回到主菜单
    log.info("退出弹窗回到主菜单...")
    c.normal_exit()

    log.info(f"✅ Step 8 执行完成，共购买 {max_count} 次")
    return True


if __name__ == "__main__":
    ok = run_step8()
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)