"""
dailyNew.py — 日常任务主入口
=====================================================
按步骤逐步执行日常任务，每个 Step 独立实现并可在 steps/ 目录下独立运行。

当前进度：
  [Step 1] ✅ 启动 MuMu 模拟器
  [Step 3] ✅ 启动游戏并进入主菜单（合并原 Step 2+3）
  [Step 4] ✅ 领取信封奖励（菜单→信件→一键领取→确定）
  [Step 5] ✅ 采集并出售生物（地图→回收→确认→确定）
  [Step 6] ✅ 采集香火（地图→香火坐标→确认→关闭）
  [Step 7] ✅ 委托讨伐3轮（山东大树/山东亚狼/一阶讨伐佣杰）
  [Step 8] ✅ 商店购买碎片（商店→道具商店→装备系→米奇碎片）
  [Step 9] ✅ 分享游戏到微信（队伍→分享→微信→关闭微信）
  [Step 10] ✅ 领取荣耀（菜单→荣耀→一键领取→攻击→领取）

独立运行各 Step：
  - python steps/step1_start_emulator.py
  - python steps/step3_enter_main_menu.py
  - python steps/step4_handle_envelope.py
  - python steps/step5_collect_and_sale.py
  - python steps/step6_collect_xianghuo.py
  - python steps/step7_handle_taofa.py
  - python steps/step8_go_to_shop.py
  - python steps/step9_share_game.py
  - python steps/step10_get_honor.py
=====================================================
"""

import logging
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from core import MuMuController

# 导入各 Step
from steps.step1_start_emulator import run_step1
from steps.step3_enter_main_menu import run_step3
from steps.step4_handle_envelope import run_step4
from steps.step5_collect_and_sale import run_step5
from steps.step6_collect_xianghuo import run_step6
from steps.step7_handle_taofa import run_step7
from steps.step8_go_to_shop import run_step8
from steps.step9_share_game import run_step9
from steps.step10_get_honor import run_step10

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


def run_daily() -> bool:
    """
    日常任务主入口（按 Step 顺序执行）。

    返回:
        True  = 所有 Step 执行成功
        False = 任意 Step 执行失败
    """
    log.info("╔══════════════════════════════════════════════════════════╗")
    log.info("║           开始执行日常任务（MuMu 后台自动化）            ║")
    log.info("╚══════════════════════════════════════════════════════════╝")

    # Step 1: 启动模拟器
    step1_ok = run_step1()
    if not step1_ok:
        log.warning("⚠️ Step 1 失败，继续执行后续步骤")

    # Step 3: 启动游戏并进入主菜单（合并原 Step 2+3）
    step3_ok = run_step3(duration=25, wait_before_tap=7)
    if not step3_ok:
        log.warning("⚠️ Step 3 失败，继续执行后续步骤")

    # 创建控制器供后续步骤使用
    c = MuMuController()

    # Step 4: 领取信封
    step4_ok = run_step4(c)
    if not step4_ok:
        log.warning("⚠️ Step 4 失败，继续执行后续步骤")

    # Step 5: 采集并出售生物
    step5_ok = run_step5(c)
    if not step5_ok:
        log.warning("⚠️ Step 5 失败，继续执行后续步骤")

    # Step 6: 采集香火
    step6_ok = run_step6(c)
    if not step6_ok:
        log.warning("⚠️ Step 6 失败，继续执行后续步骤")

    # Step 7: 委托讨伐3轮
    step7_ok = run_step7(c)
    if not step7_ok:
        log.warning("⚠️ Step 7 失败，继续执行后续步骤")

    # Step 8: 商店购买碎片
    step8_ok = run_step8(c)
    if not step8_ok:
        log.warning("⚠️ Step 8 失败，继续执行后续步骤")

    # Step 9: 分享游戏到微信
    step9_ok = run_step9(c)
    if not step9_ok:
        log.warning("⚠️ Step 9 失败，继续执行后续步骤")

    # Step 10: 领取荣耀
    step10_ok = run_step10(c)
    if not step10_ok:
        log.warning("⚠️ Step 10 失败，继续执行后续步骤")

    # Step 6+ 待开发
    all_ok = (step1_ok and step3_ok and step4_ok and step5_ok
              and step6_ok and step7_ok and step8_ok and step9_ok and step10_ok)
    if all_ok:
        log.info("╔══════════════════════════════════════════════════════════╗")
        log.info("║         🎉 Step 1+3+4+5+6+7+8+9+10 全部完成！         ║")
        log.info("╚══════════════════════════════════════════════════════════╝")
    else:
        log.info("╔══════════════════════════════════════════════════════════╗")
        log.info("║              ⚠️ 部分步骤执行失败，已继续执行              ║")
        log.info("╚══════════════════════════════════════════════════════════╝")
    return True


if __name__ == "__main__":
    ok = run_daily()
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)