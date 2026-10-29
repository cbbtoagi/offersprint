/// 题目内容模型 —— 与 assets/content/*.json 的 schema v2 一一对应。
library;

/// 测试样例
class Sample {
  final String input;
  final String output;
  final String? explain;

  const Sample({required this.input, required this.output, this.explain});

  factory Sample.fromJson(Map<String, dynamic> j) => Sample(
        input: j['input'] as String,
        output: j['output'] as String,
        explain: j['explain'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'input': input,
        'output': output,
        if (explain != null) 'explain': explain,
      };
}

class Approach {
  final String name;
  final String idea; // 一句话思路
  final String detail; // 展开教学：步骤拆解 + 示例走查 + 易错点
  final String complexity;
  final bool optimal;
  final String? code; // 该思路的可运行 Python 实现

  const Approach({
    required this.name,
    required this.idea,
    required this.detail,
    required this.complexity,
    this.optimal = false,
    this.code,
  });

  factory Approach.fromJson(Map<String, dynamic> j) => Approach(
        name: j['name'] as String,
        idea: j['idea'] as String,
        detail: (j['detail'] as String?) ?? '',
        complexity: j['complexity'] as String,
        optimal: (j['optimal'] as bool?) ?? false,
        code: j['code'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'idea': idea,
        'detail': detail,
        'complexity': complexity,
        'optimal': optimal,
        if (code != null) 'code': code,
      };
}

class Problem {
  final int id;
  final String title;
  final String titleCn;
  final String topic;
  final String difficulty;
  final int frequency; // 1-5 高频程度
  final List<String> companies; // 大厂高频标签
  final String question;
  final List<Sample> samples; // 测试样例（评测界面展示）
  final List<String> hints; // 审题诀窍
  final List<String> keyPoints; // 关键点（自评清单）
  final List<String> structureTags; // 结构标签（默写比对用）
  final List<Approach> approaches;
  final String code; // 最优解 Python（LeetCode 核心代码形式）
  final String acmCode; // ACM 模式完整程序（Python，stdin/stdout）
  final String codeCpp; // C++ 核心代码
  final String acmCodeCpp; // ACM 模式完整程序（C++）
  final String codeJava; // Java 核心代码
  final String codeJs; // JavaScript 核心代码
  final String codeGo; // Go 核心代码
  final List<String> templates;

  const Problem({
    required this.id,
    required this.title,
    required this.titleCn,
    required this.topic,
    required this.difficulty,
    required this.frequency,
    required this.companies,
    required this.question,
    required this.samples,
    required this.hints,
    required this.keyPoints,
    required this.structureTags,
    required this.approaches,
    required this.code,
    required this.acmCode,
    this.codeCpp = '',
    this.acmCodeCpp = '',
    this.codeJava = '',
    this.codeJs = '',
    this.codeGo = '',
    required this.templates,
  });

  factory Problem.fromJson(Map<String, dynamic> j, String topic) => Problem(
        id: j['id'] as int,
        title: j['title'] as String,
        titleCn: j['titleCn'] as String,
        topic: topic,
        difficulty: j['difficulty'] as String,
        frequency: j['frequency'] as int,
        companies:
            (j['companies'] as List?)?.cast<String>() ?? const <String>[],
        question: j['question'] as String,
        samples: ((j['samples'] as List?) ?? const [])
            .map((e) => Sample.fromJson(e as Map<String, dynamic>))
            .toList(),
        hints: List<String>.from(j['hints'] as List),
        keyPoints: List<String>.from(j['keyPoints'] as List),
        structureTags: List<String>.from(j['structureTags'] as List),
        approaches: (j['approaches'] as List)
            .map((e) => Approach.fromJson(e as Map<String, dynamic>))
            .toList(),
        code: j['code'] as String,
        acmCode: (j['acmCode'] as String?) ?? '',
        codeCpp: (j['codeCpp'] as String?) ?? '',
        acmCodeCpp: (j['acmCodeCpp'] as String?) ?? '',
        codeJava: (j['codeJava'] as String?) ?? '',
        codeJs: (j['codeJs'] as String?) ?? '',
        codeGo: (j['codeGo'] as String?) ?? '',
        templates: List<String>.from(j['templates'] as List),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'titleCn': titleCn,
        'topic': topic,
        'difficulty': difficulty,
        'frequency': frequency,
        'companies': companies,
        'question': question,
        'samples': samples.map((s) => s.toJson()).toList(),
        'hints': hints,
        'keyPoints': keyPoints,
        'structureTags': structureTags,
        'approaches': approaches.map((a) => a.toJson()).toList(),
        'code': code,
        'acmCode': acmCode,
        if (codeCpp.isNotEmpty) 'codeCpp': codeCpp,
        if (acmCodeCpp.isNotEmpty) 'acmCodeCpp': acmCodeCpp,
        if (codeJava.isNotEmpty) 'codeJava': codeJava,
        if (codeJs.isNotEmpty) 'codeJs': codeJs,
        if (codeGo.isNotEmpty) 'codeGo': codeGo,
        'templates': templates,
      };
}

/// 评测记录类型
enum ReviewKind { learn, typing, verbal }

extension ReviewKindX on ReviewKind {
  String get label => switch (this) {
        ReviewKind.learn => '学习',
        ReviewKind.typing => '默写',
        ReviewKind.verbal => '自述',
      };
}

/// 一次评测/学习的结果，用于落盘与回看。
class ReviewRecord {
  final int? id;
  final int problemId;
  final ReviewKind kind;
  final double score; // 0-100
  final String detail; // 差异/命中/自述文本 等
  final List<int> hitKeyPoints; // 命中的关键点下标
  final DateTime createdAt;

  const ReviewRecord({
    this.id,
    required this.problemId,
    required this.kind,
    required this.score,
    required this.detail,
    required this.hitKeyPoints,
    required this.createdAt,
  });
}
