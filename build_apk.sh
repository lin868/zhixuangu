#!/bin/bash
# 在 WSL (Ubuntu) 中执行，打包安卓 APK
set -e

echo "===== 1. 安装系统依赖 ====="
sudo apt-get update
sudo apt-get install -y python3-pip build-essential libssl-dev libffi-dev \
  libncurses5 libncurses5-dev ccache autoconf automake libtool pkg-config \
  cmake zip unzip git openjdk-17-jdk

echo "===== 2. 安装 flet ====="
pip3 install --user --upgrade flet
export PATH="$HOME/.local/bin:$PATH"

echo "===== 3. 打包 APK（首次约 30-60 分钟，需下载 Android 工具链）====="
cd "/mnt/c/Users/linjq/AppData/Roaming/TRAE SOLO CN/ModularData/ai-agent/work-mode-projects/6a8120602f4f8695a9d6460c/zhixuangu_android"
flet build apk

echo "===== 4. 完成，APK 位置 ====="
ls -la build/apk/
echo ""
echo "APK 已生成，路径："
realpath build/apk/*.apk
