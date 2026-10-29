import 'package:flutter/material.dart';

/// 统一主题常量
class AppTheme {
  static ThemeData get dark {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF6E8BFF),
        brightness: Brightness.dark,
      ),
      scaffoldBackgroundColor: const Color(0xFF0D1017),
      cardTheme: const CardThemeData(
        color: Color(0xFF171D26),
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.all(Radius.circular(16)),
          side: BorderSide(color: Color(0xFF252A35)),
        ),
      ),
    );
  }

  static const difficultyColors = {
    'easy': Color(0xFF4CC38A),
    'medium': Color(0xFFF2B94B),
    'hard': Color(0xFFF26D6D),
  };

  static const codeBackground = Color(0xFF0B0D11);
  static const accent = Color(0xFF6E8BFF);
  static const good = Color(0xFF4CC38A);
  static const bad = Color(0xFFF26D6D);
  static const muted = Color(0xFF8A91A3);

  static String difficultyCn(String d) =>
      switch (d) { 'easy' => '简单', 'medium' => '中等', _ => '困难' };
}
