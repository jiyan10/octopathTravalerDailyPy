"""
配置文件 — 统一管理所有可变参数
修改设备ID或图片路径时只需改这里
"""
import os

# ── ADB 设备 ──────────────────────────────────────────────
DEVICE_ID = "127.0.0.1:16384"   # MuMu 默认端口，多开时改这里

# ── MuMu CLI（官方输入注入） ──────────────────────────────
MUMU_CLI = r"D:\Program Files\Netease\MuMu Player 12\nx_main\mumu-cli.exe"
ADB = r"D:\Program Files\Netease\MuMu Player 12\nx_device\12.0\shell\adb.exe"
VM_INDEX = 0                    # 模拟器实例编号（从 0 开始）

# ── 图片资源根目录（相对路径，相对于本文件所在目录） ─────
PIC_ROOT = os.path.join(os.path.dirname(__file__), "pics")

# ── 点击默认延迟（秒）────────────────────────────────────
DEFAULT_CLICK_DELAY   = 0.5   # 普通点击后等待时间（用户偏好较慢）
FAST_CLICK_DELAY      = 0.2   # 战斗操作用
SLOW_CLICK_DELAY      = 1.0   # 界面切换后等待时间
SWIPE_DELAY           = 0.8   # 滑动后等待时间

# ── 模板匹配默认阈值 ─────────────────────────────────────
DEFAULT_THRESHOLD = 0.8

# ── find_and_click_sure 最大重试次数 ─────────────────────
DEFAULT_RETRY_CNT = 5

# ── 日志 ─────────────────────────────────────────────────
LOG_FILE = os.path.join(os.path.dirname(__file__), "run.log")
