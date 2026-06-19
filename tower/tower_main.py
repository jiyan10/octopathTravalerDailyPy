"""
tower_main.py — 职业塔自动化主入口
=====================================================
独立运行：python tower_main.py
功能：自动挑战试炼之塔（职业塔）1-4层

用法：
  python tower_main.py                    # 运行所有职业
  python tower_main.py --job lieren       # 只运行猎人职业
  python tower_main.py --job lieren xuezhe  # 运行多个职业
=====================================================
"""

import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core import MuMuController
from tower.step1_enter_tower import run_step1
from tower.step2_select_job import run_step2
from tower.step3_battle_floors import run_step3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# 支持的职业列表
SUPPORTED_JOBS = {
    "lieren": "猎人",
    "xingguan": "行商",
    "xuezhe": "学者",
    "youxia": "游侠",
    "yaoshi": "药师",
    "jianshi": "剑士",
    "shangren": "商人",
    "wuzhe": "武者",
}


def run_tower(jobs: list = None) -> bool:
    """
    执行职业塔自动化。

    参数:
        jobs : 要执行的职业列表（None = 执行所有职业）

    返回:
        True  = 所有职业完成
        False = 出现错误
    """
    if jobs is None:
        jobs = list(SUPPORTED_JOBS.keys())

    log.info("╔══════════════════════════════════════════════════════════╗")
    log.info("║           开始执行职业塔自动化（MuMu 后台）            ║")
    log.info("╚══════════════════════════════════════════════════════════╝")

    c = MuMuController()
    success_count = 0

    for job in jobs:
        job_name = SUPPORTED_JOBS.get(job, job)
        log.info("=" * 50)
        log.info(f"开始执行职业塔: {job_name} ({job})")
        log.info("=" * 50)

        try:
            # Step 1+2: 进入试炼之塔并选择职业
            if not run_step1(c, job):
                log.warning(f"⚠️ {job_name}: Step 1+2 进入试炼之塔并选择职业失败，跳过")
                continue

            # Step 3: 挑战 1-4 层
            if not run_step3(c):
                log.warning(f"⚠️ {job_name}: Step 3 战斗失败，跳过")
                continue

            success_count += 1
            log.info(f"✅ {job_name} 完成")

        except Exception as e:
            log.error(f"❌ {job_name} 执行异常: {e}")

    log.info("=" * 50)
    log.info(f"职业塔完成: {success_count}/{len(jobs)} 个职业成功")
    log.info("=" * 50)

    return success_count == len(jobs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="职业塔自动化")
    parser.add_argument(
        "--job",
        nargs="+",
        choices=list(SUPPORTED_JOBS.keys()),
        help="指定要执行的职业（默认所有职业）",
    )
    args = parser.parse_args()

    ok = run_tower(args.job)
    sys.exit(0 if ok else 1)
