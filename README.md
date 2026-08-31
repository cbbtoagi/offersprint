# 面试速刷 · 大模型算法面试离线 App

面向秋招/实习的**大模型算法岗**离线刷题与模拟面试应用，一套代码覆盖 **macOS / iPhone / Android** 三端（Flutter 构建）。

- **完全离线**：题库内置资源，学习数据存本地 SQLite；录音只保存在本机。
- **内容**：10 大领域题库八股（含追问链与参考实现）、手撕代码、项目实战深挖（带可运行代码）、30 家公司面经库。
- **方法**：SM-2 间隔重复（记得/模糊/忘了三档自评），到期优先、按面试频率补新题；错题本自动沉淀。

## 功能总览

| 模块 | 说明 |
|---|---|
| 首页 | 今日任务（到期/新题/进度）、连续打卡、18 周热力图、领域掌握度 |
| 题库 | 八股题库（搜索 + 状态筛选 + 按域/主题分组）、项目实战、面经库三个页签 |
| 速刷 | SM-2 卡片会话，桌面端支持空格翻面、1/2/3 打分快捷键；手撕特训/随机一题入口 |
| 模拟面试 | 限时作答 + 自动录音 + 语音转写（系统识别）+ 参考答案对照 + 自评战报，薄弱题自动进复习队列；支持**按公司组卷**（对接面经库）与**面试官追问模式**（每题答完追加高频追问） |
| 朗读 | 题目/追问一键 TTS 朗读（系统语音，离线可用），通勤速听 |
| 记笔记 | 随时「记一笔」（文字 + 标签 + 附加语音），可关联题目；笔记列表可回听录音 |
| 我的 | 统计、错题本、学习数据导出/导入（JSON 备份）、重置 |

## 目录结构

```
interview-flash/
├── lib/                  # Dart 应用代码
│   ├── models.dart / repo.dart / db.dart / sr.dart / state.dart / audio.dart
│   └── views/            # 首页 / 题库 / 速刷 / 模拟 / 我的
├── src_raw/              # 内容源（Python 纯数据文件，人可读可改）
├── scripts/convert.py    # 内容校验 + 转换：src_raw/*.py → assets/content/*.json
├── assets/content/       # 构建时打包进 App 的题库 JSON
└── pubspec.yaml
```

## 内容扩展（添加/修改题库）

1. 编辑或新建 `src_raw/<域名>.py`，定义 `QUESTIONS = [dict(...), ...]`（字段：`id/topic/type/difficulty/frequency/companies/years/question/answerMd/keyPoints/followUps/code`；`answerMd` 支持 Markdown + LaTeX + 代码块；手撕题在 `code` 里给完整代码）。
2. 转换并校验：
   ```bash
   python3 scripts/convert.py            # 全量：题库 + projects_* 合并 + exps
   python3 scripts/convert.py pretrain   # 单个域
   ```
3. 重新构建/热重载 App 即生效（内容打包在资源里，改完需重新 build）。

> 注意：项目路径含中文时 `flutter analyze` 会因工具链 LSP bug 崩溃，请用 `dart analyze` 代替。

## 三端运行

先把 Flutter 加入 PATH（本机 SDK 位于 `~/development/flutter`）：

```bash
export PATH="$HOME/development/flutter/bin:$PATH"
```

### macOS
```bash
flutter run -d macos          # 开发运行
flutter build macos           # Release 产物
# 产物：build/macos/Build/Products/Release/面试速刷.app，拖入「应用程序」即可
```

### iPhone（需 Xcode + Apple ID）
```bash
bash scripts/ios_install.sh   # 一键：检查设备/证书 → 构建 → 安装 → 启动
```
- 首次使用需一次性配置（脚本会自动打开 Xcode 并给出指引）：
  1. Xcode → Settings → Accounts → 登录 Apple ID（免费个人账号即可）
  2. 打开 `ios/Runner.xcworkspace` → Runner → Signing & Capabilities → 勾选 Automatically manage signing，Team 选 (Personal Team)
  3. iPhone 上：设置 → 隐私与安全性 → 开发者模式 打开；首次安装后在 通用 → VPN与设备管理 信任开发者证书
- 免费 Apple ID 签名 7 天有效，到期重跑脚本即可；上 TestFlight 需付费开发者账号。
- 首次启动会请求「麦克风」「语音识别」权限（模拟面试录音与转写用）。

### Android
```bash
flutter run -d <android设备>
flutter build apk             # 产物：build/app/outputs/flutter-apk/app-release.apk
```
本机构建环境备忘（已配好）：
- JDK 17（Homebrew openjdk@17，构建前 `export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"`）
- Gradle 仓库走阿里云镜像（settings.gradle.kts / build.gradle.kts 已配置）
- platform-34 为手动安装（/opt/homebrew/share/android-commandlinetools/platforms/android-34）

## 测试

```bash
flutter test                  # SM-2 调度单测 + 内容包完整性测试
dart analyze                  # 静态检查
```

## 数据与隐私

- 学习进度、笔记、录音全部存本机（SQLite + 应用沙盒目录），无任何网络上传。
- 「我的 → 导出学习数据」生成 JSON 备份并走系统分享；「导入」为粘贴备份 JSON 文本（对话框内直接粘贴，自动预填剪贴板内容）。
- 语音转写使用系统识别：iOS/Android 在设置开启「离线听写/端侧识别」后可完全离线；macOS 视系统支持。

## 路线图

- [ ] 视频录制作答（移动端 camera）
- [ ] whisper.cpp 端侧转写（彻底离线的语音识别）
- [x] TTS 朗读题目（通勤速听模式）
- [x] 追问链多轮模拟（面试官式连环追问）
- [x] 按公司/岗位的组卷模式
