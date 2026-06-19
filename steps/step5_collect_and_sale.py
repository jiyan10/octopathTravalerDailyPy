"""
step5_collect_and_sale.py — Step 5: 采集并出售生物
=====================================================
独立运行：python step5_collect_and_sale.py
功能：主菜单→地图→回收→确认→确定→返回主菜单
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


def run_step5(c: MuMuController = None) -> bool:
    """
    采集并出售生物（回收资源）。

    流程：
      1. 确保在主菜单
      2. 点击地图按钮
      3. 等待地图加载
      4. 点击回收按钮
      5. 点击确认
      6. 点击确定
      7. 退出所有弹窗回到主菜单

    参数:
        c : MuMuController 实例（None 则自动创建）

    返回:
        True  = 操作成功
        False = 操作失败
    """
    log.info("=" * 50)
    log.info("Step 5: 采集并出售生物（回收资源）")
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

    # 2. 点击回收按钮
    log.info("点击回收按钮...")
    if not c.find_and_tap_sure(c._pic("map", "huishou.png"), retry=3):
        log.warning("⚠️ 未找到回收按钮，继续执行")
    time.sleep(0.5)

    # 3. 检查回收界面是否出现（确认按钮是否存在）
    # 如果确认按钮不存在，说明没有可回收的东西，直接退出
    log.info("检查回收界面是否出现...")
    if not c.is_visible(c._pic("window", "yes.png")):
        log.info("⚠️ 回收界面未出现（没有可回收的东西），跳过回收流程")
        c.normal_exit()
        log.info("✅ Step 5 执行完成")
        return True

    # 4. 点击确认
    log.info("点击确认...")
    if not c.click_yes():
        log.warning("⚠️ 未找到确认按钮，继续执行")
    time.sleep(0.5)

    # 5. 点击确定
    log.info("点击确定...")
    if not c.click_sure():
        log.warning("⚠️ 未找到确定按钮，继续执行")
    time.sleep(0.5)

    # 6. 退出所有弹窗回到主菜单
    log.info("退出弹窗回到主菜单...")
    c.normal_exit()

    log.info("✅ Step 5 执行完成")
    return True


if __name__ == "__main__":
    ok = run_step5()
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)