/// 内容仓库：从 assets/content/*.json 加载题库、项目、面经。
library;
import 'package:flutter/services.dart' show rootBundle, AssetManifest;
import 'dart:convert';

import 'models.dart';

class DomainMeta {
  final String id;
  final String name;
  final String emoji;
  final String blurb;
  const DomainMeta(this.id, this.name, this.emoji, this.blurb);
}

const List<DomainMeta> kDomainOrder = [
  DomainMeta('basics', '深度学习与ML基础', '🧮', '优化器、归一化、正则、指标等通用八股'),
  DomainMeta('transformer', 'Transformer与大模型结构', '🧠', 'Attention、位置编码、KV Cache、MoE、推理优化'),
  DomainMeta('pretrain', '预训练', '🏋️', '数据工程、Tokenizer、Scaling Laws、分布式训练'),
  DomainMeta('posttrain', '后训练与对齐', '🎯', 'SFT、LoRA、RLHF、DPO、蒸馏与评测'),
  DomainMeta('rl', '强化学习与推理模型', '♟️', 'PPO、GRPO、DAPO、RLVR、o1/R1、测试时扩展'),
  DomainMeta('agent', 'Agent与Harness', '🤖', 'ReAct、MCP、上下文工程、Claude Code/Codex 架构'),
  DomainMeta('embodied', '具身智能与VLA', '🦾', '模仿学习、Diffusion Policy、RT/OpenVLA/π0'),
  DomainMeta('driving', '自动驾驶与世界模型', '🚗', 'BEV、Occupancy、端到端、世界模型、数据闭环'),
  DomainMeta('handcoded', '手撕代码', '⌨️', '手写 Attention/RoPE/BPE/beam search 与高频算法'),
  DomainMeta('scenario', '场景设计与开放题', '🗺️', '系统设计、排障、预算规划、开放之辩'),
];

DomainMeta? domainMeta(String id) {
  for (final m in kDomainOrder) {
    if (m.id == id) return m;
  }
  return null;
}

class ContentRepo {
  final List<(DomainMeta, List<Question>)> packs; // 领域 → 题目（保持 kDomainOrder）
  final List<Project> projects;
  final List<InterviewExp> exps;
  final Map<String, Question> byId;
  final List<String> issues; // 加载过程中的异常（自诊断用）
  final int assetCount; // 发现的内容包数量

  ContentRepo({
    required this.packs,
    required this.projects,
    required this.exps,
    this.issues = const [],
    this.assetCount = 0,
  })
      : byId = {
          for (final p in packs)
            for (final q in p.$2) q.id: q,
        };

  int get totalQuestions => packs.fold(0, (s, p) => s + p.$2.length);

  List<Question> questionsOf(String domain) =>
      packs.firstWhere((p) => p.$1.id == domain, orElse: () => (domainMeta(domain) ?? const DomainMeta('', '', '', ''), [])).$2;

  List<Question> search(String query) {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) return [];
    final out = <Question>[];
    for (final p in packs) {
      for (final item in p.$2) {
        final hay = StringBuffer(item.question);
        hay.write(item.keyPoints.join());
        hay.write(item.topic);
        hay.write(item.companies.join());
        if (hay.toString().toLowerCase().contains(q)) out.add(item);
        if (out.length >= 60) return out;
      }
    }
    return out;
  }

  static Future<ContentRepo> load() async {
    final manifest = await AssetManifest.loadFromAssetBundle(rootBundle);
    final assets = manifest.listAssets();
    final contentAssets = assets.where((a) => a.startsWith('assets/content/') && a.endsWith('.json')).toList()
      ..sort();
    final domainJson = <String, Map<String, dynamic>>{};
    List<Project> projects = [];
    List<InterviewExp> exps = [];
    final issues = <String>[];
    for (final a in contentAssets) {
      try {
        final raw = await rootBundle.loadString(a);
        final data = jsonDecode(raw) as Map<String, dynamic>;
        final name = a.split('/').last.replaceAll('.json', '');
        if (name == 'projects') {
          projects = ((data['projects'] as List?) ?? const [])
              .map((e) => Project.fromJson(Map<String, dynamic>.from(e as Map)))
              .toList();
        } else if (name == 'exps') {
          exps = ((data['exps'] as List?) ?? const [])
              .map((e) => InterviewExp.fromJson(Map<String, dynamic>.from(e as Map)))
              .toList();
        } else {
          domainJson[name] = data;
        }
      } catch (e) {
        // 单个内容包损坏时跳过，不阻塞启动，但记录原因
        issues.add('${a.split('/').last}: $e');
      }
    }
    final packs = <(DomainMeta, List<Question>)>[];
    for (final meta in kDomainOrder) {
      final data = domainJson[meta.id];
      if (data == null) continue;
      try {
        final qs = ((data['questions'] as List?) ?? const [])
            .map((e) => Question.fromJson(Map<String, dynamic>.from(e as Map), meta.id, meta.name))
            .toList();
        if (qs.isNotEmpty) packs.add((meta, qs));
      } catch (e) {
        issues.add('${meta.id}: $e');
      }
    }
    return ContentRepo(packs: packs, projects: projects, exps: exps, issues: issues, assetCount: contentAssets.length);
  }
}
