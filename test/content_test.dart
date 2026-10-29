/// 内容包完整性测试：加载 assets/content/*.json 并解析成模型。
library;
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:interview_flash/repo.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('内容包可解析', () async {
    final repo = await ContentRepo.load();
    // 至少要有部分领域已生成
    expect(repo.packs, isNotEmpty, reason: 'assets/content 下没有任何题库域 JSON');
    for (final (meta, qs) in repo.packs) {
      expect(qs, isNotEmpty, reason: '${meta.id} 域为空');
      for (final q in qs) {
        expect(q.id, startsWith('${meta.id}-'), reason: '${q.id} id 前缀错误');
        expect(q.answerMd.length, greaterThan(50), reason: '${q.id} answerMd 过短');
        expect(q.keyPoints, isNotEmpty, reason: '${q.id} keyPoints 为空');
      }
    }
    // 项目与面经允许暂缺，但存在时必须可解析
    for (final p in repo.projects) {
      expect(p.bodyMd.length, greaterThan(100), reason: '${p.id} bodyMd 过短');
    }
    for (final e in repo.exps) {
      expect(e.questions.length, greaterThanOrEqualTo(5), reason: '${e.id} questions 太少');
    }
  });

  test('领域顺序与命名符合预期', () async {
    final manifest = await AssetManifest.loadFromAssetBundle(rootBundle);
    final assets = manifest.listAssets().where((a) => a.startsWith('assets/content/')).toList();
    expect(assets, isNotEmpty);
    for (final meta in kDomainOrder) {
      expect(meta.name, isNotEmpty);
    }
  });
}
