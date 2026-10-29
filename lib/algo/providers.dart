/// 全局 Provider 注册。
library;

import 'package:drift/drift.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'models/problem.dart';
import 'services/speech_service.dart';
import 'data/database.dart';
import 'data/content_repository.dart';
import 'data/scheduler.dart';

final dbProvider = Provider<AppDatabase>((ref) => throw UnimplementedError());

/// 首启内容导入完成前挂起算法侧查询（导入完成翻为 true 触发重算）
final algoReadyProvider = StateProvider<bool>((ref) => false);

final contentRepoProvider = Provider<ContentRepository>(
    (ref) => ContentRepository(ref.watch(dbProvider)));

final speechProvider = Provider<SpeechService>((ref) {
  final s = SpeechService();
  ref.onDispose(s.cancel);
  return s;
});

/// 全部题目
final problemsProvider = FutureProvider<Map<int, Problem>>((ref) async {
  if (!ref.watch(algoReadyProvider)) return const {};
  return ref.watch(contentRepoProvider).allProblems();
});

/// 进度表 {problemId: ProgressRow}
final allProgressProvider = FutureProvider<Map<int, ProgressRow>>((ref) async {
  if (!ref.watch(algoReadyProvider)) return const {};
  return {for (final p in await ref.watch(dbProvider).allProgress()) p.problemId: p};
});

/// 专题汇总（按平均热度排序）
final topicsProvider = FutureProvider<List<TopicInfo>>((ref) async {
  final problems = await ref.watch(problemsProvider.future);
  final progress = await ref.watch(allProgressProvider.future);
  final byTopic = <String, List<Problem>>{};
  for (final p in problems.values) {
    byTopic.putIfAbsent(p.topic, () => []).add(p);
  }
  final topics = byTopic.entries.map((e) {
    final done = e.value.where((p) => (progress[p.id]?.status ?? 0) >= 2).length;
    return TopicInfo(
      name: e.key,
      total: e.value.length,
      done: done,
      avgFrequency:
          e.value.map((p) => p.frequency).reduce((a, b) => a + b) / e.value.length,
      problems: e.value,
    );
  }).toList()
    ..sort((a, b) => b.avgFrequency.compareTo(a.avgFrequency));
  return topics;
});

/// 大厂高频汇总
final companiesProvider = FutureProvider<List<CompanyInfo>>((ref) async {
  final problems = await ref.watch(problemsProvider.future);
  final byCompany = <String, List<Problem>>{};
  for (final p in problems.values) {
    for (final c in p.companies) {
      byCompany.putIfAbsent(c, () => []).add(p);
    }
  }
  final list = byCompany.entries
      .map((e) => CompanyInfo(name: e.key, problems: e.value..sort(
          (a, b) => b.frequency.compareTo(a.frequency))))
      .toList()
    ..sort((a, b) => b.problems.length.compareTo(a.problems.length));
  return list;
});

/// 今日待复习（已学且到期）
final dueTodayProvider = FutureProvider<List<Problem>>((ref) async {
  final now = DateTime.now();
  final problems = await ref.watch(problemsProvider.future);
  final progress = await ref.watch(allProgressProvider.future);
  return progress.values
      .where((p) => p.status != 0 && p.dueAt != null && p.dueAt!.isBefore(now))
      .map((p) => problems[p.problemId])
      .whereType<Problem>()
      .toList();
});

/// 全局统计
final statsProvider = FutureProvider<Stats>((ref) async {
  final problems = await ref.watch(problemsProvider.future);
  final progress = await ref.watch(allProgressProvider.future);
  final mastered = progress.values.where((p) => p.status == 2).length;
  final learning = progress.values.where((p) => p.status == 1).length;
  return Stats(
    total: problems.length,
    mastered: mastered,
    learning: learning,
    newCount: problems.length - mastered - learning,
  );
});

/// 提交学习/评测结果并更新调度
final submitProvider = Provider(_Submitter.new);

class _Submitter {
  _Submitter(this._ref);

  final Ref _ref;

  AppDatabase get _db => _ref.watch(dbProvider);

  Future<void> record({
    required int problemId,
    required ReviewKind kind,
    required double score,
    String detail = '',
    List<int> hitKeyPoints = const [],
    bool reschedule = true,
  }) async {
    await _db.addReview(ReviewLogsCompanion.insert(
      problemId: problemId,
      kind: kind.index,
      score: score,
      detail: detail,
      hitKeyPoints: jsonEncodeList(hitKeyPoints),
      createdAt: Value(DateTime.now()),
    ));
    if (reschedule) {
      final prev = await _db.progressOf(problemId);
      await _db
          .saveProgress(Scheduler.next(problemId, prev, score));
    }
    _ref.invalidate(allProgressProvider);
    _ref.invalidate(statsProvider);
    _ref.invalidate(dueTodayProvider);
    _ref.invalidate(topicsProvider);
  }
}

String jsonEncodeList(List<int> xs) =>
    xs.isEmpty ? '' : xs.join(',');

class TopicInfo {
  final String name;
  final int total;
  final int done;
  final double avgFrequency;
  final List<Problem> problems;

  const TopicInfo({
    required this.name,
    required this.total,
    required this.done,
    required this.avgFrequency,
    required this.problems,
  });
}

class Stats {
  final int total;
  final int mastered;
  final int learning;
  final int newCount;

  const Stats({
    required this.total,
    required this.mastered,
    required this.learning,
    required this.newCount,
  });

  double get progress => total == 0 ? 0 : mastered / total;
}

class CompanyInfo {
  final String name;
  final List<Problem> problems;

  const CompanyInfo({required this.name, required this.problems});
}
