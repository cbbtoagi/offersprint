#!/bin/bash
# iPhone 真机一键安装（免费 Apple ID 个人签名）
# 用法: bash scripts/ios_install.sh
set -e
cd "$(dirname "$0")/.."

export PATH="$HOME/development/flutter/bin:$PATH"
# 规避部分网络下 GitHub SPM 克隆失败
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=http.version GIT_CONFIG_VALUE_0=HTTP/1.1

BUNDLE_ID="dev.jesse.interviewFlash"

echo "== 1/4 检查 iPhone 连接 =="
DEV_LINE=$(xcrun devicectl list devices 2>/dev/null | grep -iE "iphone" | head -1)
if [ -z "$DEV_LINE" ]; then
  echo "❌ 未检测到 iPhone。"
  echo "   请用数据线连接 iPhone，手机上点「信任此电脑」，并在 设置→隐私与安全性→开发者模式 打开开发者模式，然后重跑本脚本。"
  exit 1
fi
UDID=$(echo "$DEV_LINE" | awk '{print $NF}')
DEV_NAME=$(echo "$DEV_LINE" | sed -E 's/^[^A-Za-z]*([^(]+)\(.*/\1/' | xargs)
echo "✓ 找到设备: $DEV_NAME ($UDID)"

echo "== 2/4 检查开发证书 =="
IDENTITY=$(security find-identity -v -p codesigning 2>/dev/null | grep "Apple Development" | head -1)
if [ -z "$IDENTITY" ]; then
  echo "⚠️ 本机还没有开发证书（免费 Apple ID 即可）。"
  echo "   正在打开 Xcode，请做一次性配置："
  echo "   1. Xcode 菜单 Settings → Accounts → 左下 + → 登录你的 Apple ID"
  echo "   2. 左侧选中 Runner → Signing & Capabilities → 勾选 Automatically manage signing → Team 选择你的 (Personal Team)"
  echo "   3. 首次安装后需在 iPhone：设置→通用→VPN与设备管理→信任该开发者证书"
  open ios/Runner.xcworkspace
  exit 1
fi
echo "✓ 证书: $(echo "$IDENTITY" | sed 's/^[0-9]* //')"

echo "== 3/4 构建 iOS Release（含全部离线内容）=="
flutter build ios --release

echo "== 4/4 安装到 iPhone 并启动 =="
xcrun devicectl device install app --device "$UDID" build/ios/iphoneos/Runner.app
xcrun devicectl device process launch --device "$UDID" "$BUNDLE_ID" && echo "🎉 已在 iPhone 上启动「面试速刷」"
