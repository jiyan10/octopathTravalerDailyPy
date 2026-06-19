"""
mumu-cli 官方输入注入测试
使用 mumu-cli.exe control tool cmd 发送触摸事件
这是 MuMu12 官方输入管线，游戏100%响应
支持后台运行，无需窗口在前台
"""

import subprocess
import time
import sys
import os

# ============================================================
# 配置
# ============================================================
MUMU_CLI = r"D:\Program Files\Netease\MuMu Player 12\nx_main\mumu-cli.exe"
ADB = r"D:\Program Files\Netease\MuMu Player 12\nx_device\12.0\shell\adb.exe"
DEVICE_SERIAL = "127.0.0.1:16384"
VM_INDEX = 0  # MuMu 实例编号

# 截图保存目录
SCREENSHOT_DIR = r"H:\AI"


def mumu_tap(x, y, vm_index=VM_INDEX):
    """
    使用 mumu-cli 官方接口点击指定坐标
    坐标系: ADB 截图坐标系 (1920x1080)
    返回: (成功与否, 返回信息)
    """
    cmd = [
        MUMU_CLI,
        "control",
        f"--vmindex", str(vm_index),
        "tool",
        "cmd",
        "--cmd", f"input tap {int(x)} {int(y)}"
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8"
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        # 检查返回值中是否包含 errcode: 0
        if '"errcode": 0' in stdout or result.returncode == 0:
            return True, stdout
        else:
            return False, f"stdout={stdout}, stderr={stderr}"
    except subprocess.TimeoutExpired:
        return False, "命令超时"
    except Exception as e:
        return False, str(e)


def mumu_swipe(x1, y1, x2, y2, duration_ms=300, vm_index=VM_INDEX):
    """
    使用 mumu-cli 官方接口滑动
    duration_ms: 滑动时长(毫秒)，设为 x1==x2 且 y1==y2 时即为长按
    """
    cmd = [
        MUMU_CLI,
        "control",
        f"--vmindex", str(vm_index),
        "tool",
        "cmd",
        "--cmd", f"input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration_ms)}"
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8"
        )
        stdout = result.stdout.strip()
        return '"errcode": 0' in stdout or result.returncode == 0, stdout
    except Exception as e:
        return False, str(e)


def mumu_long_press(x, y, duration_ms=900, vm_index=VM_INDEX):
    """长按（滑动到自身位置）"""
    return mumu_swipe(x, y, x, y, duration_ms, vm_index)


def adb_screenshot(save_path=None):
    """截取 ADB 屏幕"""
    cmd = [ADB, "-s", DEVICE_SERIAL, "shell", "screencap", "-p"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=15
        )
        if result.returncode != 0:
            print(f"  ADB 截图失败: {result.stderr.decode('utf-8', errors='replace')}")
            return False
        
        if save_path:
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(result.stdout)
        return True
    except Exception as e:
        print(f"  ADB 截图异常: {e}")
        return False


def main():
    print("=" * 60)
    print("  MuMu-CLI 官方输入注入测试")
    print("=" * 60)
    print(f"  mumu-cli: {MUMU_CLI}")
    print(f"  设备: {DEVICE_SERIAL}, vmindex={VM_INDEX}")

    # ===== 测试 1: 点击测试 =====
    print("\n" + "=" * 60)
    print("  测试 1: 点击测试 — 关闭「要关闭应用吗？」对话框")
    print("=" * 60)

    # 先截图看当前状态
    before_path = os.path.join(SCREENSHOT_DIR, "mumucli_test1_before.png")
    print("\n[1] 截取当前屏幕...")
    if adb_screenshot(before_path):
        print(f"  ✓ 已保存: {before_path}")
    else:
        print("  ✗ 截图失败!")

    # 「否」按钮坐标 (从之前的 ADB 截图测量)
    # 对话框在屏幕中央，「否」按钮在左侧
    tap_x, tap_y = 718, 590

    print(f"\n[2] 发送点击 ({tap_x}, {tap_y})...")
    ok, info = mumu_tap(tap_x, tap_y)
    print(f"  结果: {'✓ 成功' if ok else '✗ 失败'}")
    print(f"  信息: {info}")

    # 等待动画
    time.sleep(1.5)

    # 点击后截图
    after_path = os.path.join(SCREENSHOT_DIR, "mumucli_test1_after.png")
    print(f"\n[3] 点击后截图...")
    if adb_screenshot(after_path):
        print(f"  ✓ 已保存: {after_path}")
    
    # ===== 测试 2: 连续多次点击测试稳定性 =====
    print("\n" + "=" * 60)
    print("  测试 2: 稳定性测试 — 连续 5 次点击屏幕中心")
    print("=" * 60)

    center_x, center_y = 960, 540  # 屏幕中心
    success_count = 0
    
    for i in range(5):
        print(f"\n  点击 #{i+1}/5 @ ({center_x}, {center_x})...", end=" ", flush=True)
        ok, _ = mumu_tap(center_x, center_y)
        if ok:
            print("✓")
            success_count += 1
        else:
            print("✗")
        time.sleep(0.5)  # 间隔 500ms
    
    print(f"\n  稳定性结果: {success_count}/5 成功")

    # ===== 测试 3: 滑动测试 =====
    print("\n" + "=" * 60)
    print("  测试 3: 滑动测试")
    print("=" * 60)

    print("\n  执行向上滑动 (从下往上)...")
    # 从屏幕下方中间滑到上方中间（模拟向上滚动）
    ok, info = mumu_swipe(960, 800, 960, 300, 500)
    print(f"  结果: {'✓ 成功' if ok else '✗ 失败'}  |  {info}")

    time.sleep(1.5)

    after_swipe_path = os.path.join(SCREENSHOT_DIR, "mumucli_test3_after_swipe.png")
    print(f"\n  滑动后截图...")
    if adb_screenshot(after_swipe_path):
        print(f"  ✓ 已保存: {after_swipe_path}")

    # ===== 总结 =====
    print("\n" + "=" * 60)
    print("  测试完成!")
    print("=" * 60)
    print(f"  截图文件:")
    print(f"    - {before_path}")
    print(f"    - {after_path}")
    print(f"    - {after_swipe_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
