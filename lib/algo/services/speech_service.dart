/// 语音识别封装：平台原生能力（iOS Speech Framework / Android SpeechRecognizer /
/// macOS 原生支持），完全本地系统服务，无自建网络依赖。
library;

import 'package:speech_to_text/speech_to_text.dart';

class SpeechService {
  final _speech = SpeechToText();
  bool _available = false;

  bool get isListening => _speech.isListening;

  Future<bool> init() async {
    if (_available) return true;
    _available = await _speech.initialize();
    return _available;
  }

  Future<bool> hasPermission() async {
    if (!await init()) return false;
    return _available;
  }

  /// 开始听写，结果持续回调（部分结果 + 最终结果）。
  Future<void> listen({
    required void Function(String text, bool final_) onResult,
    String locale = 'zh_CN',
  }) async {
    if (!await init()) return;
    _speech.listen(
      onResult: (r) => onResult(r.recognizedWords, r.finalResult),
      listenOptions: SpeechListenOptions(
        partialResults: true,
        cancelOnError: true,
        listenMode: ListenMode.dictation,
        localeId: locale,
      ),
    );
  }

  Future<void> stop() => _speech.stop();

  Future<void> cancel() => _speech.cancel();

  /// 列出可用语音包（用于无中文语音包时提示）
  Future<List<String>> locales() async {
    if (!await init()) return [];
    final list = await _speech.locales();
    return list.map((e) => '${e.localeId} (${e.name})').toList();
  }
}
