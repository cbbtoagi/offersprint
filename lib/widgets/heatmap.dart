/// 打卡热力图（近 N 周）。
library;
import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models.dart';

class HeatmapGrid extends StatelessWidget {
  final Map<String, DailyRec> daily;
  final int weeks;
  const HeatmapGrid({super.key, required this.daily, this.weeks = 18});

  @override
  Widget build(BuildContext context) {
    final today = DateTime.now();
    // 对齐到周一开头
    final endOfWeek = today.add(Duration(days: 7 - (today.weekday)));
    final cells = <(DateTime, int)>[];
    int maxCount = 1;
    for (int w = 0; w < weeks; w++) {
      for (int d = 0; d < 7; d++) {
        final day = endOfWeek.subtract(Duration(days: (weeks - 1 - w) * 7 + (6 - d)));
        if (day.isAfter(today)) {
          cells.add((day, -1));
          continue;
        }
        final key = '${day.year}-${day.month.toString().padLeft(2, '0')}-${day.day.toString().padLeft(2, '0')}';
        final n = daily[key]?.reviewed ?? 0;
        final total = n + (daily[key]?.mockCount ?? 0) * 3;
        maxCount = math.max(maxCount, total);
        cells.add((day, total));
      }
    }
    return LayoutBuilder(builder: (context, cons) {
      final gap = 2.5;
      final cell = ((cons.maxWidth - gap * 7) / weeks).clamp(4.0, 16.0);
      return SizedBox(
        height: cell * 7 + gap * 6,
        child: CustomPaint(
          painter: _HeatPainter(cells: cells, weeks: weeks, cell: cell, gap: gap, maxCount: maxCount),
        ),
      );
    });
  }
}

class _HeatPainter extends CustomPainter {
  final List<(DateTime, int)> cells;
  final int weeks;
  final double cell;
  final double gap;
  final int maxCount;
  _HeatPainter({required this.cells, required this.weeks, required this.cell, required this.gap, required this.maxCount});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint();
    for (int i = 0; i < cells.length; i++) {
      final (day, n) = cells[i];
      final col = i % weeks;
      final row = i ~/ weeks;
      Color c;
      if (n < 0) {
        c = Colors.transparent;
      } else if (n == 0) {
        c = Colors.grey.shade800;
      } else {
        final t = math.min(1.0, 0.25 + 0.75 * (math.log(1 + n) / math.log(1 + maxCount)));
        c = Color.lerp(Colors.green.shade700, Colors.greenAccent, t)!;
      }
      paint.color = c;
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(col * (cell + gap), row * (cell + gap), cell, cell),
          Radius.circular(cell * 0.25),
        ),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _HeatPainter oldDelegate) => oldDelegate.maxCount != maxCount;
}
