/// 逐题公式渲染测试：每题独立 testWidgets，定位渲染卡顿的具体题目。
library;
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:interview_flash/repo.dart';
import 'package:interview_flash/widgets/markdown_view.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late ContentRepo repo;

  setUpAll(() async {
    repo = await ContentRepo.load();
  });

  Future<void> renderAndCheck(WidgetTester tester, String qid) async {
    final q = repo.byId[qid];
    expect(q, isNotNull, reason: '题目不存在: $qid');
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(
            width: 400,
            height: 3000,
            child: SingleChildScrollView(child: Md(q!.answerMd)),
          ),
        ),
      ),
    );
    for (int i = 0; i < 6; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }
    final texts = tester.widgetList<Text>(find.byType(Text)).map((t) => t.data ?? '');
    for (final t in texts) {
      expect(t.contains('\u0024'), isFalse, reason: '$qid 渲染残留美元符号: ${t.substring(0, t.length.clamp(0, 80))}');
    }
  }

  testWidgets('basics-029', (tester) => renderAndCheck(tester, 'basics-029'), timeout: const Timeout(Duration(minutes: 2)));
  testWidgets('rl-017', (tester) => renderAndCheck(tester, 'rl-017'), timeout: const Timeout(Duration(minutes: 2)));
  testWidgets('basics-037', (tester) => renderAndCheck(tester, 'basics-037'), timeout: const Timeout(Duration(minutes: 2)));
  testWidgets('basics-022', (tester) => renderAndCheck(tester, 'basics-022'), timeout: const Timeout(Duration(minutes: 2)));
  testWidgets('rl-015', (tester) => renderAndCheck(tester, 'rl-015'), timeout: const Timeout(Duration(minutes: 2)));
  testWidgets('posttrain-030', (tester) => renderAndCheck(tester, 'posttrain-030'), timeout: const Timeout(Duration(minutes: 2)));
  testWidgets('posttrain-025', (tester) => renderAndCheck(tester, 'posttrain-025'), timeout: const Timeout(Duration(minutes: 2)));
  testWidgets('handcoded-025', (tester) => renderAndCheck(tester, 'handcoded-025'), timeout: const Timeout(Duration(minutes: 2)));
}
