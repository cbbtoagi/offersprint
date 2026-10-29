/// 公式定界符归一化 + 渲染无残留美元符号的回归测试。
library;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:interview_flash/widgets/markdown_view.dart';

const String dollar = '\$';
const String ddouble = '\$\$';

void main() {
  test('normalizeLatex: 显示公式与行内公式均转为反斜杠定界', () {
    const src = '梯度为 ${ddouble}\\\\nabla L(\\\\theta)=\\\\frac{1}{m}\\\\sum X$ddouble，其中 ${dollar}\\\\alpha>0$dollar 是学习率。';
    final out = Md.normalizeLatex(src);
    expect(out.contains(r'\['), isTrue, reason: out);
    expect(out.contains(r'\('), isTrue, reason: out);
    expect(out.contains(ddouble), isFalse, reason: out);
  });

  testWidgets('渲染后不残留裸美元符号', (tester) async {
    const src = '损失 ${ddouble}L=-\\\\sum_i y_i\\\\log(\\\\hat{y}_i)$ddouble 与 ${dollar}\\\\lambda\\\\ge 0$dollar 的关系';
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: Md(src)),
      ),
    );
    await tester.pumpAndSettle();
    final texts = tester.widgetList<Text>(find.byType(Text)).map((t) => t.data ?? '').toList();
    for (final t in texts) {
      expect(t.contains(dollar), isFalse, reason: '发现残留美元符号: $t');
    }
  });

  testWidgets('代码块内的美元符号不参与公式', (tester) async {
    const src = '示例：```python\nprice = "${dollar}100"\n``` 完';
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Md(src))));
    await tester.pumpAndSettle();
    expect(find.textContaining('price'), findsWidgets);
  });
}
