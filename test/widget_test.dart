import 'package:flutter_test/flutter_test.dart';
import 'package:interview_flash/models.dart';
import 'package:interview_flash/sr.dart';

void main() {
  test('新题「记得」进入 2 天后复习', () {
    final r = schedule(ProgressRec.newRec('q-1'), kGradeKnown, nowMs: 0);
    expect(r.reps, 1);
    expect(r.intervalDays, 2);
    expect(r.dueAt, 2 * 86400000);
    expect(r.lastGrade, kGradeKnown);
  });

  test('新题「忘了」10 分钟后重现', () {
    final r = schedule(ProgressRec.newRec('q-2'), kGradeForgot, nowMs: 0);
    expect(r.dueAt, 600000);
    expect(r.lapses, 1);
  });

  test('连续「记得」间隔按 ease 拉长且不超过上限', () {
    ProgressRec r = ProgressRec.newRec('q-3');
    r = schedule(r, kGradeKnown, nowMs: 0);
    r = schedule(r, kGradeKnown, nowMs: 0);
    expect(r.intervalDays, 5);
    for (int i = 0; i < 12; i++) {
      r = schedule(r, kGradeKnown, nowMs: 0);
    }
    expect(r.intervalDays, lessThanOrEqualTo(kMaxIntervalDays));
    expect(r.ease, greaterThanOrEqualTo(kMaxEase));
  });

  test('「模糊」后 ease 不变但间隔增长打折', () {
    ProgressRec r = ProgressRec.newRec('q-4');
    r = schedule(r, kGradeKnown, nowMs: 0);
    final easeBefore = r.ease;
    final ivBefore = r.intervalDays;
    r = schedule(r, kGradeFuzzy, nowMs: 0);
    expect(r.ease, easeBefore);
    expect(r.intervalDays, lessThan(ivBefore * 2.9));
  });
}
