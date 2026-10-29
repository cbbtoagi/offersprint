/// 详情页：题目详情 / 项目详情 / 面经详情，以及记笔记弹层。
library;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../audio.dart';
import '../sr.dart' show intervalLabel;
import '../state.dart';
import '../tts.dart';
import '../widgets/common.dart';
import '../widgets/markdown_view.dart';

class QuestionDetailPage extends StatefulWidget {
  final String qid;
  final bool reveal;
  const QuestionDetailPage({super.key, required this.qid, this.reveal = false});

  @override
  State<QuestionDetailPage> createState() => _QuestionDetailPageState();
}

class _QuestionDetailPageState extends State<QuestionDetailPage> {
  late bool revealed = widget.reveal;

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final q = state.repo?.byId[widget.qid];
    if (q == null) {
      return Scaffold(appBar: AppBar(), body: const EmptyView('题目不存在'));
    }
    final rec = state.progress[q.id];
    return Scaffold(
      appBar: AppBar(
        title: Text('${q.domainName} · ${q.topic}', style: const TextStyle(fontSize: 14)),
        actions: [
          IconButton(
            tooltip: '记笔记',
            icon: const Icon(Icons.edit_note),
            onPressed: () => showNoteSheet(context, qid: q.id),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          Row(children: [
            TypeChip(q.type),
            const SizedBox(width: 8),
            DifficultyDots(q.difficulty),
            const SizedBox(width: 8),
            FreqBadge(q.frequency),
            const Spacer(),
            if (rec != null && !rec.isNew)
              Text(
                rec.isMastered ? '已掌握' : (rec.isDue ? '待复习' : '复习于 ${intervalLabel(rec.intervalDays)}后'),
                style: TextStyle(fontSize: 11, color: rec.isMastered ? Colors.greenAccent : Colors.orangeAccent),
              ),
          ]),
          if (q.companies.isNotEmpty) ...[
            const SizedBox(height: 10),
            CompanyChips(q.companies),
          ],
          const SizedBox(height: 14),
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(
              child: Text(q.question, style: const TextStyle(fontSize: 17, height: 1.5, fontWeight: FontWeight.w600)),
            ),
            IconButton(
              tooltip: '朗读题目',
              visualDensity: VisualDensity.compact,
              icon: const Icon(Icons.volume_up_outlined, size: 20),
              onPressed: () => TtsController.instance.speak(q.question),
            ),
          ]),
          const SizedBox(height: 16),
          if (!revealed)
            Center(
              child: FilledButton.icon(
                onPressed: () => setState(() => revealed = true),
                icon: const Icon(Icons.visibility, size: 18),
                label: const Text('显示参考答案'),
              ),
            )
          else ...[
            Md(q.answerMd),
            const SizedBox(height: 16),
            if (q.keyPoints.isNotEmpty) ...[
              _sectionTitle('核心要点'),
              Panel(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    for (final k in q.keyPoints)
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          const Text('• ', style: TextStyle(color: Colors.lightBlueAccent)),
                          Expanded(child: Text(k, style: const TextStyle(fontSize: 13.5, height: 1.5))),
                        ]),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 14),
            ],
            if (q.code != null) ...[
              _sectionTitle('参考实现'),
              Md('```${q.code!.lang}\n${q.code!.content}\n```'),
              const SizedBox(height: 14),
            ],
            if (q.followUps.isNotEmpty) ...[
              _sectionTitle('高频追问'),
              for (final f in q.followUps)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: ExpansionTile(
                    tilePadding: const EdgeInsets.symmetric(horizontal: 12),
                    childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
                    backgroundColor: Theme.of(context).colorScheme.surfaceContainerLowest,
                    collapsedBackgroundColor: Theme.of(context).colorScheme.surfaceContainerLowest,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    title: Text('追问：${f.q}', style: const TextStyle(fontSize: 13.5)),
                    children: [Align(alignment: Alignment.centerLeft, child: Md(f.a, fontSize: 13))],
                  ),
                ),
            ],
          ],
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 6, 16, 10),
          child: revealed
              ? GradeButtons(onGrade: (g) async {
                  await context.read<AppState>().grade(q.id, g);
                  if (context.mounted) Navigator.of(context).pop();
                })
              : TextButton(
                  onPressed: () => setState(() => revealed = true),
                  child: const Text('先自己想一想，再对答案'),
                ),
        ),
      ),
    );
  }

  Widget _sectionTitle(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(t, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: Colors.grey.shade400)),
      );
}

class ProjectDetailPage extends StatelessWidget {
  final String projectId;
  const ProjectDetailPage({super.key, required this.projectId});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final p = state.repo?.projects.where((e) => e.id == projectId).firstOrNull;
    if (p == null) {
      return Scaffold(appBar: AppBar(), body: const EmptyView('项目不存在'));
    }
    return Scaffold(
      appBar: AppBar(title: Text(p.name, style: const TextStyle(fontSize: 14))),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        children: [
          Md(p.summaryMd),
          const Divider(height: 28),
          Md(p.bodyMd),
        ],
      ),
    );
  }
}

class ExpDetailPage extends StatelessWidget {
  final String expId;
  const ExpDetailPage({super.key, required this.expId});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final e = state.repo?.exps.where((x) => x.id == expId).firstOrNull;
    if (e == null) {
      return Scaffold(appBar: AppBar(), body: const EmptyView('面经不存在'));
    }
    return Scaffold(
      appBar: AppBar(title: Text(e.company, style: const TextStyle(fontSize: 14))),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        children: [
          Text(e.role, style: TextStyle(fontSize: 13, color: Colors.grey.shade400)),
          const SizedBox(height: 4),
          Text('难度 ${'★' * e.difficulty}${'☆' * (5 - e.difficulty)} · 更新 ${e.updated} · 高频题 ${e.questions.length}',
              style: TextStyle(fontSize: 12, color: Colors.grey.shade500)),
          const SizedBox(height: 14),
          _card(context, '轮次结构', e.rounds.join('\n')),
          const SizedBox(height: 10),
          _card(context, '考察重点', e.focus),
          const SizedBox(height: 10),
          _card(context, '高频真题（点击在题库中搜索）', e.questions.map((q) => '• $q').join('\n')),
          const SizedBox(height: 10),
          _card(context, '备考建议', e.advice),
        ],
      ),
    );
  }

  Widget _card(BuildContext context, String title, String body) {
    return Panel(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: Colors.grey.shade400)),
        const SizedBox(height: 8),
        SelectableText(body, style: const TextStyle(fontSize: 13.5, height: 1.6)),
      ]),
    );
  }
}

/// 记笔记弹层（可顺带录音）。
Future<void> showNoteSheet(BuildContext context, {String? qid}) async {
  final textCtrl = TextEditingController();
  final tagCtrl = TextEditingController();
  final rec = AudioRecController();
  (String, int)? audio;

  await showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    builder: (sheetCtx) {
      return StatefulBuilder(builder: (ctx, setSheet) {
        return Padding(
          padding: EdgeInsets.fromLTRB(16, 16, 16, MediaQuery.of(ctx).viewInsets.bottom + 16),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('记一笔', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            TextField(
              controller: textCtrl,
              maxLines: 5,
              autofocus: true,
              decoration: const InputDecoration(
                hintText: '记录此刻的想法、易错点、自己的话复述…',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: tagCtrl,
              decoration: const InputDecoration(
                hintText: '标签（逗号分隔，如：RoPE,易错）',
                border: OutlineInputBorder(),
                isDense: true,
              ),
            ),
            const SizedBox(height: 12),
            Row(children: [
              TextButton.icon(
                onPressed: () async {
                  if (rec.isRecording) {
                    final r = await rec.stop();
                    if (r != null) setSheet(() => audio = r);
                  } else {
                    final ok = await rec.start();
                    setSheet(() {});
                    if (!ok && ctx.mounted) {
                      ScaffoldMessenger.of(ctx).showSnackBar(const SnackBar(content: Text('无法访问麦克风')));
                    }
                  }
                },
                icon: Icon(rec.isRecording ? Icons.stop : Icons.mic, size: 18,
                    color: rec.isRecording ? Colors.redAccent : null),
                label: Text(
                  rec.isRecording ? '停止录音' : (audio == null ? '附加语音' : '✓ 已录 ${(audio!.$2 / 1000).round()}s'),
                  style: const TextStyle(fontSize: 12),
                ),
              ),
              const Spacer(),
              FilledButton(
                onPressed: () async {
                  final navigator = Navigator.of(sheetCtx);
                  if (textCtrl.text.trim().isEmpty && audio == null) return;
                  await ctx.read<AppState>().addNote(textCtrl.text.trim(), tagCtrl.text.trim(), qid, audio?.$1);
                  navigator.pop();
                },
                child: const Text('保存'),
              ),
            ]),
          ]),
        );
      });
    },
  );
}
