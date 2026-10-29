/// 题库视图：题库 / 项目实战 / 面经 三个子页签。
library;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../repo.dart';
import '../state.dart';
import '../widgets/common.dart';
import 'detail_pages.dart';

class LibraryView extends StatelessWidget {
  const LibraryView({super.key});

  @override
  Widget build(BuildContext context) {
    final ui = context.watch<UiState>();
    return DefaultTabController(
      length: 3,
      initialIndex: ui.libraryTab.clamp(0, 2),
      child: Scaffold(
        appBar: AppBar(
          title: const Text('题库'),
          bottom: TabBar(
            dividerColor: Colors.transparent,
            labelStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
            tabs: const [Tab(text: '八股题库'), Tab(text: '项目实战'), Tab(text: '面经库')],
            onTap: (i) => ui.libraryTab = i,
          ),
        ),
        body: const TabBarView(children: [_BankTab(), _ProjectsTab(), _ExpsTab()]),
      ),
    );
  }
}

// ---------------- 题库 ----------------

class _BankTab extends StatefulWidget {
  const _BankTab();

  @override
  State<_BankTab> createState() => _BankTabState();
}

class _BankTabState extends State<_BankTab> with AutomaticKeepAliveClientMixin {
  String query = '';
  int statusFilter = -1; // -1 全部 0 未学 1 待复习 2 已安排 3 已掌握 4 错题

  @override
  bool get wantKeepAlive => true;

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final state = context.watch<AppState>();
    final repo = state.repo;
    if (repo == null) return const SizedBox.shrink();

    final searching = query.trim().isNotEmpty;

    return Column(children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(14, 10, 14, 6),
        child: TextField(
          decoration: InputDecoration(
            hintText: '搜索题干 / 要点 / 公司…',
            prefixIcon: const Icon(Icons.search, size: 20),
            isDense: true,
            filled: true,
            fillColor: Theme.of(context).colorScheme.surfaceContainerLowest,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
            suffixIcon: searching
                ? IconButton(icon: const Icon(Icons.close, size: 18), onPressed: () => setState(() => query = ''))
                : null,
          ),
          onChanged: (v) => setState(() => query = v),
        ),
      ),
      SizedBox(
        height: 40,
        child: ListView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 14),
          children: [
            for (final (label, val) in [('全部', -1), ('未学', 0), ('待复习', 1), ('进行中', 2), ('已掌握', 3), ('错题', 4)])
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  label: Text(label, style: const TextStyle(fontSize: 12)),
                  selected: statusFilter == val,
                  visualDensity: VisualDensity.compact,
                  onSelected: (_) => setState(() => statusFilter = val),
                ),
              ),
          ],
        ),
      ),
      Expanded(
        child: searching ? _buildSearch(repo) : _buildDomains(state, repo),
      ),
    ]);
  }

  bool _matchStatus(AppState state, Question q) {
    if (statusFilter == -1) return true;
    final st = state.statusOf(q.id);
    if (statusFilter == 4) {
      final r = state.progress[q.id];
      return r != null && r.isShaky;
    }
    return st == statusFilter;
  }

  Widget _buildSearch(ContentRepo repo) {
    final state = context.read<AppState>();
    final results = repo.search(query).where((q) => _matchStatus(state, q)).toList();
    if (results.isEmpty) return const EmptyView('没有匹配的题目');
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(14, 4, 14, 20),
      itemCount: results.length,
      itemBuilder: (context, i) {
        final q = results[i];
        return Column(children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.secondaryContainer.withValues(alpha: 0.4),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(q.domainName, style: const TextStyle(fontSize: 10)),
            ),
            const SizedBox(width: 8),
            Text(q.topic, style: TextStyle(fontSize: 10.5, color: Colors.grey.shade500)),
          ]),
          QuestionTile(
            q: q,
            status: state.statusOf(q.id),
            onTap: () => _openDetail(context, q),
          ),
        ]);
      },
    );
  }

  Widget _buildDomains(AppState state, ContentRepo repo) {
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(10, 4, 10, 20),
      itemCount: repo.packs.length,
      itemBuilder: (context, i) {
        final (meta, qs) = repo.packs[i];
        final filtered = qs.where((q) => _matchStatus(state, q)).toList();
        final learned = qs.where((q) => !(state.progress[q.id]?.isNew ?? true)).length;
        final m = state.masteryOf(meta.id);
        return ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 12),
          childrenPadding: const EdgeInsets.fromLTRB(10, 0, 10, 8),
          initiallyExpanded: i == 0,
          title: Row(children: [
            Text(meta.emoji, style: const TextStyle(fontSize: 17)),
            const SizedBox(width: 8),
            Expanded(child: Text(meta.name, style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.w600))),
            Text('$learned/${qs.length}', style: TextStyle(fontSize: 12, color: Colors.grey.shade500)),
          ]),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 4),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(2),
              child: LinearProgressIndicator(
                value: m,
                minHeight: 3.5,
                backgroundColor: Colors.grey.shade800,
                valueColor: AlwaysStoppedAnimation(m > 0.6 ? Colors.greenAccent : Colors.lightBlueAccent),
              ),
            ),
          ),
          children: [
            if (filtered.isEmpty) const Padding(padding: EdgeInsets.all(12), child: Text('该筛选下暂无题目', style: TextStyle(color: Colors.grey))),
            ..._groupedByTopic(filtered),
          ],
        );
      },
    );
  }

  List<Widget> _groupedByTopic(List<Question> qs) {
    final order = <String>[];
    final map = <String, List<Question>>{};
    for (final q in qs) {
      map.putIfAbsent(q.topic, () => []).add(q);
      if (!order.contains(q.topic)) order.add(q.topic);
    }
    final state = context.read<AppState>();
    final widgets = <Widget>[];
    for (final t in order) {
      widgets.add(Padding(
        padding: const EdgeInsets.fromLTRB(4, 8, 0, 2),
        child: Row(children: [
          Container(width: 3, height: 12, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 6),
          Text(t, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.grey.shade400)),
          const SizedBox(width: 8),
          Text('${map[t]!.length}题', style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
        ]),
      ));
      for (final q in map[t]!) {
        widgets.add(QuestionTile(
          q: q,
          status: state.statusOf(q.id),
          onTap: () => _openDetail(context, q),
        ));
      }
    }
    return widgets;
  }

  void _openDetail(BuildContext context, Question q) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => QuestionDetailPage(qid: q.id)));
  }
}

// ---------------- 项目实战 ----------------

class _ProjectsTab extends StatelessWidget {
  const _ProjectsTab();

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final projects = state.repo?.projects ?? const [];
    if (projects.isEmpty) return const EmptyView('项目实战内容生成中…');
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 20),
      itemCount: projects.length,
      itemBuilder: (context, i) {
        final p = projects[i];
        final meta = domainMeta(p.domain);
        final levelColor = switch (p.level) {
          '前沿' => Colors.deepOrangeAccent,
          '进阶' => Colors.lightBlueAccent,
          _ => Colors.greenAccent,
        };
        return Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Panel(
            onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ProjectDetailPage(projectId: p.id))),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Text(meta?.emoji ?? '📌', style: const TextStyle(fontSize: 16)),
                const SizedBox(width: 8),
                Expanded(child: Text(p.name, style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.w600))),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                  decoration: BoxDecoration(
                    border: Border.all(color: levelColor.withValues(alpha: 0.5)),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(p.level, style: TextStyle(fontSize: 10, color: levelColor)),
                ),
              ]),
              const SizedBox(height: 8),
              Text(
                p.summaryMd.replaceAll(RegExp(r'[*#\n]'), ' ').trim(),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 12.5, color: Colors.grey.shade400, height: 1.4),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                children: p.tags.map((t) => Text('#$t', style: TextStyle(fontSize: 11, color: Theme.of(context).colorScheme.primary))).toList(),
              ),
            ]),
          ),
        );
      },
    );
  }
}

// ---------------- 面经库 ----------------

class _ExpsTab extends StatelessWidget {
  const _ExpsTab();

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final exps = state.repo?.exps ?? const [];
    if (exps.isEmpty) return const EmptyView('面经库内容生成中…');
    final groups = <String, List<InterviewExp>>{};
    for (final e in exps) {
      groups.putIfAbsent(e.group, () => []).add(e);
    }
    return ListView(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 20),
      children: [
        for (final g in groups.keys)
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text(g, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: Colors.grey.shade400)),
            ),
            for (final e in groups[g]!)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Panel(
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ExpDetailPage(expId: e.id))),
                  child: Row(children: [
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(e.company, style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.w600)),
                        const SizedBox(height: 3),
                        Text(e.role, style: TextStyle(fontSize: 12, color: Colors.grey.shade500)),
                      ]),
                    ),
                    Column(children: [
                      Text('★' * e.difficulty, style: const TextStyle(fontSize: 11, color: Colors.amberAccent)),
                      const SizedBox(height: 4),
                      Text('${e.questions.length}题', style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
                    ]),
                  ]),
                ),
              ),
          ]),
      ],
    );
  }
}
