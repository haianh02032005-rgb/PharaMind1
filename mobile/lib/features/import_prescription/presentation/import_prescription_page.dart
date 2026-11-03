import 'dart:typed_data';

import 'package:file_selector/file_selector.dart' as file_selector;
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart' as image_picker;

import '../../../core/network/api_client.dart';
import '../data/import_prescription_api.dart';
import '../domain/import_session.dart';

class ImportPrescriptionPage extends StatefulWidget {
  const ImportPrescriptionPage({
    required this.api,
    required this.familyId,
    required this.members,
    this.initialMemberId,
    this.onCommitted,
    super.key,
  });

  final ApiClient api;
  final int familyId;
  final List<Map<String, dynamic>> members;
  final int? initialMemberId;
  final ValueChanged<ImportSessionData>? onCommitted;

  @override
  State<ImportPrescriptionPage> createState() => _ImportPrescriptionPageState();
}

class _ImportPrescriptionPageState extends State<ImportPrescriptionPage> {
  final image_picker.ImagePicker _imagePicker = image_picker.ImagePicker();

  late ImportPrescriptionApi _imports;
  int? _memberId;
  ImportSessionData? _session;
  bool _busy = false;
  bool _confirmSchedules = true;
  bool _confirmHealth = false;
  bool _confirmOcrReview = false;
  String? _error;

  List<Map<String, dynamic>> get _activeMembers => widget.members
      .where((member) =>
          member['status'] != 'INACTIVE' && member['status'] != 'ARCHIVED')
      .toList(growable: false);

  @override
  void initState() {
    super.initState();
    _imports = ImportPrescriptionApi(widget.api);
    _memberId = _initialMemberId();
  }

  @override
  void didUpdateWidget(covariant ImportPrescriptionPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.api != widget.api) {
      _imports = ImportPrescriptionApi(widget.api);
    }
    if (!_activeMembers.any((member) => member['id'] == _memberId)) {
      _memberId = _initialMemberId();
      _session = null;
    }
  }

  int? _initialMemberId() {
    final members = _activeMembers;
    final requested = widget.initialMemberId;
    if (requested != null &&
        members.any((member) => member['id'] == requested)) {
      return requested;
    }
    return members.length == 1 ? members.first['id'] as int? : null;
  }

  Future<void> _run(
    Future<ImportSessionData> Function() operation, {
    bool notifyCommitted = false,
  }) async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await operation();
      if (!mounted) return;
      setState(() => _session = result);
      if (notifyCommitted && result.isCommitted) {
        widget.onCommitted?.call(result);
      }
    } catch (error) {
      if (mounted) {
        setState(() => _error = widget.api.messageFor(error));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _upload({
    required String filename,
    required Future<int> Function() length,
    required Future<Uint8List> Function() readBytes,
  }) async {
    final memberId = _memberId;
    if (memberId == null) {
      setState(() => _error = 'Hãy chọn thành viên nhận đơn thuốc trước.');
      return;
    }
    final sourceType = inferImportSourceType(filename);
    if (sourceType == null) {
      setState(() => _error =
          'Định dạng tệp chưa được hỗ trợ. Hãy chọn JPG, JPEG, PNG, PDF, XLSX hoặc CSV.');
      return;
    }

    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final size = await length();
      if (size <= 0) throw StateError('Tệp đã chọn bị rỗng.');
      final limit = importFileLimitBytes(filename);
      if (size > limit) {
        throw StateError(
          'Tệp vượt quá giới hạn ${limit ~/ (1024 * 1024)}MB.',
        );
      }
      final bytes = await readBytes();
      final result = await _imports.upload(
        familyId: widget.familyId,
        memberId: memberId,
        filename: filename,
        bytes: bytes,
        sourceType: sourceType,
      );
      if (!mounted) return;
      setState(() {
        _session = result;
        _confirmOcrReview = false;
        _confirmSchedules = true;
        _confirmHealth = false;
      });
    } catch (error) {
      if (mounted) {
        final message = error is StateError
            ? error.message.toString()
            : widget.api.messageFor(error);
        setState(() => _error = message);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pickImage(image_picker.ImageSource source) async {
    try {
      final file = await _imagePicker.pickImage(
        source: source,
        imageQuality: 95,
        requestFullMetadata: false,
      );
      if (file == null) return;
      await _upload(
        filename: file.name,
        length: file.length,
        readBytes: file.readAsBytes,
      );
    } catch (error) {
      if (mounted) setState(() => _error = widget.api.messageFor(error));
    }
  }

  Future<void> _pickDocument() async {
    try {
      // Validate after selection. This remains portable because iOS filters by
      // UTI while Android filters by MIME/extension.
      final file = await file_selector.openFile();
      if (file == null) return;
      await _upload(
        filename: file.name,
        length: file.length,
        readBytes: file.readAsBytes,
      );
    } catch (error) {
      if (mounted) setState(() => _error = widget.api.messageFor(error));
    }
  }

  Future<void> _acknowledge(String field) async {
    final session = _session;
    if (session == null) return;
    await _run(() => _imports.updateDraft(
          session: session,
          payload: <String, dynamic>{field: true},
        ));
  }

  Future<void> _validate() async {
    final session = _session;
    if (session == null) return;
    await _run(() => _imports.validate(session));
  }

  Future<void> _commit() async {
    final session = _session;
    if (session == null) return;
    await _run(
      () => _imports.commit(
        session: session,
        confirmScheduleCreation: _confirmSchedules,
        confirmHealthUpdates: _confirmHealth,
        confirmOcrReview: _confirmOcrReview,
      ),
      notifyCommitted: true,
    );
  }

  Future<void> _cancelSession() async {
    final session = _session;
    if (session == null) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Hủy phiên nhập?'),
        content: const Text(
          'Dữ liệu đang rà soát sẽ không được ghi vào hồ sơ thành viên.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Quay lại'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Hủy phiên'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    await _run(() => _imports.reject(session));
    if (mounted && _session?.status == 'REJECTED') _reset();
  }

  void _reset() {
    setState(() {
      _session = null;
      _error = null;
      _confirmSchedules = true;
      _confirmHealth = false;
      _confirmOcrReview = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nhập đơn thuốc')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 32),
          children: [
            Text(
              'OCR ảnh, PDF và Excel',
              style: Theme.of(context)
                  .textTheme
                  .headlineSmall
                  ?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            const Text(
              'Dữ liệu chỉ được lưu sau khi bạn rà soát và xác nhận ở bước cuối.',
            ),
            const SizedBox(height: 18),
            if (_error != null) ...[
              _MessageCard(message: _error!, isError: true),
              const SizedBox(height: 12),
            ],
            _memberSelector(),
            const SizedBox(height: 16),
            if (_session == null) _uploadCard() else _reviewContent(_session!),
            if (_busy) ...[
              const SizedBox(height: 16),
              const LinearProgressIndicator(),
              const SizedBox(height: 6),
              const Text(
                'Đang xử lý tài liệu. OCR có thể mất một lúc…',
                textAlign: TextAlign.center,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _memberSelector() {
    final members = _activeMembers;
    if (members.isEmpty) {
      return const _MessageCard(
        message:
            'Gia đình chưa có thành viên. Hãy tạo thành viên trước khi nhập đơn.',
        isError: true,
      );
    }
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: DropdownButtonFormField<int>(
          initialValue: _memberId,
          decoration: const InputDecoration(
            labelText: 'Thành viên nhận đơn thuốc',
            prefixIcon: Icon(Icons.person_outline),
          ),
          items: members
              .map((member) => DropdownMenuItem<int>(
                    value: member['id'] as int?,
                    child:
                        Text(member['full_name']?.toString() ?? 'Thành viên'),
                  ))
              .toList(growable: false),
          onChanged: _session != null || _busy
              ? null
              : (value) => setState(() => _memberId = value),
        ),
      ),
    );
  }

  Widget _uploadCard() {
    final enabled = _memberId != null && !_busy;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Chọn tài liệu nguồn',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            const Text(
              'Ảnh tối đa 10MB, PDF tối đa 20MB; Excel và CSV tối đa 10MB.',
              style: TextStyle(color: Color(0xFF687875)),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: enabled
                  ? () => _pickImage(image_picker.ImageSource.camera)
                  : null,
              icon: const Icon(Icons.photo_camera_outlined),
              label: const Text('Chụp đơn thuốc'),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: enabled
                  ? () => _pickImage(image_picker.ImageSource.gallery)
                  : null,
              icon: const Icon(Icons.photo_library_outlined),
              label: const Text('Chọn ảnh trong thư viện'),
            ),
            const SizedBox(height: 10),
            OutlinedButton.icon(
              onPressed: enabled ? _pickDocument : null,
              icon: const Icon(Icons.upload_file_outlined),
              label: const Text('Chọn PDF, Excel hoặc CSV'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _reviewContent(ImportSessionData session) {
    if (session.isCommitted) return _committedCard(session);
    if (session.status == 'FAILED') {
      return _MessageCard(
        message:
            'Không thể xử lý tài liệu này. Hãy chọn ảnh rõ hơn hoặc kiểm tra lại tệp Excel/CSV.',
        isError: true,
        actionLabel: 'Chọn tệp khác',
        onAction: _reset,
      );
    }
    final prescription = session.prescription;
    final medications = session.medicationItems;
    final issues = [...session.unresolvedIssues]..sort((a, b) =>
        _severityRank(a.severity).compareTo(_severityRank(b.severity)));
    final healthCount = _healthItemCount(session.healthUpdates);
    final canCommit = !_busy &&
        !session.isTerminal &&
        session.blockingIssues.isEmpty &&
        (!session.isOcr || _confirmOcrReview);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _sessionSummary(session),
        const SizedBox(height: 12),
        if (prescription.isNotEmpty) _prescriptionCard(prescription),
        if (prescription.isNotEmpty) const SizedBox(height: 12),
        _medicationReview(medications),
        const SizedBox(height: 12),
        _issuesCard(issues),
        if (session.hasIssue('MEMBER_MISMATCH') ||
            session.hasIssue('DUPLICATE_FILE')) ...[
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (session.hasIssue('MEMBER_MISMATCH'))
                    OutlinedButton.icon(
                      onPressed: _busy
                          ? null
                          : () => _acknowledge('confirm_member_match'),
                      icon: const Icon(Icons.person_search_outlined),
                      label: const Text(
                        'Xác nhận đơn thuộc thành viên đã chọn',
                      ),
                    ),
                  if (session.hasIssue('DUPLICATE_FILE'))
                    OutlinedButton.icon(
                      onPressed: _busy
                          ? null
                          : () => _acknowledge('confirm_duplicate_override'),
                      icon: const Icon(Icons.copy_all_outlined),
                      label: const Text('Tôi biết tài liệu đã từng được nhập'),
                    ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              children: [
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  value: _confirmSchedules,
                  onChanged: _busy
                      ? null
                      : (value) => setState(() => _confirmSchedules = value),
                  title: const Text('Tạo lịch uống thuốc'),
                  subtitle:
                      const Text('Dùng các giờ uống đã trích xuất và rà soát.'),
                ),
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  value: _confirmHealth,
                  onChanged: _busy || healthCount == 0
                      ? null
                      : (value) => setState(() => _confirmHealth = value),
                  title: Text('Cập nhật hồ sơ sức khỏe ($healthCount mục)'),
                  subtitle:
                      const Text('Chỉ lưu khi bạn chủ động bật xác nhận.'),
                ),
                if (session.isOcr)
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    value: _confirmOcrReview,
                    controlAffinity: ListTileControlAffinity.leading,
                    onChanged: _busy
                        ? null
                        : (value) => setState(
                              () => _confirmOcrReview = value ?? false,
                            ),
                    title: const Text('Tôi đã đối chiếu với đơn thuốc gốc'),
                    subtitle: const Text(
                      'Đã kiểm tra tên thuốc, hàm lượng, liều, đường dùng và tần suất.',
                    ),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 14),
        OutlinedButton.icon(
          onPressed: _busy ? null : _validate,
          icon: const Icon(Icons.fact_check_outlined),
          label: const Text('Kiểm tra lại dữ liệu'),
        ),
        const SizedBox(height: 10),
        FilledButton.icon(
          onPressed: canCommit ? _commit : null,
          icon: const Icon(Icons.save_outlined),
          label: const Text('Xác nhận và lưu đơn thuốc'),
        ),
        if (session.blockingIssues.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(
            'Cần xử lý ${session.blockingIssues.length} lỗi trước khi có thể lưu.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        ],
        const SizedBox(height: 6),
        TextButton(
          onPressed: _busy ? null : _cancelSession,
          child: const Text('Hủy phiên nhập'),
        ),
      ],
    );
  }

  Widget _sessionSummary(ImportSessionData session) {
    final confidence = session.overallConfidence;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const CircleAvatar(child: Icon(Icons.description_outlined)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    session.sourceFilename,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  Text(
                    confidence == null
                        ? session.sourceType
                        : '${session.sourceType} · Tin cậy ${(confidence * 100).round()}%',
                    style: const TextStyle(color: Color(0xFF687875)),
                  ),
                ],
              ),
            ),
            _StatusBadge(status: session.status),
          ],
        ),
      ),
    );
  }

  Widget _prescriptionCard(Map<String, dynamic> prescription) {
    final details = <String>[
      if (prescription['doctor_name'] != null)
        'Bác sĩ: ${prescription['doctor_name']}',
      if (prescription['facility_name'] != null)
        'Cơ sở: ${prescription['facility_name']}',
      if (prescription['issued_at'] != null)
        'Ngày kê: ${prescription['issued_at']}',
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Thông tin đơn thuốc',
              style: TextStyle(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Text(
              prescription['title']?.toString() ?? 'Đơn thuốc không tiêu đề',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
            ),
            ...details.map((detail) => Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(detail),
                )),
          ],
        ),
      ),
    );
  }

  Widget _medicationReview(List<Map<String, dynamic>> medications) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Thuốc đã trích xuất (${medications.length})',
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            if (medications.isEmpty)
              const Text('Chưa trích xuất được thuốc nào từ tài liệu.'),
            ...medications.map((item) {
              final schedule = _asMap(item['schedule']);
              final times = _stringList(schedule['schedule_times']);
              final warnings = <String>[
                ..._stringList(item['allergy_warnings']),
                ..._stringList(item['reaction_warnings']),
              ];
              return Container(
                width: double.infinity,
                margin: const EdgeInsets.only(top: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFF5F8F7),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item['medication_name']?.toString() ??
                          'Chưa nhận diện tên thuốc',
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 3),
                    Text(_medicationDescription(item)),
                    if (times.isNotEmpty)
                      Text(
                        'Giờ uống: ${times.join(', ')}',
                        style: const TextStyle(color: Color(0xFF087E79)),
                      ),
                    ...warnings.map((warning) => Text(
                          '⚠ $warning',
                          style: const TextStyle(color: Color(0xFFB34338)),
                        )),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _issuesCard(List<ImportValidationIssue> issues) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              issues.isEmpty
                  ? 'Không còn cảnh báo cần xử lý'
                  : 'Cảnh báo và lỗi (${issues.length})',
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
            if (issues.isEmpty) ...[
              const SizedBox(height: 8),
              const Row(
                children: [
                  Icon(Icons.check_circle_outline, color: Color(0xFF319567)),
                  SizedBox(width: 8),
                  Expanded(child: Text('Dữ liệu đã sẵn sàng để xác nhận.')),
                ],
              ),
            ],
            ...issues.map((issue) => Padding(
                  padding: const EdgeInsets.only(top: 10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        issue.isBlocking
                            ? Icons.error_outline
                            : Icons.warning_amber_rounded,
                        color: issue.isBlocking
                            ? Theme.of(context).colorScheme.error
                            : const Color(0xFFB66A19),
                      ),
                      const SizedBox(width: 9),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              issue.message,
                              style:
                                  const TextStyle(fontWeight: FontWeight.w600),
                            ),
                            if (issue.suggestedFix != null)
                              Text(
                                issue.suggestedFix!,
                                style:
                                    const TextStyle(color: Color(0xFF687875)),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _committedCard(ImportSessionData session) {
    final summary = session.commitSummary;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            const Icon(Icons.check_circle, color: Color(0xFF319567), size: 54),
            const SizedBox(height: 10),
            const Text(
              'Đã lưu đơn thuốc',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            Text(
              'Đã tạo ${summary['prescriptions_created'] ?? 0} đơn, '
              '${summary['prescription_items_created'] ?? 0} thuốc và '
              '${summary['schedules_created'] ?? 0} lịch uống.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _reset,
              icon: const Icon(Icons.add),
              label: const Text('Nhập đơn khác'),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final ready = status == 'READY_TO_COMMIT';
    final label = switch (status) {
      'READY_TO_COMMIT' => 'Sẵn sàng',
      'REVIEW_REQUIRED' => 'Cần rà soát',
      'FAILED' => 'Thất bại',
      _ => status,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(
        color: ready ? const Color(0xFFE7F4ED) : const Color(0xFFFFF1E8),
        borderRadius: BorderRadius.circular(30),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: ready ? const Color(0xFF24734F) : const Color(0xFF995A27),
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _MessageCard extends StatelessWidget {
  const _MessageCard({
    required this.message,
    required this.isError,
    this.actionLabel,
    this.onAction,
  });

  final String message;
  final bool isError;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) => Card(
        color: isError ? const Color(0xFFFFEFED) : const Color(0xFFE7F4ED),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Icon(
                isError ? Icons.error_outline : Icons.info_outline,
                color: isError
                    ? Theme.of(context).colorScheme.error
                    : const Color(0xFF24734F),
              ),
              const SizedBox(width: 10),
              Expanded(child: Text(message)),
              if (actionLabel != null && onAction != null)
                TextButton(onPressed: onAction, child: Text(actionLabel!)),
            ],
          ),
        ),
      );
}

Map<String, dynamic> _asMap(dynamic value) {
  if (value is! Map) return <String, dynamic>{};
  return value.map((key, item) => MapEntry(key.toString(), item));
}

List<String> _stringList(dynamic value) {
  if (value is! List) return const <String>[];
  return value.map((item) => item.toString()).toList(growable: false);
}

int _severityRank(String severity) => switch (severity) {
      'BLOCKING' => 0,
      'ERROR' => 1,
      'WARNING' => 2,
      _ => 3,
    };

int _healthItemCount(Map<String, dynamic> health) {
  var count = 0;
  for (final key in const ['conditions', 'allergies', 'drug_reactions']) {
    final value = health[key];
    if (value is List) count += value.length;
  }
  return count;
}

String _medicationDescription(Map<String, dynamic> item) {
  final parts = <String>[
    if (item['strength'] != null) item['strength'].toString(),
    if (item['dose_amount'] != null)
      '${item['dose_amount']} ${item['dose_unit'] ?? ''}'.trim(),
    if (item['frequency_text'] != null) item['frequency_text'].toString(),
    if (item['route'] != null) item['route'].toString(),
  ];
  return parts.isEmpty ? 'Chưa đủ thông tin liều dùng' : parts.join(' · ');
}
