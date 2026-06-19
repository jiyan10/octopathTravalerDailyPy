"""
emulator.py — MuMu 模拟器启动/状态检测
=====================================================
封装 mumu-cli 的模拟器生命周期管理：
  - 启动模拟器 (launch)
  - 检测模拟器是否已启动
  - 等待模拟器完全就绪 (is_android_started=true)
=====================================================

依赖：mumu-cli.exe（MuMu12 安装自带）

已知坑（2026-06-16）：
  - `mumu-cli control --vmindex=0 launch` 会被解析成 help ❌
  - 必须用 `mumu-cli control --vmindex 0 launch`（空格分隔）✅
  - 或 `mumu-cli control -v 0 launch`（短参数）✅
  - 但 `mumu-cli info --vmindex=0` 用等号却可以 ⚠️（子命令参数风格不一致）
  - subprocess 的 returncode 在 Windows 下常返回 0xFFFFFFFF/-1，
    必须看 stdout 的 "errcode": 0 来判断成功
=====================================================
"""

import subprocess
import time
import json
import logging

import config

log = logging.getLogger(__name__)


def _run_mumu(args: list, timeout: int = 10) -> subprocess.CompletedProcess:
    """
    调用 mumu-cli 子命令，捕获 stdout/stderr。
    args: 不含 mumu-cli.exe 路径本身的参数列表

    注意：mumu-cli 在 Windows 下 subprocess 的 returncode 经常返回
    0xFFFFFFFF (4294967295) 或 0xFFFFFFC5 (4294967275) 这种 wrap-around 值，
    但 stdout 里包含的 "errcode": 0 才是真正的执行结果。
    调用方应优先看 stdout 的 errcode。
    """
    cmd = [config.MUMU_CLI, *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )


def _is_mumu_success(r: subprocess.CompletedProcess) -> bool:
    """
    判断 mumu-cli 命令是否成功（容忍 Windows 下诡异的 returncode）：
      - returncode == 0 ✅
      - returncode 为负数 wrap-around 但 stdout 含 "errcode": 0 ✅
      - 其他情况 ❌
    """
    if r.returncode == 0:
        return True
    # Windows 下的诡异 returncode（如 0xFFFFFFFF=-1）但 JSON 输出成功
    if '"errcode": 0' in r.stdout or '"errcode":0' in r.stdout:
        return True
    return False


def get_emulator_info(vm_index: int = None) -> dict:
    """
    获取模拟器信息，返回 dict（解析 mumu-cli info 的 JSON 输出）。
    失败返回空 dict。

    注意：info 命令即使成功也常返回 rc=4294967275 这种 wrap-around 值，
    但 stdout 是完整 JSON。优先看 stdout 是否有可解析的 JSON。
    """
    vm = vm_index if vm_index is not None else config.VM_INDEX
    try:
        # info 子命令用空格形式（--vmindex 0），不能是 --vmindex=0
        r = _run_mumu(["info", "--vmindex", str(vm)], timeout=5)
        # info 走 --vmindex=0 形式（control 子命令才是空格）
        # 即使 rc 非 0，只要 stdout 能解析成有效 JSON 就视为成功
        if not r.stdout.strip():
            log.warning(f"mumu-cli info 无输出: rc={r.returncode}, err={r.stderr.strip()[:200]}")
            return {}
        return json.loads(r.stdout)
    except subprocess.TimeoutExpired:
        log.warning("mumu-cli info 超时")
        return {}
    except json.JSONDecodeError as e:
        log.warning(f"mumu-cli info JSON 解析失败: {e}, raw={r.stdout[:200]}")
        return {}
    except Exception as e:
        log.warning(f"mumu-cli info 异常: {e}")
        return {}


def is_android_started(vm_index: int = None) -> bool:
    """
    判断模拟器 Android 系统是否已完全启动。
    通过 mumu-cli info 返回的 is_android_started 字段判断。
    """
    info = get_emulator_info(vm_index)
    return info.get("is_android_started", False) is True


def is_player_running(vm_index: int = None) -> bool:
    """
    判断模拟器进程是否在运行（比 is_android_started 更宽松，
    即便 Android 没启动完也算"在跑"）。
    """
    info = get_emulator_info(vm_index)
    # 常见字段：is_player_running / is_started / running
    for key in ("is_player_running", "is_started", "running"):
        if key in info:
            return bool(info[key])
    # 兜底：如果没拿到这些字段，用 is_android_started 推断
    return info.get("is_android_started", False) is True


def launch_emulator(vm_index: int = None, wait_ready: bool = True,
                     timeout: float = 90.0) -> bool:
    """
    启动 MuMu 模拟器（后台启动，不弹窗阻塞）。

    参数:
        vm_index   : 模拟器实例编号（默认取 config.VM_INDEX）
        wait_ready : 是否等待 Android 系统完全启动
        timeout    : wait_ready 时的最长等待时间（秒）

    返回:
        True  = 启动并就绪
        False = 启动失败 / 超时

    实现:
        1. mumu-cli control --vmindex N launch   （发送启动命令）
        2. 轮询 mumu-cli info 检查 is_android_started
    """
    vm = vm_index if vm_index is not None else config.VM_INDEX

    # 先检查是否已经在跑
    if is_android_started(vm):
        log.info(f"模拟器 vmindex={vm} 已启动，跳过 launch")
        return True

    log.info(f"启动 MuMu 模拟器: vmindex={vm}")
    try:
        r = _run_mumu(
            ["control", "--vmindex", str(vm), "launch"],
            timeout=15,
        )
        if not _is_mumu_success(r):
            log.error(f"launch 命令失败: rc={r.returncode}, err={r.stderr.strip()[:200]}, "
                      f"out={r.stdout.strip()[:200]}")
            return False
        log.info(f"launch 命令已发送: {r.stdout.strip()[:200]}")
    except subprocess.TimeoutExpired:
        log.error("launch 命令超时")
        return False
    except Exception as e:
        log.error(f"launch 异常: {e}")
        return False

    if not wait_ready:
        return True

    # 轮询等待 Android 启动完成
    log.info(f"等待 Android 启动完成（最长 {timeout:.0f}s）...")
    start = time.time()
    check_interval = 2.0
    while time.time() - start < timeout:
        if is_android_started(vm):
            elapsed = time.time() - start
            log.info(f"模拟器就绪，耗时 {elapsed:.1f}s")
            return True
        time.sleep(check_interval)

    log.error(f"等待 Android 启动超时（{timeout:.0f}s）")
    return False


def shutdown_emulator(vm_index: int = None, timeout: float = 30.0) -> bool:
    """
    关闭 MuMu 模拟器（优雅关闭，会触发 Android 关机流程）。
    """
    vm = vm_index if vm_index is not None else config.VM_INDEX
    log.info(f"关闭 MuMu 模拟器: vmindex={vm}")
    try:
        r = _run_mumu(
            ["control", "--vmindex", str(vm), "shutdown"],
            timeout=15,
        )
        if not _is_mumu_success(r):
            log.error(f"shutdown 失败: rc={r.returncode}, err={r.stderr.strip()[:200]}")
            return False
    except Exception as e:
        log.error(f"shutdown 异常: {e}")
        return False

    # 等待进程退出
    start = time.time()
    while time.time() - start < timeout:
        if not is_player_running(vm):
            log.info("模拟器已关闭")
            return True
        time.sleep(1.0)

    log.warning(f"等待关闭超时（{timeout:.0f}s），可能未完全关闭")
    return False


if __name__ == "__main__":
    # 单独运行：检测 + 启动 + 打印最终状态
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    log.info("=" * 50)
    log.info("MuMu 模拟器启动工具")
    log.info("=" * 50)

    info = get_emulator_info()
    log.info(f"当前模拟器信息: {info}")

    if is_android_started():
        log.info("✅ 模拟器已就绪，无需启动")
    else:
        log.info("模拟器未就绪，开始启动...")
        ok = launch_emulator(wait_ready=True, timeout=90)
        if ok:
            log.info("✅ 启动成功")
        else:
            log.error("❌ 启动失败")
