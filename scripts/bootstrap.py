#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mpt-text-to-video 引导脚本（跨项目 / 跨环境复用）
一次性把 MoneyPrinterTurbo 仓库、Python 隔离环境、最小依赖、Pexels Key 准备好。
幂等：已存在则不重复克隆/安装。

用法：
  # WorkBuddy 环境（默认用 managed venv）
  python bootstrap.py --repo <仓库目录> --key <PEXELS_KEY>

  # 任意环境（自动降级到 <repo>/.venv）
  python bootstrap.py --repo ./MoneyPrinterTurbo
  python bootstrap.py --repo ./MoneyPrinterTurbo --venv ./myenv --key <PEXELS_KEY>

依赖：标准库（os/sys/shutil/subprocess/argparse/urllib），无需额外安装。
"""
import os
import sys
import shutil
import subprocess
import argparse


def _fix_encoding():
    """强制 stdout/stderr 用 UTF-8，避免 Windows(cp1252)/Linux(C locale) 下中文 print 抛 UnicodeEncodeError。"""
    for s in (sys.stdout, sys.stderr):
        enc = getattr(s, "encoding", "") or ""
        if enc.lower() not in ("utf-8", "utf8"):
            try:
                s.reconfigure(encoding="utf-8")
            except Exception:
                pass


_fix_encoding()

HOME = os.path.expanduser("~")
# WorkBuddy 的 managed venv 路径；非 WorkBuddy 环境通常不存在，会自动降级
MANAGED_VENV = os.path.join(HOME, ".workbuddy", "binaries", "python", "envs", "default")
REPO_URL = "https://github.com/harry0703/MoneyPrinterTurbo.git"
DEPS = ["openai==2.24.0", "edge_tts==7.2.7", "moviepy==2.2.1", "toml", "pydantic"]
MIRROR = "https://mirrors.aliyun.com/pypi/simple/"


def resolve_venv(repo: str, venv_arg: str) -> str:
    """决定 venv 位置：显式 > managed(若存在) > 仓库本地 .venv"""
    if venv_arg:
        return os.path.abspath(venv_arg)
    if os.path.isfile(os.path.join(MANAGED_VENV, "Scripts", "python.exe") if os.name == "nt"
                      else os.path.join(MANAGED_VENV, "bin", "python")):
        return MANAGED_VENV
    return os.path.join(repo, ".venv")


def venv_bins(venv: str):
    if os.name == "nt":
        return os.path.join(venv, "Scripts", "python.exe"), os.path.join(venv, "Scripts", "pip.exe")
    return os.path.join(venv, "bin", "python"), os.path.join(venv, "bin", "pip")


def run(cmd, cwd=None):
    print(">>", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        sys.exit(f"[ERR] 命令失败: {' '.join(cmd)}")


def ensure_repo(repo: str):
    if os.path.isdir(os.path.join(repo, ".git")) or os.path.isfile(os.path.join(repo, "cli.py")):
        print(f"[OK] 复用已有仓库: {repo}")
        return
    os.makedirs(os.path.dirname(repo) or ".", exist_ok=True)
    print(f"[+] 克隆 MoneyPrinterTurbo 到 {repo}")
    run(["git", "clone", "--depth", "1", REPO_URL, repo])


def ensure_venv(venv: str):
    py, _ = venv_bins(venv)
    if os.path.isfile(py):
        print(f"[OK] 复用已有 venv: {venv}")
        return
    print(f"[+] 创建 venv: {venv}")
    run([sys.executable, "-m", "venv", venv])


def ensure_deps(pip: str):
    print("[+] 安装最小依赖（阿里云镜像）")
    run([pip, "install", "-i", MIRROR, *DEPS])


def write_config(repo: str, key: str):
    cfg = os.path.join(repo, "config.toml")
    if not os.path.isfile(cfg):
        src = os.path.join(repo, "config.example.toml")
        if os.path.isfile(src):
            shutil.copy(src, cfg)
    if not os.path.isfile(cfg):
        print("[WARN] 未找到 config.toml / config.example.toml，请手动配置")
        return
    with open(cfg, "r", encoding="utf-8") as f:
        text = f.read()
    if key:
        if 'pexels_api_keys = []' in text:
            text = text.replace('pexels_api_keys = []', f'pexels_api_keys = ["{key}"]')
        else:
            text += f'\npexels_api_keys = ["{key}"]\n'
    text = text.replace("open_task_folder_on_completion = true",
                        "open_task_folder_on_completion = false")
    with open(cfg, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[OK] 已写入 config.toml (key={'已填' if key else '未填'})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.join(os.getcwd(), "MoneyPrinterTurbo"))
    ap.add_argument("--venv", default="", help="自定义 venv 路径；留空则优先 managed venv，否则用 <repo>/.venv")
    ap.add_argument("--key", default=os.environ.get("MPT_PEXELS_KEY", ""))
    args = ap.parse_args()

    venv = resolve_venv(args.repo, args.venv)
    py, pip = venv_bins(venv)

    ensure_repo(args.repo)
    ensure_venv(venv)
    ensure_deps(pip)
    write_config(args.repo, args.key)
    print("\n[完成] 环境就绪。下一步：写 script.txt 和 video-terms，运行 cli.py --video-script ...")
    print(f"  PY={py}")
    print(f"  REPO={os.path.abspath(args.repo)}")


if __name__ == "__main__":
    main()
