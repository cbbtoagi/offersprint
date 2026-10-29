import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/database.dart' show ReviewLog;
import '../models/problem.dart';
import '../providers.dart';
import '../theme.dart';
import 'study/study_screen.dart';

/// 学习记录：全部评测落盘记录 + 快捷回看。
class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final db = ref.watch(dbProvider);
    final problems = ref.watch(problemsProvider);
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 860),
        child: FutureBuilder(
          future: db.recentReviews(),
          builder: (context, snap) {
            if (snap.hasError) return Center(child: Text('${snap.error}'));
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final logs = snap.data!;
            if (logs.isEmpty) {
              return const Center(
                child: Text('暂无记录 — 从「题库」开始你的第一张卡',
                    style: TextStyle(color: AppTheme.muted)),
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: logs.length,
              itemBuilder: (context, i) {
                final log = logs[i];
                return problems.maybeWhen(
                  data: (map) => _LogTile(log: log, problem: map[log.problemId]),
                  orElse: () => _LogTile(log: log, problem: null),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

class _LogTile extends StatelessWidget {
  const _LogTile({required this.log, required this.problem});

  final ReviewLog log;
  final Problem? problem;

  @override
  Widget build(BuildContext context) {
    final kind = ReviewKind.values[log.kind];
    final color = log.score >= 85
        ? AppTheme.good
        : log.score >= 60
            ? AppTheme.accent
            : AppTheme.bad;
    final dt = log.createdAt?.toLocal() ?? DateTime.now();
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        title: Text(problem == null
            ? '题目 #${log.problemId}'
            : '#${problem!.id} ${problem!.titleCn}'),
        subtitle: Text(
            '${kind.label} · ${dt.month}/${dt.day} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}\n'
            '${log.detail.isEmpty ? '' : log.detail}'),
        isThreeLine: log.detail.isNotEmpty,
        trailing: Text(log.score.toStringAsFixed(0),
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: color)),
        onTap: problem == null
            ? null
            : () => Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) =>
                      StudyScreen(problems: [problem!], startIndex: 0),
                )),
      ),
    );
  }
}
