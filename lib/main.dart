import 'dart:developer' as developer;
import 'dart:io';

import 'package:drift/drift.dart' hide Column;
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart' hide ChangeNotifierProvider;
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';

import 'package:interview_flash/algo/data/content_repository.dart';
import 'package:interview_flash/algo/data/database.dart';
import 'package:interview_flash/algo/providers.dart' as algo;
import 'app.dart';
import 'state.dart';
import 'views/detail_pages.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final appState = AppState();
  final uiState = UiState();

  // 算法冲刺（algosprint）数据库：独立 SQLite 文件，注入 Riverpod 根 scope
  final db = AppDatabase(
    LazyDatabase(() async {
      final support = await getApplicationSupportDirectory();
      if (!Platform.isAndroid && !Platform.isIOS) {
        // 桌面端由 sqlite3_flutter_libs 提供动态库
      }
      return NativeDatabase.createInBackground(
        File(p.join(support.path, 'algosprint.sqlite')),
      );
    }),
  );
  final algoContent = ContentRepository(db);
  final container = ProviderContainer(
    overrides: [algo.dbProvider.overrideWithValue(db)],
  );
  appState.init(algoContent: algoContent).then((_) {
    debugPrint('gate: flipping algoReady=true');
    // 首启导入完成：翻开算法侧查询门闩，触发 Provider 重算
    container.read(algo.algoReadyProvider.notifier).state = true;
    debugPrint('gate: flipped');
  });
  // 调试/自动化验证用：算法侧容器内数据
  developer.registerExtension('ext.interview.algoStats', (method, parameters) async {
    final problems = await container.read(algo.problemsProvider.future);
    return developer.ServiceExtensionResponse.result('{"problems":${problems.length}}');
  });

  runApp(
    UncontrolledProviderScope(
      container: container,
      child: MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: appState),
          ChangeNotifierProvider.value(value: uiState),
        ],
        child: const InterviewApp(),
      ),
    ),
  );

  // 调试/自动化验证用：HTTP 调用 ext.interview.setTab?tab=N 切换页签
  developer.registerExtension('ext.interview.setTab', (method, parameters) async {
    final tab = int.tryParse(parameters['tab'] ?? '') ?? 0;
    uiState.goto(tab.clamp(0, 4));
    return developer.ServiceExtensionResponse.result('{"tab":$tab}');
  });
  // 调试/自动化验证用：算法模块状态
  developer.registerExtension('ext.interview.algo', (method, parameters) async {
    final count = await db.contentCount();
    final imported = await db.metaValue('content_version');
    return developer.ServiceExtensionResponse.result(
      '{"contentCount":$count,"contentVersion":"$imported"}',
    );
  });
  // 调试/自动化验证用：HTTP 调用 ext.interview.openQ?qid=xxx 打开题目详情
  developer.registerExtension('ext.interview.openQ', (method, parameters) async {
    final qid = parameters['qid'] ?? '';
    final q = appState.repo?.byId[qid];
    if (q == null) {
      return developer.ServiceExtensionResponse.error(
        developer.ServiceExtensionResponse.invalidParams,
        'qid not found',
      );
    }
    final reveal = parameters['reveal'] == '1';
    routerKey.currentState!.push(
      MaterialPageRoute(builder: (_) => QuestionDetailPage(qid: qid, reveal: reveal)),
    );
    return developer.ServiceExtensionResponse.result('{"qid":"$qid"}');
  });
}
