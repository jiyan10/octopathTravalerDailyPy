"""
step7_handle_taofa.py — Step 7: 委托讨伐（3轮）
=====================================================
独立运行：python step7_handle_taofa.py
功能：执行三轮讨伐任务
  第1轮：山东大树
  第2轮：山东亚狼
  第3轮：一阶讨伐佣杰
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


def _do_one_taofa_round(c: MuMuController, round_name: str,
                         weituo_img: str, target_img: str) -> bool:
    """
    执行单轮讨伐。

    参数:
        c           : MuMuController 实例
        round_name  : 轮次名称（如"第1轮：山东大树"）
        weituo_img  : 讨伐委托模板路径
        target_img  : 讨伐目标模板路径

    返回:
        True  = 该轮成功完成
        False = 该轮失败（找不到入口）
    """
    log.info(f"--- {round_name} ---")

    # 1. 点击搜索按钮
    log.info("点击搜索按钮...")
    if not c.find_and_tap_sure(c._pic("menu", "search.png"), retry=3):
        log.warning(f"⚠️ {round_name}: 未找到搜索按钮，跳过")
        return False
    time.sleep(0.5)

    # 2. 点击讨伐委托
    log.info("点击讨伐委托...")
    if not c.find_and_tap_sure(c._pic("menu", "taofa", "taofaweituo.png"), retry=3):
        log.warning(f"⚠️ {round_name}: 未找到讨伐委托按钮，跳过")
        return False
    time.sleep(0.5)

    # 3. 如果不是普通委托，需要额外点击对应标签
    if weituo_img != c._pic("menu", "taofa", "taofaweituo.png"):
        log.info("点击高级/一阶委托标签...")
        if not c.find_and_tap_sure(weituo_img, retry=3):
            log.warning(f"⚠️ {round_name}: 未找到高级/一阶委托标签，跳过")
            return False
        time.sleep(0.5)

    # 4. 点击具体目标
    log.info(f"点击目标: {target_img}")
    if not c.find_and_tap_sure(target_img, retry=3):
        log.warning(f"⚠️ {round_name}: 未找到目标按钮，跳过")
        return False
    time.sleep(0.5)

    # 5. 点击开始准备
    log.info("点击开始准备...")
    if not c.find_and_tap_sure(c._pic("menu", "taofa", "kaishizhunbei.png"), retry=3):
        log.warning(f"⚠️ {round_name}: 未找到开始准备按钮，跳过")
        return False
    time.sleep(0.5)

    # 6. 点击简易讨伐
    log.info("点击简易讨伐...")
    if not c.find_and_tap_sure(c._pic("menu", "taofa", "jianyitaofa.png"), retry=3):
        log.warning(f"⚠️ {round_name}: 未找到简易讨伐按钮，跳过")
        return False
    time.sleep(0.5)

    # 7. 点击确认
    log.info("点击确认...")
    if not c.click_yes():
        log.warning(f"⚠️ {round_name}: 未找到确认按钮，继续")
    time.sleep(3)  # 等待战斗

    # 8. 滑动3次消除战斗UI
    log.info("滑动3次消除战斗UI...")
    for _ in range(3):
        c.swipe(540, 960, 540, 500, duration_ms=300)
        time.sleep(0.3)

    # 9. 循环点击确定直到退出
    log.info("等待结算...")
    while c.click_sure():
        time.sleep(0.3)

    # 10. 滑动3次
    log.info("滑动3次...")
    for _ in range(3):
        c.swipe(540, 960, 540, 500, duration_ms=300)
        time.sleep(0.3)

    # 11. 点击继续
    log.info("点击继续...")
    if not c.click_continue():
        log.info("⚠️ 未找到继续按钮")
    time.sleep(0.5)

    # 12. 再滑动3次
    log.info("再滑动3次...")
    for _ in range(3):
        c.swipe(540, 960, 540, 500, duration_ms=300)
        time.sleep(0.3)

    # 12. 退出回到主菜单
    log.info("退出回到主菜单...")
    c.normal_exit()

    log.info(f"✅ {round_name} 完成")
    return True


def run_step7(c: MuMuController = None) -> bool:
    """
    执行三轮讨伐任务。

    参数:
        c : MuMuController 实例（None 则自动创建）

    返回:
        True  = 操作成功（或部分成功）
        False = 操作失败
    """
    log.info("=" * 50)
    log.info("Step 7: 委托讨伐（3轮）")
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

    # 切换到队伍（确保在正确的队伍标签页）
    log.info("切换到队伍...")
    if not c.click_team():
        log.warning("⚠️ 未找到队伍按钮，继续执行")
    time.sleep(1.0)

    # 等待讨伐专用标签出现
    log.info("等待讨伐标签出现...")
    for _ in range(20):
        if c.is_visible(c._pic("menu", "taofa", "taofazhuanyong.png")):
            break
        c.find_and_tap(c._pic("window", "team_left.png"))
        time.sleep(0.3)
    else:
        log.warning("⚠️ 未找到讨伐专用标签，但继续执行")

    c.normal_exit()

    # 第1轮：山东大树（普通委托，默认就在这个页面）
    round1_ok = _do_one_taofa_round(
        c,
        "第1轮：山东大树",
        c._pic("menu", "taofa", "taofaweituo.png"),
        c._pic("menu", "taofa", "shandongdashu.png")
    )

    # 第2轮：山东亚狼（先点击普通委托，再点击高级委托）
    round2_ok = _do_one_taofa_round(
        c,
        "第2轮：山东亚狼",
        c._pic("menu", "taofa", "gaojitaofaweituo.png"),
        c._pic("menu", "taofa", "shandongyalang.png")
    )

    # 第3轮：一阶讨伐佣杰（先点击普通委托，再点击一阶委托）
    round3_ok = _do_one_taofa_round(
        c,
        "第3轮：一阶讨伐佣杰",
        c._pic("menu", "taofa", "yijietaofaweituo.png"),
        c._pic("menu", "taofa", "yongjie.png")
    )

    # 总结
    completed = sum([round1_ok, round2_ok, round3_ok])
    log.info(f"讨伐完成: {completed}/3 轮成功")

    log.info("✅ Step 7 执行完成")
    return True


if __name__ == "__main__":
    ok = run_step7()
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)