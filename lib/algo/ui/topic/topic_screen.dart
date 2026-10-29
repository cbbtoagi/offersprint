import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/database.dart' show ProgressRow;
import '../../models/problem.dart';
import '../../providers.dart';
import '../../theme.dart';
import '../study/study_screen.dart';

/// 专题内题目列表，支持按难度/状态筛选与排序。
class TopicScreen extends ConsumerStatefulWidget {
  const TopicScreen({super.key, required this.info});

  final TopicInfo info;

  @override
  ConsumerState<TopicScreen> createState() => _TopicScreenState();
}

class _TopicScreenState extends ConsumerState<TopicScreen> {
  String _filter = '全部'; // 全部 / 未学 / 学习中 / 已掌握
  bool _byHot = true; // 热度排序 or id 排序

  @override
  Widget build(BuildContext context) {
    final progressAsync = ref.watch(allProgressProvider);
    final problems = [...widget.info.problems];
    if (_byHot) problems.sort((a, b) => b.frequency.compareTo(a.frequency));

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.info.name),
      ),
      body: progressAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (progress) {
          final list = problems.where((p) {
            final st = progress[p.id]?.status ?? 0;
            return switch (_filter) {
              '未学' => st == 0,
              '学习中' => st == 1,
              '已掌握' => st == 2,
              _ => true,
            };
          }).toList();
          return Align(
            alignment: Alignment.topCenter,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 860),
              child: ListView(
                padding: const EdgeInsets.all(12),
                children: [
                  Row(
                    children: [
                      for (final f in const ['全部', '未学', '学习中', '已掌握'])
                        Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: ChoiceChip(
                            label: Text(f),
                            selected: _filter == f,
                            onSelected: (_) => setState(() => _filter = f),
                          ),
                        ),
                      const Spacer(),
                      ActionChip(
                        label: Text(_byHot ? '按热度' : '按编号'),
                        onPressed: () => setState(() => _byHot = !_byHot),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  for (final p in list) _ProblemTile(p: p, progress: progress),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

class _ProblemTile extends ConsumerWidget {
  const _ProblemTile({required this.p, required this.progress});

  final Problem p;
  final Map<int, ProgressRow> progress;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final st = progress[p.id]?.status ?? 0;
    final statusLabel = switch (st) { 2 => '已掌握', 1 => '学习中', _ => '未学' };
    final statusColor = switch (st) { 2 => AppTheme.good, 1 => AppTheme.accent, _ => AppTheme.muted };
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        leading: SizedBox(
          width: 44,
          child: Text('#${p.id}',
              style: const TextStyle(color: AppTheme.muted, fontSize: 12)),
        ),
        title: Text(p.titleCn),
        subtitle: Text('${p.title} · 热度${'★' * p.frequency}'),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(statusLabel, style: TextStyle(color: statusColor, fontSize: 12)),
            const SizedBox(height: 2),
            Text(AppTheme.difficultyCn(p.difficulty),
                style: TextStyle(
                    color: AppTheme.difficultyColors[p.difficulty], fontSize: 12)),
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
