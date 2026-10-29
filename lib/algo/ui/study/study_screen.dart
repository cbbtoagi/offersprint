import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../demo/demo_mode.dart';
import '../../models/problem.dart';
import '../../theme.dart';
import '../widgets/code_view.dart';
import 'typing_drill_screen.dart';
import 'verbal_screen.dart';

/// 卡片学习流：每题一叠卡
///   题目卡（读题+审题诀窍）→ 思路卡（多思路）→ 代码卡 → 出口卡
/// 支持多题连续学习（如「今日待复习」整组进入）。
class StudyScreen extends ConsumerStatefulWidget {
  const StudyScreen({super.key, required this.problems, required this.startIndex});

  final List<Problem> problems;
  final int startIndex;

  @override
  ConsumerState<StudyScreen> createState() => _StudyScreenState();
}

class _StudyScreenState extends ConsumerState<StudyScreen> {
  late final PageController _controller;
  late int _page;

  @override
  void initState() {
    super.initState();
    _page = widget.startIndex;
    _controller = PageController(initialPage: widget.startIndex);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  int get _total => widget.problems.length;

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 700;
    return Scaffold(
      appBar: AppBar(
        title: Text('学习 ${_page + 1}/$_total'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('结束本组'),
          ),
        ],
      ),
      body: PageView.builder(
        controller: _controller,
        itemCount: _total,
        onPageChanged: (i) => setState(() => _page = i),
        itemBuilder: (context, i) => _ProblemDeck(
          problem: widget.problems[i],
          wide: wide,
          onNext: i < _total - 1
              ? () => _controller.nextPage(
                  duration: const Duration(milliseconds: 250), curve: Curves.easeOut)
              : null,
        ),
      ),
    );
  }
}

/// 单题卡片组
class _ProblemDeck extends ConsumerStatefulWidget {
  const _ProblemDeck({
    required this.problem,
    required this.wide,
    required this.onNext,
  });

  final Problem problem;
  final bool wide;
  final VoidCallback? onNext;

  @override
  ConsumerState<_ProblemDeck> createState() => _ProblemDeckState();
}

class _ProblemDeckState extends ConsumerState<_ProblemDeck>
    with TickerProviderStateMixin {
  late final TabController _tab = TabController(length: 4, vsync: this);

  @override
  void initState() {
    super.initState();
    if (DemoMode.enabled) {
      // 演示时间线：读题 12s → 思路 13s → 代码 8s → 评测
      Future.delayed(const Duration(milliseconds: 10500),
          () => _tab.animateTo(1));
      Future.delayed(const Duration(milliseconds: 23500),
          () => _tab.animateTo(2));
      Future.delayed(const Duration(milliseconds: 31500),
          () => _tab.animateTo(3));
    }
  }

  @override
  void dispose() {
    _tab.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final content = <Widget>[
      _QuestionCard(problem: widget.problem, wide: widget.wide),
      _ApproachCard(problem: widget.problem, wide: widget.wide),
      _CodeCard(problem: widget.problem, wide: widget.wide),
      _ExitCard(problem: widget.problem, onNext: widget.onNext),
    ];
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 780),
        child: Scaffold(
          backgroundColor: Colors.transparent,
          appBar: TabBar(
            controller: _tab,
            tabs: const [
              Tab(text: '① 读题'),
              Tab(text: '② 思路'),
              Tab(text: '③ 代码'),
              Tab(text: '④ 评测'),
            ],
          ),
          body: TabBarView(controller: _tab, children: content),
        ),
      ),
    );
  }
}

String _difficultyLabel(String d) => AppTheme.difficultyCn(d);

class _QuestionCard extends StatefulWidget {
  const _QuestionCard({required this.problem, required this.wide});

  final Problem problem;
  final bool wide;

  @override
  State<_QuestionCard> createState() => _QuestionCardState();
}

class _QuestionCardState extends State<_QuestionCard> {
  final revealed = ValueNotifier<bool>(false);

  @override
  void initState() {
    super.initState();
    if (DemoMode.enabled) {
      Future.delayed(const Duration(milliseconds: 5500),
          () => revealed.value = true);
    }
  }

  @override
  void dispose() {
    revealed.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final problem = widget.problem;
    return Padding(
      padding: const EdgeInsets.all(14),
      child: ListView(
        children: [
          Row(
            children: [
              Text('#${problem.id} ${problem.titleCn}',
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
              const SizedBox(width: 10),
              _Badge(text: _difficultyLabel(problem.difficulty),
                  color: AppTheme.difficultyColors[problem.difficulty]!),
              _Badge(text: '热度${'★' * problem.frequency}', color: AppTheme.accent),
            ],
          ),
          Text(problem.title, style: const TextStyle(color: AppTheme.muted)),
          const SizedBox(height: 8),
          if (problem.companies.isNotEmpty)
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: [
                for (final c in problem.companies)
                  _Badge(text: c, color: const Color(0xFF9B7DF2)),
              ],
            ),
          const SizedBox(height: 12),
          Text(problem.question, style: const TextStyle(height: 1.6)),
          for (var i = 0; i < problem.samples.length; i++) ...[
            const SizedBox(height: 12),
            SampleBlock(index: i + 1, sample: problem.samples[i]),
          ],
          const Divider(height: 28),
          ValueListenableBuilder<bool>(
            valueListenable: revealed,
            builder: (context, ok, _) => ok
                ? Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('🔍 审题诀窍',
                          style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                      const SizedBox(height: 8),
                      for (final h in problem.hints)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('· ', style: TextStyle(color: AppTheme.accent)),
                              Expanded(child: Text(h, style: const TextStyle(height: 1.5))),
                            ],
                          ),
                        ),
                    ],
                  )
                : FilledButton.tonalIcon(
                    onPressed: () => revealed.value = true,
                    icon: const Icon(Icons.visibility),
                    label: const Text('先自己想 30 秒，再揭示审题诀窍'),
                  ),
          ),
        ],
      ),
    );
  }
}

class _ApproachCard extends StatefulWidget {
  const _ApproachCard({required this.problem, required this.wide});

  final Problem problem;
  final bool wide;

  @override
  State<_ApproachCard> createState() => _ApproachCardState();
}

class _ApproachCardState extends State<_ApproachCard> {
  final revealed = ValueNotifier<int>(0); // 已揭示的思路数

  @override
  void initState() {
    super.initState();
    if (DemoMode.enabled) {
      Future.delayed(const Duration(milliseconds: 1500),
          () => revealed.value = 1);
      Future.delayed(const Duration(milliseconds: 10500),
          () => revealed.value = 2);
    }
  }

  @override
  void dispose() {
    revealed.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final problem = widget.problem;
    return Padding(
      padding: const EdgeInsets.all(14),
      child: ValueListenableBuilder<int>(
        valueListenable: revealed,
        builder: (context, shown, _) => ListView(
          children: [
            const Text('解题思路（由浅入深，逐个揭示）',
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
            const SizedBox(height: 10),
            for (var i = 0; i < problem.approaches.length; i++)
              if (i < shown)
                _ApproachTile(a: problem.approaches[i])
              else
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: OutlinedButton(
                    onPressed: () => revealed.value = i + 1,
                    child: Text('揭示思路 ${i + 1}'),
                  ),
                ),
          ],
        ),
      ),
    );
  }
}

class _ApproachTile extends StatefulWidget {
  const _ApproachTile({required this.a});

  final Approach a;

  @override
  State<_ApproachTile> createState() => _ApproachTileState();
}

class _ApproachTileState extends State<_ApproachTile> {
  bool _detailOpen = false;
  bool _codeOpen = false;

  @override
  void initState() {
    super.initState();
    if (DemoMode.enabled) {
      Future.delayed(const Duration(milliseconds: 3000),
          () => mounted ? setState(() => _detailOpen = true) : null);
      Future.delayed(const Duration(milliseconds: 6500),
          () => mounted ? setState(() => _codeOpen = true) : null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final a = widget.a;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Flexible(
                child: Text(a.name,
                    style: const TextStyle(
                        fontWeight: FontWeight.w700, fontSize: 15)),
              ),
              const SizedBox(width: 8),
              if (a.optimal) const _Badge(text: '最优解', color: AppTheme.good),
            ]),
            const SizedBox(height: 6),
            Text(a.idea, style: const TextStyle(height: 1.5)),
            const SizedBox(height: 8),
            Text(a.complexity,
                style: const TextStyle(color: AppTheme.accent, fontSize: 12)),
            // 展开教学：步骤拆解 + 示例走查 + 易错点
            if (a.detail.isNotEmpty) ...[
              const SizedBox(height: 10),
              InkWell(
                onTap: () => setState(() => _detailOpen = !_detailOpen),
                child: Row(children: [
                  Icon(_detailOpen ? Icons.expand_less : Icons.expand_more,
                      size: 18, color: AppTheme.accent),
                  const SizedBox(width: 4),
                  Text(_detailOpen ? '收起讲解' : '展开讲解（步骤拆解 · 走查 · 易错点）',
                      style: const TextStyle(color: AppTheme.accent, fontSize: 13)),
                ]),
              ),
              if (_detailOpen)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(a.detail,
                      style: const TextStyle(height: 1.65, fontSize: 13.5)),
                ),
            ],
            // 该思路的实现代码
            if (a.code != null && a.code!.isNotEmpty) ...[
              const SizedBox(height: 10),
              InkWell(
                onTap: () => setState(() => _codeOpen = !_codeOpen),
                child: Row(children: [
                  Icon(_codeOpen ? Icons.code_off : Icons.code,
                      size: 18, color: AppTheme.accent),
                  const SizedBox(width: 4),
                  Text(_codeOpen ? '收起本思路代码' : '查看本思路代码',
                      style:
                          const TextStyle(color: AppTheme.accent, fontSize: 13)),
                ]),
              ),
              if (_codeOpen) ...[
                const SizedBox(height: 8),
                CodeView(code: a.code!),
              ],
            ],
          ],
        ),
      ),
    );
  }
}

class _CodeCard extends StatefulWidget {
  const _CodeCard({required this.problem, required this.wide});

  final Problem problem;
  final bool wide;

  @override
  State<_CodeCard> createState() => _CodeCardState();
}

class _CodeCardState extends State<_CodeCard> {
  bool _showAcm = false;
  bool _acmCpp = false; // ACM 模式下选 C++ 还是 Python
  String _lang = 'python'; // 核心代码语言

  @override
  void initState() {
    super.initState();
    if (DemoMode.enabled) {
      Future.delayed(const Duration(milliseconds: 4000),
          () => mounted ? setState(() => _showAcm = true) : null);
      Future.delayed(const Duration(milliseconds: 6500),
          () => mounted ? setState(() => _acmCpp = true) : null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final problem = widget.problem;
    final optimal = problem.approaches.where((a) => a.optimal).toList();
    final hasAcm = problem.acmCode.isNotEmpty;
    final hasAcmCpp = problem.acmCodeCpp.isNotEmpty;
    final langs = <(String, String, String)>[
      ('python', 'Python', problem.code),
      if (problem.codeCpp.isNotEmpty) ('cpp', 'C++', problem.codeCpp),
      if (problem.codeJava.isNotEmpty) ('java', 'Java', problem.codeJava),
      if (problem.codeJs.isNotEmpty) ('javascript', 'JS', problem.codeJs),
      if (problem.codeGo.isNotEmpty) ('go', 'Go', problem.codeGo),
    ];
    if (!langs.any((l) => l.$1 == _lang)) _lang = 'python';
    final currentCore =
        langs.firstWhere((l) => l.$1 == _lang, orElse: () => langs.first).$3;

    return Padding(
      padding: const EdgeInsets.all(14),
      child: ListView(
        children: [
          Text('最优解：${optimal.isNotEmpty ? optimal.first.name : '参考实现'}',
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
          const SizedBox(height: 6),
          if (optimal.isNotEmpty)
            Text(optimal.first.complexity,
                style: const TextStyle(color: AppTheme.accent, fontSize: 12)),
          const SizedBox(height: 10),
          if (hasAcm)
            SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: false, label: Text('核心代码')),
                ButtonSegment(value: true, label: Text('ACM 完整代码')),
              ],
              selected: {_showAcm},
              onSelectionChanged: (s) => setState(() => _showAcm = s.first),
            ),
          const SizedBox(height: 8),
          if (!_showAcm) ...[
            // 语言选择器
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: [
                for (final (id, label, _) in langs)
                  ChoiceChip(
                    label: Text(label, style: const TextStyle(fontSize: 12)),
                    selected: _lang == id,
                    onSelected: (_) => setState(() => _lang = id),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            CodeView(code: currentCore, language: _lang),
          ] else if (hasAcm) ...[
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppTheme.accent.withValues(alpha: .08),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Text(
                'ACM 模式：自己处理输入读取与结果打印（stdin → stdout），'
                '适用于牛客/各大厂笔试机考。核心逻辑不变，重点在读入模板。',
                style: TextStyle(fontSize: 12, height: 1.5, color: AppTheme.muted),
              ),
            ),
            const SizedBox(height: 8),
            if (hasAcmCpp)
              SegmentedButton<bool>(
                segments: const [
                  ButtonSegment(value: false, label: Text('Python')),
                  ButtonSegment(value: true, label: Text('C++')),
                ],
                selected: {_acmCpp},
                onSelectionChanged: (s) => setState(() => _acmCpp = s.first),
              ),
            const SizedBox(height: 8),
            CodeView(
              code: (_acmCpp && hasAcmCpp) ? problem.acmCodeCpp : problem.acmCode,
              language: (_acmCpp && hasAcmCpp) ? 'cpp' : 'python',
            ),
          ],
          const SizedBox(height: 14),
          const Text('💡 模板迁移提示',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
          const SizedBox(height: 6),
          for (final t in problem.templates)
            Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('· ', style: TextStyle(color: AppTheme.accent)),
                Expanded(child: Text(t, style: const TextStyle(height: 1.5))),
              ]),
            ),
        ],
      ),
    );
  }
}

class _ExitCard extends StatefulWidget {
  const _ExitCard({required this.problem, required this.onNext});

  final Problem problem;
  final VoidCallback? onNext;

  @override
  State<_ExitCard> createState() => _ExitCardState();
}

class _ExitCardState extends State<_ExitCard> {
  @override
  void initState() {
    super.initState();
    if (DemoMode.enabled) {
      // 演示：先默写评测，返回后再来一路思路自述（两者都会自行 pop 回本卡）
      Future.delayed(const Duration(milliseconds: 1500), () {
        if (!mounted) return;
        Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => TypingDrillScreen(problem: widget.problem),
        ));
      });
      Future.delayed(const Duration(milliseconds: 21000), () {
        if (!mounted) return;
        Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => VerbalScreen(problem: widget.problem),
        ));
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final problem = widget.problem;
    final onNext = widget.onNext;
    return Padding(
      padding: const EdgeInsets.all(14),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('已学完本卡，怎么继续？',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 20),
            FilledButton.icon(
              icon: const Icon(Icons.keyboard),
              label: const Text('默写评测（代码默写，逐行比对）'),
              onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => TypingDrillScreen(problem: problem),
              )),
            ),
            const SizedBox(height: 10),
            FilledButton.tonalIcon(
              icon: const Icon(Icons.mic),
              label: const Text('思路自述（语音 / 文本）'),
              onPressed: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => VerbalScreen(problem: problem),
              )),
            ),
            const SizedBox(height: 10),
            OutlinedButton(
              onPressed: onNext,
              child: Text(onNext == null ? '本组学习完成 ✓' : '下一题 →'),
            ),
          ],
        ),
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.text, required this.color});

  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(text, style: TextStyle(color: color, fontSize: 11)),
    );
  }
}

/// 样例输入输出块（读题卡与默写评测共用）
class SampleBlock extends StatelessWidget {
  const SampleBlock({super.key, required this.index, required this.sample});

  final int index;
  final Sample sample;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppTheme.codeBackground,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF1F2430)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('样例 $index',
              style: const TextStyle(
                  fontSize: 12,
                  color: AppTheme.muted,
                  fontWeight: FontWeight.w600)),
          const SizedBox(height: 6),
          if (sample.input.isNotEmpty)
            Text('输入：${sample.input}',
                style: const TextStyle(
                    fontFamily: 'Menlo', fontSize: 12, height: 1.5)),
          if (sample.output.isNotEmpty)
            Text('输出：${sample.output}',
                style: const TextStyle(
                    fontFamily: 'Menlo', fontSize: 12, height: 1.5)),
          if (sample.explain?.isNotEmpty == true)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text('解释：${sample.explain}',
                  style: const TextStyle(
                      fontSize: 12, height: 1.5, color: AppTheme.muted)),
            ),
        ],
      ),
    );
  }
}
