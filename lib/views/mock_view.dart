/// 模拟面试：限时作答 + 录音 + 语音转写 + 自评 + 战报。
/// v2：支持公司组卷（按面经库出题）与面试官追问模式（答完追加高频追问）。
library;
import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../audio.dart';
import '../models.dart';
import '../repo.dart';
import '../state.dart';
import '../tts.dart';
import '../widgets/common.dart';
import '../widgets/markdown_view.dart';

class MockView extends StatefulWidget {
  const MockView({super.key});

  @override
  State<MockView> createState() => _MockViewState();
}

class _MockItem {
  final Question q;
  int secondsUsed = 0;
  int grade = -1; // 2 答上 1 一般 0 没答上
  String transcript = '';
  String? audioPath;

  _MockItem(this.q);
}

class _MockViewState extends State<MockView> {
  int phase = 0; // 0 setup 1 running 2 report
  final Set<String> selectedDomains = {};
  int count = 5;
  int secondsPerQ = 120;
  bool useStt = true;

  // 组卷方式：0 题库组卷（按领域），1 公司组卷（按面经库）
  int paperMode = 0;
  String? companyId;
  bool followUpMode = false;

  List<_MockItem> items = [];
  int idx = 0;
  int remain = 0;
  Timer? timer;
  final AudioRecController recorder = AudioRecController();
  final AudioPlayController player = AudioPlayController();
  final SttController stt = SttController();
  final TextEditingController transcriptCtrl = TextEditingController();

  // 追问阶段
  bool fuPhase = false;
  int fuIdx = 0;
  bool fuRevealed = false;

  @override
  void dispose() {
    timer?.cancel();
    player.dispose();
    transcriptCtrl.dispose();
    super.dispose();
  }

  static String companyToken(String name) {
    return name.split(RegExp(r'[·（(]')).first.trim();
  }

  static bool matchCompany(Question q, String token) {
    if (token.isEmpty) return false;
    return q.companies.any((c) => token.contains(c) || c.contains(token));
  }

  Future<void> _start() async {
    final state = context.read<AppState>();
    final repo = state.repo;
    if (repo == null) return;
    final pool = <Question>[];

    if (paperMode == 1 && companyId != null) {
      final exp = repo.exps.where((e) => e.id == companyId).firstOrNull;
      final token = exp == null ? '' : companyToken(exp.company);
      for (final p in repo.packs) {
        pool.addAll(p.$2.where((q) => matchCompany(q, token)));
      }
      if (pool.length < count) {
        final have = pool.map((q) => q.id).toSet();
        final extras = <Question>[
          for (final p in repo.packs)
            for (final q in p.$2)
              if (!have.contains(q.id)) q,
        ]..sort((a, b) => b.frequency.compareTo(a.frequency));
        pool.addAll(extras.take(count - pool.length));
      }
    } else {
      for (final p in repo.packs) {
        if (selectedDomains.isNotEmpty && !selectedDomains.contains(p.$1.id)) continue;
        pool.addAll(p.$2);
      }
    }

    if (pool.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('该范围没有可用的题目')));
      return;
    }
    pool.shuffle();
    pool.sort((a, b) => b.frequency.compareTo(a.frequency));
    items = [for (final q in pool.take(count)) _MockItem(q)];
    idx = 0;
    fuPhase = false;
    fuIdx = 0;
    fuRevealed = false;
    if (useStt) await stt.init();
    phase = 1;
    remain = secondsPerQ;
    timer?.cancel();
    timer = Timer.periodic(const Duration(seconds: 1), (_) => _tick());
    _beginQuestion();
    setState(() {});
  }

  void _beginQuestion() {
    transcriptCtrl.clear();
    stt.committed = '';
    if (!fuPhase && useStt && stt.available) {
      stt.start((full) {
        if (mounted && !transcriptCtrl.text.startsWith(full)) {
          transcriptCtrl
            ..text = full
            ..selection = TextSelection.fromPosition(TextPosition(offset: full.length));
        }
      });
    }
  }

  void _tick() {
    if (phase != 1) return;
    setState(() {
      remain--;
      if (fuPhase) {
        if (remain <= 0) _nextFu();
      } else {
        items[idx].secondsUsed++;
        if (remain <= 0) _finishCurrent(auto: true);
      }
    });
  }

  /// 答完主问题：录音收尾 + 评分 + 进入追问或下一题。
  Future<void> _finishCurrent({bool auto = false}) async {
    final state = context.read<AppState>();
    final item = items[idx];
    item.transcript = transcriptCtrl.text.trim();
    await stt.stop();
    final rec = await recorder.stop();
    if (rec != null) {
      item.audioPath = rec.$1;
      await state.saveRecording(qid: item.q.id, path: rec.$1, durationMs: rec.$2, transcript: item.transcript);
    }
    if (auto) item.grade = 0;
    if (item.grade >= 0) {
      await state.grade(item.q.id, item.grade);
    }
    if (!mounted) return;
    if (followUpMode && item.q.followUps.isNotEmpty) {
      fuPhase = true;
      fuIdx = 0;
      fuRevealed = false;
      remain = math.max(30, secondsPerQ ~/ 2);
      _beginQuestion();
    } else {
      _advanceQuestion();
    }
    setState(() {});
  }

  void _nextFu() {
    final item = items[idx];
    if (fuIdx + 1 < item.q.followUps.length) {
      fuIdx++;
      fuRevealed = false;
      remain = math.max(30, secondsPerQ ~/ 2);
    } else {
      fuPhase = false;
      _advanceQuestion();
    }
  }

  Future<void> _advanceQuestion() async {
    final state = context.read<AppState>();
    if (idx + 1 >= items.length) {
      timer?.cancel();
      await state.bumpMock((items.fold<int>(0, (s, i) => s + i.secondsUsed) / 60).ceilToDouble());
      phase = 2;
    } else {
      idx++;
      remain = secondsPerQ;
      _beginQuestion();
    }
  }

  void _gradeCurrent(int g) {
    items[idx].grade = g;
    _finishCurrent();
  }

  void _showAnswerMarkdown(String title, String md) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => Container(
        constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.75),
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        child: ListView(children: [
          Row(children: [
            Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
            const Spacer(),
            IconButton(icon: const Icon(Icons.close, size: 20), onPressed: () => Navigator.of(context).pop()),
          ]),
          Md(md),
        ]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return switch (phase) {
      0 => _buildSetup(),
      1 => _buildRunning(),
      _ => _buildReport(),
    };
  }

  Widget _buildSetup() {
    final repo = context.watch<AppState>().repo;
    final exps = repo?.exps ?? const [];
    return Scaffold(
      appBar: AppBar(title: const Text('模拟面试')),
      body: repo == null || repo.totalQuestions == 0
          ? const EmptyView('题库为空，请先生成内容包')
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Panel(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('组卷方式', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 10),
                    SegmentedButton<int>(
                      showSelectedIcon: false,
                      style: const ButtonStyle(visualDensity: VisualDensity.compact),
                      segments: const [
                        ButtonSegment(value: 0, label: Text('按领域', style: TextStyle(fontSize: 12))),
                        ButtonSegment(value: 1, label: Text('按公司', style: TextStyle(fontSize: 12))),
                      ],
                      selected: {paperMode},
                      onSelectionChanged: (s) => setState(() => paperMode = s.first),
                    ),
                    const SizedBox(height: 12),
                    if (paperMode == 1 && exps.isNotEmpty) ...[
                      DropdownButtonFormField<String>(
                        initialValue: companyId,
                        isDense: true,
                        decoration: const InputDecoration(
                          labelText: '目标公司（来自面经库）',
                          border: OutlineInputBorder(),
                        ),
                        items: [
                          for (final e in exps)
                            DropdownMenuItem(value: e.id, child: Text('${e.company} · ${e.role}', style: const TextStyle(fontSize: 12.5))),
                        ],
                        onChanged: (v) => setState(() => companyId = v),
                      ),
                      const SizedBox(height: 6),
                      Text('优先出该公司高频题，不足时按面试频率补题',
                          style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
                    ] else
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          for (final meta in kDomainOrder)
                            if (repo.questionsOf(meta.id).isNotEmpty)
                              FilterChip(
                                label: Text('${meta.emoji} ${meta.name}', style: const TextStyle(fontSize: 12)),
                                selected: selectedDomains.contains(meta.id),
                                onSelected: (v) => setState(() => v ? selectedDomains.add(meta.id) : selectedDomains.remove(meta.id)),
                              ),
                        ],
                      ),
                  ]),
                ),
                const SizedBox(height: 12),
                Panel(
                  child: Column(children: [
                    _seg('题数', ['3', '5', '10'], count.toString(), (v) => setState(() => count = int.parse(v))),
                    _seg('每题限时', ['60s', '120s', '180s'], '${secondsPerQ}s', (v) => setState(() => secondsPerQ = int.parse(v.replaceAll('s', '')))),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      dense: true,
                      title: const Text('语音转写', style: TextStyle(fontSize: 13.5)),
                      subtitle: Text('说出你的回答并自动转成文字（首次使用需授权）',
                          style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
                      value: useStt,
                      onChanged: (v) => setState(() => useStt = v),
                    ),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      dense: true,
                      title: const Text('面试官追问模式', style: TextStyle(fontSize: 13.5)),
                      subtitle: Text('每题答完后追加该题高频追问（半场限时，可对答案）',
                          style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
                      value: followUpMode,
                      onChanged: (v) => setState(() => followUpMode = v),
                    ),
                  ]),
                ),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: paperMode == 1 && companyId == null ? null : _start,
                  icon: const Icon(Icons.play_arrow),
                  label: const Text('开始面试', style: TextStyle(fontSize: 15)),
                ),
                const SizedBox(height: 10),
                Text('每题作答时自动录音；结束后生成战报，薄弱题自动进入复习队列。',
                    textAlign: TextAlign.center, style: TextStyle(fontSize: 11.5, color: Colors.grey.shade600)),
              ],
            ),
    );
  }

  Widget _seg(String label, List<String> options, String current, ValueChanged<String> onPick) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(children: [
        Text(label, style: const TextStyle(fontSize: 13.5)),
        const Spacer(),
        SegmentedButton<String>(
          showSelectedIcon: false,
          style: const ButtonStyle(visualDensity: VisualDensity.compact),
          segments: [for (final o in options) ButtonSegment(value: o, label: Text(o, style: const TextStyle(fontSize: 12)))],
          selected: {current},
          onSelectionChanged: (s) => onPick(s.first),
        ),
      ]),
    );
  }

  Widget _buildRunning() {
    final item = items[idx];
    final ratio = remain / secondsPerQ;
    final urgent = remain <= 30;

    if (fuPhase) {
      final fu = item.q.followUps[fuIdx];
      return Scaffold(
        appBar: AppBar(
          title: Text('追问 ${fuIdx + 1}/${item.q.followUps.length}', style: const TextStyle(fontSize: 14)),
          leading: IconButton(
            icon: const Icon(Icons.close),
            onPressed: () {
              timer?.cancel();
              setState(() => phase = 0);
            },
          ),
        ),
        body: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
          children: [
            Row(children: [
              Icon(Icons.timer_outlined, size: 18, color: urgent ? Colors.redAccent : Colors.grey.shade500),
              const SizedBox(width: 8),
              Text('${remain}s', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: urgent ? Colors.redAccent : null)),
              const SizedBox(width: 12),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(3),
                  child: LinearProgressIndicator(
                    value: ratio.clamp(0, 1),
                    minHeight: 5,
                    valueColor: AlwaysStoppedAnimation(urgent ? Colors.redAccent : Colors.deepPurpleAccent),
                  ),
                ),
              ),
            ]),
            const SizedBox(height: 6),
            Text('原题：${item.q.question}', maxLines: 2, overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
            const SizedBox(height: 12),
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(
                child: Text('追问：${fu.q}', style: const TextStyle(fontSize: 16.5, height: 1.55, fontWeight: FontWeight.w600)),
              ),
              IconButton(
                tooltip: '朗读追问',
                visualDensity: VisualDensity.compact,
                icon: const Icon(Icons.volume_up_outlined, size: 20),
                onPressed: () => TtsController.instance.speak(fu.q),
              ),
            ]),
            const SizedBox(height: 14),
            if (!fuRevealed)
              Center(
                child: OutlinedButton.icon(
                  onPressed: () => setState(() => fuRevealed = true),
                  icon: const Icon(Icons.visibility, size: 17),
                  label: const Text('显示追问参考答案'),
                ),
              )
            else ...[
              Md(fu.a, fontSize: 13.5),
              const SizedBox(height: 10),
            ],
          ],
        ),
        bottomNavigationBar: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 10),
            child: FilledButton.tonal(
              onPressed: () => setState(_nextFu),
              child: Text(fuIdx + 1 >= item.q.followUps.length ? '进入下一题' : '下一追问'),
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('第 ${idx + 1} / ${items.length} 题', style: const TextStyle(fontSize: 14)),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () {
            timer?.cancel();
            setState(() => phase = 0);
          },
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
        children: [
          Row(children: [
            Icon(Icons.timer_outlined, size: 18, color: urgent ? Colors.redAccent : Colors.grey.shade500),
            const SizedBox(width: 8),
            Text('${remain}s', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: urgent ? Colors.redAccent : null)),
            const SizedBox(width: 12),
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: LinearProgressIndicator(
                  value: ratio.clamp(0, 1),
                  minHeight: 5,
                  valueColor: AlwaysStoppedAnimation(urgent ? Colors.redAccent : Theme.of(context).colorScheme.primary),
                ),
              ),
            ),
          ]),
          const SizedBox(height: 14),
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(
              child: Text(item.q.question, style: const TextStyle(fontSize: 17, height: 1.55, fontWeight: FontWeight.w600)),
            ),
            IconButton(
              tooltip: '朗读题目',
              visualDensity: VisualDensity.compact,
              icon: const Icon(Icons.volume_up_outlined, size: 20),
              onPressed: () => TtsController.instance.speak(item.q.question),
            ),
          ]),
          const SizedBox(height: 14),
          TextField(
            controller: transcriptCtrl,
            maxLines: 6,
            decoration: InputDecoration(
              hintText: stt.listening ? '正在聆听…请口头作答（自动转写）' : '在此写下/粘贴你的作答要点',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              isDense: true,
            ),
          ),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () async {
                  final state = context.read<AppState>();
                  if (recorder.isRecording) {
                    final r = await recorder.stop();
                    if (r != null) {
                      item.audioPath = r.$1;
                      await state.saveRecording(qid: item.q.id, path: r.$1, durationMs: r.$2, transcript: transcriptCtrl.text.trim());
                      setState(() {});
                      if (mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('录音已保存，可在「我的 → 笔记/录音」回听')));
                      }
                    }
                  } else {
                    final ok = await recorder.start();
                    setState(() {});
                    if (!ok && mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('无法访问麦克风')));
                    }
                  }
                },
                icon: Icon(
                  recorder.isRecording ? Icons.stop : Icons.mic,
                  size: 18,
                  color: recorder.isRecording ? Colors.redAccent : null,
                ),
                label: Text(recorder.isRecording ? '停止录音' : (item.audioPath != null ? '重录' : '录音'), style: const TextStyle(fontSize: 12.5)),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () {
                  _showAnswerMarkdown('参考答案', item.q.answerMd);
                  setState(() {});
                },
                icon: const Icon(Icons.menu_book, size: 18),
                label: const Text('看参考答案', style: TextStyle(fontSize: 12.5)),
              ),
            ),
          ]),
          const SizedBox(height: 6),
          if (stt.available && !stt.listening)
            TextButton(
              onPressed: () {
                stt.start((full) {
                  if (mounted) {
                    transcriptCtrl
                      ..text = full
                      ..selection = TextSelection.fromPosition(TextPosition(offset: full.length));
                  }
                });
                setState(() {});
              },
              child: const Text('重新开始转写', style: TextStyle(fontSize: 12)),
            ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 4, 16, 10),
          child: GradeButtons(onGrade: _gradeCurrent),
        ),
      ),
    );
  }

  Widget _buildReport() {
    final good = items.where((i) => i.grade == 2).length;
    final mid = items.where((i) => i.grade == 1).length;
    final bad = items.where((i) => i.grade <= 0).length;
    return Scaffold(
      appBar: AppBar(title: const Text('面试战报')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Panel(
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
              _stat('答上了', '$good', Colors.greenAccent),
              _stat('一般', '$mid', Colors.orangeAccent),
              _stat('没答上', '$bad', Colors.redAccent),
              _stat('用时', '${(items.fold<int>(0, (s, i) => s + i.secondsUsed) / 60).toStringAsFixed(1)}分', Colors.lightBlueAccent),
            ]),
          ),
          const SizedBox(height: 12),
          for (final i in items)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Panel(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Icon(
                      i.grade == 2 ? Icons.check_circle : (i.grade == 1 ? Icons.help_outline : Icons.cancel),
                      size: 16,
                      color: i.grade == 2 ? Colors.greenAccent : (i.grade == 1 ? Colors.orangeAccent : Colors.redAccent),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(i.q.question, maxLines: 2, overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                    ),
                    Text('${i.secondsUsed}s', style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
                  ]),
                  if (i.transcript.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(i.transcript, maxLines: 3, overflow: TextOverflow.ellipsis,
                        style: TextStyle(fontSize: 12, color: Colors.grey.shade400, height: 1.5)),
                  ],
                  const SizedBox(height: 6),
                  Row(children: [
                    if (i.audioPath != null)
                      TextButton.icon(
                        onPressed: () => player.toggle(i.audioPath!),
                        icon: Icon(player.playingPath == i.audioPath ? Icons.stop : Icons.play_arrow, size: 16),
                        label: const Text('回听', style: TextStyle(fontSize: 11.5)),
                      ),
                    const Spacer(),
                    if (i.q.followUps.isNotEmpty)
                      TextButton(
                        onPressed: () => _showAnswerMarkdown(
                            '追问链 · ${i.q.followUps.length} 问',
                            i.q.followUps.map((f) => '**追问：${f.q}**\n\n${f.a}').join('\n\n---\n\n')),
                        child: Text('追问链 ${i.q.followUps.length} 问', style: const TextStyle(fontSize: 11.5)),
                      ),
                    TextButton(
                      onPressed: () => _showAnswerMarkdown('参考答案', i.q.answerMd),
                      child: const Text('参考答案', style: TextStyle(fontSize: 11.5)),
                    ),
                  ]),
                ]),
              ),
            ),
          const SizedBox(height: 8),
          Text('薄弱题已按「忘了/模糊」进入复习队列，下次速刷优先出现。',
              textAlign: TextAlign.center, style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
          const SizedBox(height: 14),
          FilledButton(
            onPressed: () => setState(() => phase = 0),
            child: const Text('完成'),
          ),
        ],
      ),
    );
  }

  Widget _stat(String label, String n, Color c) {
    return Column(children: [
      Text(n, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: c)),
      Text(label, style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
    ]);
  }
}
