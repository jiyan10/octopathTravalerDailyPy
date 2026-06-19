"""
临时测试脚本：长按空白三次
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import MuMuController

c = MuMuController()

print("=" * 50)
print("长按空白三次")
print("=" * 50)

c.tap_empty_long(3)
# c.tap_empty(3)

print("=" * 50)
print("测试完成")
