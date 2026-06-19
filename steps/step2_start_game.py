"""
step2_start_game.py — Step 2: 启动游戏「大陆的霸者」
=====================================================
独立运行：python step2_start_game.py
功能：启动游戏（用 monkey 启动器，无需知道具体 Activity）
=====================================================
"""

import logging
import subprocess
import sys
import os
import time

# 添加父目录到路径，以便导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

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

# 大陆的霸者（歧路旅人 IP）官方包名
GAME_PACKAGE = "com.netease.ma167"


def _adb(*args, timeout: int = 15) -> tuple:
    """
    通过 mumu-cli 代理执行 adb 命令（统一走 mumu-cli 通道）。
    返回 (success, output_str)
    """
    cmd = [config.MUMU_CLI, "adb", "--vmindex", str(config.VM_INDEX), "--cmd", *args]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return True, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return False, "超时"
    except Exception as e:
        return False, str(e)


def is_game_running() -> bool:
    """检查游戏进程是否在运行（通过 pidof）"""
    ok, out = _adb("shell", "pidof", GAME_PACKAGE)
    return ok and bool(out.strip())


def run_step2(wait_running: bool = True, timeout: float = 30.0) -> bool:
    """
    启动游戏（用 monkey 启动器，无需知道具体 Activity）。

    参数:
        wait_running : 是否等待进程跑起来
        timeout      : wait_running 时的最长等待时间（秒）

    返回:
        True  = 游戏进程已运行
        False = 启动失败
    """
    log.info("=" * 50)
    log.info(f"Step 2: 启动游戏「大陆的霸者」(pkg={GAME_PACKAGE})")
    log.info("=" * 50)

    # 检查是否已运行
    if is_game_running():
        log.info("游戏已在运行中，跳过启动")
        return True

    # 启动游戏
    log.info("用 monkey 启动游戏...")
    ok, out = _adb("shell", "monkey", "-p", GAME_PACKAGE,
                   "-c", "android.intent.category.LAUNCHER", "1")
    if not ok or "Events injected: 0" in out:
        log.error(f"启动游戏失败: {out[:200]}")
        return False
    log.info(f"启动命令已发送: Events injected=1")

    if not wait_running:
        return True

    # 等待游戏进程出现
    log.info(f"等待游戏进程出现（最长 {timeout:.0f}s）...")
    start = time.time()
    while time.time() - start < timeout:
        if is_game_running():
            elapsed = time.time() - start
            log.info(f"✅ 游戏进程已就绪，耗时 {elapsed:.1f}s")
            return True
        time.sleep(1.0)

    log.error(f"等待游戏进程超时（{timeout:.0f}s）")
    return False


if __name__ == "__main__":
    ok = run_step2(wait_running=True, timeout=30)
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)