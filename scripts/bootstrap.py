#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mpt-text-to-video 引导脚本（跨项目复用）
一次性把 MoneyPrinterTurbo 仓库、Python 隔离环境、最小依赖、Pexels Key 准备好。
幂等：已存在则不重复克隆/安装。

用法（用 managed python 运行本脚本）：
  python bootstrap.py --repo <仓库目录> --key <PEXELS_KEY>
  python bootstrap.py --repo <仓库目录>            # 仅准备环境，Key 走 config 或环境变量

依赖：标准库（os/sys/shutil/subprocess/urllib），无需额外安装。
"""
import os
import sys
import shutil
import subprocess
import argparse

HOME = os.path.expanduser("~")
DEFAULT_VENV = os.path.join(HOME, ".workbuddy", "binaries", "python", "envs", "default")
REPO_URL = "https://github.com/FujiwaraChoki/MoneyPrinterTurbo.git"
PY = os.path.join(DEFAULT_VENV, "Scripts", "python.exe") if os.name == "nt" \
    else os.path.join(DEFAULT_VENV, "bin", "python")
PIP = os.path.join(DEFAULT_VENV, "Scripts", "pip.exe") if os.name == "nt" \
    else os.path.join(DEFAULT_VENV, "bin", "pip")
DEPS = ["openai==2.24.0", "edge_tts==7.2.7", "moviepy==2.2.1", "toml", "pydantic"]
MIRROR = "https://mirrors.aliyun.com/pypi/simple/"


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


def ensure_venv():
    if os.path.isfile(PY):
        print(f"[OK] 复用已有 venv: {DEFAULT_VENV}")
        return
    print(f"[+] 创建 venv: {DEFAULT_VENV}")
    run([sys.executable, "-m", "venv", DEFAULT_VENV])


def ensure_deps():
    print(f"[+] 安装最小依赖（阿里云镜像）")
    run([PIP, "install", "-i", MIRROR, *DEPS])


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
    # 填 Pexels Key
    if key:
        import re
        if 'pexels_api_keys = []' in text:
            text = text.replace('pexels_api_keys = []', f'pexels_api_keys = ["{key}"]')
        else:
            text += f'\npexels_api_keys = ["{key}"]\n'
    # 关闭完成弹窗（无头环境）
    text = text.replace("open_task_folder_on_completion = true",
                        "open_task_folder_on_completion = false")
    with open(cfg, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[OK] 已写入 config.toml (key={'已填' if key else '未填'})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.join(os.getcwd(), "MoneyPrinterTurbo"))
    ap.add_argument("--key", default=os.environ.get("MPT_PEXELS_KEY", ""))
    args = ap.parse_args()

    ensure_repo(args.repo)
    ensure_venv()
    ensure_deps()
    write_config(args.repo, args.key)
    print("\n[完成] 环境就绪。下一步：写 script.txt 和 video-terms，运行 cli.py --video-script ...")
    print(f"  PY={PY}")
    print(f"  REPO={args.repo}")


if __name__ == "__main__":
    main()
