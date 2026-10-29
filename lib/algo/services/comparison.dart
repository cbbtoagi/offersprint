/// 默写代码比对：归一化 token 相似度（LCS）+ 结构标签命中检测。
library;

class ComparisonResult {
  final double similarity; // 0-1 token 相似度
  final double score; // 0-100 综合得分
  final List<String> missingStructures; // 参考答案有而默写缺失的结构
  final List<List<String>> diffLines; // [type, text] type: same/missing/extra
  final String normalizedRef;
  final String normalizedUser;

  const ComparisonResult({
    required this.similarity,
    required this.score,
    required this.missingStructures,
    required this.diffLines,
    required this.normalizedRef,
    required this.normalizedUser,
  });
}

/// 结构标签 -> Python 代码特征正则
const structurePatterns = <String, List<String>>{
  'hashmap': [r'\{\}', r'\bdict\(', r'\bset\(', r'\bdefaultdict\(', r'\w\[\s*\w+\s*\]\s*=[^=]'],
  'two_pointer': [r'\bl\s*,\s*r\b', r'\bleft\s*,\s*right\b'],
  'sliding_window': [r'\bwhile\b.*\bl\b', r'\bl\s*\+=?\s*1\b'],
  'sort': [r'\.sort\(', r'\bsorted\('],
  'dedup': [r'==\s*\w+\s*\[\s*\w+\s*-\s*1\s*\]', r'\bcontinue\b'],
  'bfs': [r'\bdeque\(', r'\bpopleft\('],
  'queue': [r'\bdeque\(', r'\.append\('],
  'dfs': [r'\.left\b', r'\.right\b'],
  'recursion': [r'\bdfs\(', r'\breturn\s+self\.', r'\bhelper\('],
  'dp': [r'\bdp\s*=', r'\bdp\[', r'\@cache', r'\bf\s*=\s*\['],
  'greedy': [r'\bmax\(', r'\bmin\('],
  'stack': [r'\bstack\s*=', r'\.pop\('],
  'binary_search': [r'\bmid\b', r'\bwhile\s+\w+\s*<'],
  'backtracking': [r'\.pop\(\)', r'\bdfs\(', r'\bbacktrack\('],
  'heap': [r'\bheapq\b', r'\bheappush\b', r'\bheappop\b'],
  'linked_list': [r'\.next\b'],
  'single_pass': [r'\bfor\s+\w+(\s*,\s*\w+)?\s+in\b'],
  'intervals': [r'\.sort\(', r'\bend\b'],
  'matrix': [r'\[\s*\]\s*for\b', r'\bnrows\b|\brows\b|\bm\s*\]\s*\['],
  'bit': [r'&', r'\|', r'\^', r'>>'],
  'trie': [r'\bclass\s+\w*Trie\b', r'\bchildren\b'],
  'math': [r'\bdivmod\(', r'%'],
};

/// 去掉注释、空行，压缩空白。
String normalizeCode(String src) {
  final lines = <String>[];
  for (final raw in src.split('\n')) {
    var l = raw;
    // 粗略剥离 # 注释（不处理字符串中的 #，作为启发式足够）
    final hashIdx = l.indexOf('#');
    if (hashIdx >= 0) l = l.substring(0, hashIdx);
    l = l.trim();
    if (l.isNotEmpty) lines.add(l);
  }
  return lines.join('\n');
}

/// 分词：标识符/数字/运算符
List<String> tokenize(String src) =>
    RegExp(r'[A-Za-z_]\w*|\d+|[^\w\s]').allMatches(src).map((m) => m.group(0)!).toList();

double _lcsSimilarity(List<String> a, List<String> b) {
  if (a.isEmpty && b.isEmpty) return 1;
  if (a.isEmpty || b.isEmpty) return 0;
  final prev = List.filled(b.length + 1, 0);
  final cur = List.filled(b.length + 1, 0);
  for (var i = 1; i <= a.length; i++) {
    for (var j = 1; j <= b.length; j++) {
      cur[j] = a[i - 1] == b[j - 1] ? prev[j - 1] + 1 : (prev[j] > cur[j - 1] ? prev[j] : cur[j - 1]);
    }
    for (var j = 0; j <= b.length; j++) {
      prev[j] = cur[j];
      cur[j] = 0;
    }
  }
  return prev[b.length] / (a.length > b.length ? a.length : b.length);
}

/// 逐行 diff（LCS on lines），返回 [type, line] 列表。
List<List<String>> diffLines(String ref, String user) {
  final a = ref.isEmpty ? <String>[] : ref.split('\n');
  final b = user.isEmpty ? <String>[] : user.split('\n');
  final n = a.length, m = b.length;
  final dp = List.generate(n + 1, (_) => List.filled(m + 1, 0));
  for (var i = n - 1; i >= 0; i--) {
    for (var j = m - 1; j >= 0; j--) {
      dp[i][j] = a[i] == b[j]
          ? dp[i + 1][j + 1] + 1
          : (dp[i + 1][j] > dp[i][j + 1] ? dp[i + 1][j] : dp[i][j + 1]);
    }
  }
  final out = <List<String>>[];
  var i = 0, j = 0;
  while (i < n && j < m) {
    if (a[i] == b[j]) {
      out.add(['same', a[i]]);
      i++;
      j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      out.add(['missing', a[i]]);
      i++;
    } else {
      out.add(['extra', b[j]]);
      j++;
    }
  }
  while (i < n) {
    out.add(['missing', a[i]]);
    i++;
  }
  while (j < m) {
    out.add(['extra', b[j]]);
    j++;
  }
  return out;
}

/// 检测默写代码命中了哪些结构标签
List<String> missingStructures(List<String> tags, String userCode) {
  final missing = <String>[];
  for (final tag in tags) {
    final patterns = structurePatterns[tag];
    if (patterns == null) continue;
    final hit = patterns.any((p) => RegExp(p).hasMatch(userCode));
    if (!hit) missing.add(tag);
  }
  return missing;
}

ComparisonResult compare(String refCode, String userCode, List<String> tags) {
  final normRef = normalizeCode(refCode);
  final normUser = normalizeCode(userCode);
  final sim = _lcsSimilarity(tokenize(normRef), tokenize(normUser));
  final missing = missingStructures(tags, normUser);

  // 综合分：token 相似度 70% + 结构命中 30%
  final structScore = tags.isEmpty ? 1.0 : 1 - missing.length / tags.length;
  final score = (sim * 0.7 + structScore * 0.3) * 100;

  return ComparisonResult(
    similarity: sim,
    score: score.clamp(0, 100).toDouble(),
    missingStructures: missing,
    diffLines: diffLines(normRef, normUser),
    normalizedRef: normRef,
    normalizedUser: normUser,
  );
}
