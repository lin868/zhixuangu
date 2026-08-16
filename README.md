# 智选股 安卓版

由桌面程序 `智选股_v2.0.exe` 移植而来。砍掉了依赖 Windows 桌面客户端的通达信/同花顺联动功能，保留了核心的选股算法与数据获取，用 Flet 重做界面，可打包成安卓 APK。

## 文件结构

| 文件 | 作用 |
|------|------|
| `core.py` | 数据获取 + 四维选股算法（纯标准库，零第三方依赖） |
| `main.py` | Flet 安卓界面 |
| `requirements.txt` | 依赖（仅 flet） |
| `pyproject.toml` | Flet 打包配置（含安卓 INTERNET 权限） |
| `.github/workflows/build-apk.yml` | GitHub Actions 云端打包流程 |

## 算法说明（已实测验证）

- 数据源：东方财富 `push2.eastmoney.com`（备用 push2delay 自动切换）
- 全市场快照：分页拉取沪深 A 股约 5500 只
- 四维评分（满分 100）：资金 40 + 量比 20 + 换手 20 + 涨幅 20
- 大盘环境判断：按上证涨跌幅分偏空/偏弱/震荡/偏多/偏强五档，给仓位建议
- 默认参数：最高价 35、涨幅 3%~20%、量比≥1、换手 3%~25%、排除科创板/北交所、展示前 30

## 打包成 APK

打包必须在 Linux 环境下完成（Flet/buildozer 限制）。两种方式任选其一。

### 方式一：GitHub Actions 云端打包（推荐，零本机环境）

1. 在 GitHub 新建一个仓库
2. 把 `zhixuangu_android` 目录里的**所有文件**（含 `.github` 文件夹）上传到仓库根目录
3. 上传后 GitHub Actions 会自动触发构建（约 20~40 分钟，首次需下载 Android 工具链）
4. 构建完成后，在仓库 Actions 页 → 对应运行 → Artifacts 下载 `zhixuangu-apk`
5. 把下载的 `.apk` 传到手机安装

> 若要手动触发：Actions 页 → Build Android APK → Run workflow

### 方式二：本机 WSL 打包

前提：已安装 WSL（Windows 11 可在管理员 PowerShell 执行 `wsl --install`，装完重启）。

```bash
# 在 WSL 里
sudo apt update && sudo apt install -y python3-pip build-essential libssl-dev libffi-dev
pip3 install flet
cd /mnt/c/Users/你的用户名/AppData/Roaming/TRAE\ SOLO\ CN/ModularData/ai-agent/work-mode-projects/6a8120602f4f8695a9d6460c/zhixuangu_android
flet build apk
# 生成的 APK 在 build/apk/ 目录
```

## 安装到手机

1. 把 `.apk` 文件传到安卓手机
2. 手机设置里允许「安装未知来源应用」
3. 点击安装

## 与原桌面版的差异

| 功能 | 原桌面版 | 安卓版 |
|------|---------|--------|
| 选股算法 | 保留 | 保留 |
| 东方财富数据 | 保留 | 保留 |
| 大盘环境判断 | 保留 | 保留 |
| Tkinter 界面 | — | 改为 Flet |
| 联动通达信 | 有 | 移除（安卓无桌面客户端） |
| 联动同花顺 | 有 | 移除（同上） |
| CSV 导出 | 有 | 暂未移植 |
