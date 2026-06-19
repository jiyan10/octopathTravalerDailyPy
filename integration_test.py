"""
端到端集成测试 — 验证新 core.py 完整链路
截图(adb) → 找图(opencv) → 点击(mumu-cli) → 截图验证
"""

import sys
import os
import time
import cv2

# 确保能导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core


def test_basic_connection():
    """测试 1: 基本连接"""
    print("\n" + "=" * 60)
    print("  测试 1: 连接测试")
    print("=" * 60)
    ctl = core.MuMuController()
    ok = ctl.connect()
    print(f"  结果: {'✓ 连接成功' if ok else '✗ 连接失败'}")
    return ok, ctl


def test_screenshot(ctl):
    """测试 2: 截图"""
    print("\n" + "=" * 60)
    print("  测试 2: ADB 截图")
    print("=" * 60)
    
    save_path = r"H:\AI\integration_test_screenshot.png"
    img = ctl.capture_screen(save_path=save_path)
    if img is not None:
        h, w = img.shape[:2]
        print(f"  ✓ 截图成功: {w}x{h}")
        print(f"  已保存: {save_path}")
        return True, img
    else:
        print("  ✗ 截图失败")
        return False, None


def test_find_template(ctl, screen):
    """测试 3: 模板匹配"""
    print("\n" + "=" * 60)
    print("  测试 3: 模板匹配（找菜单按钮）")
    print("=" * 60)
    
    # 测试找 menu_new.png（之前确认存在的）
    template = r"H:\pic\menu\menu_new.png"
    if not os.path.exists(template):
        print(f"  ✗ 模板不存在: {template}")
        # 尝试其他模板
        template = r"H:\pic\menu\menu.png"
    
    pos = ctl.find_image(template, threshold=0.8, screen=screen)
    if pos:
        print(f"  ✓ 找到模板! 位置: ({pos[0]}, {pos[1]})")
        return True, pos, template
    else:
        print(f"  ✗ 未找到模板（可能不在当前屏幕上）")
        return False, None, template


def test_tap(ctl, x, y, label="目标"):
    """测试 4: 点击"""
    print(f"\n  点击 {label} @ ({x}, {y})...")
    ok = ctl.tap(x, y, delay=1.0)
    print(f"  结果: {'✓ 成功' if ok else '✗ 失败'}")
    return ok


def test_find_and_tap(ctl):
    """测试 5: 找图+点击一体化"""
    print("\n" + "=" * 60)
    print("  测试 5: find_and_tap 一体化")
    print("=" * 60)
    
    # 尝试找几个常见按钮
    templates_to_try = [
        (r"H:\pic\window\sure.png", "确定按钮"),
        (r"H:\pic\window\close.png", "关闭按钮"),
        (r"H:\pic\window\no.png", "否/取消按钮"),
        (r"H:\pic\menu\menu.png", "菜单按钮"),
        (r"H:\pic\menu\menu_new.png", "新菜单按钮"),
    ]
    
    for tpl_path, name in templates_to_try:
        if not os.path.exists(tpl_path):
            continue
        print(f"\n  尝试找: {name} ...")
        ok = ctl.find_and_tap(tpl_path, threshold=0.75)
        if ok:
            print(f"  ✓ 成功找到并点击: {name}")
            time.sleep(1.5)
            
            # 截图验证变化
            after = ctl.capture_screen(save_path=r"H:\AI\integration_test_after_tap.png")
            if after is not None:
                print(f"  ✓ 点击后截图已保存")
            return True
    
    print("  ⚠ 所有模板均未在当前屏幕上找到（正常——取决于游戏当前界面）")
    return False


def main():
    print("=" * 60)
    print("  Core.py 集成测试 (mumu-cli 版)")
    print("=" * 60)

    results = {}

    # 测试 1: 连接
    ok, ctl = test_basic_connection()
    results['connect'] = ok
    if not ok:
        print("\n连接失败，终止测试")
        return

    # 测试 2: 截图
    ok, screen = test_screenshot(ctl)
    results['screenshot'] = ok
    if not ok:
        print("\n截图失败，跳过后续测试")
        return

    # 测试 3: 模板匹配
    ok, pos, tpl = test_find_template(ctl, screen)
    results['find'] = ok
    found_pos = pos

    # 测试 4: 如果找到了模板就点击它
    if found_pos:
        ok = test_tap(ctl, found_pos[0], found_pos[1], "模板位置")
        results['tap_at_pos'] = ok

    # 测试 4b: 如果没找到模板，点屏幕中心测试
    else:
        ok = test_tap(ctl, 960, 540, "屏幕中心")
        results['tap_center'] = ok

    # 测试 5: find_and_tap 一体化
    ok = test_find_and_tap(ctl)
    results['find_and_tap'] = ok

    # 总结
    print("\n" + "=" * 60)
    print("  测试总结")
    print("=" * 60)
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n  总计: {passed}/{total} 通过")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
