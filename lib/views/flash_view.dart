/// 速刷：SM-2 间隔复习会话。
library;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../repo.dart';
import '../state.dart';
import '../tts.dart';
import '../widgets/common.dart';
import '../widgets/markdown_view.dart';
import 'detail_pages.dart';

class FlashView extends StatefulWidget {
  const FlashView({super.key});

  @override
  State<FlashView> createState() => _FlashViewState();
}

class _FlashViewState extends State<FlashView> {
  int phase = 0; // 0 setup 1 running 2 done
  int sessionSize = 20;
  bool includeNew = true;
  final Set<String> selectedDomains = {};
  List<Question> queue = [];
  int idx = 0;
  bool revealed = false;
  int gradeCount = 0, fuzzyCount = 0, knownCount = 0;
  int forgotCount = 0;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final ui = context.read<UiState>();
    if (ui.flashPresetIds != null || ui.flashDomainsPreset != null) {
      if (ui.flashDomainsPreset != null) {
        selectedDomains
          ..clear()
          ..addAll(ui.flashDomainsPreset!);
      }
      final ids = ui.flashPresetIds;
      ui.flashPresetIds = null;
      ui.flashDomainsPreset = null;
      if (ids != null) {
        final state = context.read<AppState>();
        queue = [for (final id in ids) if (state.repo?.byId[id] != null) state.repo!.byId[id]!];
        if (queue.isNotEmpty) {
          phase = 1;
          WidgetsBinding.instance.addPostFrameCallback((_) => setState(() {}));
        }
      }
    }
  }

  void _start() {
    final state = context.read<AppState>();
    final q = state.buildQueue(
      domains: selectedDomains.isEmpty ? {} : selectedDomains,
      size: sessionSize,
      includeNew: includeNew,
    );
    if (q.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('该范围内没有可刷的题')));
      return;
    }
    setState(() {
      queue = q;
      idx = 0;
      revealed = false;
      phase = 1;
      gradeCount = 0;
      forgotCount = 0;
      fuzzyCount = 0;
      knownCount = 0;
    });
  }

  Future<void> _grade(int g) async {
    final state = context.read<AppState>();
    await state.grade(queue[idx].id, g);
    if (!mounted) return;
    setState(() {
      if (g == 0) forgotCount++;
      if (g == 1) fuzzyCount++;
      if (g == 2) knownCount++;
      gradeCount++;
      if (idx + 1 >= queue.length) {
        phase = 2;
      } else {
        idx++;
        revealed = false;
      }
    });
  }

  KeyEventResult _onKey(FocusNode node, KeyEvent e) {
    if (phase != 1) return KeyEventResult.ignored;
    if (e is KeyDownEvent) {
      if (e.logicalKey == LogicalKeyboardKey.space && !revealed) {
        setState(() => revealed = true);
        return KeyEventResult.handled;
      }
      if (revealed) {
        if (e.logicalKey == LogicalKeyboardKey.digit1) {
          _grade(0);
          return KeyEventResult.handled;
        }
        if (e.logicalKey == LogicalKeyboardKey.digit2) {
          _grade(1);
          return KeyEventResult.handled;
        }
        if (e.logicalKey == LogicalKeyboardKey.digit3) {
          _grade(2);
          return KeyEventResult.handled;
        }
      }
    }
    return KeyEventResult.ignored;
  }

  @override
  Widget build(BuildContext context) {
    return Focus(
      autofocus: true,
      onKeyEvent: _onKey,
      child: switch (phase) {
        0 => _buildSetup(),
        1 => _buildSession(),
        _ => _buildDone(),
      },
    );
  }

  Widget _buildSetup() {
    final state = context.watch<AppState>();
    final repo = state.repo;
    final due = state.dueCount;
    return Scaffold(
      appBar: AppBar(title: const Text('速刷')),
      body: repo == null || repo.totalQuestions == 0
          ? const EmptyView('题库为空，请先生成内容包')
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Panel(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('本次范围', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 10),
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
                    const SizedBox(height: 6),
                    Text('不选则默认全部领域', style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
                  ]),
                ),
                const SizedBox(height: 12),
                Panel(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      const Text('卡片数量', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                      const Spacer(),
                      Text('$sessionSize 张', style: TextStyle(fontSize: 13, color: Theme.of(context).colorScheme.primary)),
                    ]),
                    Slider(
                      value: sessionSize.toDouble(),
                      min: 10,
                      max: 50,
                      divisions: 4,
                      label: '$sessionSize',
                      onChanged: (v) => setState(() => sessionSize = v.round()),
                    ),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      dense: true,
                      title: const Text('混入新题', style: TextStyle(fontSize: 13.5)),
                      subtitle: Text('到期不足时按面试频率补入新题', style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
                      value: includeNew,
                      onChanged: (v) => setState(() => includeNew = v),
                    ),
                    Text(
                      '当前到期 $due 题，将优先安排复习',
                      style: TextStyle(fontSize: 12, color: Colors.orangeAccent.shade200),
                    ),
                  ]),
                ),
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: _start,
                  icon: const Icon(Icons.play_arrow),
                  label: const Text('开始', style: TextStyle(fontSize: 15)),
                ),
                if (!kIsWeb && defaultTargetPlatform == TargetPlatform.macOS)
                  Padding(
                    padding: const EdgeInsets.only(top: 10),
                    child: Text('桌面快捷键：空格翻面 · 1/2/3 = 忘了/模糊/记得',
                        textAlign: TextAlign.center, style: TextStyle(fontSize: 11.5, color: Colors.grey.shade600)),
                  ),
              ],
            ),
    );
  }

  Widget _buildSession() {
    final q = queue[idx];
    return Scaffold(
      appBar: AppBar(
        title: Text('${idx + 1} / ${queue.length}', style: const TextStyle(fontSize: 14)),
        leading: IconButton(icon: const Icon(Icons.close), onPressed: () => setState(() => phase = 0)),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(value: (idx + (revealed ? 0.5 : 0)) / queue.length, minHeight: 4),
          ),
          const SizedBox(height: 14),
          Row(children: [
            Text('${q.domainName} · ${q.topic}', style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
            const SizedBox(width: 8),
            TypeChip(q.type),
            const Spacer(),
            DifficultyDots(q.difficulty),
          ]),
          const SizedBox(height: 14),
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(
              child: Text(q.question, style: const TextStyle(fontSize: 17, height: 1.55, fontWeight: FontWeight.w600)),
            ),
            IconButton(
              tooltip: '朗读题目',
              visualDensity: VisualDensity.compact,
              icon: const Icon(Icons.volume_up_outlined, size: 20),
              onPressed: () => TtsController.instance.speak(q.question),
            ),
          ]),
          const SizedBox(height: 18),
          if (!revealed)
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 18),
                child: Column(children: [
                  FilledButton.icon(
                    onPressed: () => setState(() => revealed = true),
                    icon: const Icon(Icons.visibility, size: 18),
                    label: const Text('显示答案'),
                  ),
                  const SizedBox(height: 8),
                  Text('先在心里过一遍要点再看答案', style: TextStyle(fontSize: 11.5, color: Colors.grey.shade600)),
                ]),
              ),
            )
          else ...[
            Md(q.answerMd),
            if (q.keyPoints.isNotEmpty) ...[
              const SizedBox(height: 12),
              Panel(
                padding: const EdgeInsets.all(10),
                child: Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [for (final k in q.keyPoints) _kpChip(k)],
                ),
              ),
            ],
            const SizedBox(height: 10),
            TextButton(
              onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => QuestionDetailPage(qid: q.id))),
              child: const Text('查看追问链与完整解析', style: TextStyle(fontSize: 12.5)),
            ),
          ],
        ],
      ),
      bottomNavigationBar: revealed
          ? SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 10),
                child: GradeButtons(onGrade: _grade),
              ),
            )
          : null,
    );
  }

  Widget _kpChip(String k) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.lightBlueAccent.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(k, style: const TextStyle(fontSize: 11.5)),
    );
  }

  Widget _buildDone() {
    final state = context.watch<AppState>();
    return Scaffold(
      appBar: AppBar(title: const Text('本轮完成')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Text('🎉', style: TextStyle(fontSize: 42)),
            const SizedBox(height: 12),
            Text('完成 $gradeCount 张卡片', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 14),
            Row(mainAxisSize: MainAxisSize.min, children: [
              _stat('记得', '$knownCount', Colors.greenAccent),
              _stat('模糊', '$fuzzyCount', Colors.orangeAccent),
              _stat('忘了', '$forgotCount', Colors.redAccent),
            ]),
            const SizedBox(height: 14),
            Text('连续打卡 ${state.streak} 天 · 今日已刷 ${state.todayRec().reviewed} 题',
                style: TextStyle(fontSize: 12.5, color: Colors.grey.shade500)),
            const SizedBox(height: 24),
            Row(mainAxisSize: MainAxisSize.min, children: [
              FilledButton(onPressed: () => setState(() => phase = 0), child: const Text('再来一组')),
              const SizedBox(width: 12),
              OutlinedButton(onPressed: () => context.read<UiState>().goto(0), child: const Text('回首页')),
            ]),
          ]),
        ),
      ),
    );
  }

  Widget _stat(String label, String n, Color c) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: Column(children: [
        Text(n, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: c)),
        Text(label, style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
      ]),
    );
  }
}
