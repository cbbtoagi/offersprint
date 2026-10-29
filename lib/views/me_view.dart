/// 我的：统计、错题本、笔记、导入导出、设置。
library;
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';

import '../audio.dart';
import '../models.dart';
import '../repo.dart';
import '../state.dart';
import '../widgets/common.dart';
import '../widgets/heatmap.dart';
import 'detail_pages.dart';

class MeView extends StatelessWidget {
  const MeView({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final today = state.todayRec();
    final shakyCount = state.progress.values.where((r) => r.isShaky).length;

    return Scaffold(
      appBar: AppBar(title: const Text('我的')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          Panel(
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
              _stat('已学', '${state.totalLearned}', Colors.lightBlueAccent),
              _stat('连续打卡', '${state.streak}天', Colors.orangeAccent),
              _stat('今日', '${today.reviewed}题', Colors.greenAccent),
              _stat('错题', '$shakyCount', Colors.redAccent),
            ]),
          ),
          const SizedBox(height: 12),
          Panel(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('打卡热力 · 近 18 周', style: TextStyle(fontSize: 13, color: Colors.grey.shade400)),
              const SizedBox(height: 10),
              HeatmapGrid(daily: state.daily),
            ]),
          ),
          const SizedBox(height: 12),
          Panel(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Column(children: [
              _tile(context, Icons.local_fire_department_outlined, '错题本', '$shakyCount 道需要复盘',
                  () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const WrongBookPage()))),
              _divider(),
              _tile(context, Icons.sticky_note_2_outlined, '我的笔记', '${state.notes.length} 条速记',
                  () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const NotesPage()))),
              _divider(),
              _tile(context, Icons.file_download_outlined, '导出学习数据', '备份进度 / 笔记 / 打卡',
                  () => _export(context)),
              _divider(),
              _tile(context, Icons.file_upload_outlined, '导入学习数据', '从备份 JSON 恢复', () => _import(context)),
              _divider(),
              _tile(context, Icons.restart_alt, '重置学习数据', '清空进度与打卡（不影响题库）', () => _reset(context)),
              _divider(),
              _tile(context, Icons.info_outline, '关于', _aboutText(state), null),
            ]),
          ),
        ],
      ),
    );
  }

  String _aboutText(AppState state) {
    final repo = state.repo;
    if (repo == null) return '内容未加载';
    return '${repo.packs.length} 个领域 · ${repo.totalQuestions} 题 · ${repo.projects.length} 个项目 · ${repo.exps.length} 家面经';
  }

  Future<void> _export(BuildContext context) async {
    try {
      final state = context.read<AppState>();
      final json = await state.exportJson();
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/interview_flash_backup_${DateTime.now().millisecondsSinceEpoch}.json');
      await file.writeAsString(json);
      if (!context.mounted) return;
      await Share.shareXFiles([XFile(file.path)], text: '冲刺Offer·学习数据备份');
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('导出失败：$e')));
      }
    }
  }

  Future<void> _import(BuildContext context) async {
    final state = context.read<AppState>();
    final ctrl = TextEditingController();
    final clipboard = await Clipboard.getData(Clipboard.kTextPlain);
    if (clipboard?.text != null && clipboard!.text!.trim().startsWith('{')) {
      ctrl.text = clipboard.text!.trim();
    }
    if (!context.mounted) return;
    final raw = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('导入学习数据'),
        content: SizedBox(
          width: 520,
          child: TextField(
            controller: ctrl,
            maxLines: 10,
            style: const TextStyle(fontSize: 12, fontFamily: 'Menlo'),
            decoration: const InputDecoration(
              hintText: '粘贴备份 JSON 内容（导出文件里的全部文本）',
              border: OutlineInputBorder(),
              isDense: true,
            ),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(null), child: const Text('取消')),
          FilledButton(onPressed: () => Navigator.of(ctx).pop(ctrl.text), child: const Text('导入')),
        ],
      ),
    );
    if (raw == null || raw.trim().isEmpty) return;
    try {
      final n = await state.importJson(raw);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('已导入 $n 条记录')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('导入失败：$e')));
      }
    }
  }

  Future<void> _reset(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('重置学习数据？'),
        content: const Text('将清空所有刷题进度、打卡记录与模拟面试战报，且不可恢复。笔记会保留。'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('取消')),
          FilledButton(onPressed: () => Navigator.of(ctx).pop(true), child: const Text('确认重置')),
        ],
      ),
    );
    if (ok == true && context.mounted) {
      await context.read<AppState>().resetStudyData();
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('已重置')));
      }
    }
  }

  Widget _stat(String label, String n, Color c) {
    return Column(children: [
      Text(n, style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: c)),
      Text(label, style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
    ]);
  }

  Widget _tile(BuildContext context, IconData icon, String title, String sub, VoidCallback? onTap) {
    return ListTile(
      dense: true,
      onTap: onTap,
      leading: Icon(icon, size: 20),
      title: Text(title, style: const TextStyle(fontSize: 14)),
      subtitle: Text(sub, style: TextStyle(fontSize: 11.5, color: Colors.grey.shade500)),
      trailing: onTap == null ? null : const Icon(Icons.chevron_right, size: 18),
    );
  }

  Widget _divider() => const Divider(indent: 12, endIndent: 12, height: 0.5);
}

/// 错题本：最近答错 / 多次遗忘的题。
class WrongBookPage extends StatelessWidget {
  const WrongBookPage({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final wrong = <Question>[];
    for (final p in state.repo?.packs ?? const <(DomainMeta, List<Question>)>[]) {
      for (final q in p.$2) {
        final r = state.progress[q.id];
        if (r != null && r.isShaky) wrong.add(q);
      }
    }
    wrong.sort((a, b) => (state.progress[b.id]!.lapses).compareTo(state.progress[a.id]!.lapses));
    return Scaffold(
      appBar: AppBar(title: Text('错题本 (${wrong.length})')),
      body: wrong.isEmpty
          ? const EmptyView('暂无错题，继续保持！')
          : ListView.builder(
              padding: const EdgeInsets.fromLTRB(14, 8, 14, 20),
              itemCount: wrong.length,
              itemBuilder: (context, i) {
                final q = wrong[i];
                final r = state.progress[q.id]!;
                return Column(children: [
                  Row(children: [
                    Text('${q.domainName} · 遗忘${r.lapses}次', style: TextStyle(fontSize: 10.5, color: Colors.redAccent.shade200)),
                  ]),
                  QuestionTile(
                    q: q,
                    status: state.statusOf(q.id),
                    onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => QuestionDetailPage(qid: q.id))),
                  ),
                ]);
              },
            ),
    );
  }
}

/// 我的笔记（含语音回听）。
class NotesPage extends StatefulWidget {
  const NotesPage({super.key});

  @override
  State<NotesPage> createState() => _NotesPageState();
}

class _NotesPageState extends State<NotesPage> {
  final player = AudioPlayController();

  @override
  void dispose() {
    player.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final notes = state.notes;
    return Scaffold(
      appBar: AppBar(title: Text('我的笔记 (${notes.length})')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => showNoteSheet(context),
        icon: const Icon(Icons.add),
        label: const Text('记一笔'),
      ),
      body: notes.isEmpty
          ? const EmptyView('还没有笔记。刷题或模拟面试时随手记一笔。')
          : ListView.builder(
              padding: const EdgeInsets.fromLTRB(14, 8, 14, 80),
              itemCount: notes.length,
              itemBuilder: (context, i) {
                final n = notes[i];
                final q = n.qid != null ? state.repo?.byId[n.qid] : null;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Panel(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      if (q != null)
                        GestureDetector(
                          onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => QuestionDetailPage(qid: q.id))),
                          child: Text('📎 ${q.question}', maxLines: 1, overflow: TextOverflow.ellipsis,
                              style: TextStyle(fontSize: 11.5, color: Theme.of(context).colorScheme.primary)),
                        ),
                      if (q != null) const SizedBox(height: 6),
                      SelectableText(n.text, style: const TextStyle(fontSize: 13.5, height: 1.5)),
                      const SizedBox(height: 8),
                      Row(children: [
                        if (n.tagList.isNotEmpty)
                          Expanded(
                            child: Wrap(
                              spacing: 6,
                              children: [for (final t in n.tagList) Text('#$t', style: TextStyle(fontSize: 11, color: Colors.lightBlueAccent.shade100))],
                            ),
                          ),
                        if (n.audioPath != null)
                          IconButton(
                            visualDensity: VisualDensity.compact,
                            icon: Icon(player.playingPath == n.audioPath ? Icons.stop : Icons.play_arrow, size: 18),
                            tooltip: '播放录音',
                            onPressed: () => player.toggle(n.audioPath!),
                          ),
                        IconButton(
                          visualDensity: VisualDensity.compact,
                          icon: Icon(Icons.delete_outline, size: 17, color: Colors.grey.shade500),
                          onPressed: () => context.read<AppState>().deleteNote(n.id!),
                        ),
                      ]),
                      Text(formatDate(n.createdAt), style: TextStyle(fontSize: 10, color: Colors.grey.shade600)),
                    ]),
                  ),
                );
              },
            ),
    );
  }
}
