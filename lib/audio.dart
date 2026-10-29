/// 录音（record）、播放（audioplayers）、语音识别（speech_to_text）封装。
library;
import 'dart:async';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

class AudioRecController {
  AudioRecorder? _rec;
  String? _path;
  final Stopwatch _sw = Stopwatch();

  bool get isRecording => _path != null;

  Future<bool> ensurePermission() async {
    _rec ??= AudioRecorder();
    try {
      return await _rec!.hasPermission();
    } catch (_) {
      return false;
    }
  }

  Future<bool> start() async {
    if (!await ensurePermission()) return false;
    final dir = await getApplicationSupportDirectory();
    final recDir = Directory(p.join(dir.path, 'recordings'));
    if (!recDir.existsSync()) await recDir.create(recursive: true);
    _path = p.join(recDir.path, 'rec_${DateTime.now().millisecondsSinceEpoch}.m4a');
    _sw
      ..reset()
      ..start();
    try {
      await _rec!.start(
        const RecordConfig(encoder: AudioEncoder.aacLc, sampleRate: 44100, numChannels: 1),
        path: _path!,
      );
      return true;
    } catch (_) {
      _path = null;
      return false;
    }
  }

  /// 返回 (路径, 时长ms)；未在录音返回 null。
  Future<(String, int)?> stop() async {
    if (_rec == null || _path == null) return null;
    final path = await _rec!.stop();
    _sw.stop();
    final result = (path ?? _path!, _sw.elapsedMilliseconds);
    _path = null;
    return result;
  }
}

class AudioPlayController {
  final AudioPlayer _player = AudioPlayer();
  String? playingPath;

  Future<void> toggle(String path) async {
    if (playingPath == path) {
      await _player.stop();
      playingPath = null;
      return;
    }
    playingPath = path;
    await _player.play(DeviceFileSource(path));
    _player.onPlayerComplete.listen((_) => playingPath = null);
  }

  Future<void> stop() => _player.stop();
  void dispose() => _player.dispose();
}

/// 语音转写控制器（iOS/Android/macOS 系统语音识别）。
class SttController {
  final stt.SpeechToText _stt = stt.SpeechToText();
  bool available = false;
  bool listening = false;
  String committed = ''; // 已确认文本

  Future<bool> init() async {
    if (available) return true;
    try {
      available = await _stt.initialize(onError: (e) => listening = false, onStatus: (s) {
        if (s == 'done' || s == 'notListening') listening = false;
      });
    } catch (_) {
      available = false;
    }
    return available;
  }

  /// 开始监听；partial 回调携带「已确认 + 进行中」全文。
  void start(void Function(String fullText) onText) {
    if (!available || listening) return;
    listening = true;
    _stt.listen(
      listenOptions: stt.SpeechListenOptions(localeId: 'zh_CN', partialResults: true, cancelOnError: true),
      onResult: (r) {
        if (r.finalResult) {
          committed = '$committed${r.recognizedWords}';
        }
        onText('$committed${r.recognizedWords}');
      },
    );
  }

  Future<void> stop() async {
    listening = false;
    try {
      await _stt.stop();
    } catch (_) {}
  }
}
