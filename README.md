# MuMu 游戏自动化 — 后台运行版

> 位置：`H:\AI\07_代码脚本\mumu-auto-bg\`

## 与原版的核心区别

| 对比项 | 原版 | 新版 |
|--------|------|------|
| 截图方式 | `pyautogui.screenshot` + `ImageGrab` | `adb exec-out screencap`（完全后台） |
| 窗口依赖 | 必须置顶 / 恢复最小化 | **不需要**，窗口可隐藏 |
| 点击方式 | pyautogui 鼠标 + ADB 混用 | **全部 ADB**，鼠标不受干扰 |
| 模板匹配 | 单尺度 TM_CCOEFF_NORMED | **多尺度匹配**（±10%），更鲁棒 |
| click delay | 写死 2s | 参数化（默认 0.3s），速度提升数倍 |
| sleep 冗余 | `is_image_visible` 每次 +1s | 无额外 sleep |
| 错误日志 | 只有 print | 同时写文件 + 控制台 |
| 代码结构 | 多文件、逻辑散落 | 单一 `MuMuController` 统一管理 |

## 文件结构

```
mumu-auto-bg/
├── config.py       # 所有可配置项（设备ID、路径、延迟等）
├── core.py         # 核心控制器（截图 + ADB 操作 + 图像匹配）
├── daily_tasks.py  # 日常任务集合
├── start_game.py   # 启动/连接游戏
├── main.py         # 入口，支持命令行参数
├── run.log         # 运行日志（自动生成）
└── README.md       # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install opencv-python numpy
# Tesseract OCR（如需文字识别）
# pip install pytesseract
```

### 2. 配置 `config.py`

```python
DEVICE_ID = "127.0.0.1:16384"   # MuMu 默认端口
PIC_ROOT  = r"H:\pic"            # 图片模板目录
```

### 3. 运行

```bash
# 全套日常（推荐）
python main.py

# 只跑职业塔
python main.py --zhi-ye

# 跳过游戏启动检查
python main.py --skip-start
```

## 截图后端切换

在 `config.py` 中修改：

```python
# 方式1（默认）：adb exec-out，无需额外安装，完全后台
SCREENSHOT_BACKEND = "adb"

# 方式2：MuMu 官方 API，速度更快（需安装 MuMuPlayer SDK）
SCREENSHOT_BACKEND = "mumu"
MUMU_INSTALL_PATH = r"D:\Program Files\Netease\MuMuPlayer 12"
```

## 可选升级：MuMu 官方 API

MuMu12 在安装目录的 `shell/` 下提供了 Python SDK，主要优势：
- 截图比 adb screencap 快 3-5 倍
- 可获取安卓原始像素数据
- 支持多实例独立控制

在 `core.py` 的 `_screenshot_via_mumu()` 中已预置接入逻辑，
只需将 `SCREENSHOT_BACKEND` 改为 `"mumu"` 即可自动使用。

## 可选升级：特征点匹配（抗分辨率变化）

如果模板匹配经常失效（界面有偏移/缩放），可在 `core.py` 的
`find_image()` 中替换为 ORB 特征点匹配：

```python
# 在 find_image 中可选启用
orb = cv2.ORB_create()
kp1, des1 = orb.detectAndCompute(template_gray, None)
kp2, des2 = orb.detectAndCompute(screen_gray, None)
# BFMatcher 匹配 ...
```

已有的多尺度匹配（±10%）对常见分辨率变化已足够。

## 添加新任务

在 `daily_tasks.py` 末尾仿照现有函数添加，
然后在 `main.py` 的 `run_daily()` 中调用即可。
