"""
start_game.py — 启动与连接模拟器
====================================================
对应原 start_game.py，后台化版本：
  - 不强制窗口置顶
  - 通过 adb shell am 启动游戏
====================================================
"""

import subprocess
import time
import logging
import os

import config

log = logging.getLogger(__name__)

# 游戏包名（按你的游戏修改）
GAME_PACKAGE = "com.netease.xxxx"      # TODO: 替换为实际包名
GAME_ACTIVITY = ".MainActivity"         # TODO: 替换为实际 Activity


def _adb(*args, timeout=15) -> tuple:
    """执行 adb 命令，返回 (success, stdout, stderr)"""
    cmd = ["adb", "-s", config.DEVICE_ID, *args]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def connect_adb() -> bool:
    """连接 ADB 到 MuMu 模拟器"""
    log.info(f"连接 ADB: {config.DEVICE_ID}")
    try:
        r = subprocess.run(
            ["adb", "connect", config.DEVICE_ID],
            capture_output=True, timeout=10, text=True
        )
        output = r.stdout + r.stderr
        if "connected" in output or "already" in output:
            log.info("ADB 连接成功")
            return True
        log.error(f"ADB 连接失败: {output}")
        return False
    except Exception as e:
        log.error(f"ADB connect 异常: {e}")
        return False


def is_game_running() -> bool:
    """检查游戏是否在运行"""
    ok, out, _ = _adb("shell", "pidof", GAME_PACKAGE)
    return ok and bool(out.strip())


def start_game() -> bool:
    """
    启动游戏（后台方式，不需要模拟器窗口可见）
    使用 adb shell am start 启动游戏 Activity
    """
    if is_game_running():
        log.info("游戏已在运行中")
        return True

    log.info(f"启动游戏: {GAME_PACKAGE}")
    ok, out, err = _adb(
        "shell", "am", "start",
        "-n", f"{GAME_PACKAGE}/{GAME_ACTIVITY}",
        timeout=20
    )
    if not ok:
        log.error(f"启动游戏失败: {err}")
        return False

    # 等待游戏加载（最多 60 秒）
    for _ in range(60):
        time.sleep(1)
        if is_game_running():
            log.info("游戏启动成功")
            time.sleep(5)   # 等界面加载
            return True

    log.error("游戏启动超时")
    return False


def start_game_script() -> bool:
    """
    完整的游戏启动脚本入口：
    1. 连接 ADB
    2. 确认游戏运行
    3. 等待主菜单
    """
    if not connect_adb():
        return False
    if not start_game():
        return False

    # 延迟导入，避免循环引用
    from core import MuMuController
    ctrl = MuMuController()
    if not ctrl.connect():
        return False

    log.info("等待主菜单...")
    return ctrl.wait_for_menu(timeout=120)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    start_game_script()
