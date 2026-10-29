/// 演示流程：自动走完「首页 → 公司 → 学习流 → 默写 → 自述 → 记录」，
/// 由 [DemoRoot] 作为 MaterialApp.home 驱动导航，页面内部的揭示/切换
/// 由各卡片在 DemoMode.enabled 下的自带定时器完成。
library;

import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers.dart';
import '../ui/company/company_screen.dart';
import '../ui/history_screen.dart';
import '../ui/study/study_screen.dart';
import 'demo_mode.dart';

final demoNavigatorKey = GlobalKey<NavigatorState>();

Future<void> _sleep(double seconds) =>
    Future.delayed(Duration(milliseconds: (seconds * 1000).round()));

enum _Phase { intro, app, outro }

/// 演示根：片头 4s → 真实 App 全流程 → 片尾 5s → 退出。
class DemoRoot extends ConsumerStatefulWidget {
  const DemoRoot({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<DemoRoot> createState() => _DemoRootState();
}

class _DemoRootState extends ConsumerState<DemoRoot> {
  _Phase _phase = _Phase.intro;
  bool _timelineStarted = false;

  @override
  void initState() {
    super.initState();
    _start();
  }

  Future<void> _start() async {
    unawaited(DemoMode.log('demo: intro start'));
    await _sleep(4);
    unawaited(DemoMode.log('demo: -> app phase'));
    if (!mounted) return;
    setState(() => _phase = _Phase.app);
    await _sleep(0.3); // 等首页首帧
    if (!mounted) return;
    unawaited(_timeline());
  }

  NavigatorState get _nav => demoNavigatorKey.currentState!;

  Future<void> _timeline() async {
    if (_timelineStarted) return;
    _timelineStarted = true;

    // 等题库与公司数据就绪
    final problems = await ref.read(problemsProvider.future);
    final companies = await ref.read(companiesProvider.future);
    final twoSum = problems[1]!;
    unawaited(DemoMode.log('demo: timeline start problems=${problems.length}'));

    // 公司页
    unawaited(DemoMode.log('demo: push company'));
    await _sleep(0.5);
    _nav.push(MaterialPageRoute(
        builder: (_) => CompanyScreen(info: companies.first)));
    await _sleep(5.5);
    if (_nav.canPop()) _nav.pop();
    await _sleep(0.5);

    // 学习流（4 张卡内部自动推进：读题→思路→代码→出口卡自动衔接
    // 默写评测与思路自述，两者均自行 pop 回出口卡）
    _nav.push(MaterialPageRoute(
        builder: (_) => StudyScreen(problems: [twoSum], startIndex: 0)));
    await _sleep(62.0);
    if (_nav.canPop()) _nav.pop(); // 弹 study 回首页
    await _sleep(0.5);

    // 记录页
    _nav.push(MaterialPageRoute(builder: (_) => const HistoryScreen()));
    await _sleep(5.0);
    if (_nav.canPop()) _nav.pop();
    await _sleep(0.5);

    // 片尾 + 退出
    if (!mounted) return;
    setState(() => _phase = _Phase.outro);
    await _sleep(5);
    unawaited(DemoMode.log('demo: exit'));
    await Future.delayed(const Duration(milliseconds: 300));
    exit(0);  }

  @override
  Widget build(BuildContext context) {
    return switch (_phase) {
      _Phase.intro => const DemoBrandCard(
          title: 'AlgoSprint 算法冲刺',
          subtitle: '完全离线的面试算法特训\n卡片学习 · 默写评测 · 思路自述',
          footer: 'Android · iPhone · macOS',
        ),
      _Phase.app => widget.child,
      _Phase.outro => const DemoBrandCard(
          title: 'AlgoSprint',
          subtitle: '162 题 · 25 专题 · 完全离线 · 三端开源',
          footer: 'GitHub · 搜索 AlgoSprint',
        ),
    };
  }
}
