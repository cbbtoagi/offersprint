import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../demo/demo_mode.dart';
import '../../models/problem.dart';
import '../../providers.dart';
import '../../theme.dart';

/// 思路自述：语音输入（平台原生识别）或文本输入 + 关键点自评清单。
class VerbalScreen extends ConsumerStatefulWidget {
  const VerbalScreen({super.key, required this.problem});

  final Problem problem;

  @override
  ConsumerState<VerbalScreen> createState() => _VerbalScreenState();
}

class _VerbalScreenState extends ConsumerState<VerbalScreen> {
  final _textCtrl = TextEditingController();
  final _checked = <int>{};
  bool _listening = false;
  bool _micError = false;
  Timer? _typingTimer;
  int _typed = 0;

  static const _demoText =
      '这道题用一遍哈希表：遍历数组，对每个数 x 先查 target - x 是否在表里，'
      '在就直接返回两个下标；不在就把 x 和它的下标存进去。'
      '先查后存保证不会用同一个元素两次，时间和空间都是 O(n)。';

  @override
  void initState() {
    super.initState();
    if (DemoMode.enabled) {
      // 演示：自动键入自述文本 → 勾选关键点 → 保存
      Future.delayed(const Duration(milliseconds: 500), () {
        _typingTimer = Timer.periodic(const Duration(milliseconds: 30), (t) {
          if (_typed >= _demoText.length) {
            t.cancel();
            return;
          }
          _typed = (_typed + 2).clamp(0, _demoText.length);
          final text = _demoText.substring(0, _typed);
          setState(() {
            _textCtrl
              ..text = text
              ..selection = TextSelection.collapsed(offset: text.length);
          });
        });
      });
      Future.delayed(const Duration(milliseconds: 4200), () {
        if (!mounted) return;
        setState(() => _checked.addAll({0, 1, 2, 3}));
      });
      Future.delayed(const Duration(milliseconds: 5600), () {
        if (mounted) _save();
      });
    }
  }

  @override
  void dispose() {
    _typingTimer?.cancel();
    _textCtrl.dispose();
    super.dispose();
  }

  Future<void> _toggleMic() async {
    final speech = ref.read(speechProvider);
    if (_listening) {
      await speech.stop();
      setState(() => _listening = false);
      return;
    }
    final ok = await speech.init();
    if (!ok) {
      setState(() => _micError = true);
      return;
    }
    setState(() {
      _micError = false;
      _listening = true;
    });
    await speech.listen(
      onResult: (text, isFinal) {
        _textCtrl
          ..text = text
          ..selection = TextSelection.collapsed(offset: text.length);
        if (isFinal) setState(() => _listening = false);
      },
    );
  }

  double get _score => _checked.isEmpty
      ? 0
      : _checked.length / widget.problem.keyPoints.length * 100;

  Future<void> _save() async {
    await ref.read(submitProvider).record(
          problemId: widget.problem.id,
          kind: ReviewKind.verbal,
          score: _score,
          detail: _textCtrl.text,
          hitKeyPoints: _checked.toList(),
        );
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final kp = widget.problem.keyPoints;
    return Scaffold(
      appBar: AppBar(title: Text('思路自述 · ${widget.problem.titleCn}')),
      body: Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 780),
          child: ListView(
            padding: const EdgeInsets.all(14),
            children: [
              Text(widget.problem.titleCn,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              const Text('假设你在面试官面前：用自己的话讲清这道题的解题思路。',
                  style: TextStyle(color: AppTheme.muted)),
              const SizedBox(height: 14),
              TextField(
                controller: _textCtrl,
                maxLines: 6,
                decoration: InputDecoration(
                  hintText: _listening ? '正在聆听…请直接说出你的思路' : '口述或键入你的解题思路…',
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 10),
              Row(children: [
                FilledButton.tonalIcon(
                  icon: Icon(_listening ? Icons.stop : Icons.mic),
                  label: Text(_listening ? '停止' : '语音输入'),
                  onPressed: _toggleMic,
                ),
                const SizedBox(width: 10),
                if (_micError)
                  const Expanded(
                    child: Text('无法启动语音识别：请检查系统麦克风权限（设置 → 隐私 → 麦克风）',
                        style: TextStyle(color: AppTheme.bad, fontSize: 12)),
                  ),
                if (_listening)
                  const Text('● 录音中', style: TextStyle(color: AppTheme.bad)),              ]),
              const Divider(height: 28),
              Text('关键点自评（命中 ${_checked.length}/${kp.length}）',
                  style: const TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(height: 6),
              for (var i = 0; i < kp.length; i++)
                CheckboxListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  value: _checked.contains(i),
                  title: Text(kp[i], style: const TextStyle(fontSize: 14)),
                  onChanged: (v) => setState(() =>
                      v == true ? _checked.add(i) : _checked.remove(i)),
                ),
              const SizedBox(height: 8),
              Text('自评得分：${_score.toStringAsFixed(0)}',
                  style: TextStyle(
                      color: _score >= 80 ? AppTheme.good : AppTheme.accent,
                      fontWeight: FontWeight.w600)),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _textCtrl.text.trim().isEmpty
                    ? null
                    : _save,
                child: const Text('保存自评并落盘'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
