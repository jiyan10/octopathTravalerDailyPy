"""
main.py — 日常任务主入口
====================================================
对应原 daily.py，完全后台运行版本。
运行方式：
    python main.py              # 执行全套日常任务
    python main.py --zhi-ye     # 只跑职业塔
    python main.py --taofa      # 只跑讨伐
====================================================
"""

import time
import logging
import argparse

import config

# 初始化日志（在所有 import 之前）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

import start_game
import daily_tasks
from core import MuMuController


def run_daily(ctrl: MuMuController) -> None:
    """完整日常任务流程（共用一个 controller 减少重复连接）"""
    log.info("▶ 开始日常任务")

    daily_tasks.handle_envelope(ctrl)
    daily_tasks.collect_and_sale(ctrl)
    daily_tasks.collect_xianghuo(ctrl)
    daily_tasks.handle_taofa(ctrl)
    daily_tasks.go_to_shop(ctrl)
    daily_tasks.get_honor(ctrl)

    log.info("▶ 日常任务全部完成")


def run_zhiye_ta(ctrl: MuMuController) -> None:
    """职业塔挑战（全职业 1-4 层）"""
    log.info("▶ 开始职业塔挑战")

    jobs = [
        "lieren",   # 猎人
        "xingguan", # 星冠
        "xuezhe",   # 学者
        "youxia",   # 游侠
        "yaoshi",   # 药师
        "jianshi",  # 剑士
        "shangren", # 商人
        "wuzhe",    # 武者
    ]
    for job in jobs:
        daily_tasks.zhi_ye_ta(job, ctrl)

    log.info("▶ 职业塔全部完成")


# ──────────────────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MuMu 游戏自动化（后台运行）")
    parser.add_argument("--daily",     action="store_true", help="只跑日常任务")
    parser.add_argument("--zhi-ye",    action="store_true", help="只跑职业塔")
    parser.add_argument("--taofa",     action="store_true", help="只跑委托讨伐")
    parser.add_argument("--skip-start",action="store_true", help="跳过游戏启动检查")
    args = parser.parse_args()

    start_ts = time.time()

    # ── 1. 启动游戏 ──────────────────────────────────────
    if not args.skip_start:
        if not start_game.start_game_script():
            log.error("游戏启动失败，退出")
            return

    # ── 2. 创建共享 controller ───────────────────────────
    ctrl = MuMuController()
    if not ctrl.connect():
        log.error("ADB 连接失败，退出")
        return

    # ── 3. 执行任务 ──────────────────────────────────────
    # 如果没有指定任何子命令，默认跑全套
    run_all = not (args.daily or args.zhi_ye or args.taofa)

    if run_all or args.daily:
        run_daily(ctrl)

    if run_all or args.zhi_ye:
        run_zhiye_ta(ctrl)

    if args.taofa:
        daily_tasks.handle_taofa(ctrl)

    # ── 4. 收尾 ──────────────────────────────────────────
    elapsed = time.time() - start_ts
    log.info(f"总耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")


if __name__ == "__main__":
    main()
