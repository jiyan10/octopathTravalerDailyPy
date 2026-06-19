"""
scrcpy v4.0 控制协议 - 通过 scrcpy 发送触摸事件到 MuMu12
使用正常窗口模式（极小化），通过控制端口发送事件
"""

import subprocess
import socket
import struct
import time
import sys
import os

# === 配置 ===
SCRCPY_PATH = r"C:\Users\ji\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.0\scrcpy.exe"
ADB_SERIAL = "127.0.0.1:16384"
CONTROL_PORT = 27183

# 消息类型
MSG_TYPE_INJECT_TOUCH_EVENT = 2
ACTION_DOWN = 0
ACTION_UP = 1
POINTER_ID_MOUSE = 0xFFFFFFFFFFFFFFFF


def build_touch_msg(action, pointer_id, x, y,
                    screen_w=1920, screen_h=1080,
                    pressure_fp=65535,
                    action_button=0, buttons=0):
    """构建 32 字节 TOUCH_EVENT 消息 (大端序)"""
    msg = bytearray(32)
    msg[0] = MSG_TYPE_INJECT_TOUCH_EVENT & 0xFF   # type
    msg[1] = action & 0xFF                         # action
    struct.pack_into('>Q', msg, 2, pointer_id)     # pointer_id
    struct.pack_into('>i', msg, 10, int(x))        # x
    struct.pack_into('>i', msg, 14, int(y))        # y
    struct.pack_into('>H', msg, 18, screen_w)      # width
    struct.pack_into('>H', msg, 20, screen_h)      # height
    struct.pack_into('>H', msg, 22, pressure_fp)   # pressure
    struct.pack_into('>I', msg, 24, action_button)
    struct.pack_into('>I', msg, 28, buttons)
    return bytes(msg)


def send_tap(sock, x, y):
    """发送一次完整点击 (DOWN + UP)"""
    down = build_touch_msg(ACTION_DOWN, POINTER_ID_MOUSE, x, y)
    sock.sendall(down)
    time.sleep(0.08)

    up = build_touch_msg(ACTION_UP, POINTER_ID_MOUSE, x, y)
    sock.sendall(up)

    print(f"  ✓ tap ({x}, {y})")


def main():
    print("=" * 60)
    print("  scrcpy v4.0 触摸控制测试")
    print("=" * 60)

    # 启动 scrcpy - 使用极小窗口但保持控制功能
    cmd = [
        SCRCPY_PATH,
        "-s", ADB_SERIAL,
        "--no-audio",
        "--window-width", "160",     # 极小窗口
        "--window-height", "90",
        "--window-x", "3000",       # 放在屏幕外/角落
        "--window-y", "0",
        "-b", "1M",                 # 低码率
        "--max-fps", "5",
    ]
    print(f"\n[1] 启动 scrcpy...")
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )

    # 等待控制端口就绪
    print("[2] 等待控制端口...")
    sock = None
    for i in range(200):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect(('127.0.0.1', CONTROL_PORT))
            print(f"    ✓ 已连接 port={CONTROL_PORT} (尝试 {i+1})")
            break
        except (ConnectionRefusedError, OSError):
            if sock:
                sock.close()
                sock = None
            time.sleep(0.1)

            if proc.poll() is not None:
                out = proc.stdout.read().decode('utf-8', errors='replace')
                print(f"    ✗ scrcpy 已退出!")
                print(f"    输出: {out[:1000]}")
                return False
    else:
        print(f"    ✗ 超时")
        proc.terminate()
        return False

    try:
        # 点击「否」按钮
        target_x, target_y = 718, 590
        print(f"\n[3] 点击「否」 at ({target_x}, {target_y})...")
        send_tap(sock, target_x, target_y)
        
        time.sleep(2)
        print("\n[4] 完成！检查游戏画面是否变化")

    except Exception as e:
        print(f"\n  错误: {e}")
        import traceback; traceback.print_exc()
    finally:
        if sock:
            try: sock.close()
            except: pass
    
    print("\n[5] 关闭 scrcpy...")
    proc.terminate()
    try: proc.wait(timeout=5)
    except: proc.kill()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
