"""
pyautogui 点击测试 - 修正版
解决之前的问题：
1. 窗口标题: "MuMu安卓设备"（不是 "MuMi"）
2. DPI 感知: 设为 Per-Monitor 模式
3. 窗口前台: 先激活再点击
4. 坐标计算: 正确处理窗口边框
"""

import ctypes
import ctypes.wintypes
import time
import sys
import os

# 设置 DPI 感知为 Per-Monitor v2
try:
    # Windows 10 1703+
    shcore = ctypes.windll.shcore
    PROCESS_PER_MONITOR_DPI_AWARE = 2
    shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
except Exception as e:
    print(f"  DPI 设置失败 (非致命): {e}")

import pyautogui

pyautogui.PAUSE = 0.2
pyautogui.FAILSAFE = False


def main():
    print("=" * 60)
    print("  pyautogui 点击测试 - 修正版")
    print("=" * 60)

    user32 = ctypes.windll.user32
    
    # 1. 查找 MuMu 窗口（正确的标题！）
    print("\n[1] 查找 MuMu 窗口...")
    hwnd = user32.FindWindowW(None, 'MuMu安卓设备')
    if not hwnd:
        print("  ✗ 未找到窗口!")
        
        # 列出所有窗口帮助调试
        EnumWindows = user32.EnumWindows
        GetWindowTextW = user32.GetWindowTextW
        IsWindowVisible = user32.IsWindowVisible
        
        def cb(h, _):
            buf = ctypes.create_unicode_buffer(256)
            GetWindowTextW(h, buf, 256)
            t = buf.value
            if IsWindowVisible(h) and t:
                r = ctypes.wintypes.RECT()
                user32.GetWindowRect(h, ctypes.byref(r))
                w, hh = r.right - r.left, r.bottom - r.top
                if 'mumu' in t.lower() or 'mu' in t.lower():
                    print(f"    匹配: HWND={h} [{w}x{hh}] '{t}'")
            return True
        
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        EnumWindows(WNDENUMPROC(cb), 0)
        return False

    # 2. 获取窗口信息
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    
    client_rect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(client_rect))
    
    dpi = user32.GetDpiForWindow(hwnd)
    scale = dpi / 96.0
    
    win_w = rect.right - rect.left
    win_h = rect.bottom - rect.top
    client_w = client_rect.right - client_rect.left
    client_h = client_rect.bottom - client_rect.top
    border_x = (win_w - client_w) // 2  # 左右边框总宽的一半（近似）
    border_y = win_h - client_h         # 标题栏+边框高度
    
    print(f"  窗口位置: ({rect.left}, {rect.top}) ~ ({rect.right}, {rect.bottom})")
    print(f"  窗口大小: {win_w}x{win_h}, 客户区: {client_w}x{client_h}")
    print(f"  DPI: {dpi}, 缩放: {scale:.2f}x")
    print(f"  边框估算: 水平={border_x}px, 垂直={border_y}px")

    # 3. 激活窗口到前台
    print("\n[2] 激活窗口...")
    
    # 最小化后恢复，强制前台
    user32.ShowWindow(hwnd, 9)   # SW_RESTORE
    time.sleep(0.2)
    
    # 使用 SetForegroundWindow 的技巧：先模拟一个按键输入
    import threading
    def bring_to_front():
        time.sleep(0.1)
        result = user32.SetForegroundWindow(hwnd)
        print(f"  SetForegroundWindow 结果: {result}")
    
    t = threading.Thread(target=bring_to_front)
    t.start()
    t.join(timeout=2)
    
    # 额外保险：用 AttachThreadInput 强制前台
    try:
        kernel32 = ctypes.windll.kernel32
        fg_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
        my_thread = kernel32.GetCurrentThreadId()
        if fg_thread != my_thread:
            user32.AttachThreadInput(my_thread, fg_thread, True)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.05)
            user32.AttachThreadInput(my_thread, fg_thread, False)
    except Exception as e:
        print(f"  AttachThreadInput 跳过: {e}")
    
    time.sleep(0.3)

    fg_now = user32.GetForegroundWindow()
    print(f"  前台状态: {'✓ 是' if fg_now == hwnd else '✗ 否'} (fg={fg_now})")

    # 4. 计算按钮位置并点击
    # adb 截图 1920x1080 → 对应客户区 1536x864
    # 「否」按钮在 adb 截图上约 (718, 590)
    # 缩放到客户区: 
    adb_x, adb_y = 718, 590
    scale_x = client_w / 1920.0   # 客户区宽/ADB宽
    scale_y = client_h / 1080.0   # 客户区高/ADB高
    
    btn_client_x = int(adb_x * scale_x)
    btn_client_y = int(adb_y * scale_y)
    
    btn_screen_x = rect.left + border_x + btn_client_x
    btn_screen_y = rect.top + border_y + btn_client_y
    
    print(f"\n[3] 计算坐标:")
    print(f"  ADB坐标: ({adb_x}, {adb_y}) in 1920x1080")
    print(f"  客户区偏移: ({btn_client_x}, {btn_client_y}) in {client_w}x{client_h}")
    print(f"  屏幕坐标: ({btn_screen_x}, {btn_screen_y})")
    print(f"  缩放因子: x={scale_x:.4f}, y={scale_y:.4f}")

    # 5. 执行点击
    print(f"\n[4] 点击「否」按钮...")
    
    # 移动到目标位置
    pyautogui.moveTo(btn_screen_x, btn_screen_y, duration=0.5)
    time.sleep(0.3)
    
    # 截图确认鼠标位置
    screenshot_before = pyautogui.screenshot()
    screenshot_before.save(r'H:\AI\pyauto_before_click.png')
    print("  已保存点击前截图: pyauto_before_click.png")
    
    # 执行点击
    pyautogui.click(btn_screen_x, btn_screen_y)
    print(f"  ✓ 已 click({btn_screen_x}, {btn_screen_y})")
    
    time.sleep(1.5)
    
    # 截图查看结果
    screenshot_after = pyautogui.screenshot()
    screenshot_after.save(r'H:\AI\pyauto_after_click.png')
    print("  已保存点击后截图: pyauto_after_click.png")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
