# mumu-auto-bg 项目交接文档

> 由 TRAE Agent 生成，供 TRAE IDE 继续开发使用

---

## 一、项目概述

**项目名称**：mumu-auto-bg  
**项目路径**：`H:\AI\07_代码脚本\mumu-auto-bg`  
**目标**：实现 MuMu 模拟器完全后台自动化，彻底摆脱窗口前台依赖  
**游戏**：《歧路旅人：大陆的霸者》（包名 `com.netease.ma167`）  

### 核心突破

通过大量实验发现，**只有 mumu-cli 官方输入管线能让游戏响应触控**：

| 输入方式 | 结果 |
|---------|------|
| `adb shell input tap/swipe` | 游戏不响应 |
| `pyautogui.click()` | 游戏不响应 |
| `sendevent MT协议` | 有圆圈但游戏不响应 |
| **mumu-cli input tap/swipe** | **100% 响应** |

因此整个项目基于 `mumu-cli` 构建，截图也走 mumu-cli 通道（`adb exec-out screencap -p` 作为兜底）。

---

## 二、文件结构

```
mumu-auto-bg/
├── config.py          # 配置中心（设备ID、路径、延迟、阈值）
├── core.py            # 核心引擎（MuMuController - 截图、点击、滑动、匹配、战斗）
├── emulator.py        # 模拟器生命周期管理（启动、关闭、状态检测）
├── actions.py         # 原子操作封装层（语义化操作 + OCR兜底）
├── daily_tasks.py     # 日常任务集合（信封、采集、讨伐、商店、荣耀、职业塔）
├── dailyNew.py        # 新入口脚本（Step 1-3：启动模拟器→启动游戏→进入主菜单）
├── start_game.py      # 游戏启动（纯ADB am start，不依赖窗口）
├── envelope_run.py    # 信封领取调试版（带截图保存）
├── main.py            # 旧入口（支持命令行参数）
└── README.md          # 项目说明
```

---

## 三、各文件详细说明

### config.py

所有可变参数集中管理：
- `DEVICE_ID = "127.0.0.1:16384"` — ADB 设备地址
- `MUMU_CLI_PATH` — mumu-cli 可执行文件路径
- `ADB_PATH` — adb 可执行文件路径
- `PIC_ROOT = r"H:\pic"` — 图片资源根目录
- 各级延迟（`DELAY_NORMAL = 0.5`、`DELAY_BATTLE = 0.2`、`DELAY_UI = 1.0`）
- 匹配阈值 `MATCH_THRESHOLD = 0.8`
- 重试次数 `MAX_RETRY = 5`
- 日志文件路径

### core.py — 核心引擎

**MuMuController 类**：
- **输入注入**：通过 `_mumu_cmd()` 调用 `mumu-cli control --vmindex N tool cmd --cmd "input tap X Y"`
- **截图**：`mumu-cli adb --vmindex N --cmd "exec-out screencap -p"`，从 stdout 读取 PNG 数据
  - 踩坑记录：不做 `\r\n` 替换（PNG 头有 `0x0D 0x0A` 固定签名）
  - mumu-cli returncode 常为 0xFFFFFFFF，但只要有 stdout 数据就算成功
  - **兜底方案**：mumu-cli 失败时自动降级到独立 ADB
- **图像匹配**：`find_image()` 实现**多尺度模板匹配**（0.90/0.95/1.0/1.05/1.10 共5个尺度）
- **战斗系统**：`FightOrder` 数据类 + `fight_one_order` / `fight_all_order`
- **地图导航**：`_map_move` + `find_town_in_map`（8方向各滑5次）

### emulator.py

基于 mumu-cli 封装：
- `launch_emulator()` — 启动模拟器
- `shutdown_emulator()` — 关闭模拟器
- `is_android_started()` / `get_emulator_info()` — 状态检测

**mumu-cli 参数格式踩坑**：`control` 子命令必须用空格分隔 `--vmindex 0`，不能用等号。

### actions.py

原子操作封装层：
- `is_in_main_menu()` — 用 `menu_marker.png` 判断是否在主菜单
- `click_top_right_close()` — 点击右上角 X
- `find_text_and_click()` — **模板匹配优先 + OCR 兜底**（懒加载 ddddocr）
- `close_all_popups()` — 批量关闭所有弹窗

### daily_tasks.py

日常任务集合，每个函数接受可选 `ctrl` 参数（共享控制器实例）：
- `handle_envolop()` — 领取信封奖励
- `collect_and_sale_creature()` — 回收出售生物
- `collect_xianghuo()` — 收取香火
- `handle_taofa()` — 三轮讨伐（山东大树、山东亚狼、一阶讨伐佣杰）
- `go_to_shop()` — 商店购买
- `get_honor()` — 领取荣耀
- `zhi_ye_ta_enter()` — 职业塔挑战（8职业 x 4层）
- `_shilian_orders()` — 试炼之塔战斗指令模板

### dailyNew.py — 当前开发重点

新入口脚本，当前已实现 **Step 1-3**：
1. 启动 MuMu 模拟器（mumu-cli control launch）
2. 启动游戏（adb am start）
3. 等待进入主菜单（轮询 menu_marker.png）

**待完成**：Step 4 及以后的日常任务执行。

### start_game.py

纯 ADB 方式启动游戏：
- `adb connect` → `adb shell am start` → 轮询 `pidof` 检测进程 → 等待主菜单
- 包名当前是 TODO 占位符 `com.netease.xxxx`，**需要确认实际包名**

---

## 四、当前状态与阻塞问题

### 已完成的
- 项目架构搭建完成
- core.py 核心引擎完成（mumu-cli 截图 + 输入 + 多尺度匹配）
- dailyNew.py Step 1-3 逻辑完成

### 当前阻塞
**模拟器无法启动**：`mumu-cli control --vmindex 0 launch` 反复报错 `VERR_OLE_FAILURE`

**根本原因**：VT 虚拟化驱动缺失
- `MuMuChecker.exe checker /vt` 诊断显示：`open driver fail`（系统找不到指定文件）
- 服务管理器访问被拒绝（error code: 5），说明当前环境无管理员权限
- VirtualBox 引擎（`VBoxHeadless`、`VBoxSVC`）进程未运行

**解决方案**：
1. 手动打开 MuMu 模拟器（通过桌面快捷方式/开始菜单），让它自动修复驱动
2. 或重启电脑，让 VT 驱动在系统启动时自动加载
3. 确认模拟器能正常启动后，再继续执行 `dailyNew.py`

### 待办事项
- [ ] 修复模拟器启动问题（VT 驱动）
- [ ] 确认游戏包名（当前 `com.netease.xxxx` 是占位符）
- [ ] 完成 dailyNew.py Step 4+（日常任务执行）
- [ ] 测试信封领取流程
- [ ] 测试讨伐流程
- [ ] 测试职业塔流程
- [ ] 验证后台运行（模拟器最小化时是否正常）

---

## 五、关键技术细节

### mumu-cli 截图踩坑
```python
# 正确做法：不做 \r\n 替换
raw = stdout.replace(b'\r\n', b'\n')  # 这会破坏 PNG 头！
# 应该直接读取 stdout，或者只替换 \r\n 为 \n 但要小心 PNG 签名
```

### mumu-cli 参数格式
```bash
# 正确
mumu-cli.exe control --vmindex 0 launch

# 错误（不能用等号）
mumu-cli.exe control --vmindex=0 launch
```

### 截图兜底逻辑
```python
# 优先 mumu-cli，失败降级到独立 ADB
img = self._screenshot_mumu()  # mumu-cli 通道
if img is None:
    img = self._screenshot_adb()  # 独立 ADB 通道
```

---

## 六、用户偏好

1. **后台运行优先**：核心目标是模拟器不需要窗口在前台
2. **mumu-cli 优先**：实验证实只有 mumu-cli 输入能让游戏响应
3. **纯 Python 方案**：不引入额外复杂依赖
4. **日志完善**：需要详细的运行日志便于调试
5. **模块化设计**：配置集中、控制器共享、原子操作分层
6. **游戏**：《歧路旅人：大陆的霸者》（包名需确认）

---

## 七、环境信息

| 项目 | 值 |
|------|-----|
| MuMu 模拟器版本 | 12（V4.0.0+） |
| mumu-cli 路径 | `D:\Program Files\Netease\MuMu Player 12\nx_main\mumu-cli.exe` |
| adb 路径 | `D:\Program Files\Netease\MuMu Player 12\nx_main\adb.exe` |
| 模拟器索引 | 0 |
| ADB 端口 | 16384 |
| 图片资源路径 | `H:\pic` |
| 显卡 | NVIDIA GTX 1660 Ti |
| 当前问题 | VT 驱动缺失，模拟器无法启动 |

---

## 八、下一步行动

1. **先修复模拟器**：手动启动 MuMu 模拟器，让系统自动修复 VT 驱动
2. **确认包名**：在模拟器里确认《歧路旅人》的实际包名，替换 `start_game.py` 中的占位符
3. **运行 dailyNew.py**：`python dailyNew.py`，观察 Step 1-3 是否成功
4. **继续开发 Step 4+**：进入主菜单后，依次执行日常任务

---

*文档生成时间：2026-06-17*  
*由 TRAE Agent 整理，供 TRAE IDE 继续开发*
