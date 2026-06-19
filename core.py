"""
core.py — MuMu12 后台核心控制器（mumu-cli 版）
=====================================================
完全后台运行，不依赖窗口焦点：
  - 截图：mumu-cli adb exec-out screencap -p（官方通道）
  - 点击/滑动：mumu-cli.exe control tool cmd（官方输入管线）
  - 图像识别：OpenCV 多尺度模板匹配
=====================================================

关键突破（2026-05-26）：
  adb shell input tap/swipe  → 游戏不响应 ❌
  pyautogui.click()          → 游戏不响应 ❌
  sendevent MT协议           → 有圆圈但游戏不响应 ⚠️
  mumu-cli input tap/swipe   → ✅ 100% 响应！（官方输入管线）

截图方案变更（2026-06-16）：
  原方案：adb shell screencap -p（依赖独立 ADB.exe）
  新方案：mumu-cli adb --cmd "exec-out screencap -p"（统一走 mumu-cli 通道）
  优势：单条通道，输入和截图都过 mumu-cli，不需要单独管理 ADB
"""

import subprocess
import time
import os
import logging
import numpy as np
import cv2
from dataclasses import dataclass
from typing import Optional, Tuple, List

import config

# ── 日志配置 ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# 输入注入：mumu-cli 官方接口
# ══════════════════════════════════════════════════════════

def _mumu_cmd(cmd_str: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    通过 mumu-cli 发送控制命令
    返回: (成功与否, 输出信息)
    """
    full_cmd = [
        config.MUMU_CLI,
        "control",
        f"--vmindex", str(config.VM_INDEX),
        "tool",
        "cmd",
        "--cmd", cmd_str,
    ]
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
        stdout = result.stdout.strip()
        if '"errcode": 0' in stdout or result.returncode == 0:
            return True, stdout
        else:
            return False, f"rc={result.returncode}, out={stdout}, err={result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "超时"
    except Exception as e:
        return False, str(e)


def adb_tap(x: int, y: int, delay: float = config.DEFAULT_CLICK_DELAY) -> bool:
    """
    使用 ADB 命令点击指定坐标（更可靠）。
    坐标系: ADB 截图坐标系 (1920x1080)，直接对应模板匹配结果。
    """
    try:
        result = subprocess.run(
            [config.ADB, "-s", config.DEVICE_ID, "shell", "input", "tap", str(int(x)), str(int(y))],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            if delay > 0:
                time.sleep(delay)
            return True
        else:
            log.warning(f"adb_tap({x},{y}) 失败: {result.stderr}")
            return False
    except Exception as e:
        log.warning(f"adb_tap({x},{y}) 异常: {e}")
        return False


def mumu_tap(x: int, y: int, delay: float = config.DEFAULT_CLICK_DELAY) -> bool:
    """
    使用 mumu-cli 官方接口点击指定坐标。
    坐标系: ADB 截图坐标系 (1920x1080)，直接对应模板匹配结果。
    """
    ok, info = _mumu_cmd(f"input tap {int(x)} {int(y)}")
    if not ok:
        log.warning(f"mumu_tap({x},{y}) 失败: {info}")
    if delay > 0:
        time.sleep(delay)
    return ok


def mumu_swipe(x1: int, y1: int, x2: int, y2: int,
               duration_ms: int = 500, delay: float = config.SWIPE_DELAY) -> bool:
    """
    使用 mumu-cli 官方接口滑动。
    当 x1==x2 且 y1==y2 时等效于长按 duration_ms 毫秒。
    """
    ok, info = _mumu_cmd(
        f"input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {duration_ms}"
    )
    if not ok:
        log.warning(f"mumu_swipe 失败: {info}")
    if delay > 0:
        time.sleep(delay)
    return ok


def mumu_long_press(x: int, y: int, duration_ms: int = 900,
                    delay: float = config.DEFAULT_CLICK_DELAY) -> bool:
    """长按"""
    return mumu_swipe(x, y, x, y, duration_ms, delay)


# ══════════════════════════════════════════════════════════
# 截图后端：mumu-cli adb exec-out screencap
# ══════════════════════════════════════════════════════════

def take_screenshot(save_path: Optional[str] = None) -> Optional[np.ndarray]:
    """
    通过 mumu-cli 官方通道截图，返回 BGR numpy 数组。

    方案 2（2026-06-16 升级）：
        mumu-cli adb --vmindex N --cmd "exec-out screencap -p"
        - 与点击/滑动共用 mumu-cli 通道，统一管理
        - 截图数据通过 stdout 输出，Python 直接读取
        - 完全后台运行，不依赖窗口

    兜底：如果 mumu-cli 通道失败（模拟器未启动、版本太旧），
    自动降级到独立 ADB（adb -s <DEVICE_ID> exec-out screencap -p）。
    """
    img = _take_screenshot_via_mumu_cli(save_path)
    if img is not None:
        return img
    log.warning("mumu-cli 截图失败，尝试降级到独立 ADB ...")
    return _take_screenshot_via_adb(save_path)


def _take_screenshot_via_mumu_cli(save_path: Optional[str]) -> Optional[np.ndarray]:
    """
    通过 mumu-cli 官方通道截图。
    命令格式：
        mumu-cli adb --vmindex <idx> --cmd "exec-out screencap -p"
    输出：PNG 二进制数据到 stdout

    注意：mumu-cli 在 Windows 下 subprocess 的 returncode 经常返回
    0xFFFFFFFF 之类 wrap-around 值，但只要 stdout 有数据就视为成功。
    """
    cmd = [
        config.MUMU_CLI,
        "adb",
        "--vmindex", str(config.VM_INDEX),  # mumu-cli adb 用空格，不用 =（实测）
        "--cmd", "exec-out screencap -p",
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=15,
        )
        raw = result.stdout
        err = result.stderr.decode(errors="replace").strip()
        # mumu-cli 经常 rc 非 0 但 stdout 有数据，按 stdout 长度判断
        if len(raw) < 1000:
            # 截图通常几十 KB~1MB，过短说明没拿到图像
            log.debug(f"mumu-cli screencap 失败: rc={result.returncode}, "
                      f"stdout_len={len(raw)}, err={err[:200]}")
            return None

        # 不要做 \r\n -> \n 替换！PNG 头里 0x0D 0x0A 是固定签名，
        # 替换后 cv2.imdecode 会失败（实际验证 2026-06-16 22:28）
        img_array = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            log.warning(f"mumu-cli screencap 解码失败: stdout_len={len(raw)}, "
                        f"first_bytes={raw[:20]!r}")
            return None

        if save_path:
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            # cv2.imwrite 不支持 Windows 中文路径，用 imencode+tofile 替代
            _, buf = cv2.imencode(".png", img)
            buf.tofile(save_path)
        return img
    except subprocess.TimeoutExpired:
        log.warning("mumu-cli screencap 超时（15s）")
        return None
    except FileNotFoundError:
        log.warning(f"mumu-cli 不存在: {config.MUMU_CLI}")
        return None
    except Exception as e:
        log.warning(f"mumu-cli screencap 异常: {e}")
        return None


def _take_screenshot_via_adb(save_path: Optional[str]) -> Optional[np.ndarray]:
    """
    降级方案：使用独立 ADB 截图（老方案，保留作为兜底）。
    """
    cmd = [config.ADB, "-s", config.DEVICE_ID, "exec-out", "screencap", "-p"]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=15)
        if result.returncode != 0:
            log.error(f"adb screencap 失败: {result.stderr.decode(errors='replace')}")
            return None
        raw = result.stdout
        # 同样不要做 \r\n -> \n 替换（PNG 头里有 0x0D 0x0A 固定签名）
        img_array = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            log.error("adb screencap 解码失败")
            return None
        if save_path:
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            _, buf = cv2.imencode(".png", img)
            buf.tofile(save_path)
        return img
    except Exception as e:
        log.error(f"adb screencap 异常: {e}")
        return None


# ══════════════════════════════════════════════════════════
# ADB 基础操作（保留用于非输入用途，如检查设备状态等）
# ══════════════════════════════════════════════════════════

def _adb(*args, timeout: int = 10) -> Tuple[bool, str]:
    """执行 adb 命令，返回 (成功, 信息)"""
    cmd = [config.ADB, "-s", config.DEVICE_ID, *args]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
        if r.returncode != 0:
            return False, r.stderr.strip()
        return True, r.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "超时"
    except Exception as e:
        return False, str(e)


# ══════════════════════════════════════════════════════════
# 战斗指令数据类
# ══════════════════════════════════════════════════════════

@dataclass
class FightOrder:
    person: int        # 人物编号 1-5
    changePerson: bool # 是否换人
    cycle: bool        # 是否循环
    skill: int         # 技能编号 1-4（0=执行指令标记）
    skillLevel: int    # 技能等级 1-4
    skillToPerson: int # 技能目标人物（0=无需选人）


def _skill_pos(order: FightOrder) -> Optional[Tuple[int,int,int,int]]:
    """根据 FightOrder 获取技能拖拽起止坐标"""
    skill_map = {
        (1, 1):(1400,304,1400,304), (1, 2):(1400,304,1552,304),
        (1, 3):(1400,304,1662,304), (1, 4):(1400,304,1800,304),
        (2, 1):(1400,460,1400,460), (2, 2):(1400,460,1552,460),
        (2, 3):(1400,460,1662,460), (2, 4):(1400,460,1800,460),
        (3, 1):(1400,631,1400,631), (3, 2):(1400,631,1552,631),
        (3, 3):(1400,631,1662,631), (3, 4):(1400,631,1800,631),
        (4, 1):(1400,791,1400,791), (4, 2):(1400,791,1552,791),
        (4, 3):(1400,791,1662,791), (4, 4):(1400,791,1800,791),
        (5, 1):(1400,951,1400,951), (5, 2):(1400,951,1552,951),
        (5, 3):(1400,951,1662,951), (5, 4):(1400,951,1800,951),
    }
    return skill_map.get((order.skill, order.skillLevel))


def _person_pos(person: int) -> Optional[Tuple[int,int]]:
    pos_map = {1:(1650,120),2:(1650,329),3:(1650,536),4:(1650,760),5:(1650,956)}
    return pos_map.get(person)


# ══════════════════════════════════════════════════════════
# 核心控制器
# ══════════════════════════════════════════════════════════

class MuMuController:
    """
    MuMu12 后台控制器（mumu-cli 全通道版）

    特性：
    - 完全后台运行，不需要窗口在前台
    - 输入（tap/swipe）和截图（screencap）都走 mumu-cli 官方通道
    - ADB 仅作为截图的兜底方案，保留用于非必要场景
    - OpenCV 多尺度模板匹配定位 UI 元素

    坐标系：所有坐标均为 ADB 截图坐标系 (1920×1080)
    """

    def __init__(self):
        self._last_pos: Tuple[int, int] = (0, 0)

    # ── 连接 ─────────────────────────────────────────────

    def connect(self) -> bool:
        """验证 mumu-cli 可用性与模拟器状态"""
        # 验证 mumu-cli 可用（用一个无害的 tap 命令测试）
        ok, msg = _mumu_cmd("input tap 1 1", timeout=5)
        if not ok:
            log.warning(f"mumu-cli 探测失败（首次测试 tap 可能本身就会 errcode-201）: {msg}")
            # 不直接返回 False，因为不同操作成功条件不同

        # 检查模拟器是否启动
        try:
            info_proc = subprocess.run(
                [config.MUMU_CLI, "info", f"--vmindex={config.VM_INDEX}"],
                capture_output=True, text=True, timeout=5, encoding="utf-8",
            )
            if "is_android_started\": true" in info_proc.stdout:
                log.info(f"连接成功: 模拟器已启动 (vmindex={config.VM_INDEX})")
            else:
                log.warning("mumu-cli 可达，但模拟器似乎未启动（is_android_started=false）")
        except Exception as e:
            log.warning(f"查询模拟器状态失败: {e}")

        log.info(f"控制器就绪: vmindex={config.VM_INDEX}")
        return True

    # ── 截图与图像匹配 ───────────────────────────────────

    def capture_screen(self, save_path: Optional[str] = None) -> Optional[np.ndarray]:
        """截取当前屏幕，可选保存到文件"""
        return take_screenshot(save_path)

    def find_image(self, template_path: str,
                   threshold: float = config.DEFAULT_THRESHOLD,
                   use_color: bool = True,
                   screen: Optional[np.ndarray] = None) -> Optional[Tuple[int, int]]:
        """
        在屏幕中查找模板图，返回中心坐标（ADB 坐标系）。
        支持多尺度匹配 (±10%)，对分辨率变化鲁棒。
        可传入已截图的 screen 参数避免重复截图。
        """
        if not os.path.exists(template_path):
            log.warning(f"模板不存在: {template_path}")
            return None

        if screen is None:
            screen = self.capture_screen()
        if screen is None:
            return None

        # 读取模板
        if use_color:
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            src = screen
        else:
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            src = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

        if template is None:
            log.warning(f"无法读取模板: {template_path}")
            return None

        sh, sw = src.shape[:2]
        th, tw = template.shape[:2]
        if sh < th or sw < tw:
            log.warning(f"屏幕({sw}x{sh}) < 模板({tw}x{th})")
            return None

        # 多尺度匹配（±10%，共 5 个尺度）
        best_val = -1.0
        best_loc = None
        best_tw, best_th = tw, th

        for scale in [0.90, 0.95, 1.0, 1.05, 1.10]:
            nw = int(tw * scale)
            nh = int(th * scale)
            if nw > sw or nh > sh or nw < 1 or nh < 1:
                continue
            resized = cv2.resize(template, (nw, nh))
            result = cv2.matchTemplate(src, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_tw, best_th = nw, nh

        if best_val < threshold or best_loc is None:
            log.debug(f"未找到模板 {os.path.basename(template_path)}, 最佳匹配度={best_val:.4f}")
            return None

        cx = best_loc[0] + best_tw // 2
        cy = best_loc[1] + best_th // 2
        log.debug(f"找到模板 {os.path.basename(template_path)} @ ({cx},{cy}), 匹配度={best_val:.4f}")
        return (cx, cy)

    def is_visible(self, template_path: str,
                   threshold: float = config.DEFAULT_THRESHOLD,
                   use_color: bool = True) -> bool:
        """判断图片是否在当前屏幕上可见"""
        pos = self.find_image(template_path, threshold, use_color)
        return pos is not None

    # ── 点击操作（使用 mumu-cli）──────────────────────────

    def tap(self, x: int, y: int, delay: float = config.DEFAULT_CLICK_DELAY) -> bool:
        """直接坐标点击（ADB 坐标系）"""
        self._last_pos = (x, y)
        return mumu_tap(x, y, delay)

    def find_and_tap(self, template_path: str,
                     threshold: float = config.DEFAULT_THRESHOLD,
                     use_color: bool = True,
                     delay: float = config.DEFAULT_CLICK_DELAY) -> bool:
        """找图并点击中心点，成功返回 True"""
        pos = self.find_image(template_path, threshold, use_color)
        log.info(f"find_and_tap({os.path.basename(template_path)}): {pos}")
        if pos is None:
            return False
        self._last_pos = pos
        return mumu_tap(pos[0], pos[1], delay)

    def find_and_tap_sure(self, template_path: str,
                          threshold: float = config.DEFAULT_THRESHOLD,
                          use_color: bool = True,
                          delay: float = config.DEFAULT_CLICK_DELAY,
                          retry: int = config.DEFAULT_RETRY_CNT) -> bool:
        """
        重试版 find_and_tap：最多重试 retry 次
        """
        for i in range(retry):
            if self.find_and_tap(template_path, threshold, use_color, delay):
                return True
            time.sleep(0.3)
        log.warning(f"find_and_tap_sure 失败({retry}次): {os.path.basename(template_path)}")
        return False

    def tap_empty(self, cnt: int = 1, delay: float = 0.3) -> None:
        """点击空白处（屏幕中央偏左上，一般无交互元素）- 使用 mumu_tap"""
        for _ in range(cnt):
            mumu_tap(400, 400, delay)

    def tap_empty_long(self, cnt: int = 1, delay: float = 0.3) -> None:
        """点击空白处（屏幕中央偏左上，一般无交互元素）- 使用长按"""
        for _ in range(cnt):
            mumu_long_press(400, 400, duration_ms=1000)
            time.sleep(delay)

    def swipe(self, x1: int, y1: int, x2: int, y2: int,
              duration_ms: int = 500) -> bool:
        """滑动操作"""
        return mumu_swipe(x1, y1, x2, y2, duration_ms)

    def long_press(self, x: int, y: int, duration_ms: int = 900) -> bool:
        """长按操作"""
        return mumu_long_press(x, y, duration_ms)

    # ── 常用界面操作封装 ──────────────────────────────────

    def _pic(self, *parts: str) -> str:
        return os.path.join(config.PIC_ROOT, *parts)

    def is_menu_visible(self) -> bool:
        return self.is_visible(self._pic("menu", "menu.png"), threshold=0.95)

    def is_attack_visible(self) -> bool:
        return self.is_visible(self._pic("fight", "attack.png"), threshold=0.95)

    def is_tiaozhan_visible(self) -> bool:
        """检查挑战按钮是否可见"""
        return self.is_visible(self._pic("menu", "zhiyeta", "tiaozhan.png"), threshold=0.9)

    def is_fight_finish(self) -> bool:
        return (self.is_menu_visible()
                or self.is_visible(self._pic("fight", "zhandoujiesuan.png"))
                or self.is_visible(self._pic("menu", "zhiyeta", "shiliantongguan.png")))

    def normal_exit(self, max_attempts: int = 10) -> None:
        """退出弹窗回到主菜单"""
        for _ in range(max_attempts):
            if self.is_menu_visible():
                return
            self.find_and_tap(self._pic("window", "cha.png"))
            if self.is_menu_visible():
                return
            self.find_and_tap(self._pic("window", "sure.png"))
            if self.is_menu_visible():
                return
            self.find_and_tap(self._pic("window", "no.png"))
            if self.is_menu_visible():
                return
            self.tap_empty()
            if self.is_menu_visible():
                return
            self.find_and_tap_sure(self._pic("window", "continue.png"))
            if self.is_menu_visible():
                return
            self.find_and_tap_sure(self._pic("window", "close.png"))
            if self.is_menu_visible():
                return
        log.warning("normal_exit: 多次尝试后仍未回到主菜单")

    def wait_for_menu(self, timeout: float = 60.0) -> bool:
        """等待主菜单出现"""
        start = time.time()
        while time.time() - start < timeout:
            if self.is_menu_visible():
                return True
            self.find_and_tap_sure(self._pic("window", "sure.png"), retry=1)
            time.sleep(0.5)
        log.warning("wait_for_menu 超时")
        return False

    def click_menu(self):
        return self.find_and_tap_sure(self._pic("menu", "menu.png"))

    def click_map(self):
        return self.find_and_tap_sure(self._pic("menu", "map.png"))

    def click_team(self):
        if not self.find_and_tap_sure(self._pic("menu", "team1.png")):
            return self.find_and_tap_sure(self._pic("menu", "team.png"))
        return True

    def click_yes(self):
        return self.find_and_tap_sure(self._pic("window", "yes.png"))

    def click_no(self):
        return self.find_and_tap_sure(self._pic("window", "no.png"))

    def click_sure(self):
        return self.find_and_tap_sure(self._pic("window", "sure.png"))

    def click_close(self):
        return self.find_and_tap_sure(self._pic("window", "close.png"))

    def click_continue(self):
        return self.find_and_tap_sure(self._pic("window", "continue.png"))

    def click_enter(self):
        return self.find_and_tap_sure(self._pic("window", "enter.png"))

    def click_small_map(self):
        self.tap(1620, 158, delay=0.3)

    def change_team_to(self, cnt: int = 1) -> None:
        target_map = {
            1: self._pic("menu", "team", "jiaobenduiwu.png"),
            2: self._pic("menu", "team", "fengmo1.png"),
            9: self._pic("menu", "team", "team9.png"),
        }
        target = target_map.get(cnt, self._pic("menu", "team", "jiaobenduiwu.png"))
        self.normal_exit()
        self.click_team()
        for _ in range(20):
            if self.is_visible(target):
                break
            self.find_and_tap(self._pic("window", "team_left.png"))
        self.normal_exit()

    # ── 地图导航 ─────────────────────────────────────────

    def _map_move(self, direction: str) -> None:
        dirs = {"up":(800,800,800,500), "down":(800,500,800,800),
                "left":(800,600,1100,600), "right":(1100,600,800,600)}
        coords = dirs.get(direction)
        if coords:
            mumu_swipe(*coords)

    def find_town_in_map(self, template_path: str,
                         threshold: float = 0.8) -> bool:
        self.normal_exit()
        self.click_map()
        self.find_and_tap_sure(self._pic("map", "xianshi.png"))
        self.find_and_tap_sure(self._pic("map", "suoxiao.png"))
        for act in ["up","right","down","left","up","right","down","left"]:
            for _ in range(5):
                if self.is_visible(template_path, threshold):
                    return True
                self._map_move(act)
        return False

    def enter_town(self, template_path: str, new_world: bool = False) -> None:
        if new_world:
            self._go_to_world(want_new=True)
        else:
            self._go_to_world(want_new=False)
        self.find_town_in_map(template_path)
        self.find_and_tap_sure(template_path)
        self.find_and_tap_sure(self._pic("map", "goto.png"))
        self.click_yes()
        self.wait_for_menu()

    def _go_to_world(self, want_new: bool) -> None:
        self.normal_exit()
        self.click_map()
        time.sleep(1)
        has_new = (self.is_visible(self._pic("map","oldworld1.png"))
                   or self.is_visible(self._pic("map","oldworld2.png")))
        if (want_new and has_new) or (not want_new and not has_new):
            self.normal_exit()
            return
        self.find_and_tap(self._pic("map","newworld1.png"))
        self.find_and_tap(self._pic("map","newworld2.png"))
        self.find_and_tap(self._pic("map","oldworld1.png"))
        self.find_and_tap(self._pic("map","oldworld2.png"))
        self.click_yes()
        time.sleep(7)
        self.normal_exit()

    def go_to_small_map_in_town(self, x: int, y: int) -> None:
        self.click_small_map()
        self.tap(x, y)
        self.wait_for_menu()

    def go_to_bed_in_town(self) -> None:
        self.normal_exit()
        self.click_small_map()
        if not self.find_and_tap_sure(self._pic("map","chuang.png")):
            self.normal_exit()
            self.find_and_tap_sure(self._pic("map","chuang.png"))
        self.wait_for_menu()
        self.find_and_tap_sure(self._pic("map","chuangnei.png"))
        time.sleep(2)
        self.tap_empty(3)
        self.click_yes()
        time.sleep(2)
        self.tap_empty(3)
        self.click_sure()
        self.click_small_map()
        self.find_and_tap_sure(self._pic("map","door.png"))
        self.normal_exit()

    # ── 战斗 ─────────────────────────────────────────────

    def fight_one_order(self, order: FightOrder) -> None:
        pp = _person_pos(order.person)
        if pp:
            mumu_tap(*pp, delay=config.FAST_CLICK_DELAY)
        if order.changePerson:
            mumu_tap(1650, 956, delay=config.FAST_CLICK_DELAY)
        if order.cycle:
            mumu_tap(1440, 62, delay=0.5)
        sp = _skill_pos(order)
        if sp:
            mumu_swipe(sp[0], sp[1], sp[2], sp[3], duration_ms=200, delay=0.2)
        if order.skillToPerson > 0:
            tp = _person_pos(order.skillToPerson)
            if tp:
                mumu_tap(*tp, delay=config.FAST_CLICK_DELAY)

    def fight_all_order(self, orders: list) -> None:
        for order in orders:
            if order.person < 5:
                self.fight_one_order(order)
            else:
                # 点击攻击按钮前，判断攻击按钮是否可见
                if not self.is_attack_visible():
                    self.tap_empty_long(1)
                    time.sleep(0.5)
                self.tap(340, 730, delay=0.2)
                self.tap(340, 730, delay=0.2)
                self.tap(340, 730, delay=0.2)
                pp = _person_pos(order.person)
                if pp:
                    mumu_tap(*pp, delay=0.2)
                start = time.time()
                while not self.is_attack_visible():
                    if self.is_fight_finish():
                        # 一直点击直到出现挑战按钮或关闭按钮
                        close_path = self._pic("window", "close.png")
                        while not self.is_tiaozhan_visible():
                            if self.is_visible(close_path):
                                self.click_close()
                            else:
                                self.tap_empty_long(1)
                            time.sleep(0.3)
                        return
                    if time.time() - start > 30:
                        break
        self.find_and_tap(self._pic("fight","fangqi.png"))
        self.click_yes()
        time.sleep(4)
        self.click_close()

    def weituo_fight(self) -> None:
        self.find_and_tap(self._pic("fight","weituo.png"))
        self.find_and_tap(self._pic("fight","weituokaishi.png"))
        self.find_and_tap(self._pic("fight","suolue.png"), threshold=0.95)

    def on_the_way_to_fight(self) -> None:
        time.sleep(1)
        timeout = time.time() + 120
        while not self.is_menu_visible():
            if time.time() > timeout:
                break
            self.find_and_tap(self._pic("fight","zhandoujiesuan.png"))
            self.find_and_tap(self._pic("window","sure.png"))
            self.weituo_fight()

    def go_to_small_map_in_fight(self, x: int, y: int, fight=None) -> None:
        self.click_small_map()
        self.tap(x, y, delay=1)
        timeout = time.time() + 120
        while not self.is_menu_visible():
            if time.time() > timeout:
                break
            if self.is_attack_visible() and fight:
                fight(self)
            self.find_and_tap(self._pic("fight","zandoujieshu.png"))
            self.find_and_tap(self._pic("window","sure.png"))
