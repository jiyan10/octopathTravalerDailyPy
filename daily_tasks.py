"""
daily_tasks.py — 日常任务集合
====================================================
对应原 envolop.py 的所有功能，完全后台运行：
  - handle_envelope()     信封领取
  - collect_and_sale()    采集 & 出售生物
  - collect_xianghuo()    采集香火
  - handle_taofa()        委托讨伐（3轮）
  - go_to_shop()          商店购买碎片
  - get_honor()           荣耀一键获取
  - zhi_ye_ta()           职业塔挑战（1-4层）
====================================================
"""

import time
import logging
import os
from typing import Optional

from core import MuMuController, FightOrder, mumu_swipe
import config

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# 工具：战斗指令模板
# ══════════════════════════════════════════════════════════

def _shilian_orders() -> list:
    """试炼之塔标准战斗指令（三循环，复用减少冗余）"""
    one_round = [
        FightOrder(1, False, False, 2, 1, 0),
        FightOrder(2, False, False, 2, 1, 0),
        FightOrder(3, False, False, 2, 1, 0),
        FightOrder(4, False, False, 2, 1, 0),
        FightOrder(5, False, False, 0, 0, 0),  # 执行标记

        FightOrder(1, False, False, 3, 1, 0),
        FightOrder(2, False, False, 3, 1, 0),
        FightOrder(3, False, False, 3, 1, 0),
        FightOrder(4, False, False, 3, 1, 0),
        FightOrder(5, False, False, 0, 0, 0),

        FightOrder(1, False, False, 4, 4, 0),
        FightOrder(2, False, False, 4, 4, 0),
        FightOrder(3, False, False, 4, 4, 0),
        FightOrder(4, False, False, 4, 4, 0),
        FightOrder(5, False, False, 0, 0, 0),
    ]
    return one_round * 3


def _shilian_fight(ctrl: MuMuController) -> None:
    """等待进入战斗后执行试炼之塔战斗指令"""
    start = time.time()
    while not ctrl.is_attack_visible():
        if time.time() - start > 10:
            log.info("攻击图标未出现，点击空白处...")
            ctrl.tap_empty()
            start = time.time()
        time.sleep(0.3)
    ctrl.fight_all_order(_shilian_orders())


# ══════════════════════════════════════════════════════════
# 任务：领取信封
# ══════════════════════════════════════════════════════════

def handle_envelope(ctrl: Optional[MuMuController] = None) -> None:
    """领取信封奖励（1号和2号信封）"""
    log.info("=== 开始领取信封 ===")
    c = ctrl or MuMuController()
    if not c.connect():
        return

    c.normal_exit()
    c.click_menu()
    c.find_and_tap(c._pic("menu","envelop.png"))

    for envelope_num in ["1", "2"]:
        log.info(f"领取信封 {envelope_num}")
        c.find_and_tap(c._pic("menu","envelope",f"{envelope_num}.png"))
        c.find_and_tap(c._pic("menu","envelope","get.png"))
        c.click_sure()
        # 原来 3×pyautogui.click() 改为 3×adb tap 空白处
        for _ in range(3):
            c.tap_empty()
            time.sleep(0.5)

    c.normal_exit()
    log.info("=== 信封领取完成 ===")


# ══════════════════════════════════════════════════════════
# 任务：采集并出售生物
# ══════════════════════════════════════════════════════════

def collect_and_sale(ctrl: Optional[MuMuController] = None) -> None:
    log.info("=== 开始采集出售生物 ===")
    c = ctrl or MuMuController()
    if not c.connect():
        return

    c.normal_exit()
    c.click_map()
    time.sleep(1)
    c.find_and_tap(c._pic("map","huishou.png"))
    c.click_yes()
    c.click_sure()
    c.normal_exit()
    log.info("=== 采集出售完成 ===")


# ══════════════════════════════════════════════════════════
# 任务：采集香火
# ══════════════════════════════════════════════════════════

def collect_xianghuo(ctrl: Optional[MuMuController] = None) -> None:
    log.info("=== 开始采集香火 ===")
    c = ctrl or MuMuController()
    if not c.connect():
        return

    c.normal_exit()
    c.click_map()
    c.tap(145, 960)   # 香火固定坐标
    c.tap(145, 960)
    c.click_no()
    c.click_sure()
    c.click_close()
    c.normal_exit()
    log.info("=== 香火采集完成 ===")


# ══════════════════════════════════════════════════════════
# 任务：委托讨伐（3轮）
# ══════════════════════════════════════════════════════════

def _do_one_taofa(c: MuMuController,
                  weituo_img: str,
                  dungeon_img: str) -> None:
    """执行单次委托讨伐流程"""
    c.find_and_tap_sure(c._pic("menu","search.png"))
    c.find_and_tap_sure(c._pic("menu","taofa","taofaweituo.png"))
    c.find_and_tap_sure(weituo_img)
    c.find_and_tap_sure(dungeon_img)
    c.find_and_tap_sure(c._pic("menu","taofa","kaishizhunbei.png"))
    c.find_and_tap_sure(c._pic("menu","taofa","jianyitaofa.png"))
    c.click_yes()
    time.sleep(3)
    c.tap_empty(5)
    while c.click_sure():
        pass
    c.click_continue()
    c.tap_empty(5)
    c.normal_exit()


def handle_taofa(ctrl: Optional[MuMuController] = None) -> None:
    """三轮委托讨伐"""
    log.info("=== 开始委托讨伐 ===")
    c = ctrl or MuMuController()
    if not c.connect():
        return

    c.normal_exit()
    c.click_team()
    # 切换到讨伐专用队伍
    for _ in range(30):
        if c.is_visible(c._pic("menu","taofa","taofazhuanyong.png")):
            break
        c.find_and_tap(c._pic("window","team_left.png"))
    c.normal_exit()

    # 普通讨伐 → 山东大树
    _do_one_taofa(
        c,
        c._pic("menu","taofa","taofaweituo.png"),
        c._pic("menu","taofa","shandongdashu.png"),
    )
    # 高级讨伐 → 山洞压浪
    _do_one_taofa(
        c,
        c._pic("menu","taofa","gaojitaofaweituo.png"),
        c._pic("menu","taofa","shandongyalang.png"),
    )
    # 一界讨伐 → 永界
    _do_one_taofa(
        c,
        c._pic("menu","taofa","yijietaofaweituo.png"),
        c._pic("menu","taofa","yongjie.png"),
    )
    log.info("=== 委托讨伐完成 ===")


# ══════════════════════════════════════════════════════════
# 任务：商店购买碎片
# ══════════════════════════════════════════════════════════

def go_to_shop(ctrl: Optional[MuMuController] = None) -> None:
    log.info("=== 开始商店购买 ===")
    c = ctrl or MuMuController()
    if not c.connect():
        return

    c.normal_exit()
    c.click_menu()
    c.find_and_tap_sure(c._pic("menu","shop.png"))
    time.sleep(1)
    c.find_and_tap_sure(c._pic("menu","shop","yidaodedaopian.png"))
    c.find_and_tap_sure(c._pic("menu","shop","zhuangbeixi.png"))
    c.find_and_tap_sure(c._pic("menu","shop","mijisuipian.png"))
    c.find_and_tap_sure(c._pic("menu","shop","huodesuipian.png"))

    for _ in range(3):
        if not c.is_visible(c._pic("menu","shop","max.png")):
            break
        c.find_and_tap_sure(c._pic("menu","shop","max.png"))
        c.find_and_tap_sure(c._pic("menu","shop","huodesuipian1.png"))
        c.tap(1185, 934)     # 购买按钮固定坐标
        c.click_sure()

    c.normal_exit()
    log.info("=== 商店购买完成 ===")


# ══════════════════════════════════════════════════════════
# 任务：荣耀一键获取
# ══════════════════════════════════════════════════════════

def get_honor(ctrl: Optional[MuMuController] = None) -> None:
    log.info("=== 开始获取荣耀 ===")
    c = ctrl or MuMuController()
    if not c.connect():
        return

    c.normal_exit()
    c.click_menu()
    c.find_and_tap_sure(c._pic("menu","honor.png"))
    time.sleep(1)
    c.find_and_tap_sure(c._pic("menu","honor","yijianhuode.png"))
    c.click_sure()
    c.find_and_tap_sure(c._pic("menu","honor","gongji.png"))
    c.find_and_tap_sure(c._pic("menu","honor","yijianhuode.png"))
    c.click_sure()
    time.sleep(1)
    c.normal_exit()
    log.info("=== 荣耀获取完成 ===")


# ══════════════════════════════════════════════════════════
# 任务：职业塔挑战
# ══════════════════════════════════════════════════════════

def _find_job(c: MuMuController, zhi_ye: str) -> bool:
    """找职业按钮，找不到则下滑重试，最多 3 次"""
    if not zhi_ye:
        return True
    path = c._pic("menu","zhiyeta",f"{zhi_ye}.png")
    for attempt in range(3):
        log.info(f"查找职业 {zhi_ye}，第{attempt+1}次")
        if c.find_and_tap(path, threshold=0.9):
            c.find_and_tap(c._pic("menu","zhiyeta","jinrushilianzhita.png"))
            time.sleep(1)
            return True
        if attempt < 2:
            log.info(f"未找到 {zhi_ye}，下滑重试")
            mumu_swipe(200, 700, 200, 300)
            time.sleep(0.8)
    log.warning(f"找不到职业 {zhi_ye}")
    return False


def _find_floor(c: MuMuController, floor: int) -> bool:
    """找楼层按钮，找不到则滑动重试"""
    path = c._pic("menu","zhiyeta",f"{floor}ceng.png")
    for attempt in range(2):
        log.info(f"查找 {floor} 层，第{attempt+1}次")
        if c.find_and_tap(path):
            return True
        if attempt < 1:
            if floor == 4:
                mumu_swipe(200, 300, 200, 700)  # 上滑
            else:
                mumu_swipe(200, 700, 200, 300)  # 下滑
            time.sleep(0.8)
    log.warning(f"找不到 {floor} 层")
    return False


def _process_floor(c: MuMuController, floor: int) -> bool:
    """处理单个楼层挑战"""
    log.info(f"--- 职业塔 {floor} 层 ---")
    if not _find_floor(c, floor):
        return False

    c.find_and_tap(c._pic("menu","zhiyeta","tiaozhan.png"))
    time.sleep(1)
    c.tap(1200, 720)
    time.sleep(1)
    if not c.find_and_tap(c._pic("window","sure.png")):
        c.find_and_tap(c._pic("menu","zhiyeta","tiaozhan.png"))
        c.tap(1200, 720)
    c.click_sure()
    c.click_sure()
    c.click_sure()

    _shilian_fight(c)

    time.sleep(4)
    for _ in range(4):
        c.click_close()
    time.sleep(2)
    return True


def zhi_ye_ta(zhi_ye: str,
              ctrl: Optional[MuMuController] = None) -> None:
    """职业塔自动挑战（指定职业，1-4层）"""
    log.info(f"=== 职业塔开始: {zhi_ye} ===")
    c = ctrl or MuMuController()
    if not c.connect():
        return

    c.normal_exit()
    c.find_and_tap(c._pic("menu","zhiyeta","ta_youxipan.png"))
    c.find_and_tap(c._pic("menu","zhiyeta","shilianzhita.png"))
    time.sleep(2)

    if not _find_job(c, zhi_ye):
        log.error(f"职业 {zhi_ye} 未找到，跳过")
        return

    for floor in range(1, 5):
        _process_floor(c, floor)

    c.normal_exit()
    time.sleep(2)
    log.info(f"=== 职业塔完成: {zhi_ye} ===")
