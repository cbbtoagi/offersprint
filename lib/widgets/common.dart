/// 通用小组件：徽章、面板、评分按钮等。
library;
import 'package:flutter/material.dart';

import '../models.dart';
import '../sr.dart';

class Panel extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final Color? color;
  final VoidCallback? onTap;

  const Panel({super.key, required this.child, this.padding = const EdgeInsets.all(14), this.color, this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Material(
      color: color ?? cs.surfaceContainerLowest,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}

class DifficultyDots extends StatelessWidget {
  final int level;
  final double size;
  const DifficultyDots(this.level, {super.key, this.size = 5});

  @override
  Widget build(BuildContext context) {
    final colors = [Colors.green, Colors.lightGreen, Colors.amber, Colors.orange, Colors.red];
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(5, (i) {
        return Container(
          width: size,
          height: size,
          margin: const EdgeInsets.only(right: 2),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: i < level ? colors[level - 1] : (colors[level - 1]).withValues(alpha: 0.18),
          ),
        );
      }),
    );
  }
}

class TypeChip extends StatelessWidget {
  final String type;
  const TypeChip(this.type, {super.key});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final color = switch (type) {
      '手撕' => Colors.tealAccent,
      '场景' => Colors.deepPurpleAccent,
      '概念' => Colors.lightBlueAccent,
      _ => cs.primary,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
      decoration: BoxDecoration(border: Border.all(color: color.withValues(alpha: 0.5)), borderRadius: BorderRadius.circular(6)),
      child: Text(type, style: TextStyle(fontSize: 10, color: color)),
    );
  }
}

class FreqBadge extends StatelessWidget {
  final int frequency;
  const FreqBadge(this.frequency, {super.key});

  @override
  Widget build(BuildContext context) {
    if (frequency < 4) return const SizedBox.shrink();
    return Text('🔥$frequency', style: TextStyle(fontSize: 10, color: Colors.orange.shade300));
  }
}

class StatusIcon extends StatelessWidget {
  final int status; // 0 fresh 1 due 2 scheduled 3 mastered
  const StatusIcon(this.status, {super.key});

  @override
  Widget build(BuildContext context) {
    return switch (status) {
      0 => Icon(Icons.circle_outlined, size: 16, color: Colors.grey.shade600),
      1 => const Icon(Icons.schedule, size: 16, color: Colors.orangeAccent),
      2 => Icon(Icons.circle, size: 14, color: Colors.lightBlueAccent.withValues(alpha: 0.8)),
      _ => const Icon(Icons.check_circle, size: 16, color: Colors.greenAccent),
    };
  }
}

class CompanyChips extends StatelessWidget {
  final List<String> companies;
  const CompanyChips(this.companies, {super.key});

  @override
  Widget build(BuildContext context) {
    if (companies.isEmpty) return const SizedBox.shrink();
    return Wrap(
      spacing: 6,
      runSpacing: 4,
      children: companies.map((c) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(c, style: TextStyle(fontSize: 10.5, color: Theme.of(context).colorScheme.primary)),
        );
      }).toList(),
    );
  }
}

class GradeButtons extends StatelessWidget {
  final void Function(int grade) onGrade;
  final bool expanded;
  const GradeButtons({super.key, required this.onGrade, this.expanded = false});

  @override
  Widget build(BuildContext context) {
    Widget btn(String label, String sub, int grade, Color color) {
      return Expanded(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4),
          child: FilledButton.tonal(
            style: FilledButton.styleFrom(
              foregroundColor: color,
              backgroundColor: color.withValues(alpha: 0.14),
              padding: const EdgeInsets.symmetric(vertical: 10),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () => onGrade(grade),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Text(label, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
              Text(sub, style: TextStyle(fontSize: 9, color: color.withValues(alpha: 0.7))),
            ]),
          ),
        ),
      );
    }

    return Row(children: [
      btn('忘了', kGradeForgot == 0 ? '明天再来' : '', kGradeForgot, Colors.redAccent),
      btn('模糊', '缩短间隔', kGradeFuzzy, Colors.orangeAccent),
      btn('记得', '拉长间隔', kGradeKnown, Colors.greenAccent),
    ]);
  }
}

class EmptyView extends StatelessWidget {
  final String text;
  const EmptyView(this.text, {super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.inbox_outlined, size: 42, color: Colors.grey.shade600),
          const SizedBox(height: 10),
          Text(text, textAlign: TextAlign.center, style: TextStyle(color: Colors.grey.shade500, fontSize: 13)),
        ]),
      ),
    );
  }
}

class QuestionTile extends StatelessWidget {
  final Question q;
  final int status;
  final VoidCallback onTap;
  const QuestionTile({super.key, required this.q, required this.status, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 0),
      dense: true,
      onTap: onTap,
      leading: StatusIcon(status),
      title: Text(
        q.question,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(fontSize: 13.5, height: 1.35),
      ),
      subtitle: Padding(
        padding: const EdgeInsets.only(top: 3),
        child: Row(children: [
          TypeChip(q.type),
          const SizedBox(width: 8),
          DifficultyDots(q.difficulty),
          const Spacer(),
          FreqBadge(q.frequency),
        ]),
      ),
    );
  }
}

String formatDate(int ms) {
  final d = DateTime.fromMillisecondsSinceEpoch(ms);
  return '${d.year}/${d.month}/${d.day} ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
}
