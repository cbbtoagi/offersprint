import 'package:flutter/material.dart';

import '../../theme.dart';

/// 支持语言的高亮词表（纯离线简易着色）
class LangDefs {
  static const python = _Lang(
    keywords: {
      'def', 'class', 'return', 'if', 'elif', 'else', 'for', 'while', 'in',
      'not', 'and', 'or', 'import', 'from', 'as', 'with', 'try', 'except',
      'finally', 'break', 'continue', 'pass', 'lambda', 'yield', 'None',
      'True', 'False', 'is', 'global', 'nonlocal', 'assert', 'raise', 'del',
    },
    builtins: {
      'list', 'dict', 'set', 'tuple', 'len', 'range', 'enumerate', 'max',
      'min', 'sum', 'abs', 'sorted', 'map', 'filter', 'zip', 'str', 'int',
      'float', 'bool', 'print', 'deque', 'heapq', 'defaultdict', 'Optional',
      'self',
    },
  );
  static const cpp = _Lang(
    keywords: {
      'int', 'long', 'auto', 'void', 'bool', 'char', 'double', 'float',
      'const', 'static', 'struct', 'class', 'public', 'private', 'return',
      'if', 'else', 'for', 'while', 'break', 'continue', 'using', 'namespace',
      'template', 'typename', 'new', 'delete', 'true', 'false', 'nullptr',
      'sizeof', 'switch', 'case', 'default', 'do', 'constexpr', 'inline',
      'unsigned', 'signed', 'size_t', 'vector', 'string', 'unordered_map',
      'unordered_set', 'map', 'set', 'pair', 'queue', 'stack', 'priority_queue',
      'sort', 'make_pair',
    },
    builtins: {
      'std', 'cin', 'cout', 'endl', 'push_back', 'emplace_back', 'size',
      'empty', 'begin', 'end', 'find', 'insert', 'erase', 'emplace', 'top',
      'pop', 'push', 'front', 'back', 'first', 'second', 'getLine', 'getline',
      'min', 'max', 'swap', 'abs',
    },
  );
  static const java = _Lang(
    keywords: {
      'public', 'private', 'protected', 'class', 'interface', 'extends',
      'implements', 'static', 'final', 'void', 'int', 'long', 'double',
      'float', 'boolean', 'char', 'new', 'return', 'if', 'else', 'for',
      'while', 'do', 'switch', 'case', 'break', 'continue', 'import',
      'package', 'this', 'super', 'try', 'catch', 'finally', 'throw',
      'throws', 'null', 'true', 'false', 'abstract', 'instanceof', 'var',
    },
    builtins: {
      'System', 'out', 'println', 'String', 'List', 'ArrayList', 'HashMap',
      'Map', 'Set', 'HashSet', 'Array', 'Arrays', 'Math', 'Integer',
      'Deque', 'LinkedList', 'PriorityQueue', 'size', 'get', 'put', 'add',
      'remove', 'contains', 'isEmpty', 'length', 'equals',
    },
  );
  static const js = _Lang(
    keywords: {
      'const', 'let', 'var', 'function', 'return', 'if', 'else', 'for',
      'while', 'do', 'break', 'continue', 'of', 'in', 'new', 'class',
      'extends', 'this', 'typeof', 'instanceof', 'try', 'catch', 'finally',
      'throw', 'switch', 'case', 'default', 'null', 'undefined', 'true',
      'false', 'async', 'await', 'yield', 'delete', 'export', 'import',
    },
    builtins: {
      'console', 'log', 'Map', 'Set', 'Array', 'Object', 'JSON', 'Math',
      'Number', 'String', 'push', 'pop', 'shift', 'slice', 'map', 'filter',
      'reduce', 'forEach', 'length', 'has', 'get', 'set', 'delete', 'keys',
      'values', 'entries', 'sort', 'join', 'split', 'parseInt', 'Infinity',
    },
  );
  static const go = _Lang(
    keywords: {
      'func', 'package', 'import', 'var', 'const', 'type', 'struct', 'map',
      'chan', 'go', 'defer', 'if', 'else', 'for', 'range', 'switch', 'case',
      'default', 'break', 'continue', 'return', 'interface', 'select', 'nil',
      'true', 'false', 'fallthrough', 'goto',
    },
    builtins: {
      'fmt', 'len', 'cap', 'append', 'make', 'new', 'delete', 'copy', 'min',
      'max', 'Println', 'Printf', 'Sprintf', 'Scan', 'Scanf', 'error',
      'string', 'int', 'int64', 'float64', 'bool', 'byte', 'rune',
    },
  );
}

class _Lang {
  final Set<String> keywords;
  final Set<String> builtins;
  const _Lang({required this.keywords, required this.builtins});
}

/// 多语言语法高亮代码视图（纯离线，无第三方依赖）。
class CodeView extends StatelessWidget {
  const CodeView(
      {super.key, required this.code, this.fontSize = 13, this.language});

  final String code;
  final double fontSize;
  final String? language; // python / cpp / java / javascript / go / null


  static const _langMap = {
    'cpp': LangDefs.cpp,
    'java': LangDefs.java,
    'javascript': LangDefs.js,
    'js': LangDefs.js,
    'go': LangDefs.go,
  };

  TextSpan _highlightLine(String line) {
    final children = <TextSpan>[];
    final lang = language == null || language == 'python'
        ? LangDefs.python
        : (_langMap[language] ?? LangDefs.python);
    final isC = language == 'cpp' || language == 'java' ||
        language == 'javascript' || language == 'js' || language == 'go';

    final commentIdx = isC ? _cCommentIndex(line) : _commentIndex(line);
    final codePart = commentIdx >= 0 ? line.substring(0, commentIdx) : line;
    final commentPart = commentIdx >= 0 ? line.substring(commentIdx) : '';

    final tokenRe = RegExp(r'''("[^"]*")|('[^']*')|(\b\w+\b)|(\s+)|([^\w\s])''');
    for (final m in tokenRe.allMatches(codePart)) {
      final t = m.group(0)!;
      Color color;
      if (t.startsWith('"') || t.startsWith("'")) {
        color = const Color(0xFFB5E853); // string
      } else if (lang.keywords.contains(t)) {
        color = const Color(0xFFFF79C6); // keyword
      } else if (lang.builtins.contains(t)) {
        color = const Color(0xFF8BE9FD); // builtin
      } else if (RegExp(r'^\d+$').hasMatch(t)) {
        color = const Color(0xFFBD93F9); // number
      } else if (RegExp(r'^[^\w\s]$').hasMatch(t)) {
        color = const Color(0xFFF8F8F2);
      } else {
        color = const Color(0xFFE6E6E6);
      }
      children.add(TextSpan(text: t, style: TextStyle(color: color)));
    }
    if (commentPart.isNotEmpty) {
      children.add(TextSpan(
        text: commentPart,
        style: const TextStyle(color: Color(0xFF6272A4), fontStyle: FontStyle.italic),
      ));
    }
    return TextSpan(children: children);
  }

  /// C 系注释起点（// 或 /*）
  int _cCommentIndex(String line) {
    for (var i = 0; i < line.length - 1; i++) {
      final two = line.substring(i, i + 2);
      if (two == '//' || two == '/*') {
        // 避免把字符串里的 // 当注释：统计前面引号数量
        var quotes = 0;
        for (var j = 0; j < i; j++) {
          if (line[j] == '"' || line[j] == "'") quotes++;
        }
        if (quotes % 2 == 0) return i;
      }
    }
    return -1;
  }

  /// 行内 # 的位置（跳过字符串内的 #）
  int _commentIndex(String line) {
    var inS = false;
    var sChar = '';
    for (var i = 0; i < line.length; i++) {
      final c = line[i];
      if (inS) {
        if (c == sChar) inS = false;
      } else if (c == '"' || c == "'") {
        inS = true;
        sChar = c;
      } else if (c == '#') {
        return i;
      }
    }
    return -1;
  }

  @override
  Widget build(BuildContext context) {
    final lines = code.split('\n');
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.codeBackground,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1F2430)),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (var i = 0; i < lines.length; i++)
              SelectableText.rich(
                TextSpan(style: TextStyle(
                    fontSize: fontSize,
                    fontFamily: 'Menlo',
                    height: 1.5,
                    color: Colors.white),
                  children: [_highlightLine(lines[i])],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// 带行号的编辑器（默写用）：TextField + 等宽。
class CodeField extends StatelessWidget {
  const CodeField({super.key, required this.controller});

  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      maxLines: null,
      keyboardType: TextInputType.multiline,
      style: const TextStyle(fontFamily: 'Menlo', fontSize: 13, height: 1.5),
      decoration: InputDecoration(
        hintText: 'def solution(...):\n    # 在此默写你的 Python 代码…',
        hintStyle: const TextStyle(color: AppTheme.muted, fontFamily: 'Menlo'),
        filled: true,
        fillColor: AppTheme.codeBackground,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF1F2430)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF1F2430)),
        ),
      ),
    );
  }
}
