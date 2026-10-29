/// 冲刺Offer 应用根：主题 + 路由 + 全局 Esc 返回（桌面端逃生通道）。
library;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import 'package:interview_flash/algo/ui/history_screen.dart';
import 'package:interview_flash/algo/ui/home_screen.dart';
import 'state.dart';
import 'views/flash_view.dart';
import 'views/home_view.dart';
import 'views/library_view.dart';
import 'views/me_view.dart';
import 'views/mock_view.dart';

/// 全局导航 key，供调试扩展打开页面。
final GlobalKey<NavigatorState> routerKey = GlobalKey<NavigatorState>();

class InterviewApp extends StatelessWidget {
  const InterviewApp({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF6E8BFF),
      brightness: Brightness.dark,
      surface: const Color(0xFF161B23),
      surfaceContainerLowest: const Color(0xFF171D26),
    );
    return MaterialApp(
      title: '冲刺Offer',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: scheme,
        scaffoldBackgroundColor: const Color(0xFF0D1017),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0D1017),
          scrolledUnderElevation: 0,
          centerTitle: true,
        ),
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: const Color(0xFF131822),
          indicatorColor: scheme.primary.withValues(alpha: 0.25),
          labelTextStyle: WidgetStatePropertyAll(TextStyle(fontSize: 11, color: scheme.onSurface)),
        ),
        cardTheme: const CardThemeData(
          color: Color(0xFF171D26),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(14)),
            side: BorderSide(color: Color(0xFF252A35)),
          ),
        ),
        dividerTheme: DividerThemeData(color: scheme.outlineVariant.withValues(alpha: 0.25), thickness: 0.5),
        snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
      ),
      home: const RootShell(),
      navigatorKey: routerKey,
      builder: (context, child) {
        // 桌面端：Esc 关闭当前推入页面
        return CallbackShortcuts(
          bindings: {
            const SingleActivator(LogicalKeyboardKey.escape): () {
              final nav = routerKey.currentState;
              if (nav != null && nav.canPop()) nav.maybePop();
            },
          },
          child: Focus(autofocus: true, child: child ?? const SizedBox.shrink()),
        );
      },
    );
  }
}

/// 算法页：algosprint 首页 + 学习记录入口。
class AlgorithmTab extends StatelessWidget {
  const AlgorithmTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('算法冲刺'),
        actions: [
          IconButton(
            tooltip: '学习记录',
            icon: const Icon(Icons.history_edu_outlined),
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => Scaffold(
                appBar: AppBar(title: const Text('学习记录')),
                body: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 860),
                    child: HistoryScreen(),
                  ),
                ),
              ),
            )),
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: 860),
          child: HomeScreen(),
        ),
      ),
    );
  }
}

class RootShell extends StatefulWidget {
  const RootShell({super.key});

  @override
  State<RootShell> createState() => _RootShellState();
}

class _RootShellState extends State<RootShell> {
  @override
  Widget build(BuildContext context) {
    final ui = context.watch<UiState>();
    final pages = const [
      HomeView(),
      AlgorithmTab(),
      LibraryView(),
      FlashView(),
      MockView(),
    ];
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 720),
            child: IndexedStack(index: ui.tab, children: pages),
          ),
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: ui.tab,
        height: 64,
        onDestinationSelected: (i) => ui.goto(i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: '首页'),
          NavigationDestination(icon: Icon(Icons.code_outlined), selectedIcon: Icon(Icons.code), label: '算法'),
          NavigationDestination(icon: Icon(Icons.library_books_outlined), selectedIcon: Icon(Icons.library_books), label: '八股'),
          NavigationDestination(icon: Icon(Icons.flash_on_outlined), selectedIcon: Icon(Icons.flash_on), label: '速刷'),
          NavigationDestination(icon: Icon(Icons.record_voice_over_outlined), selectedIcon: Icon(Icons.record_voice_over), label: '模拟'),
        ],
      ),
    );
  }
}
