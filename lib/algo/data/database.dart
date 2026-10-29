/// drift 数据库：内容镜像 + 学习进度 + 评测记录落盘。
library;

import 'dart:convert';

import 'package:drift/drift.dart';

part 'database.g.dart';

/// 题目内容（首启从 JSON 资产导入）
class ProblemRows extends Table {
  IntColumn get id => integer()();
  TextColumn get title => text()();
  TextColumn get titleCn => text()();
  TextColumn get topic => text()();
  TextColumn get difficulty => text()();
  IntColumn get frequency => integer()();
  TextColumn get question => text()();
  TextColumn get hints => text()(); // JSON 数组
  TextColumn get keyPoints => text()(); // JSON 数组
  TextColumn get structureTags => text()(); // JSON 数组
  TextColumn get approaches => text()(); // JSON 数组
  TextColumn get code => text()();
  TextColumn get acmCode => text().nullable()(); // ACM 模式完整程序（Python）
  TextColumn get codeCpp => text().nullable()(); // C++ 核心代码
  TextColumn get acmCodeCpp => text().nullable()(); // ACM 模式完整程序（C++）
  TextColumn get codeJava => text().nullable()(); // Java 核心代码
  TextColumn get codeJs => text().nullable()(); // JavaScript 核心代码
  TextColumn get codeGo => text().nullable()(); // Go 核心代码
  TextColumn get samples => text().nullable()(); // JSON 数组
  TextColumn get companies => text().nullable()(); // JSON 数组
  TextColumn get templates => text()(); // JSON 数组

  @override
  Set<Column> get primaryKey => {id};
}

/// 内容版本号，内容更新时增量重导
class Meta extends Table {
  TextColumn get key => text()();
  TextColumn get value => text()();

  @override
  Set<Column> get primaryKey => {key};
}

/// 每题学习进度（SM-2 简化版调度参数）
class ProgressRows extends Table {
  IntColumn get problemId => integer()();
  IntColumn get status => integer()(); // 0 新题 1 学习中 2 已掌握
  RealColumn get easiness => real()(); // EF
  IntColumn get intervalDays => integer()();
  IntColumn get reps => integer()();
  IntColumn get lapses => integer()();
  DateTimeColumn get dueAt => dateTime().nullable()();
  DateTimeColumn get lastStudiedAt => dateTime().nullable()();

  @override
  Set<Column> get primaryKey => {problemId};
}

/// 评测/学习记录（落盘，可回看）
class ReviewLogs extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get problemId => integer()();
  IntColumn get kind => integer()(); // 0 学习 1 默写 2 自述
  RealColumn get score => real()(); // 0-100
  TextColumn get detail => text()(); // 差异详情 / 自述文本
  TextColumn get hitKeyPoints => text()(); // JSON: [0,2,3]
  DateTimeColumn get createdAt => dateTime().nullable()();
}

@DriftDatabase(tables: [ProblemRows, Meta, ProgressRows, ReviewLogs])
class AppDatabase extends _$AppDatabase {
  AppDatabase(super.e);

  @override
  int get schemaVersion => 3;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onUpgrade: (m, from, to) async {
          if (from < 2) {
            await m.addColumn(problemRows, problemRows.acmCode);
            await m.addColumn(problemRows, problemRows.samples);
            await m.addColumn(problemRows, problemRows.companies);
          }
          if (from < 3) {
            await m.addColumn(problemRows, problemRows.codeCpp);
            await m.addColumn(problemRows, problemRows.acmCodeCpp);
            await m.addColumn(problemRows, problemRows.codeJava);
            await m.addColumn(problemRows, problemRows.codeJs);
            await m.addColumn(problemRows, problemRows.codeGo);
          }
        },
      );

  // ---------- 内容导入 ----------

  Future<void> upsertProblems(List<ProblemRowsCompanion> rows) async {
    await batch((b) {
      b.insertAllOnConflictUpdate(problemRows, rows);
    });
  }

  Future<List<int>> allProblemIds() =>
      (select(problemRows)..orderBy([(p) => OrderingTerm.asc(p.id)]))
          .get()
          .then((l) => l.map((e) => e.id).toList());

  Future<int> contentCount() async {
    final c = countAll();
    final q = selectOnly(problemRows)..addColumns([c]);
    final r = await q.getSingle();
    return r.read(c) ?? 0;
  }

  Future<String?> metaValue(String key) async {
    final q = select(meta)..where((m) => m.key.equals(key));
    final r = await q.getSingleOrNull();
    return r?.value;
  }

  Future<void> setMeta(String key, String value) => into(meta).insertOnConflictUpdate(
        MetaCompanion.insert(key: key, value: value),
      );

  // ---------- 进度 ----------

  Future<ProgressRow?> progressOf(int problemId) =>
      (select(progressRows)..where((p) => p.problemId.equals(problemId)))
          .getSingleOrNull();

  Future<void> saveProgress(ProgressRowsCompanion row) =>
      into(progressRows).insertOnConflictUpdate(row);

  Future<List<ProgressRow>> allProgress() => select(progressRows).get();

  Future<List<ProblemRow>> problemsByIds(List<int> ids) {
    final q = select(problemRows);
    if (ids.isEmpty) return Future.value([]);
    return (q..where((p) => p.id.isIn(ids))).get();
  }

  // ---------- 评测记录 ----------

  Future<void> addReview(ReviewLogsCompanion row) =>
      into(reviewLogs).insert(row);

  Future<List<ReviewLog>> recentReviews({int limit = 200}) =>
      (select(reviewLogs)..orderBy([(r) => OrderingTerm.desc(r.createdAt)])..limit(limit))
          .get();

  Future<List<ReviewLog>> reviewsOfProblem(int problemId) =>
      (select(reviewLogs)
            ..where((r) => r.problemId.equals(problemId))
            ..orderBy([(r) => OrderingTerm.desc(r.createdAt)]))
          .get();
}

/// JSON 辅助
List<String> jsonStrList(String s) =>
    (jsonDecode(s) as List).cast<String>();
