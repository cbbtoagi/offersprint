/// 本地数据库（sqflite；iOS/macOS 走原生 sqflite_darwin 实现）。
library;
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

import 'models.dart';

class AppDb {
  static Database? _db;

  static Future<Database> instance() async {
    if (_db != null) return _db!;
    final dir = await getApplicationSupportDirectory();
    _db = await openDatabase(p.join(dir.path, 'interview_flash.db'), version: 1, onCreate: (db, v) async {
      await db.execute('''
        CREATE TABLE progress(
          qid TEXT PRIMARY KEY, ease REAL, interval_days REAL, due_at INTEGER,
          reps INTEGER, lapses INTEGER, last_grade INTEGER, last_at INTEGER)
      ''');
      await db.execute('''
        CREATE TABLE notes(
          id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, tags TEXT,
          qid TEXT, audio_path TEXT, created_at INTEGER)
      ''');
      await db.execute('''
        CREATE TABLE recordings(
          id INTEGER PRIMARY KEY AUTOINCREMENT, qid TEXT, session_id INTEGER,
          path TEXT, duration_ms INTEGER, transcript TEXT, created_at INTEGER)
      ''');
      await db.execute('''
        CREATE TABLE sessions(
          id INTEGER PRIMARY KEY AUTOINCREMENT, started_at INTEGER, ended_at INTEGER,
          mode TEXT, domains TEXT, items TEXT)
      ''');
      await db.execute('''
        CREATE TABLE daily(
          date TEXT PRIMARY KEY, reviewed INTEGER, new_learned INTEGER,
          mock_count INTEGER, minutes REAL)
      ''');
      await db.execute('CREATE TABLE settings(k TEXT PRIMARY KEY, v TEXT)');
    });
    return _db!;
  }

  // ---- progress ----
  static Future<Map<String, ProgressRec>> loadProgress() async {
    final db = await instance();
    final rows = await db.query('progress');
    return {for (final r in rows) r['qid'] as String: ProgressRec.fromMap(r)};
  }

  static Future<void> upsertProgress(ProgressRec rec) async {
    final db = await instance();
    await db.insert('progress', rec.toMap(), conflictAlgorithm: ConflictAlgorithm.replace);
  }

  // ---- notes ----
  static Future<List<NoteRec>> loadNotes() async {
    final db = await instance();
    final rows = await db.query('notes', orderBy: 'created_at DESC');
    return rows.map(NoteRec.fromMap).toList();
  }

  static Future<void> insertNote(NoteRec n) async {
    final db = await instance();
    await db.insert('notes', n.toMap()..remove('id'));
  }

  static Future<void> deleteNote(int id) async {
    final db = await instance();
    await db.delete('notes', where: 'id = ?', whereArgs: [id]);
  }

  // ---- recordings ----
  static Future<void> insertRecording(RecordingRec r) async {
    final db = await instance();
    await db.insert('recordings', r.toMap()..remove('id'));
  }

  static Future<List<RecordingRec>> loadRecordings({String? qid}) async {
    final db = await instance();
    final rows = await db.query('recordings',
        where: qid != null ? 'qid = ?' : null, whereArgs: qid != null ? [qid] : null, orderBy: 'created_at DESC');
    return rows.map(RecordingRec.fromMap).toList();
  }

  static Future<void> deleteRecording(int id) async {
    final db = await instance();
    await db.delete('recordings', where: 'id = ?', whereArgs: [id]);
  }

  // ---- daily ----
  static Future<Map<String, DailyRec>> loadDaily() async {
    final db = await instance();
    final rows = await db.query('daily');
    return {for (final r in rows) r['date'] as String: DailyRec.fromMap(r)};
  }

  static Future<void> bumpDaily(String date, {int reviewed = 0, int newLearned = 0, int mock = 0, double minutes = 0}) async {
    final db = await instance();
    final rows = await db.query('daily', where: 'date = ?', whereArgs: [date]);
    if (rows.isEmpty) {
      await db.insert('daily', DailyRec(date: date).toMap());
    }
    await db.execute(
      'UPDATE daily SET reviewed = reviewed + ?, new_learned = new_learned + ?, mock_count = mock_count + ?, minutes = minutes + ? WHERE date = ?',
      [reviewed, newLearned, mock, minutes, date],
    );
  }

  // ---- sessions ----
  static Future<void> insertSession(SessionRec s) async {
    final db = await instance();
    await db.insert('sessions', s.toMap()..remove('id'));
  }

  // ---- settings ----
  static Future<String?> getSetting(String k) async {
    final db = await instance();
    final rows = await db.query('settings', where: 'k = ?', whereArgs: [k]);
    return rows.isEmpty ? null : rows.first['v'] as String?;
  }

  static Future<void> setSetting(String k, String v) async {
    final db = await instance();
    await db.insert('settings', {'k': k, 'v': v}, conflictAlgorithm: ConflictAlgorithm.replace);
  }

  // ---- reset ----
  static Future<void> clearStudyData() async {
    final db = await instance();
    await db.delete('progress');
    await db.delete('daily');
    await db.delete('sessions');
  }

  /// 导出用：读取全部表。
  static Future<Map<String, dynamic>> exportAll() async {
    final db = await instance();
    return {
      'progress': await db.query('progress'),
      'notes': await db.query('notes'),
      'daily': await db.query('daily'),
      'sessions': await db.query('sessions'),
      'settings': await db.query('settings'),
    };
  }

  static Future<int> importAll(Map<String, dynamic> data) async {
    final db = await instance();
    int count = 0;
    final batch = db.batch();
    for (final row in ((data['progress'] as List?) ?? const [])) {
      batch.insert('progress', Map<String, Object?>.from(row as Map), conflictAlgorithm: ConflictAlgorithm.replace);
      count++;
    }
    for (final row in ((data['daily'] as List?) ?? const [])) {
      batch.insert('daily', Map<String, Object?>.from(row as Map), conflictAlgorithm: ConflictAlgorithm.replace);
      count++;
    }
    for (final row in ((data['notes'] as List?) ?? const [])) {
      batch.insert('notes', Map<String, Object?>.from(row as Map)..remove('id'));
      count++;
    }
    await batch.commit(noResult: true);
    return count;
  }
}
