/// SM-2 间隔重复调度（简化版）。
/// grade: 0=忘了 1=模糊 2=记得
library;
import 'dart:math' as math;

import 'models.dart';

const int kGradeForgot = 0;
const int kGradeFuzzy = 1;
const int kGradeKnown = 2;

const double kMinEase = 1.3;
const double kMaxEase = 2.9;
const double kMaxIntervalDays = 240;

/// 返回调度后的新记录。
ProgressRec schedule(ProgressRec prev, int grade, {int? nowMs}) {
  final now = nowMs ?? DateTime.now().millisecondsSinceEpoch;
  final dayMs = 86400000;
  final tenMinMs = 600000;

  double ease = prev.ease;
  int reps = prev.reps;
  int lapses = prev.lapses;
  double interval = prev.intervalDays;
  int dueAt;

  if (grade == kGradeForgot) {
    lapses += 1;
    ease = math.max(kMinEase, ease - 0.2);
    // 掉回短期重学：10 分钟后再来
    interval = interval > 1 ? math.max(0.3, interval * 0.25) : 0.007;
    dueAt = now + (interval < 0.02 ? tenMinMs : (interval * dayMs).round());
  } else {
    reps += 1;
    if (grade == kGradeKnown) {
      ease = math.min(kMaxEase, ease + 0.1);
    } else {
      // 模糊：ease 不变，但间隔增长打折
    }
    if (reps == 1) {
      interval = grade == kGradeKnown ? 2 : 1;
    } else if (reps == 2) {
      interval = grade == kGradeKnown ? 5 : 3;
    } else {
      final growth = grade == kGradeKnown ? ease : ease * 0.55;
      interval = math.min(kMaxIntervalDays, math.max(1, interval * growth));
    }
    dueAt = now + (interval * dayMs).round();
  }

  return prev.copyWith(
    ease: ease,
    intervalDays: interval,
    dueAt: dueAt,
    reps: reps,
    lapses: lapses,
    lastGrade: grade,
    lastAt: now,
  );
}

String intervalLabel(double days) {
  if (days < 0.02) return '10分钟';
  if (days < 1) return '${(days * 24).round()}小时';
  if (days < 30) return '${days.round()}天';
  return '${(days / 30).toStringAsFixed(1)}个月';
}
