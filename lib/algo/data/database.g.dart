// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'database.dart';

// ignore_for_file: type=lint
class $ProblemRowsTable extends ProblemRows
    with TableInfo<$ProblemRowsTable, ProblemRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ProblemRowsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: false);
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
      'title', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _titleCnMeta =
      const VerificationMeta('titleCn');
  @override
  late final GeneratedColumn<String> titleCn = GeneratedColumn<String>(
      'title_cn', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _topicMeta = const VerificationMeta('topic');
  @override
  late final GeneratedColumn<String> topic = GeneratedColumn<String>(
      'topic', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _difficultyMeta =
      const VerificationMeta('difficulty');
  @override
  late final GeneratedColumn<String> difficulty = GeneratedColumn<String>(
      'difficulty', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _frequencyMeta =
      const VerificationMeta('frequency');
  @override
  late final GeneratedColumn<int> frequency = GeneratedColumn<int>(
      'frequency', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _questionMeta =
      const VerificationMeta('question');
  @override
  late final GeneratedColumn<String> question = GeneratedColumn<String>(
      'question', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _hintsMeta = const VerificationMeta('hints');
  @override
  late final GeneratedColumn<String> hints = GeneratedColumn<String>(
      'hints', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _keyPointsMeta =
      const VerificationMeta('keyPoints');
  @override
  late final GeneratedColumn<String> keyPoints = GeneratedColumn<String>(
      'key_points', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _structureTagsMeta =
      const VerificationMeta('structureTags');
  @override
  late final GeneratedColumn<String> structureTags = GeneratedColumn<String>(
      'structure_tags', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _approachesMeta =
      const VerificationMeta('approaches');
  @override
  late final GeneratedColumn<String> approaches = GeneratedColumn<String>(
      'approaches', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _codeMeta = const VerificationMeta('code');
  @override
  late final GeneratedColumn<String> code = GeneratedColumn<String>(
      'code', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _acmCodeMeta =
      const VerificationMeta('acmCode');
  @override
  late final GeneratedColumn<String> acmCode = GeneratedColumn<String>(
      'acm_code', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _codeCppMeta =
      const VerificationMeta('codeCpp');
  @override
  late final GeneratedColumn<String> codeCpp = GeneratedColumn<String>(
      'code_cpp', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _acmCodeCppMeta =
      const VerificationMeta('acmCodeCpp');
  @override
  late final GeneratedColumn<String> acmCodeCpp = GeneratedColumn<String>(
      'acm_code_cpp', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _codeJavaMeta =
      const VerificationMeta('codeJava');
  @override
  late final GeneratedColumn<String> codeJava = GeneratedColumn<String>(
      'code_java', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _codeJsMeta = const VerificationMeta('codeJs');
  @override
  late final GeneratedColumn<String> codeJs = GeneratedColumn<String>(
      'code_js', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _codeGoMeta = const VerificationMeta('codeGo');
  @override
  late final GeneratedColumn<String> codeGo = GeneratedColumn<String>(
      'code_go', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _samplesMeta =
      const VerificationMeta('samples');
  @override
  late final GeneratedColumn<String> samples = GeneratedColumn<String>(
      'samples', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _companiesMeta =
      const VerificationMeta('companies');
  @override
  late final GeneratedColumn<String> companies = GeneratedColumn<String>(
      'companies', aliasedName, true,
      type: DriftSqlType.string, requiredDuringInsert: false);
  static const VerificationMeta _templatesMeta =
      const VerificationMeta('templates');
  @override
  late final GeneratedColumn<String> templates = GeneratedColumn<String>(
      'templates', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [
        id,
        title,
        titleCn,
        topic,
        difficulty,
        frequency,
        question,
        hints,
        keyPoints,
        structureTags,
        approaches,
        code,
        acmCode,
        codeCpp,
        acmCodeCpp,
        codeJava,
        codeJs,
        codeGo,
        samples,
        companies,
        templates
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'problem_rows';
  @override
  VerificationContext validateIntegrity(Insertable<ProblemRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('title')) {
      context.handle(
          _titleMeta, title.isAcceptableOrUnknown(data['title']!, _titleMeta));
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('title_cn')) {
      context.handle(_titleCnMeta,
          titleCn.isAcceptableOrUnknown(data['title_cn']!, _titleCnMeta));
    } else if (isInserting) {
      context.missing(_titleCnMeta);
    }
    if (data.containsKey('topic')) {
      context.handle(
          _topicMeta, topic.isAcceptableOrUnknown(data['topic']!, _topicMeta));
    } else if (isInserting) {
      context.missing(_topicMeta);
    }
    if (data.containsKey('difficulty')) {
      context.handle(
          _difficultyMeta,
          difficulty.isAcceptableOrUnknown(
              data['difficulty']!, _difficultyMeta));
    } else if (isInserting) {
      context.missing(_difficultyMeta);
    }
    if (data.containsKey('frequency')) {
      context.handle(_frequencyMeta,
          frequency.isAcceptableOrUnknown(data['frequency']!, _frequencyMeta));
    } else if (isInserting) {
      context.missing(_frequencyMeta);
    }
    if (data.containsKey('question')) {
      context.handle(_questionMeta,
          question.isAcceptableOrUnknown(data['question']!, _questionMeta));
    } else if (isInserting) {
      context.missing(_questionMeta);
    }
    if (data.containsKey('hints')) {
      context.handle(
          _hintsMeta, hints.isAcceptableOrUnknown(data['hints']!, _hintsMeta));
    } else if (isInserting) {
      context.missing(_hintsMeta);
    }
    if (data.containsKey('key_points')) {
      context.handle(_keyPointsMeta,
          keyPoints.isAcceptableOrUnknown(data['key_points']!, _keyPointsMeta));
    } else if (isInserting) {
      context.missing(_keyPointsMeta);
    }
    if (data.containsKey('structure_tags')) {
      context.handle(
          _structureTagsMeta,
          structureTags.isAcceptableOrUnknown(
              data['structure_tags']!, _structureTagsMeta));
    } else if (isInserting) {
      context.missing(_structureTagsMeta);
    }
    if (data.containsKey('approaches')) {
      context.handle(
          _approachesMeta,
          approaches.isAcceptableOrUnknown(
              data['approaches']!, _approachesMeta));
    } else if (isInserting) {
      context.missing(_approachesMeta);
    }
    if (data.containsKey('code')) {
      context.handle(
          _codeMeta, code.isAcceptableOrUnknown(data['code']!, _codeMeta));
    } else if (isInserting) {
      context.missing(_codeMeta);
    }
    if (data.containsKey('acm_code')) {
      context.handle(_acmCodeMeta,
          acmCode.isAcceptableOrUnknown(data['acm_code']!, _acmCodeMeta));
    }
    if (data.containsKey('code_cpp')) {
      context.handle(_codeCppMeta,
          codeCpp.isAcceptableOrUnknown(data['code_cpp']!, _codeCppMeta));
    }
    if (data.containsKey('acm_code_cpp')) {
      context.handle(
          _acmCodeCppMeta,
          acmCodeCpp.isAcceptableOrUnknown(
              data['acm_code_cpp']!, _acmCodeCppMeta));
    }
    if (data.containsKey('code_java')) {
      context.handle(_codeJavaMeta,
          codeJava.isAcceptableOrUnknown(data['code_java']!, _codeJavaMeta));
    }
    if (data.containsKey('code_js')) {
      context.handle(_codeJsMeta,
          codeJs.isAcceptableOrUnknown(data['code_js']!, _codeJsMeta));
    }
    if (data.containsKey('code_go')) {
      context.handle(_codeGoMeta,
          codeGo.isAcceptableOrUnknown(data['code_go']!, _codeGoMeta));
    }
    if (data.containsKey('samples')) {
      context.handle(_samplesMeta,
          samples.isAcceptableOrUnknown(data['samples']!, _samplesMeta));
    }
    if (data.containsKey('companies')) {
      context.handle(_companiesMeta,
          companies.isAcceptableOrUnknown(data['companies']!, _companiesMeta));
    }
    if (data.containsKey('templates')) {
      context.handle(_templatesMeta,
          templates.isAcceptableOrUnknown(data['templates']!, _templatesMeta));
    } else if (isInserting) {
      context.missing(_templatesMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  ProblemRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ProblemRow(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      title: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title'])!,
      titleCn: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}title_cn'])!,
      topic: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}topic'])!,
      difficulty: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}difficulty'])!,
      frequency: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}frequency'])!,
      question: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}question'])!,
      hints: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}hints'])!,
      keyPoints: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}key_points'])!,
      structureTags: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}structure_tags'])!,
      approaches: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}approaches'])!,
      code: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}code'])!,
      acmCode: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}acm_code']),
      codeCpp: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}code_cpp']),
      acmCodeCpp: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}acm_code_cpp']),
      codeJava: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}code_java']),
      codeJs: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}code_js']),
      codeGo: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}code_go']),
      samples: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}samples']),
      companies: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}companies']),
      templates: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}templates'])!,
    );
  }

  @override
  $ProblemRowsTable createAlias(String alias) {
    return $ProblemRowsTable(attachedDatabase, alias);
  }
}

class ProblemRow extends DataClass implements Insertable<ProblemRow> {
  final int id;
  final String title;
  final String titleCn;
  final String topic;
  final String difficulty;
  final int frequency;
  final String question;
  final String hints;
  final String keyPoints;
  final String structureTags;
  final String approaches;
  final String code;
  final String? acmCode;
  final String? codeCpp;
  final String? acmCodeCpp;
  final String? codeJava;
  final String? codeJs;
  final String? codeGo;
  final String? samples;
  final String? companies;
  final String templates;
  const ProblemRow(
      {required this.id,
      required this.title,
      required this.titleCn,
      required this.topic,
      required this.difficulty,
      required this.frequency,
      required this.question,
      required this.hints,
      required this.keyPoints,
      required this.structureTags,
      required this.approaches,
      required this.code,
      this.acmCode,
      this.codeCpp,
      this.acmCodeCpp,
      this.codeJava,
      this.codeJs,
      this.codeGo,
      this.samples,
      this.companies,
      required this.templates});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['title'] = Variable<String>(title);
    map['title_cn'] = Variable<String>(titleCn);
    map['topic'] = Variable<String>(topic);
    map['difficulty'] = Variable<String>(difficulty);
    map['frequency'] = Variable<int>(frequency);
    map['question'] = Variable<String>(question);
    map['hints'] = Variable<String>(hints);
    map['key_points'] = Variable<String>(keyPoints);
    map['structure_tags'] = Variable<String>(structureTags);
    map['approaches'] = Variable<String>(approaches);
    map['code'] = Variable<String>(code);
    if (!nullToAbsent || acmCode != null) {
      map['acm_code'] = Variable<String>(acmCode);
    }
    if (!nullToAbsent || codeCpp != null) {
      map['code_cpp'] = Variable<String>(codeCpp);
    }
    if (!nullToAbsent || acmCodeCpp != null) {
      map['acm_code_cpp'] = Variable<String>(acmCodeCpp);
    }
    if (!nullToAbsent || codeJava != null) {
      map['code_java'] = Variable<String>(codeJava);
    }
    if (!nullToAbsent || codeJs != null) {
      map['code_js'] = Variable<String>(codeJs);
    }
    if (!nullToAbsent || codeGo != null) {
      map['code_go'] = Variable<String>(codeGo);
    }
    if (!nullToAbsent || samples != null) {
      map['samples'] = Variable<String>(samples);
    }
    if (!nullToAbsent || companies != null) {
      map['companies'] = Variable<String>(companies);
    }
    map['templates'] = Variable<String>(templates);
    return map;
  }

  ProblemRowsCompanion toCompanion(bool nullToAbsent) {
    return ProblemRowsCompanion(
      id: Value(id),
      title: Value(title),
      titleCn: Value(titleCn),
      topic: Value(topic),
      difficulty: Value(difficulty),
      frequency: Value(frequency),
      question: Value(question),
      hints: Value(hints),
      keyPoints: Value(keyPoints),
      structureTags: Value(structureTags),
      approaches: Value(approaches),
      code: Value(code),
      acmCode: acmCode == null && nullToAbsent
          ? const Value.absent()
          : Value(acmCode),
      codeCpp: codeCpp == null && nullToAbsent
          ? const Value.absent()
          : Value(codeCpp),
      acmCodeCpp: acmCodeCpp == null && nullToAbsent
          ? const Value.absent()
          : Value(acmCodeCpp),
      codeJava: codeJava == null && nullToAbsent
          ? const Value.absent()
          : Value(codeJava),
      codeJs:
          codeJs == null && nullToAbsent ? const Value.absent() : Value(codeJs),
      codeGo:
          codeGo == null && nullToAbsent ? const Value.absent() : Value(codeGo),
      samples: samples == null && nullToAbsent
          ? const Value.absent()
          : Value(samples),
      companies: companies == null && nullToAbsent
          ? const Value.absent()
          : Value(companies),
      templates: Value(templates),
    );
  }

  factory ProblemRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ProblemRow(
      id: serializer.fromJson<int>(json['id']),
      title: serializer.fromJson<String>(json['title']),
      titleCn: serializer.fromJson<String>(json['titleCn']),
      topic: serializer.fromJson<String>(json['topic']),
      difficulty: serializer.fromJson<String>(json['difficulty']),
      frequency: serializer.fromJson<int>(json['frequency']),
      question: serializer.fromJson<String>(json['question']),
      hints: serializer.fromJson<String>(json['hints']),
      keyPoints: serializer.fromJson<String>(json['keyPoints']),
      structureTags: serializer.fromJson<String>(json['structureTags']),
      approaches: serializer.fromJson<String>(json['approaches']),
      code: serializer.fromJson<String>(json['code']),
      acmCode: serializer.fromJson<String?>(json['acmCode']),
      codeCpp: serializer.fromJson<String?>(json['codeCpp']),
      acmCodeCpp: serializer.fromJson<String?>(json['acmCodeCpp']),
      codeJava: serializer.fromJson<String?>(json['codeJava']),
      codeJs: serializer.fromJson<String?>(json['codeJs']),
      codeGo: serializer.fromJson<String?>(json['codeGo']),
      samples: serializer.fromJson<String?>(json['samples']),
      companies: serializer.fromJson<String?>(json['companies']),
      templates: serializer.fromJson<String>(json['templates']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'title': serializer.toJson<String>(title),
      'titleCn': serializer.toJson<String>(titleCn),
      'topic': serializer.toJson<String>(topic),
      'difficulty': serializer.toJson<String>(difficulty),
      'frequency': serializer.toJson<int>(frequency),
      'question': serializer.toJson<String>(question),
      'hints': serializer.toJson<String>(hints),
      'keyPoints': serializer.toJson<String>(keyPoints),
      'structureTags': serializer.toJson<String>(structureTags),
      'approaches': serializer.toJson<String>(approaches),
      'code': serializer.toJson<String>(code),
      'acmCode': serializer.toJson<String?>(acmCode),
      'codeCpp': serializer.toJson<String?>(codeCpp),
      'acmCodeCpp': serializer.toJson<String?>(acmCodeCpp),
      'codeJava': serializer.toJson<String?>(codeJava),
      'codeJs': serializer.toJson<String?>(codeJs),
      'codeGo': serializer.toJson<String?>(codeGo),
      'samples': serializer.toJson<String?>(samples),
      'companies': serializer.toJson<String?>(companies),
      'templates': serializer.toJson<String>(templates),
    };
  }

  ProblemRow copyWith(
          {int? id,
          String? title,
          String? titleCn,
          String? topic,
          String? difficulty,
          int? frequency,
          String? question,
          String? hints,
          String? keyPoints,
          String? structureTags,
          String? approaches,
          String? code,
          Value<String?> acmCode = const Value.absent(),
          Value<String?> codeCpp = const Value.absent(),
          Value<String?> acmCodeCpp = const Value.absent(),
          Value<String?> codeJava = const Value.absent(),
          Value<String?> codeJs = const Value.absent(),
          Value<String?> codeGo = const Value.absent(),
          Value<String?> samples = const Value.absent(),
          Value<String?> companies = const Value.absent(),
          String? templates}) =>
      ProblemRow(
        id: id ?? this.id,
        title: title ?? this.title,
        titleCn: titleCn ?? this.titleCn,
        topic: topic ?? this.topic,
        difficulty: difficulty ?? this.difficulty,
        frequency: frequency ?? this.frequency,
        question: question ?? this.question,
        hints: hints ?? this.hints,
        keyPoints: keyPoints ?? this.keyPoints,
        structureTags: structureTags ?? this.structureTags,
        approaches: approaches ?? this.approaches,
        code: code ?? this.code,
        acmCode: acmCode.present ? acmCode.value : this.acmCode,
        codeCpp: codeCpp.present ? codeCpp.value : this.codeCpp,
        acmCodeCpp: acmCodeCpp.present ? acmCodeCpp.value : this.acmCodeCpp,
        codeJava: codeJava.present ? codeJava.value : this.codeJava,
        codeJs: codeJs.present ? codeJs.value : this.codeJs,
        codeGo: codeGo.present ? codeGo.value : this.codeGo,
        samples: samples.present ? samples.value : this.samples,
        companies: companies.present ? companies.value : this.companies,
        templates: templates ?? this.templates,
      );
  ProblemRow copyWithCompanion(ProblemRowsCompanion data) {
    return ProblemRow(
      id: data.id.present ? data.id.value : this.id,
      title: data.title.present ? data.title.value : this.title,
      titleCn: data.titleCn.present ? data.titleCn.value : this.titleCn,
      topic: data.topic.present ? data.topic.value : this.topic,
      difficulty:
          data.difficulty.present ? data.difficulty.value : this.difficulty,
      frequency: data.frequency.present ? data.frequency.value : this.frequency,
      question: data.question.present ? data.question.value : this.question,
      hints: data.hints.present ? data.hints.value : this.hints,
      keyPoints: data.keyPoints.present ? data.keyPoints.value : this.keyPoints,
      structureTags: data.structureTags.present
          ? data.structureTags.value
          : this.structureTags,
      approaches:
          data.approaches.present ? data.approaches.value : this.approaches,
      code: data.code.present ? data.code.value : this.code,
      acmCode: data.acmCode.present ? data.acmCode.value : this.acmCode,
      codeCpp: data.codeCpp.present ? data.codeCpp.value : this.codeCpp,
      acmCodeCpp:
          data.acmCodeCpp.present ? data.acmCodeCpp.value : this.acmCodeCpp,
      codeJava: data.codeJava.present ? data.codeJava.value : this.codeJava,
      codeJs: data.codeJs.present ? data.codeJs.value : this.codeJs,
      codeGo: data.codeGo.present ? data.codeGo.value : this.codeGo,
      samples: data.samples.present ? data.samples.value : this.samples,
      companies: data.companies.present ? data.companies.value : this.companies,
      templates: data.templates.present ? data.templates.value : this.templates,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ProblemRow(')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('titleCn: $titleCn, ')
          ..write('topic: $topic, ')
          ..write('difficulty: $difficulty, ')
          ..write('frequency: $frequency, ')
          ..write('question: $question, ')
          ..write('hints: $hints, ')
          ..write('keyPoints: $keyPoints, ')
          ..write('structureTags: $structureTags, ')
          ..write('approaches: $approaches, ')
          ..write('code: $code, ')
          ..write('acmCode: $acmCode, ')
          ..write('codeCpp: $codeCpp, ')
          ..write('acmCodeCpp: $acmCodeCpp, ')
          ..write('codeJava: $codeJava, ')
          ..write('codeJs: $codeJs, ')
          ..write('codeGo: $codeGo, ')
          ..write('samples: $samples, ')
          ..write('companies: $companies, ')
          ..write('templates: $templates')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hashAll([
        id,
        title,
        titleCn,
        topic,
        difficulty,
        frequency,
        question,
        hints,
        keyPoints,
        structureTags,
        approaches,
        code,
        acmCode,
        codeCpp,
        acmCodeCpp,
        codeJava,
        codeJs,
        codeGo,
        samples,
        companies,
        templates
      ]);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ProblemRow &&
          other.id == this.id &&
          other.title == this.title &&
          other.titleCn == this.titleCn &&
          other.topic == this.topic &&
          other.difficulty == this.difficulty &&
          other.frequency == this.frequency &&
          other.question == this.question &&
          other.hints == this.hints &&
          other.keyPoints == this.keyPoints &&
          other.structureTags == this.structureTags &&
          other.approaches == this.approaches &&
          other.code == this.code &&
          other.acmCode == this.acmCode &&
          other.codeCpp == this.codeCpp &&
          other.acmCodeCpp == this.acmCodeCpp &&
          other.codeJava == this.codeJava &&
          other.codeJs == this.codeJs &&
          other.codeGo == this.codeGo &&
          other.samples == this.samples &&
          other.companies == this.companies &&
          other.templates == this.templates);
}

class ProblemRowsCompanion extends UpdateCompanion<ProblemRow> {
  final Value<int> id;
  final Value<String> title;
  final Value<String> titleCn;
  final Value<String> topic;
  final Value<String> difficulty;
  final Value<int> frequency;
  final Value<String> question;
  final Value<String> hints;
  final Value<String> keyPoints;
  final Value<String> structureTags;
  final Value<String> approaches;
  final Value<String> code;
  final Value<String?> acmCode;
  final Value<String?> codeCpp;
  final Value<String?> acmCodeCpp;
  final Value<String?> codeJava;
  final Value<String?> codeJs;
  final Value<String?> codeGo;
  final Value<String?> samples;
  final Value<String?> companies;
  final Value<String> templates;
  const ProblemRowsCompanion({
    this.id = const Value.absent(),
    this.title = const Value.absent(),
    this.titleCn = const Value.absent(),
    this.topic = const Value.absent(),
    this.difficulty = const Value.absent(),
    this.frequency = const Value.absent(),
    this.question = const Value.absent(),
    this.hints = const Value.absent(),
    this.keyPoints = const Value.absent(),
    this.structureTags = const Value.absent(),
    this.approaches = const Value.absent(),
    this.code = const Value.absent(),
    this.acmCode = const Value.absent(),
    this.codeCpp = const Value.absent(),
    this.acmCodeCpp = const Value.absent(),
    this.codeJava = const Value.absent(),
    this.codeJs = const Value.absent(),
    this.codeGo = const Value.absent(),
    this.samples = const Value.absent(),
    this.companies = const Value.absent(),
    this.templates = const Value.absent(),
  });
  ProblemRowsCompanion.insert({
    this.id = const Value.absent(),
    required String title,
    required String titleCn,
    required String topic,
    required String difficulty,
    required int frequency,
    required String question,
    required String hints,
    required String keyPoints,
    required String structureTags,
    required String approaches,
    required String code,
    this.acmCode = const Value.absent(),
    this.codeCpp = const Value.absent(),
    this.acmCodeCpp = const Value.absent(),
    this.codeJava = const Value.absent(),
    this.codeJs = const Value.absent(),
    this.codeGo = const Value.absent(),
    this.samples = const Value.absent(),
    this.companies = const Value.absent(),
    required String templates,
  })  : title = Value(title),
        titleCn = Value(titleCn),
        topic = Value(topic),
        difficulty = Value(difficulty),
        frequency = Value(frequency),
        question = Value(question),
        hints = Value(hints),
        keyPoints = Value(keyPoints),
        structureTags = Value(structureTags),
        approaches = Value(approaches),
        code = Value(code),
        templates = Value(templates);
  static Insertable<ProblemRow> custom({
    Expression<int>? id,
    Expression<String>? title,
    Expression<String>? titleCn,
    Expression<String>? topic,
    Expression<String>? difficulty,
    Expression<int>? frequency,
    Expression<String>? question,
    Expression<String>? hints,
    Expression<String>? keyPoints,
    Expression<String>? structureTags,
    Expression<String>? approaches,
    Expression<String>? code,
    Expression<String>? acmCode,
    Expression<String>? codeCpp,
    Expression<String>? acmCodeCpp,
    Expression<String>? codeJava,
    Expression<String>? codeJs,
    Expression<String>? codeGo,
    Expression<String>? samples,
    Expression<String>? companies,
    Expression<String>? templates,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (title != null) 'title': title,
      if (titleCn != null) 'title_cn': titleCn,
      if (topic != null) 'topic': topic,
      if (difficulty != null) 'difficulty': difficulty,
      if (frequency != null) 'frequency': frequency,
      if (question != null) 'question': question,
      if (hints != null) 'hints': hints,
      if (keyPoints != null) 'key_points': keyPoints,
      if (structureTags != null) 'structure_tags': structureTags,
      if (approaches != null) 'approaches': approaches,
      if (code != null) 'code': code,
      if (acmCode != null) 'acm_code': acmCode,
      if (codeCpp != null) 'code_cpp': codeCpp,
      if (acmCodeCpp != null) 'acm_code_cpp': acmCodeCpp,
      if (codeJava != null) 'code_java': codeJava,
      if (codeJs != null) 'code_js': codeJs,
      if (codeGo != null) 'code_go': codeGo,
      if (samples != null) 'samples': samples,
      if (companies != null) 'companies': companies,
      if (templates != null) 'templates': templates,
    });
  }

  ProblemRowsCompanion copyWith(
      {Value<int>? id,
      Value<String>? title,
      Value<String>? titleCn,
      Value<String>? topic,
      Value<String>? difficulty,
      Value<int>? frequency,
      Value<String>? question,
      Value<String>? hints,
      Value<String>? keyPoints,
      Value<String>? structureTags,
      Value<String>? approaches,
      Value<String>? code,
      Value<String?>? acmCode,
      Value<String?>? codeCpp,
      Value<String?>? acmCodeCpp,
      Value<String?>? codeJava,
      Value<String?>? codeJs,
      Value<String?>? codeGo,
      Value<String?>? samples,
      Value<String?>? companies,
      Value<String>? templates}) {
    return ProblemRowsCompanion(
      id: id ?? this.id,
      title: title ?? this.title,
      titleCn: titleCn ?? this.titleCn,
      topic: topic ?? this.topic,
      difficulty: difficulty ?? this.difficulty,
      frequency: frequency ?? this.frequency,
      question: question ?? this.question,
      hints: hints ?? this.hints,
      keyPoints: keyPoints ?? this.keyPoints,
      structureTags: structureTags ?? this.structureTags,
      approaches: approaches ?? this.approaches,
      code: code ?? this.code,
      acmCode: acmCode ?? this.acmCode,
      codeCpp: codeCpp ?? this.codeCpp,
      acmCodeCpp: acmCodeCpp ?? this.acmCodeCpp,
      codeJava: codeJava ?? this.codeJava,
      codeJs: codeJs ?? this.codeJs,
      codeGo: codeGo ?? this.codeGo,
      samples: samples ?? this.samples,
      companies: companies ?? this.companies,
      templates: templates ?? this.templates,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (titleCn.present) {
      map['title_cn'] = Variable<String>(titleCn.value);
    }
    if (topic.present) {
      map['topic'] = Variable<String>(topic.value);
    }
    if (difficulty.present) {
      map['difficulty'] = Variable<String>(difficulty.value);
    }
    if (frequency.present) {
      map['frequency'] = Variable<int>(frequency.value);
    }
    if (question.present) {
      map['question'] = Variable<String>(question.value);
    }
    if (hints.present) {
      map['hints'] = Variable<String>(hints.value);
    }
    if (keyPoints.present) {
      map['key_points'] = Variable<String>(keyPoints.value);
    }
    if (structureTags.present) {
      map['structure_tags'] = Variable<String>(structureTags.value);
    }
    if (approaches.present) {
      map['approaches'] = Variable<String>(approaches.value);
    }
    if (code.present) {
      map['code'] = Variable<String>(code.value);
    }
    if (acmCode.present) {
      map['acm_code'] = Variable<String>(acmCode.value);
    }
    if (codeCpp.present) {
      map['code_cpp'] = Variable<String>(codeCpp.value);
    }
    if (acmCodeCpp.present) {
      map['acm_code_cpp'] = Variable<String>(acmCodeCpp.value);
    }
    if (codeJava.present) {
      map['code_java'] = Variable<String>(codeJava.value);
    }
    if (codeJs.present) {
      map['code_js'] = Variable<String>(codeJs.value);
    }
    if (codeGo.present) {
      map['code_go'] = Variable<String>(codeGo.value);
    }
    if (samples.present) {
      map['samples'] = Variable<String>(samples.value);
    }
    if (companies.present) {
      map['companies'] = Variable<String>(companies.value);
    }
    if (templates.present) {
      map['templates'] = Variable<String>(templates.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ProblemRowsCompanion(')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('titleCn: $titleCn, ')
          ..write('topic: $topic, ')
          ..write('difficulty: $difficulty, ')
          ..write('frequency: $frequency, ')
          ..write('question: $question, ')
          ..write('hints: $hints, ')
          ..write('keyPoints: $keyPoints, ')
          ..write('structureTags: $structureTags, ')
          ..write('approaches: $approaches, ')
          ..write('code: $code, ')
          ..write('acmCode: $acmCode, ')
          ..write('codeCpp: $codeCpp, ')
          ..write('acmCodeCpp: $acmCodeCpp, ')
          ..write('codeJava: $codeJava, ')
          ..write('codeJs: $codeJs, ')
          ..write('codeGo: $codeGo, ')
          ..write('samples: $samples, ')
          ..write('companies: $companies, ')
          ..write('templates: $templates')
          ..write(')'))
        .toString();
  }
}

class $MetaTable extends Meta with TableInfo<$MetaTable, MetaData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $MetaTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _keyMeta = const VerificationMeta('key');
  @override
  late final GeneratedColumn<String> key = GeneratedColumn<String>(
      'key', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _valueMeta = const VerificationMeta('value');
  @override
  late final GeneratedColumn<String> value = GeneratedColumn<String>(
      'value', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  @override
  List<GeneratedColumn> get $columns => [key, value];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'meta';
  @override
  VerificationContext validateIntegrity(Insertable<MetaData> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('key')) {
      context.handle(
          _keyMeta, key.isAcceptableOrUnknown(data['key']!, _keyMeta));
    } else if (isInserting) {
      context.missing(_keyMeta);
    }
    if (data.containsKey('value')) {
      context.handle(
          _valueMeta, value.isAcceptableOrUnknown(data['value']!, _valueMeta));
    } else if (isInserting) {
      context.missing(_valueMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  MetaData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return MetaData(
      key: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}key'])!,
      value: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}value'])!,
    );
  }

  @override
  $MetaTable createAlias(String alias) {
    return $MetaTable(attachedDatabase, alias);
  }
}

class MetaData extends DataClass implements Insertable<MetaData> {
  final String key;
  final String value;
  const MetaData({required this.key, required this.value});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['key'] = Variable<String>(key);
    map['value'] = Variable<String>(value);
    return map;
  }

  MetaCompanion toCompanion(bool nullToAbsent) {
    return MetaCompanion(
      key: Value(key),
      value: Value(value),
    );
  }

  factory MetaData.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return MetaData(
      key: serializer.fromJson<String>(json['key']),
      value: serializer.fromJson<String>(json['value']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'key': serializer.toJson<String>(key),
      'value': serializer.toJson<String>(value),
    };
  }

  MetaData copyWith({String? key, String? value}) => MetaData(
        key: key ?? this.key,
        value: value ?? this.value,
      );
  MetaData copyWithCompanion(MetaCompanion data) {
    return MetaData(
      key: data.key.present ? data.key.value : this.key,
      value: data.value.present ? data.value.value : this.value,
    );
  }

  @override
  String toString() {
    return (StringBuffer('MetaData(')
          ..write('key: $key, ')
          ..write('value: $value')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(key, value);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is MetaData && other.key == this.key && other.value == this.value);
}

class MetaCompanion extends UpdateCompanion<MetaData> {
  final Value<String> key;
  final Value<String> value;
  final Value<int> rowid;
  const MetaCompanion({
    this.key = const Value.absent(),
    this.value = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  MetaCompanion.insert({
    required String key,
    required String value,
    this.rowid = const Value.absent(),
  })  : key = Value(key),
        value = Value(value);
  static Insertable<MetaData> custom({
    Expression<String>? key,
    Expression<String>? value,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (key != null) 'key': key,
      if (value != null) 'value': value,
      if (rowid != null) 'rowid': rowid,
    });
  }

  MetaCompanion copyWith(
      {Value<String>? key, Value<String>? value, Value<int>? rowid}) {
    return MetaCompanion(
      key: key ?? this.key,
      value: value ?? this.value,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) {
      map['key'] = Variable<String>(key.value);
    }
    if (value.present) {
      map['value'] = Variable<String>(value.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('MetaCompanion(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $ProgressRowsTable extends ProgressRows
    with TableInfo<$ProgressRowsTable, ProgressRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ProgressRowsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _problemIdMeta =
      const VerificationMeta('problemId');
  @override
  late final GeneratedColumn<int> problemId = GeneratedColumn<int>(
      'problem_id', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: false);
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<int> status = GeneratedColumn<int>(
      'status', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _easinessMeta =
      const VerificationMeta('easiness');
  @override
  late final GeneratedColumn<double> easiness = GeneratedColumn<double>(
      'easiness', aliasedName, false,
      type: DriftSqlType.double, requiredDuringInsert: true);
  static const VerificationMeta _intervalDaysMeta =
      const VerificationMeta('intervalDays');
  @override
  late final GeneratedColumn<int> intervalDays = GeneratedColumn<int>(
      'interval_days', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _repsMeta = const VerificationMeta('reps');
  @override
  late final GeneratedColumn<int> reps = GeneratedColumn<int>(
      'reps', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _lapsesMeta = const VerificationMeta('lapses');
  @override
  late final GeneratedColumn<int> lapses = GeneratedColumn<int>(
      'lapses', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _dueAtMeta = const VerificationMeta('dueAt');
  @override
  late final GeneratedColumn<DateTime> dueAt = GeneratedColumn<DateTime>(
      'due_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  static const VerificationMeta _lastStudiedAtMeta =
      const VerificationMeta('lastStudiedAt');
  @override
  late final GeneratedColumn<DateTime> lastStudiedAt =
      GeneratedColumn<DateTime>('last_studied_at', aliasedName, true,
          type: DriftSqlType.dateTime, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns => [
        problemId,
        status,
        easiness,
        intervalDays,
        reps,
        lapses,
        dueAt,
        lastStudiedAt
      ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'progress_rows';
  @override
  VerificationContext validateIntegrity(Insertable<ProgressRow> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('problem_id')) {
      context.handle(_problemIdMeta,
          problemId.isAcceptableOrUnknown(data['problem_id']!, _problemIdMeta));
    }
    if (data.containsKey('status')) {
      context.handle(_statusMeta,
          status.isAcceptableOrUnknown(data['status']!, _statusMeta));
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('easiness')) {
      context.handle(_easinessMeta,
          easiness.isAcceptableOrUnknown(data['easiness']!, _easinessMeta));
    } else if (isInserting) {
      context.missing(_easinessMeta);
    }
    if (data.containsKey('interval_days')) {
      context.handle(
          _intervalDaysMeta,
          intervalDays.isAcceptableOrUnknown(
              data['interval_days']!, _intervalDaysMeta));
    } else if (isInserting) {
      context.missing(_intervalDaysMeta);
    }
    if (data.containsKey('reps')) {
      context.handle(
          _repsMeta, reps.isAcceptableOrUnknown(data['reps']!, _repsMeta));
    } else if (isInserting) {
      context.missing(_repsMeta);
    }
    if (data.containsKey('lapses')) {
      context.handle(_lapsesMeta,
          lapses.isAcceptableOrUnknown(data['lapses']!, _lapsesMeta));
    } else if (isInserting) {
      context.missing(_lapsesMeta);
    }
    if (data.containsKey('due_at')) {
      context.handle(
          _dueAtMeta, dueAt.isAcceptableOrUnknown(data['due_at']!, _dueAtMeta));
    }
    if (data.containsKey('last_studied_at')) {
      context.handle(
          _lastStudiedAtMeta,
          lastStudiedAt.isAcceptableOrUnknown(
              data['last_studied_at']!, _lastStudiedAtMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {problemId};
  @override
  ProgressRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ProgressRow(
      problemId: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}problem_id'])!,
      status: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}status'])!,
      easiness: attachedDatabase.typeMapping
          .read(DriftSqlType.double, data['${effectivePrefix}easiness'])!,
      intervalDays: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}interval_days'])!,
      reps: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}reps'])!,
      lapses: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}lapses'])!,
      dueAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}due_at']),
      lastStudiedAt: attachedDatabase.typeMapping.read(
          DriftSqlType.dateTime, data['${effectivePrefix}last_studied_at']),
    );
  }

  @override
  $ProgressRowsTable createAlias(String alias) {
    return $ProgressRowsTable(attachedDatabase, alias);
  }
}

class ProgressRow extends DataClass implements Insertable<ProgressRow> {
  final int problemId;
  final int status;
  final double easiness;
  final int intervalDays;
  final int reps;
  final int lapses;
  final DateTime? dueAt;
  final DateTime? lastStudiedAt;
  const ProgressRow(
      {required this.problemId,
      required this.status,
      required this.easiness,
      required this.intervalDays,
      required this.reps,
      required this.lapses,
      this.dueAt,
      this.lastStudiedAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['problem_id'] = Variable<int>(problemId);
    map['status'] = Variable<int>(status);
    map['easiness'] = Variable<double>(easiness);
    map['interval_days'] = Variable<int>(intervalDays);
    map['reps'] = Variable<int>(reps);
    map['lapses'] = Variable<int>(lapses);
    if (!nullToAbsent || dueAt != null) {
      map['due_at'] = Variable<DateTime>(dueAt);
    }
    if (!nullToAbsent || lastStudiedAt != null) {
      map['last_studied_at'] = Variable<DateTime>(lastStudiedAt);
    }
    return map;
  }

  ProgressRowsCompanion toCompanion(bool nullToAbsent) {
    return ProgressRowsCompanion(
      problemId: Value(problemId),
      status: Value(status),
      easiness: Value(easiness),
      intervalDays: Value(intervalDays),
      reps: Value(reps),
      lapses: Value(lapses),
      dueAt:
          dueAt == null && nullToAbsent ? const Value.absent() : Value(dueAt),
      lastStudiedAt: lastStudiedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(lastStudiedAt),
    );
  }

  factory ProgressRow.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ProgressRow(
      problemId: serializer.fromJson<int>(json['problemId']),
      status: serializer.fromJson<int>(json['status']),
      easiness: serializer.fromJson<double>(json['easiness']),
      intervalDays: serializer.fromJson<int>(json['intervalDays']),
      reps: serializer.fromJson<int>(json['reps']),
      lapses: serializer.fromJson<int>(json['lapses']),
      dueAt: serializer.fromJson<DateTime?>(json['dueAt']),
      lastStudiedAt: serializer.fromJson<DateTime?>(json['lastStudiedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'problemId': serializer.toJson<int>(problemId),
      'status': serializer.toJson<int>(status),
      'easiness': serializer.toJson<double>(easiness),
      'intervalDays': serializer.toJson<int>(intervalDays),
      'reps': serializer.toJson<int>(reps),
      'lapses': serializer.toJson<int>(lapses),
      'dueAt': serializer.toJson<DateTime?>(dueAt),
      'lastStudiedAt': serializer.toJson<DateTime?>(lastStudiedAt),
    };
  }

  ProgressRow copyWith(
          {int? problemId,
          int? status,
          double? easiness,
          int? intervalDays,
          int? reps,
          int? lapses,
          Value<DateTime?> dueAt = const Value.absent(),
          Value<DateTime?> lastStudiedAt = const Value.absent()}) =>
      ProgressRow(
        problemId: problemId ?? this.problemId,
        status: status ?? this.status,
        easiness: easiness ?? this.easiness,
        intervalDays: intervalDays ?? this.intervalDays,
        reps: reps ?? this.reps,
        lapses: lapses ?? this.lapses,
        dueAt: dueAt.present ? dueAt.value : this.dueAt,
        lastStudiedAt:
            lastStudiedAt.present ? lastStudiedAt.value : this.lastStudiedAt,
      );
  ProgressRow copyWithCompanion(ProgressRowsCompanion data) {
    return ProgressRow(
      problemId: data.problemId.present ? data.problemId.value : this.problemId,
      status: data.status.present ? data.status.value : this.status,
      easiness: data.easiness.present ? data.easiness.value : this.easiness,
      intervalDays: data.intervalDays.present
          ? data.intervalDays.value
          : this.intervalDays,
      reps: data.reps.present ? data.reps.value : this.reps,
      lapses: data.lapses.present ? data.lapses.value : this.lapses,
      dueAt: data.dueAt.present ? data.dueAt.value : this.dueAt,
      lastStudiedAt: data.lastStudiedAt.present
          ? data.lastStudiedAt.value
          : this.lastStudiedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ProgressRow(')
          ..write('problemId: $problemId, ')
          ..write('status: $status, ')
          ..write('easiness: $easiness, ')
          ..write('intervalDays: $intervalDays, ')
          ..write('reps: $reps, ')
          ..write('lapses: $lapses, ')
          ..write('dueAt: $dueAt, ')
          ..write('lastStudiedAt: $lastStudiedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(problemId, status, easiness, intervalDays,
      reps, lapses, dueAt, lastStudiedAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ProgressRow &&
          other.problemId == this.problemId &&
          other.status == this.status &&
          other.easiness == this.easiness &&
          other.intervalDays == this.intervalDays &&
          other.reps == this.reps &&
          other.lapses == this.lapses &&
          other.dueAt == this.dueAt &&
          other.lastStudiedAt == this.lastStudiedAt);
}

class ProgressRowsCompanion extends UpdateCompanion<ProgressRow> {
  final Value<int> problemId;
  final Value<int> status;
  final Value<double> easiness;
  final Value<int> intervalDays;
  final Value<int> reps;
  final Value<int> lapses;
  final Value<DateTime?> dueAt;
  final Value<DateTime?> lastStudiedAt;
  const ProgressRowsCompanion({
    this.problemId = const Value.absent(),
    this.status = const Value.absent(),
    this.easiness = const Value.absent(),
    this.intervalDays = const Value.absent(),
    this.reps = const Value.absent(),
    this.lapses = const Value.absent(),
    this.dueAt = const Value.absent(),
    this.lastStudiedAt = const Value.absent(),
  });
  ProgressRowsCompanion.insert({
    this.problemId = const Value.absent(),
    required int status,
    required double easiness,
    required int intervalDays,
    required int reps,
    required int lapses,
    this.dueAt = const Value.absent(),
    this.lastStudiedAt = const Value.absent(),
  })  : status = Value(status),
        easiness = Value(easiness),
        intervalDays = Value(intervalDays),
        reps = Value(reps),
        lapses = Value(lapses);
  static Insertable<ProgressRow> custom({
    Expression<int>? problemId,
    Expression<int>? status,
    Expression<double>? easiness,
    Expression<int>? intervalDays,
    Expression<int>? reps,
    Expression<int>? lapses,
    Expression<DateTime>? dueAt,
    Expression<DateTime>? lastStudiedAt,
  }) {
    return RawValuesInsertable({
      if (problemId != null) 'problem_id': problemId,
      if (status != null) 'status': status,
      if (easiness != null) 'easiness': easiness,
      if (intervalDays != null) 'interval_days': intervalDays,
      if (reps != null) 'reps': reps,
      if (lapses != null) 'lapses': lapses,
      if (dueAt != null) 'due_at': dueAt,
      if (lastStudiedAt != null) 'last_studied_at': lastStudiedAt,
    });
  }

  ProgressRowsCompanion copyWith(
      {Value<int>? problemId,
      Value<int>? status,
      Value<double>? easiness,
      Value<int>? intervalDays,
      Value<int>? reps,
      Value<int>? lapses,
      Value<DateTime?>? dueAt,
      Value<DateTime?>? lastStudiedAt}) {
    return ProgressRowsCompanion(
      problemId: problemId ?? this.problemId,
      status: status ?? this.status,
      easiness: easiness ?? this.easiness,
      intervalDays: intervalDays ?? this.intervalDays,
      reps: reps ?? this.reps,
      lapses: lapses ?? this.lapses,
      dueAt: dueAt ?? this.dueAt,
      lastStudiedAt: lastStudiedAt ?? this.lastStudiedAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (problemId.present) {
      map['problem_id'] = Variable<int>(problemId.value);
    }
    if (status.present) {
      map['status'] = Variable<int>(status.value);
    }
    if (easiness.present) {
      map['easiness'] = Variable<double>(easiness.value);
    }
    if (intervalDays.present) {
      map['interval_days'] = Variable<int>(intervalDays.value);
    }
    if (reps.present) {
      map['reps'] = Variable<int>(reps.value);
    }
    if (lapses.present) {
      map['lapses'] = Variable<int>(lapses.value);
    }
    if (dueAt.present) {
      map['due_at'] = Variable<DateTime>(dueAt.value);
    }
    if (lastStudiedAt.present) {
      map['last_studied_at'] = Variable<DateTime>(lastStudiedAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ProgressRowsCompanion(')
          ..write('problemId: $problemId, ')
          ..write('status: $status, ')
          ..write('easiness: $easiness, ')
          ..write('intervalDays: $intervalDays, ')
          ..write('reps: $reps, ')
          ..write('lapses: $lapses, ')
          ..write('dueAt: $dueAt, ')
          ..write('lastStudiedAt: $lastStudiedAt')
          ..write(')'))
        .toString();
  }
}

class $ReviewLogsTable extends ReviewLogs
    with TableInfo<$ReviewLogsTable, ReviewLog> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ReviewLogsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
      'id', aliasedName, false,
      hasAutoIncrement: true,
      type: DriftSqlType.int,
      requiredDuringInsert: false,
      defaultConstraints:
          GeneratedColumn.constraintIsAlways('PRIMARY KEY AUTOINCREMENT'));
  static const VerificationMeta _problemIdMeta =
      const VerificationMeta('problemId');
  @override
  late final GeneratedColumn<int> problemId = GeneratedColumn<int>(
      'problem_id', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _kindMeta = const VerificationMeta('kind');
  @override
  late final GeneratedColumn<int> kind = GeneratedColumn<int>(
      'kind', aliasedName, false,
      type: DriftSqlType.int, requiredDuringInsert: true);
  static const VerificationMeta _scoreMeta = const VerificationMeta('score');
  @override
  late final GeneratedColumn<double> score = GeneratedColumn<double>(
      'score', aliasedName, false,
      type: DriftSqlType.double, requiredDuringInsert: true);
  static const VerificationMeta _detailMeta = const VerificationMeta('detail');
  @override
  late final GeneratedColumn<String> detail = GeneratedColumn<String>(
      'detail', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _hitKeyPointsMeta =
      const VerificationMeta('hitKeyPoints');
  @override
  late final GeneratedColumn<String> hitKeyPoints = GeneratedColumn<String>(
      'hit_key_points', aliasedName, false,
      type: DriftSqlType.string, requiredDuringInsert: true);
  static const VerificationMeta _createdAtMeta =
      const VerificationMeta('createdAt');
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
      'created_at', aliasedName, true,
      type: DriftSqlType.dateTime, requiredDuringInsert: false);
  @override
  List<GeneratedColumn> get $columns =>
      [id, problemId, kind, score, detail, hitKeyPoints, createdAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'review_logs';
  @override
  VerificationContext validateIntegrity(Insertable<ReviewLog> instance,
      {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('problem_id')) {
      context.handle(_problemIdMeta,
          problemId.isAcceptableOrUnknown(data['problem_id']!, _problemIdMeta));
    } else if (isInserting) {
      context.missing(_problemIdMeta);
    }
    if (data.containsKey('kind')) {
      context.handle(
          _kindMeta, kind.isAcceptableOrUnknown(data['kind']!, _kindMeta));
    } else if (isInserting) {
      context.missing(_kindMeta);
    }
    if (data.containsKey('score')) {
      context.handle(
          _scoreMeta, score.isAcceptableOrUnknown(data['score']!, _scoreMeta));
    } else if (isInserting) {
      context.missing(_scoreMeta);
    }
    if (data.containsKey('detail')) {
      context.handle(_detailMeta,
          detail.isAcceptableOrUnknown(data['detail']!, _detailMeta));
    } else if (isInserting) {
      context.missing(_detailMeta);
    }
    if (data.containsKey('hit_key_points')) {
      context.handle(
          _hitKeyPointsMeta,
          hitKeyPoints.isAcceptableOrUnknown(
              data['hit_key_points']!, _hitKeyPointsMeta));
    } else if (isInserting) {
      context.missing(_hitKeyPointsMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(_createdAtMeta,
          createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta));
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  ReviewLog map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ReviewLog(
      id: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}id'])!,
      problemId: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}problem_id'])!,
      kind: attachedDatabase.typeMapping
          .read(DriftSqlType.int, data['${effectivePrefix}kind'])!,
      score: attachedDatabase.typeMapping
          .read(DriftSqlType.double, data['${effectivePrefix}score'])!,
      detail: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}detail'])!,
      hitKeyPoints: attachedDatabase.typeMapping
          .read(DriftSqlType.string, data['${effectivePrefix}hit_key_points'])!,
      createdAt: attachedDatabase.typeMapping
          .read(DriftSqlType.dateTime, data['${effectivePrefix}created_at']),
    );
  }

  @override
  $ReviewLogsTable createAlias(String alias) {
    return $ReviewLogsTable(attachedDatabase, alias);
  }
}

class ReviewLog extends DataClass implements Insertable<ReviewLog> {
  final int id;
  final int problemId;
  final int kind;
  final double score;
  final String detail;
  final String hitKeyPoints;
  final DateTime? createdAt;
  const ReviewLog(
      {required this.id,
      required this.problemId,
      required this.kind,
      required this.score,
      required this.detail,
      required this.hitKeyPoints,
      this.createdAt});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['problem_id'] = Variable<int>(problemId);
    map['kind'] = Variable<int>(kind);
    map['score'] = Variable<double>(score);
    map['detail'] = Variable<String>(detail);
    map['hit_key_points'] = Variable<String>(hitKeyPoints);
    if (!nullToAbsent || createdAt != null) {
      map['created_at'] = Variable<DateTime>(createdAt);
    }
    return map;
  }

  ReviewLogsCompanion toCompanion(bool nullToAbsent) {
    return ReviewLogsCompanion(
      id: Value(id),
      problemId: Value(problemId),
      kind: Value(kind),
      score: Value(score),
      detail: Value(detail),
      hitKeyPoints: Value(hitKeyPoints),
      createdAt: createdAt == null && nullToAbsent
          ? const Value.absent()
          : Value(createdAt),
    );
  }

  factory ReviewLog.fromJson(Map<String, dynamic> json,
      {ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ReviewLog(
      id: serializer.fromJson<int>(json['id']),
      problemId: serializer.fromJson<int>(json['problemId']),
      kind: serializer.fromJson<int>(json['kind']),
      score: serializer.fromJson<double>(json['score']),
      detail: serializer.fromJson<String>(json['detail']),
      hitKeyPoints: serializer.fromJson<String>(json['hitKeyPoints']),
      createdAt: serializer.fromJson<DateTime?>(json['createdAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'problemId': serializer.toJson<int>(problemId),
      'kind': serializer.toJson<int>(kind),
      'score': serializer.toJson<double>(score),
      'detail': serializer.toJson<String>(detail),
      'hitKeyPoints': serializer.toJson<String>(hitKeyPoints),
      'createdAt': serializer.toJson<DateTime?>(createdAt),
    };
  }

  ReviewLog copyWith(
          {int? id,
          int? problemId,
          int? kind,
          double? score,
          String? detail,
          String? hitKeyPoints,
          Value<DateTime?> createdAt = const Value.absent()}) =>
      ReviewLog(
        id: id ?? this.id,
        problemId: problemId ?? this.problemId,
        kind: kind ?? this.kind,
        score: score ?? this.score,
        detail: detail ?? this.detail,
        hitKeyPoints: hitKeyPoints ?? this.hitKeyPoints,
        createdAt: createdAt.present ? createdAt.value : this.createdAt,
      );
  ReviewLog copyWithCompanion(ReviewLogsCompanion data) {
    return ReviewLog(
      id: data.id.present ? data.id.value : this.id,
      problemId: data.problemId.present ? data.problemId.value : this.problemId,
      kind: data.kind.present ? data.kind.value : this.kind,
      score: data.score.present ? data.score.value : this.score,
      detail: data.detail.present ? data.detail.value : this.detail,
      hitKeyPoints: data.hitKeyPoints.present
          ? data.hitKeyPoints.value
          : this.hitKeyPoints,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ReviewLog(')
          ..write('id: $id, ')
          ..write('problemId: $problemId, ')
          ..write('kind: $kind, ')
          ..write('score: $score, ')
          ..write('detail: $detail, ')
          ..write('hitKeyPoints: $hitKeyPoints, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, problemId, kind, score, detail, hitKeyPoints, createdAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ReviewLog &&
          other.id == this.id &&
          other.problemId == this.problemId &&
          other.kind == this.kind &&
          other.score == this.score &&
          other.detail == this.detail &&
          other.hitKeyPoints == this.hitKeyPoints &&
          other.createdAt == this.createdAt);
}

class ReviewLogsCompanion extends UpdateCompanion<ReviewLog> {
  final Value<int> id;
  final Value<int> problemId;
  final Value<int> kind;
  final Value<double> score;
  final Value<String> detail;
  final Value<String> hitKeyPoints;
  final Value<DateTime?> createdAt;
  const ReviewLogsCompanion({
    this.id = const Value.absent(),
    this.problemId = const Value.absent(),
    this.kind = const Value.absent(),
    this.score = const Value.absent(),
    this.detail = const Value.absent(),
    this.hitKeyPoints = const Value.absent(),
    this.createdAt = const Value.absent(),
  });
  ReviewLogsCompanion.insert({
    this.id = const Value.absent(),
    required int problemId,
    required int kind,
    required double score,
    required String detail,
    required String hitKeyPoints,
    this.createdAt = const Value.absent(),
  })  : problemId = Value(problemId),
        kind = Value(kind),
        score = Value(score),
        detail = Value(detail),
        hitKeyPoints = Value(hitKeyPoints);
  static Insertable<ReviewLog> custom({
    Expression<int>? id,
    Expression<int>? problemId,
    Expression<int>? kind,
    Expression<double>? score,
    Expression<String>? detail,
    Expression<String>? hitKeyPoints,
    Expression<DateTime>? createdAt,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (problemId != null) 'problem_id': problemId,
      if (kind != null) 'kind': kind,
      if (score != null) 'score': score,
      if (detail != null) 'detail': detail,
      if (hitKeyPoints != null) 'hit_key_points': hitKeyPoints,
      if (createdAt != null) 'created_at': createdAt,
    });
  }

  ReviewLogsCompanion copyWith(
      {Value<int>? id,
      Value<int>? problemId,
      Value<int>? kind,
      Value<double>? score,
      Value<String>? detail,
      Value<String>? hitKeyPoints,
      Value<DateTime?>? createdAt}) {
    return ReviewLogsCompanion(
      id: id ?? this.id,
      problemId: problemId ?? this.problemId,
      kind: kind ?? this.kind,
      score: score ?? this.score,
      detail: detail ?? this.detail,
      hitKeyPoints: hitKeyPoints ?? this.hitKeyPoints,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (problemId.present) {
      map['problem_id'] = Variable<int>(problemId.value);
    }
    if (kind.present) {
      map['kind'] = Variable<int>(kind.value);
    }
    if (score.present) {
      map['score'] = Variable<double>(score.value);
    }
    if (detail.present) {
      map['detail'] = Variable<String>(detail.value);
    }
    if (hitKeyPoints.present) {
      map['hit_key_points'] = Variable<String>(hitKeyPoints.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ReviewLogsCompanion(')
          ..write('id: $id, ')
          ..write('problemId: $problemId, ')
          ..write('kind: $kind, ')
          ..write('score: $score, ')
          ..write('detail: $detail, ')
          ..write('hitKeyPoints: $hitKeyPoints, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $ProblemRowsTable problemRows = $ProblemRowsTable(this);
  late final $MetaTable meta = $MetaTable(this);
  late final $ProgressRowsTable progressRows = $ProgressRowsTable(this);
  late final $ReviewLogsTable reviewLogs = $ReviewLogsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities =>
      [problemRows, meta, progressRows, reviewLogs];
}

typedef $$ProblemRowsTableCreateCompanionBuilder = ProblemRowsCompanion
    Function({
  Value<int> id,
  required String title,
  required String titleCn,
  required String topic,
  required String difficulty,
  required int frequency,
  required String question,
  required String hints,
  required String keyPoints,
  required String structureTags,
  required String approaches,
  required String code,
  Value<String?> acmCode,
  Value<String?> codeCpp,
  Value<String?> acmCodeCpp,
  Value<String?> codeJava,
  Value<String?> codeJs,
  Value<String?> codeGo,
  Value<String?> samples,
  Value<String?> companies,
  required String templates,
});
typedef $$ProblemRowsTableUpdateCompanionBuilder = ProblemRowsCompanion
    Function({
  Value<int> id,
  Value<String> title,
  Value<String> titleCn,
  Value<String> topic,
  Value<String> difficulty,
  Value<int> frequency,
  Value<String> question,
  Value<String> hints,
  Value<String> keyPoints,
  Value<String> structureTags,
  Value<String> approaches,
  Value<String> code,
  Value<String?> acmCode,
  Value<String?> codeCpp,
  Value<String?> acmCodeCpp,
  Value<String?> codeJava,
  Value<String?> codeJs,
  Value<String?> codeGo,
  Value<String?> samples,
  Value<String?> companies,
  Value<String> templates,
});

class $$ProblemRowsTableFilterComposer
    extends Composer<_$AppDatabase, $ProblemRowsTable> {
  $$ProblemRowsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get titleCn => $composableBuilder(
      column: $table.titleCn, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get topic => $composableBuilder(
      column: $table.topic, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get difficulty => $composableBuilder(
      column: $table.difficulty, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get frequency => $composableBuilder(
      column: $table.frequency, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get question => $composableBuilder(
      column: $table.question, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get hints => $composableBuilder(
      column: $table.hints, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get keyPoints => $composableBuilder(
      column: $table.keyPoints, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get structureTags => $composableBuilder(
      column: $table.structureTags, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get approaches => $composableBuilder(
      column: $table.approaches, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get code => $composableBuilder(
      column: $table.code, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get acmCode => $composableBuilder(
      column: $table.acmCode, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get codeCpp => $composableBuilder(
      column: $table.codeCpp, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get acmCodeCpp => $composableBuilder(
      column: $table.acmCodeCpp, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get codeJava => $composableBuilder(
      column: $table.codeJava, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get codeJs => $composableBuilder(
      column: $table.codeJs, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get codeGo => $composableBuilder(
      column: $table.codeGo, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get samples => $composableBuilder(
      column: $table.samples, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get companies => $composableBuilder(
      column: $table.companies, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get templates => $composableBuilder(
      column: $table.templates, builder: (column) => ColumnFilters(column));
}

class $$ProblemRowsTableOrderingComposer
    extends Composer<_$AppDatabase, $ProblemRowsTable> {
  $$ProblemRowsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get title => $composableBuilder(
      column: $table.title, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get titleCn => $composableBuilder(
      column: $table.titleCn, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get topic => $composableBuilder(
      column: $table.topic, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get difficulty => $composableBuilder(
      column: $table.difficulty, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get frequency => $composableBuilder(
      column: $table.frequency, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get question => $composableBuilder(
      column: $table.question, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get hints => $composableBuilder(
      column: $table.hints, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get keyPoints => $composableBuilder(
      column: $table.keyPoints, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get structureTags => $composableBuilder(
      column: $table.structureTags,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get approaches => $composableBuilder(
      column: $table.approaches, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get code => $composableBuilder(
      column: $table.code, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get acmCode => $composableBuilder(
      column: $table.acmCode, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get codeCpp => $composableBuilder(
      column: $table.codeCpp, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get acmCodeCpp => $composableBuilder(
      column: $table.acmCodeCpp, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get codeJava => $composableBuilder(
      column: $table.codeJava, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get codeJs => $composableBuilder(
      column: $table.codeJs, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get codeGo => $composableBuilder(
      column: $table.codeGo, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get samples => $composableBuilder(
      column: $table.samples, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get companies => $composableBuilder(
      column: $table.companies, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get templates => $composableBuilder(
      column: $table.templates, builder: (column) => ColumnOrderings(column));
}

class $$ProblemRowsTableAnnotationComposer
    extends Composer<_$AppDatabase, $ProblemRowsTable> {
  $$ProblemRowsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<String> get titleCn =>
      $composableBuilder(column: $table.titleCn, builder: (column) => column);

  GeneratedColumn<String> get topic =>
      $composableBuilder(column: $table.topic, builder: (column) => column);

  GeneratedColumn<String> get difficulty => $composableBuilder(
      column: $table.difficulty, builder: (column) => column);

  GeneratedColumn<int> get frequency =>
      $composableBuilder(column: $table.frequency, builder: (column) => column);

  GeneratedColumn<String> get question =>
      $composableBuilder(column: $table.question, builder: (column) => column);

  GeneratedColumn<String> get hints =>
      $composableBuilder(column: $table.hints, builder: (column) => column);

  GeneratedColumn<String> get keyPoints =>
      $composableBuilder(column: $table.keyPoints, builder: (column) => column);

  GeneratedColumn<String> get structureTags => $composableBuilder(
      column: $table.structureTags, builder: (column) => column);

  GeneratedColumn<String> get approaches => $composableBuilder(
      column: $table.approaches, builder: (column) => column);

  GeneratedColumn<String> get code =>
      $composableBuilder(column: $table.code, builder: (column) => column);

  GeneratedColumn<String> get acmCode =>
      $composableBuilder(column: $table.acmCode, builder: (column) => column);

  GeneratedColumn<String> get codeCpp =>
      $composableBuilder(column: $table.codeCpp, builder: (column) => column);

  GeneratedColumn<String> get acmCodeCpp => $composableBuilder(
      column: $table.acmCodeCpp, builder: (column) => column);

  GeneratedColumn<String> get codeJava =>
      $composableBuilder(column: $table.codeJava, builder: (column) => column);

  GeneratedColumn<String> get codeJs =>
      $composableBuilder(column: $table.codeJs, builder: (column) => column);

  GeneratedColumn<String> get codeGo =>
      $composableBuilder(column: $table.codeGo, builder: (column) => column);

  GeneratedColumn<String> get samples =>
      $composableBuilder(column: $table.samples, builder: (column) => column);

  GeneratedColumn<String> get companies =>
      $composableBuilder(column: $table.companies, builder: (column) => column);

  GeneratedColumn<String> get templates =>
      $composableBuilder(column: $table.templates, builder: (column) => column);
}

class $$ProblemRowsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $ProblemRowsTable,
    ProblemRow,
    $$ProblemRowsTableFilterComposer,
    $$ProblemRowsTableOrderingComposer,
    $$ProblemRowsTableAnnotationComposer,
    $$ProblemRowsTableCreateCompanionBuilder,
    $$ProblemRowsTableUpdateCompanionBuilder,
    (ProblemRow, BaseReferences<_$AppDatabase, $ProblemRowsTable, ProblemRow>),
    ProblemRow,
    PrefetchHooks Function()> {
  $$ProblemRowsTableTableManager(_$AppDatabase db, $ProblemRowsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ProblemRowsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ProblemRowsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ProblemRowsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<String> title = const Value.absent(),
            Value<String> titleCn = const Value.absent(),
            Value<String> topic = const Value.absent(),
            Value<String> difficulty = const Value.absent(),
            Value<int> frequency = const Value.absent(),
            Value<String> question = const Value.absent(),
            Value<String> hints = const Value.absent(),
            Value<String> keyPoints = const Value.absent(),
            Value<String> structureTags = const Value.absent(),
            Value<String> approaches = const Value.absent(),
            Value<String> code = const Value.absent(),
            Value<String?> acmCode = const Value.absent(),
            Value<String?> codeCpp = const Value.absent(),
            Value<String?> acmCodeCpp = const Value.absent(),
            Value<String?> codeJava = const Value.absent(),
            Value<String?> codeJs = const Value.absent(),
            Value<String?> codeGo = const Value.absent(),
            Value<String?> samples = const Value.absent(),
            Value<String?> companies = const Value.absent(),
            Value<String> templates = const Value.absent(),
          }) =>
              ProblemRowsCompanion(
            id: id,
            title: title,
            titleCn: titleCn,
            topic: topic,
            difficulty: difficulty,
            frequency: frequency,
            question: question,
            hints: hints,
            keyPoints: keyPoints,
            structureTags: structureTags,
            approaches: approaches,
            code: code,
            acmCode: acmCode,
            codeCpp: codeCpp,
            acmCodeCpp: acmCodeCpp,
            codeJava: codeJava,
            codeJs: codeJs,
            codeGo: codeGo,
            samples: samples,
            companies: companies,
            templates: templates,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required String title,
            required String titleCn,
            required String topic,
            required String difficulty,
            required int frequency,
            required String question,
            required String hints,
            required String keyPoints,
            required String structureTags,
            required String approaches,
            required String code,
            Value<String?> acmCode = const Value.absent(),
            Value<String?> codeCpp = const Value.absent(),
            Value<String?> acmCodeCpp = const Value.absent(),
            Value<String?> codeJava = const Value.absent(),
            Value<String?> codeJs = const Value.absent(),
            Value<String?> codeGo = const Value.absent(),
            Value<String?> samples = const Value.absent(),
            Value<String?> companies = const Value.absent(),
            required String templates,
          }) =>
              ProblemRowsCompanion.insert(
            id: id,
            title: title,
            titleCn: titleCn,
            topic: topic,
            difficulty: difficulty,
            frequency: frequency,
            question: question,
            hints: hints,
            keyPoints: keyPoints,
            structureTags: structureTags,
            approaches: approaches,
            code: code,
            acmCode: acmCode,
            codeCpp: codeCpp,
            acmCodeCpp: acmCodeCpp,
            codeJava: codeJava,
            codeJs: codeJs,
            codeGo: codeGo,
            samples: samples,
            companies: companies,
            templates: templates,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$ProblemRowsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $ProblemRowsTable,
    ProblemRow,
    $$ProblemRowsTableFilterComposer,
    $$ProblemRowsTableOrderingComposer,
    $$ProblemRowsTableAnnotationComposer,
    $$ProblemRowsTableCreateCompanionBuilder,
    $$ProblemRowsTableUpdateCompanionBuilder,
    (ProblemRow, BaseReferences<_$AppDatabase, $ProblemRowsTable, ProblemRow>),
    ProblemRow,
    PrefetchHooks Function()>;
typedef $$MetaTableCreateCompanionBuilder = MetaCompanion Function({
  required String key,
  required String value,
  Value<int> rowid,
});
typedef $$MetaTableUpdateCompanionBuilder = MetaCompanion Function({
  Value<String> key,
  Value<String> value,
  Value<int> rowid,
});

class $$MetaTableFilterComposer extends Composer<_$AppDatabase, $MetaTable> {
  $$MetaTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get key => $composableBuilder(
      column: $table.key, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get value => $composableBuilder(
      column: $table.value, builder: (column) => ColumnFilters(column));
}

class $$MetaTableOrderingComposer extends Composer<_$AppDatabase, $MetaTable> {
  $$MetaTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get key => $composableBuilder(
      column: $table.key, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get value => $composableBuilder(
      column: $table.value, builder: (column) => ColumnOrderings(column));
}

class $$MetaTableAnnotationComposer
    extends Composer<_$AppDatabase, $MetaTable> {
  $$MetaTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get key =>
      $composableBuilder(column: $table.key, builder: (column) => column);

  GeneratedColumn<String> get value =>
      $composableBuilder(column: $table.value, builder: (column) => column);
}

class $$MetaTableTableManager extends RootTableManager<
    _$AppDatabase,
    $MetaTable,
    MetaData,
    $$MetaTableFilterComposer,
    $$MetaTableOrderingComposer,
    $$MetaTableAnnotationComposer,
    $$MetaTableCreateCompanionBuilder,
    $$MetaTableUpdateCompanionBuilder,
    (MetaData, BaseReferences<_$AppDatabase, $MetaTable, MetaData>),
    MetaData,
    PrefetchHooks Function()> {
  $$MetaTableTableManager(_$AppDatabase db, $MetaTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$MetaTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$MetaTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$MetaTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<String> key = const Value.absent(),
            Value<String> value = const Value.absent(),
            Value<int> rowid = const Value.absent(),
          }) =>
              MetaCompanion(
            key: key,
            value: value,
            rowid: rowid,
          ),
          createCompanionCallback: ({
            required String key,
            required String value,
            Value<int> rowid = const Value.absent(),
          }) =>
              MetaCompanion.insert(
            key: key,
            value: value,
            rowid: rowid,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$MetaTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $MetaTable,
    MetaData,
    $$MetaTableFilterComposer,
    $$MetaTableOrderingComposer,
    $$MetaTableAnnotationComposer,
    $$MetaTableCreateCompanionBuilder,
    $$MetaTableUpdateCompanionBuilder,
    (MetaData, BaseReferences<_$AppDatabase, $MetaTable, MetaData>),
    MetaData,
    PrefetchHooks Function()>;
typedef $$ProgressRowsTableCreateCompanionBuilder = ProgressRowsCompanion
    Function({
  Value<int> problemId,
  required int status,
  required double easiness,
  required int intervalDays,
  required int reps,
  required int lapses,
  Value<DateTime?> dueAt,
  Value<DateTime?> lastStudiedAt,
});
typedef $$ProgressRowsTableUpdateCompanionBuilder = ProgressRowsCompanion
    Function({
  Value<int> problemId,
  Value<int> status,
  Value<double> easiness,
  Value<int> intervalDays,
  Value<int> reps,
  Value<int> lapses,
  Value<DateTime?> dueAt,
  Value<DateTime?> lastStudiedAt,
});

class $$ProgressRowsTableFilterComposer
    extends Composer<_$AppDatabase, $ProgressRowsTable> {
  $$ProgressRowsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get problemId => $composableBuilder(
      column: $table.problemId, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnFilters(column));

  ColumnFilters<double> get easiness => $composableBuilder(
      column: $table.easiness, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get intervalDays => $composableBuilder(
      column: $table.intervalDays, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get reps => $composableBuilder(
      column: $table.reps, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get lapses => $composableBuilder(
      column: $table.lapses, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get dueAt => $composableBuilder(
      column: $table.dueAt, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get lastStudiedAt => $composableBuilder(
      column: $table.lastStudiedAt, builder: (column) => ColumnFilters(column));
}

class $$ProgressRowsTableOrderingComposer
    extends Composer<_$AppDatabase, $ProgressRowsTable> {
  $$ProgressRowsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get problemId => $composableBuilder(
      column: $table.problemId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get status => $composableBuilder(
      column: $table.status, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<double> get easiness => $composableBuilder(
      column: $table.easiness, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get intervalDays => $composableBuilder(
      column: $table.intervalDays,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get reps => $composableBuilder(
      column: $table.reps, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get lapses => $composableBuilder(
      column: $table.lapses, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get dueAt => $composableBuilder(
      column: $table.dueAt, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get lastStudiedAt => $composableBuilder(
      column: $table.lastStudiedAt,
      builder: (column) => ColumnOrderings(column));
}

class $$ProgressRowsTableAnnotationComposer
    extends Composer<_$AppDatabase, $ProgressRowsTable> {
  $$ProgressRowsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get problemId =>
      $composableBuilder(column: $table.problemId, builder: (column) => column);

  GeneratedColumn<int> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<double> get easiness =>
      $composableBuilder(column: $table.easiness, builder: (column) => column);

  GeneratedColumn<int> get intervalDays => $composableBuilder(
      column: $table.intervalDays, builder: (column) => column);

  GeneratedColumn<int> get reps =>
      $composableBuilder(column: $table.reps, builder: (column) => column);

  GeneratedColumn<int> get lapses =>
      $composableBuilder(column: $table.lapses, builder: (column) => column);

  GeneratedColumn<DateTime> get dueAt =>
      $composableBuilder(column: $table.dueAt, builder: (column) => column);

  GeneratedColumn<DateTime> get lastStudiedAt => $composableBuilder(
      column: $table.lastStudiedAt, builder: (column) => column);
}

class $$ProgressRowsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $ProgressRowsTable,
    ProgressRow,
    $$ProgressRowsTableFilterComposer,
    $$ProgressRowsTableOrderingComposer,
    $$ProgressRowsTableAnnotationComposer,
    $$ProgressRowsTableCreateCompanionBuilder,
    $$ProgressRowsTableUpdateCompanionBuilder,
    (
      ProgressRow,
      BaseReferences<_$AppDatabase, $ProgressRowsTable, ProgressRow>
    ),
    ProgressRow,
    PrefetchHooks Function()> {
  $$ProgressRowsTableTableManager(_$AppDatabase db, $ProgressRowsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ProgressRowsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ProgressRowsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ProgressRowsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> problemId = const Value.absent(),
            Value<int> status = const Value.absent(),
            Value<double> easiness = const Value.absent(),
            Value<int> intervalDays = const Value.absent(),
            Value<int> reps = const Value.absent(),
            Value<int> lapses = const Value.absent(),
            Value<DateTime?> dueAt = const Value.absent(),
            Value<DateTime?> lastStudiedAt = const Value.absent(),
          }) =>
              ProgressRowsCompanion(
            problemId: problemId,
            status: status,
            easiness: easiness,
            intervalDays: intervalDays,
            reps: reps,
            lapses: lapses,
            dueAt: dueAt,
            lastStudiedAt: lastStudiedAt,
          ),
          createCompanionCallback: ({
            Value<int> problemId = const Value.absent(),
            required int status,
            required double easiness,
            required int intervalDays,
            required int reps,
            required int lapses,
            Value<DateTime?> dueAt = const Value.absent(),
            Value<DateTime?> lastStudiedAt = const Value.absent(),
          }) =>
              ProgressRowsCompanion.insert(
            problemId: problemId,
            status: status,
            easiness: easiness,
            intervalDays: intervalDays,
            reps: reps,
            lapses: lapses,
            dueAt: dueAt,
            lastStudiedAt: lastStudiedAt,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$ProgressRowsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $ProgressRowsTable,
    ProgressRow,
    $$ProgressRowsTableFilterComposer,
    $$ProgressRowsTableOrderingComposer,
    $$ProgressRowsTableAnnotationComposer,
    $$ProgressRowsTableCreateCompanionBuilder,
    $$ProgressRowsTableUpdateCompanionBuilder,
    (
      ProgressRow,
      BaseReferences<_$AppDatabase, $ProgressRowsTable, ProgressRow>
    ),
    ProgressRow,
    PrefetchHooks Function()>;
typedef $$ReviewLogsTableCreateCompanionBuilder = ReviewLogsCompanion Function({
  Value<int> id,
  required int problemId,
  required int kind,
  required double score,
  required String detail,
  required String hitKeyPoints,
  Value<DateTime?> createdAt,
});
typedef $$ReviewLogsTableUpdateCompanionBuilder = ReviewLogsCompanion Function({
  Value<int> id,
  Value<int> problemId,
  Value<int> kind,
  Value<double> score,
  Value<String> detail,
  Value<String> hitKeyPoints,
  Value<DateTime?> createdAt,
});

class $$ReviewLogsTableFilterComposer
    extends Composer<_$AppDatabase, $ReviewLogsTable> {
  $$ReviewLogsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get problemId => $composableBuilder(
      column: $table.problemId, builder: (column) => ColumnFilters(column));

  ColumnFilters<int> get kind => $composableBuilder(
      column: $table.kind, builder: (column) => ColumnFilters(column));

  ColumnFilters<double> get score => $composableBuilder(
      column: $table.score, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get detail => $composableBuilder(
      column: $table.detail, builder: (column) => ColumnFilters(column));

  ColumnFilters<String> get hitKeyPoints => $composableBuilder(
      column: $table.hitKeyPoints, builder: (column) => ColumnFilters(column));

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnFilters(column));
}

class $$ReviewLogsTableOrderingComposer
    extends Composer<_$AppDatabase, $ReviewLogsTable> {
  $$ReviewLogsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
      column: $table.id, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get problemId => $composableBuilder(
      column: $table.problemId, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<int> get kind => $composableBuilder(
      column: $table.kind, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<double> get score => $composableBuilder(
      column: $table.score, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get detail => $composableBuilder(
      column: $table.detail, builder: (column) => ColumnOrderings(column));

  ColumnOrderings<String> get hitKeyPoints => $composableBuilder(
      column: $table.hitKeyPoints,
      builder: (column) => ColumnOrderings(column));

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
      column: $table.createdAt, builder: (column) => ColumnOrderings(column));
}

class $$ReviewLogsTableAnnotationComposer
    extends Composer<_$AppDatabase, $ReviewLogsTable> {
  $$ReviewLogsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<int> get problemId =>
      $composableBuilder(column: $table.problemId, builder: (column) => column);

  GeneratedColumn<int> get kind =>
      $composableBuilder(column: $table.kind, builder: (column) => column);

  GeneratedColumn<double> get score =>
      $composableBuilder(column: $table.score, builder: (column) => column);

  GeneratedColumn<String> get detail =>
      $composableBuilder(column: $table.detail, builder: (column) => column);

  GeneratedColumn<String> get hitKeyPoints => $composableBuilder(
      column: $table.hitKeyPoints, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);
}

class $$ReviewLogsTableTableManager extends RootTableManager<
    _$AppDatabase,
    $ReviewLogsTable,
    ReviewLog,
    $$ReviewLogsTableFilterComposer,
    $$ReviewLogsTableOrderingComposer,
    $$ReviewLogsTableAnnotationComposer,
    $$ReviewLogsTableCreateCompanionBuilder,
    $$ReviewLogsTableUpdateCompanionBuilder,
    (ReviewLog, BaseReferences<_$AppDatabase, $ReviewLogsTable, ReviewLog>),
    ReviewLog,
    PrefetchHooks Function()> {
  $$ReviewLogsTableTableManager(_$AppDatabase db, $ReviewLogsTable table)
      : super(TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ReviewLogsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ReviewLogsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ReviewLogsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback: ({
            Value<int> id = const Value.absent(),
            Value<int> problemId = const Value.absent(),
            Value<int> kind = const Value.absent(),
            Value<double> score = const Value.absent(),
            Value<String> detail = const Value.absent(),
            Value<String> hitKeyPoints = const Value.absent(),
            Value<DateTime?> createdAt = const Value.absent(),
          }) =>
              ReviewLogsCompanion(
            id: id,
            problemId: problemId,
            kind: kind,
            score: score,
            detail: detail,
            hitKeyPoints: hitKeyPoints,
            createdAt: createdAt,
          ),
          createCompanionCallback: ({
            Value<int> id = const Value.absent(),
            required int problemId,
            required int kind,
            required double score,
            required String detail,
            required String hitKeyPoints,
            Value<DateTime?> createdAt = const Value.absent(),
          }) =>
              ReviewLogsCompanion.insert(
            id: id,
            problemId: problemId,
            kind: kind,
            score: score,
            detail: detail,
            hitKeyPoints: hitKeyPoints,
            createdAt: createdAt,
          ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ));
}

typedef $$ReviewLogsTableProcessedTableManager = ProcessedTableManager<
    _$AppDatabase,
    $ReviewLogsTable,
    ReviewLog,
    $$ReviewLogsTableFilterComposer,
    $$ReviewLogsTableOrderingComposer,
    $$ReviewLogsTableAnnotationComposer,
    $$ReviewLogsTableCreateCompanionBuilder,
    $$ReviewLogsTableUpdateCompanionBuilder,
    (ReviewLog, BaseReferences<_$AppDatabase, $ReviewLogsTable, ReviewLog>),
    ReviewLog,
    PrefetchHooks Function()>;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$ProblemRowsTableTableManager get problemRows =>
      $$ProblemRowsTableTableManager(_db, _db.problemRows);
  $$MetaTableTableManager get meta => $$MetaTableTableManager(_db, _db.meta);
  $$ProgressRowsTableTableManager get progressRows =>
      $$ProgressRowsTableTableManager(_db, _db.progressRows);
  $$ReviewLogsTableTableManager get reviewLogs =>
      $$ReviewLogsTableTableManager(_db, _db.reviewLogs);
}
