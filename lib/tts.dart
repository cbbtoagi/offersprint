/// TTS 朗读封装（系统语音，iOS/macOS 走 AVSpeechSynthesizer，Android 走系统 TTS）。
library;
import 'package:flutter_tts/flutter_tts.dart';

class TtsController {
  static final TtsController instance = TtsController._();
  TtsController._();

  final FlutterTts _tts = FlutterTts();
  bool _ready = false;

  Future<void> _ensure() async {
    if (_ready) return;
    try {
      await _tts.setLanguage('zh-CN');
      await _tts.setSpeechRate(0.5);
      await _tts.awaitSpeakCompletion(true);
      _ready = true;
    } catch (_) {
      // TTS 不可用时静默降级
    }
  }

  bool get isSpeaking => _ready;

  Future<void> speak(String text) async {
    await _ensure();
    if (!_ready) return;
    try {
      await _tts.stop();
      // 去掉 markdown 符号，朗读体验更好
      final clean = text
          .replaceAll(RegExp(r'```[\s\S]*?```'), ' ')
          .replaceAll(RegExp(r'[$#*_>\[\]`~\-|]'), ' ')
          .replaceAll(RegExp(r'\s+'), ' ')
          .trim();
      if (clean.isNotEmpty) await _tts.speak(clean);
    } catch (_) {}
  }

  Future<void> stop() async {
    if (!_ready) return;
    try {
      await _tts.stop();
    } catch (_) {}
  }
}
