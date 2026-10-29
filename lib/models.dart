/// 数据模型：题库、项目、面经、学习进度、笔记等。
library;

class FollowUp {
  final String q;
  final String a;
  const FollowUp({required this.q, required this.a});

  factory FollowUp.fromJson(Map<String, dynamic> j) =>
      FollowUp(q: j['q'] as String? ?? '', a: j['a'] as String? ?? '');
}

class CodeBlock {
  final String lang;
  final String? caption;
  final String content;
  const CodeBlock({required this.lang, this.caption, required this.content});

  factory CodeBlock.fromJson(Map<String, dynamic> j) => CodeBlock(
        lang: j['lang'] as String? ?? 'python',
        caption: j['caption'] as String?,
        content: j['content'] as String? ?? '',
      );
}

class Question {
  final String id;
  final String domain;
  final String domainName;
  final String topic;
  final String type;
  final int difficulty;
  final int frequency;
  final List<String> companies;
  final List<String> years;
  final String question;
  final String answerMd;
  final List<String> keyPoints;
  final List<FollowUp> followUps;
  final CodeBlock? code;

  const Question({
    required this.id,
    required this.domain,
    required this.domainName,
    required this.topic,
    required this.type,
    required this.difficulty,
    required this.frequency,
    required this.companies,
    required this.years,
    required this.question,
    required this.answerMd,
    required this.keyPoints,
    required this.followUps,
    required this.code,
  });

  factory Question.fromJson(Map<String, dynamic> j, String domain, String domainName) => Question(
        id: j['id'] as String,
        domain: domain,
        domainName: domainName,
        topic: j['topic'] as String? ?? '其他',
        type: j['type'] as String? ?? '八股',
        difficulty: (j['difficulty'] as num?)?.toInt() ?? 3,
        frequency: (j['frequency'] as num?)?.toInt() ?? 3,
        companies: ((j['companies'] as List?) ?? const [])
            .map((e) => e.toString())
            .toList(growable: false),
        years: ((j['years'] as List?) ?? const [])
            .map((e) => e.toString())
            .toList(growable: false),
        question: j['question'] as String? ?? '',
        answerMd: j['answerMd'] as String? ?? '',
        keyPoints: ((j['keyPoints'] as List?) ?? const [])
            .map((e) => e.toString())
            .toList(growable: false),
        followUps: ((j['followUps'] as List?) ?? const [])
            .map((e) => FollowUp.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(growable: false),
        code: j['code'] is Map ? CodeBlock.fromJson(Map<String, dynamic>.from(j['code'] as Map)) : null,
      );
}

class Project {
  final String id;
  final String name;
  final String domain;
  final String level;
  final List<String> tags;
  final String summaryMd;
  final String bodyMd;

  const Project({
    required this.id,
    required this.name,
    required this.domain,
    required this.level,
    required this.tags,
    required this.summaryMd,
    required this.bodyMd,
  });

  factory Project.fromJson(Map<String, dynamic> j) => Project(
        id: j['id'] as String,
        name: j['name'] as String? ?? '',
        domain: j['domain'] as String? ?? '',
        level: j['level'] as String? ?? '经典',
        tags: ((j['tags'] as List?) ?? const []).map((e) => e.toString()).toList(growable: false),
        summaryMd: j['summaryMd'] as String? ?? '',
        bodyMd: j['bodyMd'] as String? ?? '',
      );
}

class InterviewExp {
  final String id;
  final String company;
  final String group;
  final String role;
  final int difficulty;
  final String updated;
  final List<String> rounds;
  final List<String> questions;
  final String focus;
  final String advice;

  const InterviewExp({
    required this.id,
    required this.company,
    required this.group,
    required this.role,
    required this.difficulty,
    required this.updated,
    required this.rounds,
    required this.questions,
    required this.focus,
    required this.advice,
  });

  factory InterviewExp.fromJson(Map<String, dynamic> j) => InterviewExp(
        id: j['id'] as String,
        company: j['company'] as String? ?? '',
        group: j['group'] as String? ?? '其他',
        role: j['role'] as String? ?? '',
        difficulty: (j['difficulty'] as num?)?.toInt() ?? 3,
        updated: j['updated'] as String? ?? '',
        rounds: ((j['rounds'] as List?) ?? const []).map((e) => e.toString()).toList(growable: false),
        questions: ((j['questions'] as List?) ?? const []).map((e) => e.toString()).toList(growable: false),
        focus: j['focus'] as String? ?? '',
        advice: j['advice'] as String? ?? '',
      );
}

/// 单题学习进度（SM-2）。
class ProgressRec {
  final String qid;
  final double ease;
  final double intervalDays;
  final int dueAt;
  final int reps;
  final int lapses;
  final int lastGrade; // 0 忘了 / 1 模糊 / 2 记得，-1 无
  final int lastAt;

  const ProgressRec({
    required this.qid,
    required this.ease,
    required this.intervalDays,
    required this.dueAt,
    required this.reps,
    required this.lapses,
    required this.lastGrade,
    required this.lastAt,
  });

  factory ProgressRec.newRec(String qid) => ProgressRec(
        qid: qid,
        ease: 2.5,
        intervalDays: 0,
        dueAt: 0,
        reps: 0,
        lapses: 0,
        lastGrade: -1,
        lastAt: 0,
      );

  bool get isNew => reps == 0;
  bool get isDue => dueAt <= DateTime.now().millisecondsSinceEpoch;
  bool get isMastered => lastGrade == 2 && reps >= 3 && intervalDays >= 21;
  bool get isShaky => lapses > 0 || lastGrade == 0;

  Map<String, Object> toMap() => {
        'qid': qid,
        'ease': ease,
        'interval_days': intervalDays,
        'due_at': dueAt,
        'reps': reps,
        'lapses': lapses,
        'last_grade': lastGrade,
        'last_at': lastAt,
      };

  factory ProgressRec.fromMap(Map<String, Object?> m) => ProgressRec(
        qid: m['qid'] as String,
        ease: (m['ease'] as num?)?.toDouble() ?? 2.5,
        intervalDays: (m['interval_days'] as num?)?.toDouble() ?? 0,
        dueAt: (m['due_at'] as num?)?.toInt() ?? 0,
        reps: (m['reps'] as num?)?.toInt() ?? 0,
        lapses: (m['lapses'] as num?)?.toInt() ?? 0,
        lastGrade: (m['last_grade'] as num?)?.toInt() ?? -1,
        lastAt: (m['last_at'] as num?)?.toInt() ?? 0,
      );

  ProgressRec copyWith({double? ease, double? intervalDays, int? dueAt, int? reps, int? lapses, int? lastGrade, int? lastAt}) =>
      ProgressRec(
        qid: qid,
        ease: ease ?? this.ease,
        intervalDays: intervalDays ?? this.intervalDays,
        dueAt: dueAt ?? this.dueAt,
        reps: reps ?? this.reps,
        lapses: lapses ?? this.lapses,
        lastGrade: lastGrade ?? this.lastGrade,
        lastAt: lastAt ?? this.lastAt,
      );
}

class NoteRec {
  final int? id;
  final String text;
  final String tags; // 逗号分隔
  final String? qid;
  final String? audioPath;
  final int createdAt;

  const NoteRec({
    this.id,
    required this.text,
    this.tags = '',
    this.qid,
    this.audioPath,
    required this.createdAt,
  });

  List<String> get tagList => tags.isEmpty ? const [] : tags.split(',');

  Map<String, Object?> toMap() => {
        'id': id,
        'text': text,
        'tags': tags,
        'qid': qid,
        'audio_path': audioPath,
        'created_at': createdAt,
      };

  factory NoteRec.fromMap(Map<String, Object?> m) => NoteRec(
        id: m['id'] as int?,
        text: m['text'] as String? ?? '',
        tags: m['tags'] as String? ?? '',
        qid: m['qid'] as String?,
        audioPath: m['audio_path'] as String?,
        createdAt: (m['created_at'] as num?)?.toInt() ?? 0,
      );
}

class DailyRec {
  final String date; // yyyy-MM-dd
  int reviewed;
  int newLearned;
  int mockCount;
  double minutes;

  DailyRec({required this.date, this.reviewed = 0, this.newLearned = 0, this.mockCount = 0, this.minutes = 0});

  Map<String, Object> toMap() =>
      {'date': date, 'reviewed': reviewed, 'new_learned': newLearned, 'mock_count': mockCount, 'minutes': minutes};

  factory DailyRec.fromMap(Map<String, Object?> m) => DailyRec(
        date: m['date'] as String,
        reviewed: (m['reviewed'] as num?)?.toInt() ?? 0,
        newLearned: (m['new_learned'] as num?)?.toInt() ?? 0,
        mockCount: (m['mock_count'] as num?)?.toInt() ?? 0,
        minutes: (m['minutes'] as num?)?.toDouble() ?? 0,
      );
}

class RecordingRec {
  final int? id;
  final String? qid;
  final int? sessionId;
  final String path;
  final int durationMs;
  final String transcript;
  final int createdAt;

  const RecordingRec({
    this.id,
    this.qid,
    this.sessionId,
    required this.path,
    this.durationMs = 0,
    this.transcript = '',
    required this.createdAt,
  });

  Map<String, Object?> toMap() => {
        'id': id,
        'qid': qid,
        'session_id': sessionId,
        'path': path,
        'duration_ms': durationMs,
        'transcript': transcript,
        'created_at': createdAt,
      };

  factory RecordingRec.fromMap(Map<String, Object?> m) => RecordingRec(
        id: m['id'] as int?,
        qid: m['qid'] as String?,
        sessionId: m['session_id'] as int?,
        path: m['path'] as String? ?? '',
        durationMs: (m['duration_ms'] as num?)?.toInt() ?? 0,
        transcript: m['transcript'] as String? ?? '',
        createdAt: (m['created_at'] as num?)?.toInt() ?? 0,
      );
}

class SessionRec {
  final int? id;
  final int startedAt;
  final int endedAt;
  final String mode; // flash / mock
  final String domains; // 逗号分隔
  final String itemsJson;

  const SessionRec({
    this.id,
    required this.startedAt,
    required this.endedAt,
    required this.mode,
    required this.domains,
    required this.itemsJson,
  });

  Map<String, Object?> toMap() => {
        'id': id,
        'started_at': startedAt,
        'ended_at': endedAt,
        'mode': mode,
        'domains': domains,
        'items': itemsJson,
      };
}
