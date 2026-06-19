# MuMu 游戏自动化 — 后台运行版

> 位置：`H:\AI\07_代码脚本\mumu-auto-bg\`

## 与原版的核心区别

| 对比项 | 原版 | 新版 |
|--------|------|------|
| 截图方式 | `pyautogui.screenshot` + `ImageGrab` | `adb exec-out screencap`（完全后台） |
| 窗口依赖 | 必须置顶 / 恢复最小化 | **不需要**，窗口可隐藏 |
| 点击方式 | pyautogui 鼠标 + ADB 混用 | **全部 ADB**，鼠标不受干扰 |
| 模板匹配 | 单尺度 TM_CCOEFF_NORMED | **多尺度匹配**（±10%），更鲁棒 |
| 中文路径 | 不支持 | **支持**（使用 numpy 读取图片） |
| click delay | 写死 2s | 参数化（默认 0.3s），速度提升数倍 |
| sleep 冗余 | `is_image_visible` 每次 +1s | 无额外 sleep |
| 错误日志 | 只有 print | 同时写文件 + 控制台 |
| 代码结构 | 多文件、逻辑散落 | 模块化 Step 设计，统一管理 |

## 文件结构

```
mumu-auto-bg/
├── config.py           # 所有可配置项（设备ID、路径、延迟等）
├── core.py             # 核心控制器（截图 + ADB 操作 + 图像匹配）
├── actions.py          # 通用动作封装
├── emulator.py         # 模拟器控制
├── dailyNew.py         # 日常任务主入口
├── tower/              # 职业塔模块
│   ├── tower_main.py   # 职业塔主入口
│   ├── step1_enter_tower.py
│   └── step3_battle_floors.py
├── steps/              # 日常任务步骤
│   ├── step1_start_emulator.py
│   ├── step3_enter_main_menu.py
│   ├── step4_handle_envelope.py
│   ├── step5_collect_and_sale.py
│   ├── step6_collect_xianghuo.py
│   ├── step7_handle_taofa.py
│   ├── step8_go_to_shop.py
│   ├── step9_share_game.py
│   └── step10_get_honor.py
├── pics/               # 图片模板（相对路径）
│   ├── menu/           # 菜单相关
│   ├── fight/          # 战斗相关
│   ├── window/         # 窗口按钮
│   └── ...
├── test_tap_empty.py   # 测试脚本
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install opencv-python numpy
```

### 2. 配置 `config.py`

```python
DEVICE_ID = "127.0.0.1:16384"   # MuMu 默认端口
PIC_ROOT  = "pics"              # 图片模板目录（相对路径）
```

### 3. 运行

```bash
# 日常任务
python dailyNew.py

# 职业塔（所有职业）
python tower/tower_main.py

# 职业塔（指定职业）
python tower/tower_main.py --job shangren
python tower/tower_main.py --job lieren xuezhe

# 单独测试某个 Step
python steps/step7_handle_taofa.py
python tower/step1_enter_tower.py --job wuzhe
```

## 支持的职业

| 代码 | 职业 |
|------|------|
| `lieren` | 猎人 |
| `xingguan` | 行商 |
| `xuezhe` | 学者 |
| `youxia` | 游侠 |
| `yaoshi` | 药师 |
| `jianshi` | 剑士 |
| `shangren` | 商人 |
| `wuzhe` | 武者 |

## 核心功能

### 日常任务 (dailyNew.py)

1. 启动模拟器和游戏
2. 进入主菜单
3. 处理信封
4. 收集并出售
5. 收集香火
6. 讨伐任务（普通/高级/一阶）
7. 商店购买
8. 分享游戏
9. 领取荣誉

### 职业塔 (tower/tower_main.py)

1. 进入试炼之塔
2. 选择职业（支持下滑查找）
3. 挑战 1-4 层
4. 自动战斗和结算
5. 跳过已通关职业（检测 fivefive.png）

## 关键特性

### 长按操作

部分场景需要长按才能触发：

```python
c.long_press(x, y, duration_ms=1000)  # 长按1秒
c.tap_empty_long(cnt=3)               # 长按空白3次
```

### 滑动操作

```python
c.swipe(540, 800, 540, 400, duration_ms=300)  # 向上滑动
```

### 多尺度匹配

自动尝试 ±10% 缩放，适应不同分辨率：

```python
c.find_image(path, threshold=0.9)
```

### 中文路径支持

使用 `cv2.imdecode(np.fromfile())` 替代 `cv2.imread()`，完美支持中文路径。

## 添加新任务

1. 在 `steps/` 下创建 `stepN_xxx.py`
2. 实现 `run()` 函数
3. 在 `dailyNew.py` 中导入并调用

示例：

```python
# steps/stepN_xxx.py
import logging
from core import MuMuController

log = logging.getLogger(__name__)

def run(c: MuMuController = None):
    if c is None:
        c = MuMuController()
    # 你的逻辑
    log.info("Step N 完成")
```

## 图片模板

所有图片存放在 `pics/` 目录下：

```
pics/
├── menu/           # 菜单按钮
│   ├── menu.png
│   ├── search.png
│   ├── zhiyeta/    # 职业塔
│   └── taofa/      # 讨伐
├── fight/          # 战斗相关
├── window/         # 窗口按钮
│   ├── sure.png
│   ├── close.png
│   └── continue.png
└── ...
```

## 日志

运行日志保存在 `run.log`，同时输出到控制台。

## 常见问题

### 点击无效

尝试使用长按：`c.long_press(x, y, duration_ms=1000)`

### 找不到图片

1. 检查图片路径是否正确
2. 调低匹配阈值：`threshold=0.8`
3. 检查游戏界面是否有变化

### 滑动无效

确保使用 `c.swipe()` 而不是 `c.mumu_swipe()`
