/// 内容资产管理：加载 assets/algo/content/*.json 并导入 SQLite。
/// 内容版本号变更时增量重导，进度与评测记录保留。
library;

import 'dart:convert';

import 'package:drift/drift.dart' show Value;
import 'package:flutter/services.dart' show AssetManifest, rootBundle;

import '../models/problem.dart';
import 'database.dart';

const contentVersionKey = 'content_version';
const contentVersion = '6'; // 内容批次更新时递增

class ContentRepository {
  ContentRepository(this._db);

  final AppDatabase _db;
  Map<int, Problem>? _cache;

  Future<bool> needsImport() async {
    final v = await _db.metaValue(contentVersionKey);
    final count = await _db.contentCount();
    return v != contentVersion || count == 0;
  }

  /// 导入全部内容（幂等）。返回题目总数。
  Future<int> importIfNeeded() async {
    if (!await needsImport()) {
      return _db.contentCount();
    }
    final problems = await loadFromAssets();
    final rows = problems
        .map((p) => ProblemRowsCompanion.insert(
              id: Value(p.id),
              title: p.title,
              titleCn: p.titleCn,
              topic: p.topic,
              difficulty: p.difficulty,
              frequency: p.frequency,
              question: p.question,
              hints: jsonEncode(p.hints),
              keyPoints: jsonEncode(p.keyPoints),
              structureTags: jsonEncode(p.structureTags),
              approaches:
                  jsonEncode(p.approaches.map((a) => a.toJson()).toList()),
              code: p.code,
              acmCode: Value(p.acmCode.isEmpty ? null : p.acmCode),
              codeCpp: Value(p.codeCpp.isEmpty ? null : p.codeCpp),
              acmCodeCpp:
                  Value(p.acmCodeCpp.isEmpty ? null : p.acmCodeCpp),
              codeJava: Value(p.codeJava.isEmpty ? null : p.codeJava),
              codeJs: Value(p.codeJs.isEmpty ? null : p.codeJs),
              codeGo: Value(p.codeGo.isEmpty ? null : p.codeGo),
              samples: Value(
                  p.samples.isEmpty ? null : jsonEncode(
                      p.samples.map((s) => s.toJson()).toList())),
              companies: Value(p.companies.isEmpty ? null : jsonEncode(p.companies)),
              templates: jsonEncode(p.templates),
            ))
        .toList();
    await _db.upsertProblems(rows);
    await _db.setMeta(contentVersionKey, contentVersion);
    _cache = {for (final p in problems) p.id: p};
    return problems.length;
  }

  Future<Map<int, Problem>> allProblems() async {
    // 首启导入前可能查到空表并被缓存：空缓存允许重查
    if (_cache != null && _cache!.isNotEmpty) return _cache!;
    final rows = await _db.select(_db.problemRows).get();
    final map = <int, Problem>{
      for (final r in rows)
        r.id: Problem(
          id: r.id,
          title: r.title,
          titleCn: r.titleCn,
          topic: r.topic,
          difficulty: r.difficulty,
          frequency: r.frequency,
          companies:
              r.companies == null ? const [] : jsonStrList(r.companies!),
          question: r.question,
          samples: r.samples == null
              ? const []
              : ((jsonDecode(r.samples!) as List).cast<Map<String, dynamic>>())
                  .map(Sample.fromJson)
                  .toList(),
          hints: jsonStrList(r.hints),
          keyPoints: jsonStrList(r.keyPoints),
          structureTags: jsonStrList(r.structureTags),
          approaches: ((jsonDecode(r.approaches) as List)
                  .cast<Map<String, dynamic>>())
              .map(Approach.fromJson)
              .toList(),
          code: r.code,
          acmCode: r.acmCode ?? '',
          codeCpp: r.codeCpp ?? '',
          acmCodeCpp: r.acmCodeCpp ?? '',
          codeJava: r.codeJava ?? '',
          codeJs: r.codeJs ?? '',
          codeGo: r.codeGo ?? '',
          templates: jsonStrList(r.templates),
        ),
    };
    _cache = map;
    return map;
  }

  Future<Problem?> problem(int id) async =>
      (await allProblems())[id];

  /// 直接从 assets/algo/content/*.json 解析
  static Future<List<Problem>> loadFromAssets() async {
    final manifest = await AssetManifest.loadFromAssetBundle(rootBundle);
    final assets = manifest
        .listAssets()
        .where((k) => k.startsWith('assets/algo/content/') && k.endsWith('.json'))
        .toList()
      ..sort();
    final problems = <Problem>[];
    for (final path in assets) {
      final data =
          jsonDecode(await rootBundle.loadString(path)) as Map<String, dynamic>;
      final topic = data['topic'] as String;
      for (final p in (data['problems'] as List)) {
        problems.add(Problem.fromJson(p as Map<String, dynamic>, topic));
      }
    }
    return problems;
  }
}
