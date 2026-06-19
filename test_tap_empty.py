"""
临时测试脚本：识别 fivefive.png
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import MuMuController

c = MuMuController()

print("=" * 50)
print("测试：识别 fivefive.png")
print("=" * 50)

# 使用 _pic 方法自动拼接 PIC_ROOT 路径
result = c.find_and_tap(c._pic("menu", "zhiyeta", "fivefive.png"))
if result:
    print(f"✅ 识别成功并点击: {result}")
else:
    print("❌ 未识别到 fivefive.png")

print("=" * 50)
print("测试完成")
