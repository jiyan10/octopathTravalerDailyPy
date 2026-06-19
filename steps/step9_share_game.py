"""
step9_share_game.py — Step 9: 分享游戏到微信
=====================================================
独立运行：python step9_share_game.py
功能：主菜单→队伍→分享→微信分享→关闭微信→返回主菜单

注意：
  - 微信客户端安装在模拟器内
  - 分享到微信后无需操作，关闭微信即可返回游戏
  - 长按操作使用替代方案：点击数值后再点击对应位置
=====================================================
"""

import logging
import sys
import os
import time
import subprocess

# 添加父目录到路径，以便导入 config 和 core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core import MuMuController
import actions

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


def run_step9(c: MuMuController = None) -> bool:
    """
    分享游戏到微信。

    流程：
      1. 确保在主菜单
      2. 点击队伍按钮
      3. 点击分享按钮
      4. 点击微信分享按钮
      5. 点击数值（替代长按）
      6. 点击分享位置（触发分享到微信）
      7. 等待微信打开后关闭微信
      8. 返回游戏，点击空白处关闭弹窗
      9. 退出回到主菜单

    参数:
        c : MuMuController 实例（None 则自动创建）

    返回:
        True  = 操作成功
        False = 操作失败
    """
    log.info("=" * 50)
    log.info("Step 9: 分享游戏到微信")
    log.info("=" * 50)

    # 创建控制器
    if c is None:
        c = MuMuController()

    # 确保在主菜单
    if not actions.is_in_main_menu(c):
        log.warning("当前不在主菜单，尝试退出弹窗...")
        c.normal_exit()
        if not actions.wait_for_main_menu(c, timeout=10):
            log.warning("⚠️ 无法确认是否在主菜单，继续执行")

    # 1. 点击团队按钮
    log.info("点击团队按钮...")
    if not c.find_and_tap_sure(c._pic("menu", "team.png"), retry=3):
        log.warning("⚠️ 未找到团队按钮，继续执行")
    time.sleep(2.0)

    # 2. 替代长按方案：先点击数值，再点击游戏人物位置
    log.info("使用替代方案：点击数值后点击游戏人物位置...")
    
    # 点击数值（点一次就行）
    log.info("点击数值...")
    if not c.find_and_tap(c._pic("share", "shuzhi.png")):
        log.warning("⚠️ 未找到分享数值，尝试直接点击游戏人物位置")
    
    time.sleep(0.5)
    
    # 点击游戏人物位置（原长按位置）
    log.info("点击游戏人物位置 (860, 340)...")
    c.tap(860, 340)
    time.sleep(2.0)

    # 3. 点击分享按钮
    log.info("点击分享按钮...")
    if not c.find_and_tap_sure(c._pic("share", "share1.png"), retry=3):
        log.warning("⚠️ 未找到分享按钮，继续执行")
    time.sleep(2.0)

    # 4. 点击微信分享按钮
    log.info("点击微信分享按钮...")
    if not c.find_and_tap_sure(c._pic("share", "weixin.png"), retry=3):
        log.warning("⚠️ 未找到微信分享按钮，继续执行")
    time.sleep(5.0)

    # 6. 关闭微信（使用 ADB 命令关闭模拟器内的微信应用）
    log.info("关闭微信...")
    try:
        result = subprocess.run(
            [config.ADB, "-s", config.DEVICE_ID, "shell", "am", "force-stop", "com.tencent.mm"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            log.info("✅ 微信已关闭")
        else:
            log.warning(f"⚠️ 关闭微信失败: {result.stderr}")
            # 尝试通过 MuMu CLI 命令关闭
            log.info("尝试使用 MuMu CLI 命令关闭微信...")
            subprocess.run(
                [config.MUMU_CLI, "action", "stopApp", "--packageName", "com.tencent.mm"],
                capture_output=True,
                text=True
            )
    except Exception as e:
        log.warning(f"⚠️ 关闭微信异常: {e}")

    # 7. 等待返回游戏
    log.info("等待返回游戏...")
    time.sleep(2)

    # 8. 点击空白处关闭可能的弹窗
    log.info("点击空白处关闭弹窗...")
    c.tap_empty(5)
    time.sleep(1.0)

    # 9. 退出回到主菜单
    log.info("退出弹窗回到主菜单...")
    c.normal_exit()

    log.info("✅ Step 9 执行完成")
    return True


if __name__ == "__main__":
    ok = run_step9()
    log.info("=" * 50)
    log.info(f"运行结果: {'✅ 成功' if ok else '❌ 失败'}")
    log.info("=" * 50)
    sys.exit(0 if ok else 1)