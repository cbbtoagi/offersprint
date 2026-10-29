/// 全局状态：内容、进度、笔记、统计；以及界面 tab 状态。
library;
import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'db.dart' as db;
import 'models.dart';
import 'repo.dart';
import 'sr.dart';

class UiState extends ChangeNotifier {
  /// 0 首页 1 算法 2 八股 3 速刷 4 模拟（「我的」经首页头像进入）
  int tab = 0;
  int libraryTab = 0; // 八股内：0 题库 1 项目 2 面经

  /// 速刷页的一次性预设：指定题目队列 / 预选领域
  List<String>? flashPresetIds;
  Set<String>? flashDomainsPreset;

  void goto(int t, {int? lib}) {
    tab = t.clamp(0, 4);
    if (lib != null) libraryTab = lib;
    notifyListeners();
  }

  void gotoFlash({List<String>? presetIds, Set<String>? domains}) {
    flashPresetIds = presetIds;
    flashDomainsPreset = domains;
    tab = 3;
    notifyListeners();
  }
}

class AppState extends ChangeNotifier {
  ContentRepo? repo;
  Map<String, ProgressRec> progress = {};
  Map<String, DailyRec> daily = {};
  List<NoteRec> notes = [];
  bool ready = false;
  String? loadError;

  // ---- 统计 ----
  static String _today() {
    final n = DateTime.now();
    return '${n.year}-${n.month.toString().padLeft(2, '0')}-${n.day.toString().padLeft(2, '0')}';
  }

  DailyRec todayRec() => daily[_today()] ?? DailyRec(date: _today());

  int get dueCount {
    final now = DateTime.now().millisecondsSinceEpoch;
    return progress.values.where((r) => !r.isNew && r.dueAt <= now).length;
  }

  int get totalLearned => progress.values.where((r) => !r.isNew).length;

  int get streak {
    int s = 0;
    final n = DateTime.now();
    for (int i = 0; i < 400; i++) {
      final d = n.subtract(Duration(days: i));
      final key =
          '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
      final rec = daily[key];
      final active = rec != null && (rec.reviewed > 0 || rec.mockCount > 0);
      if (active) {
        s++;
      } else if (i > 0) {
        break;
      } else {
        // 今天还没学，从昨天开始算
      }
    }
    return s;
  }

  double masteryOf(String domain) {
    final qs = repo?.questionsOf(domain) ?? const [];
    if (qs.isEmpty) return 0;
    double pts = 0;
    for (final q in qs) {
      final r = progress[q.id];
      if (r == null || r.isNew) continue;
      if (r.isMastered) {
        pts += 1;
      } else if (r.lastGrade == 2) {
        pts += 0.6;
      } else if (r.lastGrade == 1) {
        pts += 0.3;
      }
    }
    return pts / qs.length;
  }

  /// 0 fresh / 1 due / 2 scheduled / 3 mastered
  int statusOf(String qid) {
    final r = progress[qid];
    if (r == null || r.isNew) return 0;
    if (r.isMastered) return 3;
    if (r.isDue) return 1;
    return 2;
  }

  // ---- 初始化 ----
  Future<void> init({dynamic algoContent}) async {
    debugPrint('init: start');
    try {
      repo = await ContentRepo.load();
      debugPrint('init: content loaded (${repo!.totalQuestions} 题)');
      progress = await db.AppDb.loadProgress();
      debugPrint('init: progress loaded');
      daily = await db.AppDb.loadDaily();
      notes = await db.AppDb.loadNotes();
      debugPrint('init: notes loaded');
    } catch (e) {
      loadError = e.toString();
      debugPrint('init: loadError $e');
    }
    // 算法题库（algosprint）导入 SQLite，失败不阻塞八股功能
    if (algoContent != null) {
      try {
        final n = await algoContent.importIfNeeded();
        debugPrint('init: algo import ok ($n 题)');
      } catch (e) {
        debugPrint('init: algo import failed $e');
      }
    }
    debugPrint('init: ready');
    ready = true;
    notifyListeners();
  }

  // ---- 学习动作 ----
  Future<void> grade(String qid, int g) async {
    final prev = progress[qid] ?? ProgressRec.newRec(qid);
    final wasNew = prev.isNew;
    final next = schedule(prev, g);
    progress[qid] = next;
    await db.AppDb.upsertProgress(next);
    await db.AppDb.bumpDaily(_today(), reviewed: 1, newLearned: wasNew ? 1 : 0);
    final key = _today();
    daily[key] = (daily[key] ?? DailyRec(date: key))
      ..reviewed += 1
      ..newLearned += wasNew ? 1 : 0;
    notifyListeners();
  }

  Future<void> bumpMock(double minutes) async {
    await db.AppDb.bumpDaily(_today(), mock: 1, minutes: minutes);
    final key = _today();
    daily[key] = (daily[key] ?? DailyRec(date: key))
      ..mockCount += 1
      ..minutes += minutes;
    notifyListeners();
  }

  // ---- 速刷队列 ----
  List<Question> buildQueue({
    required Set<String> domains,
    required int size,
    bool includeNew = true,
    bool onlyHandcoded = false,
  }) {
    final now = DateTime.now().millisecondsSinceEpoch;
    final all = <Question>[];
    for (final p in repo?.packs ?? const <(DomainMeta, List<Question>)>[]) {
      if (domains.isNotEmpty && !domains.contains(p.$1.id)) continue;
      all.addAll(p.$2);
    }
    final due = <Question>[];
    final fresh = <Question>[];
    for (final q in all) {
      final r = progress[q.id];
      if (r != null && !r.isNew && r.dueAt <= now) {
        due.add(q);
      } else if ((r == null || r.isNew) && includeNew) {
        fresh.add(q);
      }
    }
    due.sort((a, b) {
      final ra = progress[a.id]!.dueAt, rb = progress[b.id]!.dueAt;
      return ra.compareTo(rb);
    });
    fresh.sort((a, b) => b.frequency.compareTo(a.frequency));
    final queue = [...due, ...fresh];
    if (onlyHandcoded) {
      queue.sort((a, b) {
        final ha = a.domain == 'handcoded' ? 0 : 1, hb = b.domain == 'handcoded' ? 0 : 1;
        if (ha != hb) return ha - hb;
        return b.frequency.compareTo(a.frequency);
      });
    }
    return queue.take(size).toList();
  }

  Question randomQuestion([Set<String>? domains]) {
    final pool = <Question>[];
    for (final p in repo?.packs ?? const <(DomainMeta, List<Question>)>[]) {
      if (domains != null && domains.isNotEmpty && !domains.contains(p.$1.id)) continue;
      pool.addAll(p.$2);
    }
    if (pool.isEmpty) {
      return const Question(
        id: '', domain: '', domainName: '', topic: '', type: '八股',
        difficulty: 1, frequency: 1, companies: [], years: [],
        question: '题库为空，请先运行内容转换脚本', answerMd: '', keyPoints: [], followUps: [], code: null,
      );
    }
    pool.shuffle();
    return pool.first;
  }

  // ---- 笔记 / 录音 ----
  Future<void> addNote(String text, String tags, String? qid, String? audioPath) async {
    await db.AppDb.insertNote(NoteRec(text: text, tags: tags, qid: qid, audioPath: audioPath, createdAt: DateTime.now().millisecondsSinceEpoch));
    notes = await db.AppDb.loadNotes();
    notifyListeners();
  }

  Future<void> deleteNote(int id) async {
    await db.AppDb.deleteNote(id);
    notes = await db.AppDb.loadNotes();
    notifyListeners();
  }

  Future<void> saveRecording({String? qid, int? sessionId, required String path, required int durationMs, String transcript = ''}) async {
    await db.AppDb.insertRecording(RecordingRec(
      qid: qid, sessionId: sessionId, path: path, durationMs: durationMs, transcript: transcript,
      createdAt: DateTime.now().millisecondsSinceEpoch,
    ));
  }

  // ---- 导入导出 ----
  Future<String> exportJson() async {
    final data = await db.AppDb.exportAll();
    data['meta'] = {'app': 'interview_flash', 'version': 1, 'exported_at': DateTime.now().toIso8601String()};
    return const JsonEncoder.withIndent('  ').convert(data);
  }

  Future<int> importJson(String raw) async {
    final data = jsonDecode(raw) as Map<String, dynamic>;
    final n = await db.AppDb.importAll(data);
    progress = await db.AppDb.loadProgress();
    daily = await db.AppDb.loadDaily();
    notes = await db.AppDb.loadNotes();
    notifyListeners();
    return n;
  }

  Future<void> resetStudyData() async {
    await db.AppDb.clearStudyData();
    progress = {};
    daily = {};
    notes = await db.AppDb.loadNotes();
    notifyListeners();
  }
}
