/// 首页：今日任务、快捷入口、算法冲刺概览、领域掌握度。
library;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:provider/provider.dart';

import '../algo/providers.dart' as algo;
import '../state.dart';
import '../widgets/common.dart';
import '../widgets/heatmap.dart';
import 'me_view.dart';

class HomeView extends ConsumerWidget {
  const HomeView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = context.watch<AppState>();
    final ui = context.watch<UiState>();
    final today = state.todayRec();

    if (!state.ready) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.loadError != null) {
      return Center(child: Text('初始化失败：${state.loadError}'));
    }
    final repo = state.repo;
    if (repo == null || repo.totalQuestions == 0) {
      final diag = StringBuffer('尚未找到可用的题库内容。\n');
      diag.write('发现内容包 ${repo?.assetCount ?? 0} 个');
      if (repo != null && repo.issues.isNotEmpty) {
        diag.write('，其中异常：\n${repo.issues.take(3).join('\n')}');
      }
      diag.write('\n可运行 python3 scripts/convert.py 重新生成。');
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Text(diag.toString(),
              textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey, height: 1.6, fontSize: 12)),
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      children: [
        Row(children: [
          Text('冲刺Offer', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w700)),
          const Spacer(),
          Text('🔥 连续 ${state.streak} 天', style: TextStyle(color: Colors.orange.shade300, fontSize: 13)),
          const SizedBox(width: 10),
          IconButton(
            tooltip: '我的',
            icon: const Icon(Icons.account_circle_outlined, size: 26),
            onPressed: () => Navigator.of(context)
                .push(MaterialPageRoute(builder: (_) => const MeView())),
          ),
        ]),
        const SizedBox(height: 12),
        // 今日任务
        Panel(
          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.10),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              const Text('今日任务', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
              const Spacer(),
              Text('今日已刷 ${today.reviewed} 题', style: TextStyle(fontSize: 12, color: Colors.grey.shade400)),
            ]),
            const SizedBox(height: 10),
            Row(children: [
              _taskNum('${state.dueCount}', '到期复习'),
              const SizedBox(width: 24),
              _taskNum('${repo.totalQuestions - state.totalLearned}', '未学新题'),
              const SizedBox(width: 24),
              _taskNum('${state.totalLearned}/${repo.totalQuestions}', '总进度'),
            ]),
            const SizedBox(height: 14),
            Row(children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: () => ui.goto(3),
                  icon: const Icon(Icons.flash_on, size: 18),
                  label: const Text('开始速刷'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: FilledButton.tonal(
                  onPressed: () => ui.goto(4),
                  child: const Text('模拟面试'),
                ),
              ),
            ]),
          ]),
        ),
        const SizedBox(height: 14),
        // 算法冲刺（LeetCode 热题）概览
        _AlgoCard(onEnter: () => ui.goto(1)),
        const SizedBox(height: 14),
        // 快捷入口
        Row(children: [
          _quick(context, '⌨️', '手撕特训', () {
            ui.gotoFlash(domains: const {'handcoded'});
          }),
          _quick(context, '📚', '项目实战', () => ui.goto(2, lib: 1)),
          _quick(context, '🏢', '面经库', () => ui.goto(2, lib: 2)),
          _quick(context, '🎲', '随机一题', () {
            final q = state.randomQuestion();
            ui.gotoFlash(presetIds: [q.id]);
          }),
        ]),
        const SizedBox(height: 18),
        // 打卡热力图
        Panel(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('打卡热力 · 近 18 周', style: TextStyle(fontSize: 13, color: Colors.grey.shade400)),
            const SizedBox(height: 10),
            HeatmapGrid(daily: state.daily),
          ]),
        ),
        const SizedBox(height: 18),
        // 领域掌握度
        Text('领域掌握度', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.grey.shade200)),
        const SizedBox(height: 8),
        ...repo.packs.map((p) {
          final meta = p.$1;
          final qs = p.$2;
          final learned = qs.where((q) => !(state.progress[q.id]?.isNew ?? true)).length;
          final m = state.masteryOf(meta.id);
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Panel(
              onTap: () => ui.goto(2),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              child: Row(children: [
                Text(meta.emoji, style: const TextStyle(fontSize: 18)),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      Text(meta.name, style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w500)),
                      const Spacer(),
                      Text('$learned/${qs.length}', style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
                    ]),
                    const SizedBox(height: 6),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(3),
                      child: LinearProgressIndicator(
                        value: m,
                        minHeight: 5,
                        backgroundColor: Colors.grey.shade800,
                        valueColor: AlwaysStoppedAnimation(
                          m > 0.6 ? Colors.greenAccent : (m > 0.25 ? Colors.lightBlueAccent : Colors.deepOrangeAccent),
                        ),
                      ),
                    ),
                  ]),
                ),
              ]),
            ),
          );
        }),
      ],
    );
  }

  Widget _taskNum(String n, String label) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(n, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700, color: Colors.white)),
      const SizedBox(height: 2),
      Text(label, style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
    ]);
  }

  Widget _quick(BuildContext context, String emoji, String label, VoidCallback onTap) {
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 3),
        child: Panel(
          onTap: onTap,
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Column(children: [
            Text(emoji, style: const TextStyle(fontSize: 20)),
            const SizedBox(height: 6),
            Text(label, style: const TextStyle(fontSize: 12)),
          ]),
        ),
      ),
    );
  }
}

/// 算法冲刺（LeetCode 热题 150）概览卡。
class _AlgoCard extends ConsumerWidget {
  final VoidCallback onEnter;
  const _AlgoCard({required this.onEnter});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stats = ref.watch(algo.statsProvider);
    final due = ref.watch(algo.dueTodayProvider);
    return Panel(
      onTap: onEnter,
      color: Colors.deepPurpleAccent.withValues(alpha: 0.10),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Text('⌨️ 算法冲刺', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
          const SizedBox(width: 6),
          Text('LeetCode 热题', style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
          const Spacer(),
          const Icon(Icons.chevron_right, size: 18, color: Colors.grey),
        ]),
        const SizedBox(height: 10),
        stats.when(
          loading: () => const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2)),
          ),
          error: (e, _) => Text('算法题库加载失败', style: TextStyle(fontSize: 12, color: Colors.grey.shade500)),
          data: (s) => Row(children: [
            _num('${s.mastered}', '已掌握', Colors.greenAccent),
            const SizedBox(width: 20),
            _num('${s.learning}', '学习中', Colors.lightBlueAccent),
            const SizedBox(width: 20),
            _num('${s.newCount}', '未学', Colors.grey.shade400),
            const Spacer(),
          ]),
        ),
        const SizedBox(height: 8),
        due.maybeWhen(
          data: (list) => list.isEmpty
              ? const SizedBox.shrink()
              : Text('📌 今日待复习 ${list.length} 题', style: TextStyle(fontSize: 12.5, color: Colors.orangeAccent.shade200)),
          orElse: () => const SizedBox.shrink(),
        ),
      ]),
    );
  }

  Widget _num(String n, String label, Color c) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(n, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: c)),
      Text(label, style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
    ]);
  }
}
