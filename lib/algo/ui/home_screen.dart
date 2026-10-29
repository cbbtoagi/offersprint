import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/problem.dart';
import '../providers.dart';
import '../theme.dart';
import 'company/company_screen.dart';
import 'study/study_screen.dart';
import 'topic/topic_screen.dart';

/// 首页：统计总览 + 今日待复习 + 专题列表。
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stats = ref.watch(statsProvider);
    final due = ref.watch(dueTodayProvider);
    final topics = ref.watch(topicsProvider);
    final companies = ref.watch(companiesProvider);

    return SafeArea(
      child: Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 860),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const _Header(),
              const SizedBox(height: 16),
              stats.when(
                loading: () => const SizedBox(),
                error: (e, _) => Text('加载失败: $e'),
                data: (s) => _StatsRow(stats: s),
              ),
              const SizedBox(height: 16),
              due.when(
                loading: () => const SizedBox(),
                error: (e, _) => Text('加载失败: $e'),
                data: (list) => list.isEmpty
                    ? const SizedBox()
                    : _DueCard(due: list),
              ),
              const SizedBox(height: 8),
              Text('按公司冲刺', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              companies.when(
                loading: () => const SizedBox(),
                error: (e, _) => Text('加载失败: $e'),
                data: (list) => SizedBox(
                  height: 40,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: [
                      for (final c in list)
                        Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: ActionChip(
                            label: Text('${c.name} ${c.problems.length}'),
                            onPressed: () => Navigator.of(context).push(
                              MaterialPageRoute(
                                  builder: (_) => CompanyScreen(info: c)),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text('专题', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              topics.when(
                loading: () => const Center(child: Padding(
                  padding: EdgeInsets.all(32),
                  child: CircularProgressIndicator())),
                error: (e, _) => Text('加载失败: $e'),
                data: (list) => Column(
                  children: [for (final t in list) _TopicTile(info: t)],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: AppTheme.accent.withValues(alpha: .15),
            borderRadius: BorderRadius.circular(12),
          ),
          child: const Icon(Icons.flash_on, color: AppTheme.accent),
        ),
        const SizedBox(width: 12),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('算法冲刺', style: Theme.of(context).textTheme.headlineSmall),
            Text('LeetCode 热门 · 完全离线',
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: AppTheme.muted)),
          ],
        ),
      ],
    );
  }
}

class _StatsRow extends StatelessWidget {
  const _StatsRow({required this.stats});

  final Stats stats;

  @override
  Widget build(BuildContext context) {
    Widget cell(String label, String value, Color color) => Expanded(
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 14),
            decoration: BoxDecoration(
              color: const Color(0xFF171A21),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFF252A35)),
            ),
            child: Column(
              children: [
                Text(value,
                    style: TextStyle(
                        fontSize: 22, fontWeight: FontWeight.w700, color: color)),
                const SizedBox(height: 4),
                Text(label,
                    style: const TextStyle(fontSize: 12, color: AppTheme.muted)),
              ],
            ),
          ),
        );
    return Row(
      children: [
        cell('总题数', '${stats.total}', Colors.white),
        const SizedBox(width: 8),
        cell('已掌握', '${stats.mastered}', AppTheme.good),
        const SizedBox(width: 8),
        cell('学习中', '${stats.learning}', AppTheme.accent),
        const SizedBox(width: 8),
        cell('待复习', '${stats.newCount}', AppTheme.muted),
      ],
    );
  }
}

class _DueCard extends ConsumerWidget {
  const _DueCard({required this.due});

  final List<Problem> due;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.alarm, color: AppTheme.accent, size: 20),
                const SizedBox(width: 8),
                Text('今日待复习 · ${due.length} 题',
                    style: const TextStyle(fontWeight: FontWeight.w600)),
                const Spacer(),
                TextButton(
                  onPressed: due.isEmpty ? null : () async {
                    final first = await Navigator.of(context).push<bool>(
                      MaterialPageRoute(
                        builder: (_) => StudyScreen(problems: due, startIndex: 0),
                      ),
                    );
                    if (first == true) ref.invalidate(dueTodayProvider);
                  },
                  child: const Text('开始复习'),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                for (final p in due.take(8))
                  ActionChip(
                    label: Text('${p.id}. ${p.titleCn}'),
                    onPressed: () => _open(context, ref, p),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _open(BuildContext context, WidgetRef ref, Problem p) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => StudyScreen(problems: [p], startIndex: 0)),
    );
    ref.invalidate(dueTodayProvider);
  }
}

class _TopicTile extends ConsumerWidget {
  const _TopicTile({required this.info});

  final TopicInfo info;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ratio = info.total == 0 ? 0.0 : info.done / info.total;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        title: Text(info.name, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 8),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: ratio,
              minHeight: 5,
              backgroundColor: const Color(0xFF252A35),
              color: AppTheme.accent,
            ),
          ),
        ),
        trailing: Text('${info.done}/${info.total}',
            style: const TextStyle(color: AppTheme.muted)),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => TopicScreen(info: info)),
        ),
      ),
    );
  }
}
