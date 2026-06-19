"""
envelope_run.py — 日常信封领取（mumu-cli 版）
=====================================================
基于 MuMuController 后台控制器：
  - 截图：adb screencap（1920×1080）
  - 点击：mumu-cli input tap（官方输入管线）
  - 匹配：OpenCV 多尺度模板匹配
  - 坐标系：直接使用 ADB 截图坐标，无需缩放转换

流程：
  主界面 → 点菜单 → 信件 → 通常tab → 一键领取 → 确认 → 关闭弹窗
        → 运营tab → 一键领取 → 确认 → 关闭弹窗 → 退出
"""

import time
import os
import sys
import logging

# 确保能导入同目录下的 core 和 config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import MuMuController
import config

log = logging.getLogger(__name__)

# 调试截图保存目录
DEBUG_DIR = r"H:\AI\07_代码脚本\mumu-auto-bg\screenshots"


def _save_debug(ctrl: MuMuController, label: str) -> None:
    """保存调试截图"""
    path = os.path.join(DEBUG_DIR, f"env_{label}.png")
    ctrl.capture_screen(path)
    log.info(f"[debug] 保存截图: {path}")


def _wait_and_find(ctrl: MuMuController, template_path: str,
                   threshold: float = 0.8, timeout: float = 10.0,
                   poll: float = 1.0) -> bool:
    """轮询等待模板出现，找到返回 True"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ctrl.is_visible(template_path, threshold):
            return True
        time.sleep(poll)
    log.warning(f"超时未找到: {os.path.basename(template_path)}")
    return False


def handle_envelope(ctrl: MuMuController = None) -> bool:
    """
    执行完整的日常信封领取流程。

    Args:
        ctrl: 已连接的 MuMuController 实例，为 None 则自动创建

    Returns:
        是否成功完成流程
    """
    # ── 初始化 ───────────────────────────────────────────
    c = ctrl or MuMuController()
    if not c.connect():
        log.error("连接失败，退出")
        return False

    log.info("========== 日常信封领取开始 ==========")

    # Step 0: 截图记录初始状态
    _save_debug(c, "00_initial")

    # Step 1: 回到主界面（关闭所有弹窗）
    log.info("[Step 1] 关闭弹窗，回到主界面...")
    c.normal_exit()
    time.sleep(0.5)

    # Step 2: 点击菜单按钮
    log.info("[Step 2] 点击菜单按钮...")
    if not c.find_and_tap_sure(c._pic("menu", "menu.png"), threshold=0.85,
                                retry=config.DEFAULT_RETRY_CNT):
        log.error("[FAIL] 找不到菜单按钮")
        _save_debug(c, "02_fail_no_menu")
        return False
    time.sleep(1.5)
    _save_debug(c, "02_after_menu")

    # Step 3: 点击信件/信封图标
    log.info("[Step 3] 点击信封图标...")
    if not c.find_and_tap_sure(c._pic("menu", "envelop.png"), threshold=0.80,
                                retry=config.DEFAULT_RETRY_CNT):
        log.error("[FAIL] 找不到信封图标")
        _save_debug(c, "03_fail_no_envelope")
        return False
    time.sleep(2.0)
    _save_debug(c, "03_after_envelope")

    # ── 通常信封（Tab 1）─────────────────────────────────
    for tab_num, tab_name in enumerate(["通常", "运营"], start=1):
        log.info(f"--- {tab_name}信封 (Tab {tab_num}) ---")

        # 切换到对应 tab
        tab_path = c._pic("menu", "envelope", f"{tab_num}.png")
        if c.is_visible(tab_path, threshold=0.75):
            c.find_and_tap(tab_path)
            time.sleep(1.2)

        # 一键领取
        get_path = c._pic("menu", "envelope", "get.png")
        if c.is_visible(get_path, threshold=0.78):
            log.info(f"  一键领取...")
            c.find_and_tap(get_path)
            time.sleep(1.5)

            # 确认对话框
            if c.is_visible(c._pic("window", "sure.png"), threshold=0.80):
                c.click_sure()
                time.sleep(1.5)

            # 关闭奖励弹窗（点空白处）
            log.info(f"  关闭奖励弹窗...")
            c.tap_empty(3)
            time.sleep(1.0)
        else:
            log.info(f"  [INFO] {tab_name}信封无可领取内容，跳过")

        _save_debug(c, f"{tab_num:02d}_after_tab{tab_num}")

    # Step N: 退出到主界面
    log.info("[Step 退出] 关闭弹窗回到主界面...")
    c.normal_exit()
    time.sleep(0.5)

    # 最终截图
    _save_debug(c, "99_final")

    log.info("========== 信封领取完成 ==========")
    return True


if __name__ == "__main__":
    # 配置日志输出到控制台和文件
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        ],
    )

    result = handle_envelope()
    print(f"\n结果: {'成功' if result else '失败'}")
