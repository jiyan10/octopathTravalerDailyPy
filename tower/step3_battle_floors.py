"""
step3_battle_floors.py — Step 3: 挑战 1-4 层
=====================================================
功能：自动挑战试炼之塔 1-4 层
流程：
  对每层循环：
    1. 查找并点击楼层按钮
    2. 点击"挑战"按钮
    3. 点击队伍位置 (1200, 720)
    4. 点击"确定"按钮（失败则重试挑战流程）
    5. 额外点击3次确定（跳过弹窗）
    6. 执行战斗
    7. 等待4秒
    8. 点击关闭4次
=====================================================
"""

import logging
import time
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
from core import MuMuController, FightOrder

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
    except Exception as e:
        log.warning(f"ADB 点击失败: {e}")
        return False


def adb_click(x: int, y: int) -> bool:
    """使用 ADB 点击指定坐标"""
    cmd = [
        config.MUMU_CLI,
        "adb",
        "--vmindex", str(config.VM_INDEX),
        "--cmd", "shell", "input", "tap",
        str(x), str(y)
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.returncode == 0
    except Exception as e:
        log.warning(f"ADB 点击失败: {e}")
        return False


def find_floor_and_click(c: MuMuController, floor: int, retry: int = 2) -> bool:
    """
    查找楼层按钮并点击，找不到则滑动重试。

    参数:
        c     : MuMuController 实例
        floor : 楼层号 (1-4)
        retry : 最大重试次数

    返回:
        True  = 成功找到并点击
        False = 失败
    """
    floor_path = c._pic("menu", "zhiyeta", f"{floor}ceng.png")

    for attempt in range(retry):
        log.info(f"查找 {floor} 层，第 {attempt + 1} 次...")

        if c.find_and_tap(floor_path):
            log.info(f"成功点击 {floor} 层")
            return True

        if attempt < retry - 1:
            if floor == 4:
                # 4层找不到时上滑
                log.info(f"未找到 {floor} 层，执行上滑...")
                adb_swipe(200, 300, 200, 700)
            else:
                # 其他楼层下滑
                log.info(f"未找到 {floor} 层，执行下滑...")
                adb_swipe(200, 700, 200, 300)
            time.sleep(1)

    log.warning(f"经过 {retry} 次尝试，仍未找到 {floor} 层")
    return False


def execute_battle(c: MuMuController) -> None:
    """
    执行试炼之塔战斗。
    战斗模式：循环使用技能 2→3→4，所有角色使用相同技能。
    """
    log.info("等待攻击图标出现...")
    timeout = 5
    start = time.time()

    while not c.is_attack_visible():
        if time.time() - start > timeout:
            log.warning("攻击图标 5 秒未出现，点击空白处...")
            c.swipe(540, 960, 540, 500, duration_ms=300)
            start = time.time()
        time.sleep(0.5)

    # 试炼之塔战斗指令：循环 2→3→4 技能
    order = [
        # 第1循环
        FightOrder(1, False, False, 2, 1, 0),
        FightOrder(2, False, False, 2, 1, 0),
        FightOrder(3, False, False, 2, 1, 0),
        FightOrder(4, False, False, 2, 1, 0),
        FightOrder(5, False, False, 0, 0, 0),

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

        # 第2循环
        FightOrder(1, False, False, 2, 1, 0),
        FightOrder(2, False, False, 2, 1, 0),
        FightOrder(3, False, False, 2, 1, 0),
        FightOrder(4, False, False, 2, 1, 0),
        FightOrder(5, False, False, 0, 0, 0),

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

        # 第3循环
        FightOrder(1, False, False, 2, 1, 0),
        FightOrder(2, False, False, 2, 1, 0),
        FightOrder(3, False, False, 2, 1, 0),
        FightOrder(4, False, False, 2, 1, 0),
        FightOrder(5, False, False, 0, 0, 0),

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

    log.info("执行战斗指令...")
    c.fight_all_order(order)
    log.info("战斗执行完成")


def process_single_floor(c: MuMuController, floor: int) -> bool:
    """
    处理单个楼层的挑战。

    参数:
        c     : MuMuController 实例
        floor : 楼层号 (1-4)

    返回:
        True  = 成功完成
        False = 失败
    """
    log.info(f"--- 处理 {floor} 层 ---")

    tiaozhan_path = c._pic("menu", "zhiyeta", "tiaozhan.png")
    sure_path = c._pic("window", "sure.png")

    # 重试挑战流程（参考原代码）
    for retry in range(2):
        # 1. 查找并点击楼层
        if not find_floor_and_click(c, floor):
            return False
        time.sleep(0.3)

        # 2. 点击"挑战"按钮
        log.info("点击「挑战」...")
        if not c.find_and_tap(tiaozhan_path):
            log.warning("⚠️ 未找到挑战按钮")
            continue
        time.sleep(1)

        # 3. 点击队伍位置
        log.info("点击队伍位置...")
        adb_click(1200, 720)
        time.sleep(1)

        # 4. 点击确定
        if c.find_and_tap(sure_path):
            log.info("点击确定成功")
            break
        else:
            # 如果点不到确定，再试一次挑战流程
            log.warning("⚠️ 点击确定失败，重试挑战流程...")
            if retry == 0:
                # 再次点击挑战和队伍位置
                c.find_and_tap(tiaozhan_path)
                time.sleep(1)
                adb_click(1200, 720)
                time.sleep(1)
            continue

    time.sleep(0.5)

    # 5. 额外点击3次确定（跳过弹窗，参考原代码）
    log.info("额外点击确定 3 次...")
    for _ in range(3):
        if c.find_and_tap(sure_path):
            time.sleep(0.3)
        else:
            break

    # 6. 执行战斗（fight_all_order 内部会检测战斗结束并点击空白处）
    execute_battle(c)

    # 7. 战斗结束后的处理
    # fight_all_order 已经处理了战斗结束的逻辑
    # 这里额外点击几次关闭，确保退出所有弹窗
    log.info("关闭剩余弹窗...")
    time.sleep(1)
    for _ in range(3):
        c.click_close()
        time.sleep(0.3)

    return True


def run_step3(c: MuMuController, floors: list = None) -> bool:
    """
    挑战 1-4 层。

    参数:
        c      : MuMuController 实例
        floors : 要挑战的楼层列表（默认 1-4）

    返回:
        True  = 所有楼层完成
        False = 出现错误
    """
    if floors is None:
        floors = [1, 2, 3, 4]

    log.info("=" * 50)
    log.info(f"Step 3: 挑战楼层 {floors}")
    log.info("=" * 50)

    success_count = 0
    for floor in floors:
        if process_single_floor(c, floor):
            success_count += 1
        time.sleep(1)

    log.info(f"楼层挑战完成: {success_count}/{len(floors)} 层成功")

    # 返回主菜单
    log.info("返回主菜单...")
    c.normal_exit()
    time.sleep(1)

    return success_count > 0


if __name__ == "__main__":
    c = MuMuController()
    ok = run_step3(c)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    sys.exit(0 if ok else 1)
