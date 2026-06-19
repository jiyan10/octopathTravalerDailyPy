"""
actions.py — 原子操作封装层
=====================================================
把 core.py 里的低层操作（截图、找图、点击）组合成可复用的语义化函数。

设计原则：
  - 每个函数完成一个**单一职责**的原子操作
  - 优先用模板匹配（稳定可靠），OCR 作为辅助
  - 所有函数都接受 MuMuController 实例，不自己 new
  - 函数命名清晰表达意图：is_xxx / click_xxx / wait_xxx
  - 失败时返回 False/None，不抛异常（让上层决定如何处理）
=====================================================

当前已实现的原子操作：
  [A1] is_in_main_menu()        — 识别主菜单
  [A2] click_top_right_close()  — 点击右上角X关闭按钮
  [A3] find_text_and_click()    — 识别截图文字并点击（OCR + 模板匹配双策略）
=====================================================
"""

import logging
import os
from typing import Optional, Tuple, List

import cv2
import numpy as np

import config
from core import MuMuController

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# 模板路径常量（统一在这里管理，避免硬编码散落各处）
# ══════════════════════════════════════════════════════════

def _pic(*parts: str) -> str:
    """拼接 H:/pic/ 下的路径"""
    return os.path.join(config.PIC_ROOT, *parts)


# 主菜单标志（含菜单图标+红色角标+下方"菜单"文字）
TPL_MAIN_MENU = _pic("menu", "menu_marker.png")
# 子界面右上角X关闭按钮
TPL_CLOSE_TOPRIGHT = _pic("window", "close_topright.png")
# 文字识别专用模板目录（用户可按需扩展：H:/pic/text/<字>.png）
TPL_TEXT_DIR = _pic("text")


# ══════════════════════════════════════════════════════════
# A1. 识别主菜单
# ══════════════════════════════════════════════════════════

def is_in_main_menu(c: MuMuController,
                    threshold: float = 0.8,
                    screen: Optional[np.ndarray] = None) -> bool:
    """
    [A1] 判断当前是否处于游戏主菜单界面（主城/酒馆等场景）。

    判定逻辑：在屏幕上找到 menu_marker.png 模板（包含菜单图标+红角标+文字）。
    这是从 dailyNew.py Step 3 验证通过的可靠判据（匹配度=1.0）。

    参数:
        c         : MuMuController 实例
        threshold : 模板匹配阈值（默认 0.8）
        screen    : 可选，预截图（避免重复截图）

    返回:
        True  = 当前是主菜单
        False = 不是主菜单 / 截图失败 / 找不到
    """
    pos = c.find_image(TPL_MAIN_MENU, threshold=threshold, screen=screen)
    if pos is None:
        log.debug(f"[A1] is_in_main_menu: 模板未找到 ({TPL_MAIN_MENU})")
    return pos is not None


def wait_for_main_menu(c: MuMuController,
                       timeout: float = 30.0,
                       interval: float = 1.0) -> bool:
    """
    [A1] 等待直到进入主菜单，超时返回 False。

    用于：脚本启动后、游戏加载中、关闭子界面后等待回到主城。
    """
    import time
    log.info(f"[A1] 等待主菜单出现（最多 {timeout:.0f}s）...")
    start = time.time()
    while time.time() - start < timeout:
        if is_in_main_menu(c):
            elapsed = time.time() - start
            log.info(f"[A1] ✅ 已进入主菜单，耗时 {elapsed:.1f}s")
            return True
        time.sleep(interval)
    log.warning(f"[A1] ❌ 等待主菜单超时（{timeout:.0f}s）")
    return False


# ══════════════════════════════════════════════════════════
# A2. 点击右上角关闭按钮
# ══════════════════════════════════════════════════════════

def click_top_right_close(c: MuMuController,
                          threshold: float = 0.85,
                          retry: int = 3,
                          delay: float = 0.5) -> bool:
    """
    [A2] 点击子界面右上角的 X 关闭按钮，返回主菜单/上一层界面。

    适用场景：
      - 信件/任务/商店等子界面（顶部右上角都有统一X按钮）
      - 任何带标准 X 关闭按钮的弹窗

    实现：
      用 close_topright.png 模板在屏幕右上角区域（约 x>1700, y<150）查找 X。
      多次重试以应对点击被吞的情况。

    参数:
        c         : MuMuController 实例
        threshold : 匹配阈值（默认 0.85，右上角 X 特征明确，阈值可高）
        retry     : 最多重试次数
        delay     : 每次重试间隔（秒）

    返回:
        True  = 成功点击 X
        False = 未找到 / 点击失败
    """
    # 右上角 X 模板需要从全屏找
    screen = c.capture_screen()
    if screen is None:
        log.warning("[A2] 截图失败")
        return False

    pos = c.find_image(TPL_CLOSE_TOPRIGHT, threshold=threshold, screen=screen)
    if pos is None:
        log.info("[A2] 屏幕上未找到右上角 X（可能不在子界面）")
        return False

    for i in range(retry):
        log.info(f"[A2] 点击右上角 X @ {pos}（第 {i+1}/{retry} 次）")
        ok = c.tap(pos[0], pos[1], delay=delay)
        if ok:
            return True
    return False


# ══════════════════════════════════════════════════════════
# A3. 识别文字并点击（OCR + 模板匹配双策略）
# ══════════════════════════════════════════════════════════

# 懒加载 OCR（ddddocr 首次加载较慢 ~1s，按需启动）
_ocr_engine = None
_ocr_engine_failed = False


def _get_ocr():
    """
    懒加载 ddddocr 引擎（首次调用时初始化）。

    为什么不一开始就加载：ddddocr 加载 onnx 模型要 1-2 秒，拖慢脚本启动。
    实际游戏中绝大多数点击可以用模板匹配搞定，OCR 只在动态文字场景用。
    """
    global _ocr_engine, _ocr_engine_failed
    if _ocr_engine is not None:
        return _ocr_engine
    if _ocr_engine_failed:
        return None
    try:
        import ddddocr
        from PIL import Image
        _ocr_engine = ddddocr.DdddOcr(show_ad=False)
        log.info("[A3] ddddocr 引擎加载成功")
        return _ocr_engine
    except Exception as e:
        _ocr_engine_failed = True
        log.warning(f"[A3] ddddocr 加载失败: {e}")
        return None


def find_text_and_click(c: MuMuController,
                        text: str,
                        threshold: float = 0.8,
                        max_retry: int = 3) -> bool:
    """
    [A3] 在屏幕上找到包含指定文字 text 的位置并点击中心。

    双策略：
      1. **模板匹配优先**：H:/pic/text/<text>.png（如"领取.png"）
         - 游戏 UI 文字常用艺术字，模板匹配最稳
         - 预先截图保存即可，无需 OCR
      2. **OCR 兜底**：用 ddddocr 在屏幕上扫描
         - 对未预先准备模板的动态文字也能识别
         - 但游戏艺术字 OCR 识别率较低（实测 ddddocr 默认模式对菜单文字约 30% 准确率）

    参数:
        c         : MuMuController 实例
        text      : 目标文字（中文/英文都支持）
        threshold : 匹配阈值（默认 0.8）
        max_retry : 截图-匹配最大重试次数（应对网络延迟/loading）

    返回:
        True  = 找到并点击成功
        False = 模板和 OCR 都未找到
    """
    # ── 策略1：模板匹配 ──────────────────────────────────
    tpl_path = os.path.join(TPL_TEXT_DIR, f"{text}.png")
    if os.path.exists(tpl_path):
        for i in range(max_retry):
            pos = c.find_image(tpl_path, threshold=threshold)
            if pos is not None:
                log.info(f"[A3] 模板匹配到「{text}」@ {pos}，点击")
                c.tap(pos[0], pos[1], delay=config.DEFAULT_CLICK_DELAY)
                return True
            import time
            time.sleep(0.5)
        log.info(f"[A3] 模板 {text}.png {max_retry} 次未找到，尝试 OCR")
    else:
        log.debug(f"[A3] 模板 {tpl_path} 不存在，跳过模板匹配")

    # ── 策略2：OCR 兜底 ──────────────────────────────────
    ocr = _get_ocr()
    if ocr is None:
        log.warning(f"[A3] OCR 引擎不可用，无法识别「{text}」")
        return False

    import time
    try:
        from PIL import Image
        for i in range(max_retry):
            screen = c.capture_screen()
            if screen is None:
                time.sleep(0.5)
                continue

            # 把 BGR 截图转成 PIL Image
            pil_img = Image.fromarray(cv2.cvtColor(screen, cv2.COLOR_BGR2RGB))
            recognized = ocr.classification(pil_img)

            # ddddocr 返回的是无空格字符串，做宽松匹配
            if text in recognized:
                # OCR 没返回坐标，只能粗略估算（屏幕中央）
                # 这对游戏 UI 不太可靠，所以 OCR 命中时降级为提示
                log.warning(
                    f"[A3] ⚠️ OCR 识别到「{text}」文字但无法定位坐标，"
                    f"建议在 H:/pic/text/{text}.png 准备模板。"
                    f"完整识别: {recognized!r}"
                )
                # 返回 True 让上层知道文字在屏幕上（但不点击）
                return False
            time.sleep(0.5)
    except Exception as e:
        log.warning(f"[A3] OCR 异常: {e}")

    log.warning(f"[A3] ❌ 模板+OCR 都未找到「{text}」")
    return False


# ══════════════════════════════════════════════════════════
# 便捷函数：批量关闭所有弹窗回到主菜单
# ══════════════════════════════════════════════════════════

def close_all_popups(c: MuMuController, max_rounds: int = 5) -> bool:
    """
    一键关闭所有可能的弹窗/子界面，回到主菜单。

    组合调用：
      1. 点右上角 X（子界面）
      2. 找图点 continue/close/sure 等通用关闭按钮
      3. 点空白处取消选中
      4. 检测是否回到主菜单

    返回: True=回到主菜单 / False=失败
    """
    import time
    log.info("[BATCH] 开始关闭所有弹窗...")
    for round_i in range(1, max_rounds + 1):
        if is_in_main_menu(c):
            log.info(f"[BATCH] ✅ 已在主菜单（第 {round_i} 轮检测）")
            return True

        # 优先右上角X
        if click_top_right_close(c):
            time.sleep(1.0)
            continue

        # 兜底：常见关闭按钮
        for tpl_name in ["window/cha.png", "window/close.png",
                         "window/continue.png", "window/sure.png",
                         "window/no.png"]:
            tpl = _pic(*tpl_name.split("/"))
            pos = c.find_image(tpl, threshold=0.8)
            if pos is not None:
                log.info(f"[BATCH] 点击关闭按钮 {tpl_name} @ {pos}")
                c.tap(pos[0], pos[1], delay=0.5)
                time.sleep(0.8)
                break
        else:
            # 都找不到，点空白处
            c.tap_empty(cnt=1, delay=0.5)
            time.sleep(0.5)

    # 最后再检测一次
    return is_in_main_menu(c)
