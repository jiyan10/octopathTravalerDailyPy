"""
step6_collect_xianghuo.py — Step 6: 采集香火
=====================================================
独立运行：python step6_collect_xianghuo.py
功能：主菜单→地图→点击香火坐标→确认/取消→关闭→返回主菜单
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


def run_step6(c: MuMuController = None) -> bool:
    """
    采集香火。

    流程：
      1. 确保在主菜单
      2. 点击地图按钮
      3. 点击香火坐标 (145, 960) 两次
      4. 点击取消/确认/关闭
      5. 退出回到主菜单

    参数:
        c : MuMuController 实例（None 则自动创建）

    返回:
        True  = 操作成功
        False = 操作失败
    """
    log.info("=" * 50)
    log.info("Step 6: 采集香火")
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

    # 1. 点击地图按钮
    log.info("点击地图按钮...")
    if not c.find_and_tap_sure(c._pic("menu", "map.png"), retry=3):
        log.warning("⚠️ 未找到地图按钮，继续执行")
    time.sleep(1.0)

    # 2. 点击香火坐标（固定坐标，点击两次）
    log.info("点击香火坐标 (145, 960)...")
    c.tap(145, 960)
    time.sleep(0.3)
    c.tap(145, 960)
    time.sleep(1.0)

    # 3. 点击取消（可能不存在）
    log.info("点击取消...")
    if not c.click_no():
        log.info("⚠️ 未找到取消按钮，继续执行")
    time.sleep(0.5)

    # 4. 点击确认
    log.info("点击确认...")
    if not c.click_sure():
        log.warning("⚠️ 未找到确认按钮，继续执行")
    time.sleep(0.5)

    # 5. 点击关闭
    log.info("点击关闭...")
    if not c.click_close():
        log.info("⚠️ 未找到关闭按钮，继续执行")
    time.sleep(0.5)

    # 6. 退出所有弹窗回到主菜单
    log.info("退出弹窗回到主菜单...")
    c.normal_exit()

    log.info("✅ Step 6 执行完成")
    return True


if __name__ == "__main__":
    ok = run_step6()
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)