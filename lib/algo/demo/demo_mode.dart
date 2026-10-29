/// 演示录制模式：环境变量 ALGOSPRINT_DEMO=1 时启用。
/// App 自动走完「首页 → 公司 → 学习 → 默写 → 自述 → 记录」全流程，
/// 逐帧截图到 ALGOSPRINT_DEMO_DIR（%05d.png），结束时自动退出。
///
/// 不入库敏感信息；正常启动完全无感知。
library;

import 'dart:async';
import 'dart:io';
import 'dart:ui' show ImageByteFormat;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/scheduler.dart';
import 'package:path_provider/path_provider.dart';

class DemoMode {
  static bool get enabled =>
      Platform.environment['ALGOSPRINT_DEMO'] == '1';

  /// 视频帧捕获倍率（逻辑像素 → 物理像素）
  static double get pixelRatio =>
      double.tryParse(Platform.environment['ALGOSPRINT_DEMO_PX'] ?? '') ?? 2.0;

  static Directory? _dir;

  /// 帧目录：沙盒应用写入容器目录（路径异步解析，帧目录与日志共用）
  static Future<Directory> framesDir() async {
    if (_dir != null) return _dir!;
    final base = await getApplicationSupportDirectory();
    _dir = Directory('${base.path}/demo_frames');
    return _dir!;
  }

  static Future<void> log(String message) async {
    try {
      final dir = await framesDir();
      await dir.create(recursive: true);
      await File('${dir.path}/capture.log')
          .writeAsString('$message\n', mode: FileMode.append);
    } catch (_) {}
  }
}

/// 包裹整个 App 的 RepaintBoundary + 定时截帧器。
class DemoFrameCapture extends StatefulWidget {
  const DemoFrameCapture({super.key, required this.child});

  final Widget child;

  @override
  State<DemoFrameCapture> createState() => _DemoFrameCaptureState();
}

class _DemoFrameCaptureState extends State<DemoFrameCapture> {
  final _boundaryKey = GlobalKey();
  int _frame = 0;
  bool _saving = false;
  Timer? _timer;
  Directory? _dir;

  @override
  void initState() {
    super.initState();
    if (DemoMode.enabled) {
      DemoMode.framesDir().then((dir) {
        dir.createSync(recursive: true);
        _dir = dir;
        DemoMode.log('capture: dir=$dir px=${DemoMode.pixelRatio}');
        SchedulerBinding.instance.addPostFrameCallback((_) {
          _timer = Timer.periodic(
              const Duration(milliseconds: 33), (_) => _grab());
        });
      });
    }
  }

  Future<void> _grab() async {
    if (_saving || _dir == null) return; // 上一帧还在编码则跳过（帧率自适应）
    _saving = true;
    RenderRepaintBoundary? boundary;
    try {
      boundary = _boundaryKey.currentContext?.findRenderObject()
          as RenderRepaintBoundary?;
      if (boundary == null || !boundary.attached) return;
      final image = await boundary.toImage(pixelRatio: DemoMode.pixelRatio);
      final bytes = await image.toByteData(format: ImageByteFormat.png);
      image.dispose();
      if (bytes != null) {
        _frame += 1;
        await File('${_dir!.path}/${_frame.toString().padLeft(5, '0')}.png')
            .writeAsBytes(bytes.buffer.asUint8List(), flush: false);
      }
    } catch (e) {
      if (_frame == 0) {
        DemoMode.log('grab error: $e'); // 只记首帧错误，避免日志爆炸
      }
    } finally {
      _saving = false;
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!DemoMode.enabled) return widget.child;
    return RepaintBoundary(key: _boundaryKey, child: widget.child);
  }
}

/// 定时动作调度器（保留给后续扩展场景使用）。
class DemoTimeline {
  DemoTimeline(List<(double, void Function())> steps) {
    for (final (at, action) in steps) {
      _timers.add(Timer(Duration(milliseconds: (at * 1000).round()), action));
    }
  }

  final List<Timer> _timers = [];

  void cancel() {
    for (final t in _timers) {
      t.cancel();
    }
  }
}

/// 片头 / 片尾品牌卡。
class DemoBrandCard extends StatelessWidget {
  const DemoBrandCard({
    super.key,
    required this.title,
    required this.subtitle,
    this.footer,
  });

  final String title;
  final String subtitle;
  final String? footer;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: double.infinity,
      color: const Color(0xFF0F1115),
      alignment: Alignment.center,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              color: const Color(0xFF6C8CFF).withValues(alpha: .15),
              borderRadius: BorderRadius.circular(28),
            ),
            child: const Icon(Icons.flash_on,
                color: Color(0xFF6C8CFF), size: 72),
          ),
          const SizedBox(height: 28),
          Text(title,
              style: const TextStyle(
                  fontSize: 44,
                  fontWeight: FontWeight.w800,
                  color: Colors.white)),
          const SizedBox(height: 14),
          Text(subtitle,
              style: const TextStyle(
                  fontSize: 20, color: Color(0xFF8A91A3), height: 1.5),
              textAlign: TextAlign.center),
          if (footer != null) ...[
            const SizedBox(height: 40),
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
              decoration: BoxDecoration(
                border: Border.all(color: const Color(0xFF6C8CFF)),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(footer!,
                  style: const TextStyle(
                      fontSize: 15, color: Color(0xFF6C8CFF))),
            ),
          ],
        ],
      ),
    );
  }
}
