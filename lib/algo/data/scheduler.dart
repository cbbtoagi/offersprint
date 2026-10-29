/// SM-2 简化版间隔复习调度。
/// 评测得分 (0-100) -> 质量 q (0-5)，据此更新 EF / 间隔 / 到期时间。
library;

import 'package:drift/drift.dart';

import 'database.dart';

class Scheduler {
  static const masteredScore = 85.0; // 达到即倾向标记掌握

  /// 得分转 SM-2 质量
  static double _quality(double score) => (score / 100.0) * 5.0;

  /// 根据本次得分生成下一轮进度行。
  static ProgressRowsCompanion next(int problemId, ProgressRow? prev,
      double score,
      {DateTime? now}) {
    now ??= DateTime.now();
    final q = _quality(score);
    var ef = prev?.easiness ?? 2.5;
    var interval = prev?.intervalDays ?? 0;
    var reps = prev?.reps ?? 0;
    var lapses = prev?.lapses ?? 0;

    if (q < 3) {
      // 未通过：间隔重置，明天再见
      reps = 0;
      interval = 1;
      lapses += 1;
    } else {
      ef = (ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
          .clamp(1.3, 3.0)
          .toDouble();
      reps += 1;
      if (reps == 1) {
        interval = 1;
      } else if (reps == 2) {
        interval = 3;
      } else {
        interval = (interval * ef).round().clamp(4, 180);
      }
    }

    final status = q >= 3 && score >= masteredScore && reps >= 2 ? 2 : 1;
    return ProgressRowsCompanion.insert(
      problemId: Value(problemId),
      status: status,
      easiness: ef,
      intervalDays: interval,
      reps: reps,
      lapses: lapses,
      dueAt: Value(now.add(Duration(days: interval))),
      lastStudiedAt: Value(now),
    );
  }
}
