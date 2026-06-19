"""
step3_enter_main_menu.py — Step 3: 启动游戏并进入主菜单
=====================================================
独立运行：python step3_enter_main_menu.py
功能：启动游戏，然后通过点击屏幕中央进入游戏主菜单
=====================================================
"""

import logging
import subprocess
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core import MuMuController
import actions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

GAME_PACKAGE = "com.netease.ma167"
SCREEN_CENTER = (960, 540)
TAP_DURATION = 25
DOWNLOAD_EXTRA_TIME = 30


def _adb(*args, timeout: int = 15) -> tuple:
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
    ok, out = _adb("shell", "pidof", GAME_PACKAGE)
    return ok and bool(out.strip())


def start_game(timeout: float = 30.0) -> bool:
    """启动游戏（用 monkey 启动器）"""
    log.info(f"启动游戏「大陆的霸者」(pkg={GAME_PACKAGE})")

    if is_game_running():
        log.info("游戏已在运行中，跳过启动")
        return True

    log.info("用 monkey 启动游戏...")
    ok, out = _adb("shell", "monkey", "-p", GAME_PACKAGE,
                   "-c", "android.intent.category.LAUNCHER", "1")
    if not ok or "Events injected: 0" in out:
        log.error(f"启动游戏失败: {out[:200]}")
        return False
    log.info(f"启动命令已发送: Events injected=1")

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


def tap_screen_center(c: MuMuController) -> bool:
    x, y = SCREEN_CENTER
    log.info(f"点击屏幕中央: ({x}, {y})")
    return c.tap(x, y)


def check_and_handle_download(c: MuMuController) -> bool:
    """检查是否有下载弹窗（确定/下载按钮），如果有则点击。"""
    # 检查确定按钮 - 直接用 find_and_tap，避免重复截图
    sure_path = os.path.join(config.PIC_ROOT, "window", "sure.png")
    if c.find_and_tap(sure_path):
        log.info("发现并点击确定按钮")
        return True

    # 检查下载按钮
    download_path = os.path.join(config.PIC_ROOT, "xiazai.png")
    if c.find_and_tap(download_path):
        log.info("发现并点击下载按钮")
        return True

    return False


def run_step3(c: MuMuController = None, duration: int = TAP_DURATION, wait_before_tap: int = 7) -> bool:
    """
    启动游戏并进入主菜单。

    流程：
      1. 启动游戏
      2. 等待 wait_before_tap 秒（避开启动广告）
      3. 持续 duration 秒内每秒点一次屏幕中央
      4. 每秒检查是否已进主菜单（看到菜单图标）
      5. 一旦检测到主菜单，立即停止点击
      6. 截图存档

    参数:
        c               : MuMuController 实例（None 则自动创建）
        duration        : 持续点击的总秒数（默认 25s）
        wait_before_tap : 点击前等待秒数（默认 7s，避开启动广告）

    返回:
        True  = 在 duration 内进入主菜单
        False = 超时仍未进入
    """
    log.info("=" * 50)
    log.info("Step 3: 启动游戏并进入主菜单")
    log.info("=" * 50)

    if not start_game():
        return False

    if c is None:
        c = MuMuController()

    if wait_before_tap > 0:
        log.info(f"等待 {wait_before_tap}s 避开启动广告...")
        time.sleep(wait_before_tap)

    log.info("开始点击屏幕中央...")
    start = time.time()
    end_time = start + duration
    sec = 0

    while time.time() < end_time:
        sec += 1
        tap_screen_center(c)
        time.sleep(1.0)
        if actions.is_in_main_menu(c):
            elapsed = time.time() - start
            log.info(f"✅ 检测到菜单图标，第 {sec}s 进入主菜单，总耗时 {elapsed:.1f}s")
            debug_path = r"H:/AI/2026-05-26-21-48-42/daily_step3.png"
            c.capture_screen(debug_path)
            return True
        if check_and_handle_download(c):
            end_time += DOWNLOAD_EXTRA_TIME
            log.info(f"⏰ 发现下载弹窗，持续时间增加 {DOWNLOAD_EXTRA_TIME}s")
            time.sleep(1.0)
            continue
        if sec % 3 == 0:
            log.info(f"  持续中… 已 {sec}s")

    debug_path = r"H:/AI/2026-05-26-21-48-42/daily_step3.png"
    c.capture_screen(debug_path)
    log.error(f"❌ {duration}s 内未检测到菜单图标，请查看 {debug_path}")
    return False


if __name__ == "__main__":
    ok = run_step3()
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)
