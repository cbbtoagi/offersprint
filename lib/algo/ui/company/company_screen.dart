import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/database.dart' show ProgressRow;
import '../../models/problem.dart';
import '../../providers.dart';
import '../../theme.dart';
import '../study/study_screen.dart';

/// 按公司冲刺：某大厂的常考题列表（按热度排序）。
class CompanyScreen extends ConsumerWidget {
  const CompanyScreen({super.key, required this.info});

  final CompanyInfo info;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final progressAsync = ref.watch(allProgressProvider);
    return Scaffold(
      appBar: AppBar(title: Text('${info.name} · 常考 ${info.problems.length} 题')),
      body: progressAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (progress) => Align(
          alignment: Alignment.topCenter,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 860),
            child: ListView(
              padding: const EdgeInsets.all(12),
              children: [
                for (final p in info.problems)
                  _CompanyProblemTile(p: p, progress: progress),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _CompanyProblemTile extends ConsumerWidget {
  const _CompanyProblemTile({required this.p, required this.progress});

  final Problem p;
  final Map<int, ProgressRow> progress;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final st = progress[p.id]?.status ?? 0;
    final statusLabel = switch (st) { 2 => '已掌握', 1 => '学习中', _ => '未学' };
    final statusColor = switch (st) {
      2 => AppTheme.good,
      1 => AppTheme.accent,
      _ => AppTheme.muted,
    };
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        leading: SizedBox(
          width: 44,
          child: Text('#${p.id}',
              style: const TextStyle(color: AppTheme.muted, fontSize: 12)),
        ),
        title: Text(p.titleCn),
        subtitle: Text('${p.title} · ${p.topic} · 热度${'★' * p.frequency}'),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(statusLabel,
                style: TextStyle(color: statusColor, fontSize: 12)),
            const SizedBox(height: 2),
            Text(AppTheme.difficultyCn(p.difficulty),
                style: TextStyle(
                    color: AppTheme.difficultyColors[p.difficulty],
                    fontSize: 12)),
          ],
        ),
        onTap: () async {
          await Navigator.of(context).push(MaterialPageRoute(
            builder: (_) => StudyScreen(problems: [p], startIndex: 0),
          ));
          if (context.mounted) ref.invalidate(allProgressProvider);
        },
      ),
    );
  }
}
