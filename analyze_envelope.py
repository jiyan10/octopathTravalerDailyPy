"""
MuMu 模拟器后台自动化 - 信封领取流程分析与录制
通过 ADB 后台操作 + 截图分析，记录每个步骤的特征变化
"""

import subprocess
import time
import cv2
import numpy as np
import os
from datetime import datetime

# ============ 配置 ============
ADB_PATH = r"D:\Program Files\Netease\MuMu Player 12\nx_device\12.0\shell\adb.exe"
DEVICE_ID = "127.0.0.1:16384"
SCREENSHOT_DIR = r"H:\AI\07_代码脚本\mumu-auto-bg\screenshots"
PIC_BASE = r"H:\pic"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def adb_screenshot(filename=None):
    """后台截图，返回 numpy 数组和保存路径"""
    if filename is None:
        filename = f"step_{int(time.time()*1000)}.png"
    path = os.path.join(SCREENSHOT_DIR, filename)
    result = subprocess.run(
        [ADB_PATH, "-s", DEVICE_ID, "exec-out", "screencap", "-p"],
        capture_output=True
    )
    with open(path, 'wb') as f:
        f.write(result.stdout)
    img_array = np.frombuffer(result.stdout, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return img, path

def adb_tap(x, y):
    """ADB 点击（相对坐标转绝对坐标，假设分辨率 720x1280）"""
    subprocess.run(
        [ADB_PATH, "-s", DEVICE_ID, "shell", "input", "tap", str(int(x)), str(int(y))],
        capture_output=True
    )

def find_template(screen_img, template_path, threshold=0.75):
    """多尺度模板匹配"""
    if not os.path.exists(template_path):
        return None, 0
    tmpl = cv2.imread(template_path)
    if tmpl is None:
        return None, 0
    best_val, best_pos = 0, None
    for scale in [0.9, 0.95, 1.0, 1.05, 1.10]:
        new_w = int(tmpl.shape[1] * scale)
        new_h = int(tmpl.shape[0] * scale)
        resized = cv2.resize(tmpl, (new_w, new_h))
        res = cv2.matchTemplate(screen_img, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best_val:
            best_val = max_val
            best_pos = (max_loc[0] + new_w // 2, max_loc[1] + new_h // 2)
    if best_val >= threshold:
        return best_pos, best_val
    return None, best_val

def find_all_templates(screen_img, templates_dict, threshold=0.7):
    """批量查找多个模板"""
    results = {}
    for name, path in templates_dict.items():
        pos, score = find_template(screen_img, path, threshold)
        results[name] = {"pos": pos, "score": round(score, 3)}
    return results

def mark_and_save(img, positions, filename, title=""):
    """在图片上标记找到的位置并保存"""
    marked = img.copy()
    h, w = img.shape[:2]
    scale = min(680 / w, 900 / h)  # 缩放以便查看
    if scale < 1:
        marked = cv2.resize(marked, (int(w * scale), int(h * scale)))
    
    for label, pos in positions.items():
        if pos:
            sx, sy = int(pos[0] * scale), int(pos[1] * scale)
            # 红色圆圈标记
            cv2.circle(marked, (sx, sy), 15, (0, 0, 255), 2)
            # 绿色文字标签
            cv2.putText(marked, label, (sx + 20, sy), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    out_path = os.path.join(SCREENSHOT_DIR, filename)
    cv2.imwrite(out_path, marked)
    print(f"  [已保存标注图] {filename} ({len(positions)} 个目标)")
    return out_path

# ============ 常用模板定义 ============
TEMPLATES = {
    "信封入口": os.path.join(PIC_BASE, "menu", "envelop.png"),
    "搜索/菜单": os.path.join(PIC_BASE, "menu", "search.png"),
    "一键领取": os.path.join(PIC_BASE, "menu", "envelope", "get.png"),
    "确认按钮": os.path.join(PIC_BASE, "window", "sure.png"),
}

def analyze_screen(step_name=""):
    """截图 + 分析 + 标注"""
    print(f"\n{'='*50}")
    print(f"📸 步骤: {step_name}")
    print(f"{'='*50}")
    
    img, path = adb_screenshot(f"raw_{step_name.replace(' ','_')}.png")
    h, w = img.shape[:2]
    print(f"  屏幕分辨率: {w}x{h}")
    
    results = find_all_templates(img, TEMPLATES)
    for name, info in results.items():
        status = f"✅ 找到 ({info['pos']})" if info['pos'] else f"❌ 未匹配 (最高分:{info['score']})"
        print(f"  [{name}] {status}")
    
    # 只标记找到的
    found = {k: v["pos"] for k, v in results.items() if v["pos"]}
    if found:
        mark_path = mark_and_save(img, found, f"marked_{step_name.replace(' ','_')}.png", step_name)
        print(f"  标注图: {mark_path}")
    
    return img, results


if __name__ == "__main__":
    print("=" * 60)
    print("  MuMu 信封领取 - 流程录制与分析")
    print("=" * 60)
    
    # 第一步：看初始状态
    print("\n>>> 开始分析...")
