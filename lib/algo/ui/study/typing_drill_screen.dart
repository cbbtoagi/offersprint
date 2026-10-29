import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../demo/demo_mode.dart';
import '../../models/problem.dart';
import '../../providers.dart';
import '../../services/comparison.dart';
import '../../theme.dart';
import '../widgets/code_view.dart';
import 'study_screen.dart' show SampleBlock;

/// 默写评测：看题默写 Python，提交后 token 相似度 + 结构命中 + 逐行 diff。
class TypingDrillScreen extends ConsumerStatefulWidget {
  const TypingDrillScreen({super.key, required this.problem});

  final Problem problem;

  @override
  ConsumerState<TypingDrillScreen> createState() => _TypingDrillScreenState();
}

class _TypingDrillScreenState extends ConsumerState<TypingDrillScreen> {
  final _controller = TextEditingController();
  final _elapsed = Stopwatch();
  ComparisonResult? _result;
  bool _showDiff = true;
  Timer? _typingTimer;
  int _typed = 0;

  @override
  void initState() {
    super.initState();
    if (DemoMode.enabled) {
      // 演示：逐字「敲入」参考代码 → 提交 → 展示比对 → 返回
      Future.delayed(const Duration(milliseconds: 500), _demoType);
      Future.delayed(const Duration(milliseconds: 10200), _demoSubmit);
      Future.delayed(const Duration(milliseconds: 14000), () {
        if (mounted && Navigator.of(context).canPop()) {
          Navigator.of(context).pop();
        }
      });
    }
  }

  void _demoType() {
    const chunk = 7;
    _typingTimer = Timer.periodic(const Duration(milliseconds: 40), (t) {
      final code = widget.problem.code;
      if (_typed >= code.length) {
        t.cancel();
        return;
      }
      _typed = (_typed + chunk).clamp(0, code.length);
      final text = code.substring(0, _typed);
      setState(() {
        _controller
          ..text = text
          ..selection = TextSelection.collapsed(offset: text.length);
      });
    });
  }

  Future<void> _demoSubmit() async {
    _typingTimer?.cancel();
    if (_result != null) return;
    await _submit();
  }

  @override
  void dispose() {
    _typingTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final result = compare(widget.problem.code, _controller.text,
        widget.problem.structureTags);
    await ref.read(submitProvider).record(
          problemId: widget.problem.id,
          kind: ReviewKind.typing,
          score: result.score,
          detail: '相似度 ${(result.similarity * 100).toStringAsFixed(0)}% · '
              '耗时 ${_elapsed.elapsed.inSeconds}s',
        );
    setState(() => _result = result);
  }

  @override
  Widget build(BuildContext context) {
    final r = _result;
    return Scaffold(
      appBar: AppBar(title: Text('默写 · ${widget.problem.titleCn}')),
      body: Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 860),
          child: r == null ? _editor(context) : _result_(r),
        ),
      ),
    );
  }

  Widget _editor(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(
            flex: 2,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('#${widget.problem.id} ${widget.problem.titleCn}',
                      style: const TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w700)),
                  if (widget.problem.companies.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text('大厂高频：${widget.problem.companies.join(' · ')}',
                        style: const TextStyle(
                            fontSize: 12, color: Color(0xFF9B7DF2))),
                  ],
                  const SizedBox(height: 8),
                  Text(widget.problem.question,
                      style: const TextStyle(height: 1.5)),
                  for (var i = 0; i < widget.problem.samples.length; i++) ...[
                    const SizedBox(height: 10),
                    SampleBlock(
                        index: i + 1, sample: widget.problem.samples[i]),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text('⏱ ${_elapsed.elapsed.inSeconds}s · 结构标签: '
              '${widget.problem.structureTags.join(', ')}',
              style: const TextStyle(color: AppTheme.muted, fontSize: 12)),
          const SizedBox(height: 8),
          Expanded(
            flex: 3,
            child: CodeField(controller: _controller),
          ),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(
              child: FilledButton.icon(
                icon: const Icon(Icons.check),
                label: const Text('提交比对'),
                onPressed: _submit,
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              tooltip: '提示：查看审题诀窍',
              onPressed: () => showModalBottomSheet(
                context: context,
                builder: (_) => ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    const Text('🔍 审题诀窍', style: TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 8),
                    for (final h in widget.problem.hints)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Text('· $h', style: const TextStyle(height: 1.5)),
                      ),
                  ],
                ),
              ),
              icon: const Icon(Icons.lightbulb_outline),
            ),
          ]),
        ],
      ),
    );
  }

  Widget _result_(ComparisonResult r) {
    final scoreColor =
        r.score >= 85 ? AppTheme.good : (r.score >= 60 ? AppTheme.accent : AppTheme.bad);
    return ListView(
      padding: const EdgeInsets.all(14),
      children: [
        Row(children: [
          Text(r.score.toStringAsFixed(0),
              style: TextStyle(fontSize: 44, fontWeight: FontWeight.w800, color: scoreColor)),
          const SizedBox(width: 6),
          Text('分\n相似度 ${(r.similarity * 100).toStringAsFixed(0)}%',
              style: const TextStyle(color: AppTheme.muted, height: 1.4)),
          const Spacer(),
          if (r.missingStructures.isNotEmpty)
            Flexible(
              child: Text('缺失结构: ${r.missingStructures.join(', ')}',
                  style: const TextStyle(color: AppTheme.bad)),
            ),
        ]),
        const SizedBox(height: 12),
        SegmentedButton<bool>(
          segments: const [
            ButtonSegment(value: true, label: Text('逐行 diff')),
            ButtonSegment(value: false, label: Text('参考答案')),
          ],
          selected: {_showDiff},
          onSelectionChanged: (s) => setState(() => _showDiff = s.first),
        ),
        const SizedBox(height: 10),
        if (_showDiff)
          for (final d in r.diffLines)
            _DiffLine(type: d[0], text: d[1])
        else
          CodeView(code: widget.problem.code),
        const SizedBox(height: 16),
        Row(children: [
          Expanded(
            child: OutlinedButton(
              onPressed: () {
                _elapsed.reset();
                setState(() => _result = null);
              },
              child: const Text('再默写一次'),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: FilledButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('完成'),
            ),
          ),
        ]),
      ],
    );
  }
}

class _DiffLine extends StatelessWidget {
  const _DiffLine({required this.type, required this.text});

  final String type; // same / missing / extra
  final String text;

  @override
  Widget build(BuildContext context) {
    final (color, icon) = switch (type) {
      ('missing') => (AppTheme.bad, '− 缺失'),
      ('extra') => (const Color(0xFFF2B94B), '+ 多余'),
      _ => (AppTheme.muted, '  '),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      margin: const EdgeInsets.only(bottom: 2),
      decoration: BoxDecoration(
        color: type == 'same'
            ? Colors.transparent
            : color.withValues(alpha: .08),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text.rich(
        TextSpan(children: [
          TextSpan(text: '$icon  ', style: TextStyle(color: color, fontSize: 11)),
          TextSpan(text: text, style: const TextStyle(fontFamily: 'Menlo', fontSize: 12, height: 1.5)),
        ]),
      ),
    );
  }
}
