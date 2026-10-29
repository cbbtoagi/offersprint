/// Markdown 渲染封装（含 LaTeX 公式与代码块）。
library;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_math_fork/flutter_math.dart' as math;
import 'package:gpt_markdown/gpt_markdown.dart';

class Md extends StatelessWidget {
  final String data;
  final double fontSize;
  const Md(this.data, {super.key, this.fontSize = 14.5});

  /// 内容使用标准 KaTeX 定界符（$...$ / $$...$$），
  /// gpt_markdown 1.2.x 仅识别 \(...\) 与 \[...\]，这里统一转换。
  static final RegExp _displayMath = RegExp(r'\$\$([\s\S]+?)\$\$');
  static final RegExp _inlineMath = RegExp(r'(?<![\\$])\$(?!\$)((?:\\.|[^$\n])+?)\$(?!\$)');

  static String normalizeLatex(String src) {
    return src.replaceAllMapped(_displayMath, (m) => '\\[${m.group(1)}\\]').replaceAllMapped(
          _inlineMath,
          (m) => '\\(${m.group(1)}\\)',
        );
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return SelectionArea(
      child: GptMarkdown(
        normalizeLatex(data),
        style: TextStyle(fontSize: fontSize, height: 1.65, color: cs.onSurface.withValues(alpha: 0.94)),
        latexBuilder: (context, tex, textStyle, inline) {
          final rendered = math.Math.tex(
            tex,
            textStyle: textStyle,
            mathStyle: inline ? math.MathStyle.text : math.MathStyle.display,
            settings: const math.TexParserSettings(strict: math.Strict.ignore),
            options: math.MathOptions(
              style: inline ? math.MathStyle.text : math.MathStyle.display,
              fontSize: textStyle.fontSize ?? 14.5,
              color: textStyle.color ?? cs.onSurface,
            ),
          );
          // 公式内部 Line 不允许溢出：用 FittedBox 给内部无界约束并按宽缩放
          return FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: rendered,
          );
        },
        codeBuilder: (context, name, code, closed) => _codeBlock(context, code, closed),
      ),
    );
  }

  Widget _codeBlock(BuildContext context, String code, bool closed) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: cs.surfaceContainerHighest.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: cs.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Stack(children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
          child: Text(
            code,
            style: const TextStyle(fontFamily: 'Menlo', fontFamilyFallback: ['monospace'], fontSize: 12.5, height: 1.5),
          ),
        ),
        Positioned(
          right: 4,
          top: 2,
          child: IconButton(
            visualDensity: VisualDensity.compact,
            icon: Icon(Icons.copy, size: 14, color: cs.outline),
            tooltip: '复制代码',
            onPressed: () => Clipboard.setData(ClipboardData(text: code)),
          ),
        ),
      ]),
    );
  }
}
