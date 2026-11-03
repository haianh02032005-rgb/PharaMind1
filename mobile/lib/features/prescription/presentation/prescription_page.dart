import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';

class PrescriptionPage extends StatefulWidget {
  const PrescriptionPage({
    required this.api,
    required this.familyId,
    required this.members,
    required this.medications,
    super.key,
  });

  final ApiClient api;
  final int familyId;
  final List<Map<String, dynamic>> members;
  final List<Map<String, dynamic>> medications;

  @override
  State<PrescriptionPage> createState() => _PrescriptionPageState();
}

class _PrescriptionPageState extends State<PrescriptionPage> {
  bool _loading = true;
  bool _saving = false;
  String? _error;
  int? _memberFilter;
  String _statusFilter = 'ALL';
  List<Map<String, dynamic>> _prescriptions = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant PrescriptionPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.familyId != widget.familyId) {
      _memberFilter = null;
      _statusFilter = 'ALL';
      _load();
    }
  }

  static List<Map<String, dynamic>> _items(dynamic response) {
    final body = response is Map ? response['items'] : null;
    if (body is! List) return [];
    return body
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final response = await widget.api.dio.get(
        '/families/${widget.familyId}/prescriptions',
        queryParameters: {
          'include_archived': true,
          if (_memberFilter != null) 'member_id': _memberFilter,
          if (_statusFilter != 'ALL') 'status': _statusFilter,
        },
      );
      if (!mounted) return;
      setState(() => _prescriptions = _items(response.data));
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = widget.api.messageFor(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _createPrescription() async {
    if (widget.members.isEmpty) {
      _notify('Hãy thêm thành viên trước khi tạo đơn thuốc.');
      return;
    }
    if (widget.medications.isEmpty) {
      _notify('Hãy thêm thuốc vào kho gia đình trước khi tạo đơn.');
      return;
    }

    final draft = await showDialog<_PrescriptionDraft>(
      context: context,
      builder: (context) => _CreatePrescriptionDialog(
        members: widget.members,
        medications: widget.medications,
      ),
    );
    if (draft == null || !mounted) return;

    setState(() => _saving = true);
    int? createdPrescriptionId;
    try {
      final response = await widget.api.dio.post(
        '/families/${widget.familyId}/prescriptions',
        data: {
          'member_id': draft.memberId,
          'title': _optional(draft.title),
          'doctor_name': _optional(draft.doctorName),
          'facility_name': _optional(draft.facilityName),
          'status': 'ACTIVE',
          'notes': _optional(draft.notes),
        },
      );
      final responseBody = response.data;
      if (responseBody is! Map || responseBody['id'] is! int) {
        throw const FormatException('Phản hồi tạo đơn thuốc không hợp lệ.');
      }
      createdPrescriptionId = responseBody['id'] as int;

      await widget.api.dio.post(
        '/families/${widget.familyId}/prescriptions/'
        '$createdPrescriptionId/items',
        data: {
          'family_medication_id': draft.medicationId,
          'dose_amount': draft.doseAmount,
          'dose_unit': draft.doseUnit,
          'frequency_per_day': draft.frequencyPerDay,
          'frequency_text': _optional(draft.frequencyText),
          'route': draft.route,
          'instructions': _optional(draft.instructions),
        },
      );

      await _load();
      if (mounted) _notify('Đã tạo đơn thuốc và thêm thuốc thành công.');
    } catch (error) {
      if (!mounted) return;
      final prefix = createdPrescriptionId == null
          ? 'Không thể tạo đơn thuốc.'
          : 'Đơn đã được tạo nhưng chưa thể thêm thuốc.';
      final message = '$prefix ${widget.api.messageFor(error)}';
      await _load();
      if (mounted) setState(() => _error = message);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  static String? _optional(String value) {
    final trimmed = value.trim();
    return trimmed.isEmpty ? null : trimmed;
  }

  void _notify(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        RefreshIndicator(
          onRefresh: _load,
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(0, 4, 0, 96),
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      'Đơn thuốc',
                      style: Theme.of(context)
                          .textTheme
                          .titleLarge
                          ?.copyWith(fontWeight: FontWeight.w800),
                    ),
                  ),
                  FilledButton.icon(
                    onPressed: _saving ? null : _createPrescription,
                    icon: const Icon(Icons.add_rounded),
                    label: const Text('Tạo đơn'),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              const Text(
                'Theo dõi đơn thuốc và hướng dẫn dùng thuốc của từng thành viên.',
                style: TextStyle(color: Color(0xFF687875)),
              ),
              const SizedBox(height: 16),
              _FilterBar(
                members: widget.members,
                memberId: _memberFilter,
                status: _statusFilter,
                onMemberChanged: (value) {
                  setState(() => _memberFilter = value);
                  _load();
                },
                onStatusChanged: (value) {
                  setState(() => _statusFilter = value);
                  _load();
                },
              ),
              const SizedBox(height: 14),
              if (_error != null) ...[
                _MessageCard(
                  icon: Icons.error_outline_rounded,
                  message: _error!,
                  color: const Color(0xFFB34338),
                  actionLabel: 'Thử lại',
                  onAction: _load,
                ),
                const SizedBox(height: 12),
              ],
              if (_loading)
                const Padding(
                  padding: EdgeInsets.only(top: 56),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_prescriptions.isEmpty)
                _MessageCard(
                  icon: Icons.receipt_long_outlined,
                  message: _memberFilter == null && _statusFilter == 'ALL'
                      ? 'Gia đình chưa có đơn thuốc. Hãy tạo đơn đầu tiên.'
                      : 'Không có đơn thuốc phù hợp bộ lọc.',
                  color: const Color(0xFF087E79),
                  actionLabel: _memberFilter == null && _statusFilter == 'ALL'
                      ? 'Tạo đơn thuốc'
                      : 'Xóa bộ lọc',
                  onAction: _memberFilter == null && _statusFilter == 'ALL'
                      ? _createPrescription
                      : () {
                          setState(() {
                            _memberFilter = null;
                            _statusFilter = 'ALL';
                          });
                          _load();
                        },
                )
              else
                ..._prescriptions.map(
                  (prescription) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: _PrescriptionCard(prescription: prescription),
                  ),
                ),
            ],
          ),
        ),
        if (_saving)
          Positioned.fill(
            child: ColoredBox(
              color: Colors.black.withValues(alpha: .08),
              child: const Center(child: CircularProgressIndicator()),
            ),
          ),
      ],
    );
  }
}

class _FilterBar extends StatelessWidget {
  const _FilterBar({
    required this.members,
    required this.memberId,
    required this.status,
    required this.onMemberChanged,
    required this.onStatusChanged,
  });

  final List<Map<String, dynamic>> members;
  final int? memberId;
  final String status;
  final ValueChanged<int?> onMemberChanged;
  final ValueChanged<String> onStatusChanged;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final memberPicker = DropdownButtonFormField<int?>(
          initialValue: memberId,
          isExpanded: true,
          decoration: const InputDecoration(
            labelText: 'Thành viên',
            prefixIcon: Icon(Icons.person_outline),
          ),
          items: [
            const DropdownMenuItem<int?>(
              value: null,
              child: Text('Tất cả thành viên'),
            ),
            ...members.map(
              (member) => DropdownMenuItem<int?>(
                value: member['id'] as int?,
                child: Text(
                  member['full_name']?.toString() ?? 'Thành viên',
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),
          ],
          onChanged: onMemberChanged,
        );
        final statusPicker = DropdownButtonFormField<String>(
          initialValue: status,
          isExpanded: true,
          decoration: const InputDecoration(
            labelText: 'Trạng thái',
            prefixIcon: Icon(Icons.tune_rounded),
          ),
          items: const [
            DropdownMenuItem(value: 'ALL', child: Text('Tất cả')),
            DropdownMenuItem(value: 'ACTIVE', child: Text('Đang dùng')),
            DropdownMenuItem(value: 'DRAFT', child: Text('Bản nháp')),
            DropdownMenuItem(value: 'COMPLETED', child: Text('Hoàn thành')),
            DropdownMenuItem(value: 'ARCHIVED', child: Text('Đã lưu trữ')),
          ],
          onChanged: (value) {
            if (value != null) onStatusChanged(value);
          },
        );
        if (constraints.maxWidth >= 560) {
          return Row(
            children: [
              Expanded(child: memberPicker),
              const SizedBox(width: 10),
              Expanded(child: statusPicker),
            ],
          );
        }
        return Column(
          children: [
            memberPicker,
            const SizedBox(height: 10),
            statusPicker,
          ],
        );
      },
    );
  }
}

class _PrescriptionCard extends StatelessWidget {
  const _PrescriptionCard({required this.prescription});

  final Map<String, dynamic> prescription;

  @override
  Widget build(BuildContext context) {
    final member = prescription['member'] as Map?;
    final rawItems = prescription['items'];
    final items =
        rawItems is List ? rawItems.whereType<Map>().toList() : <Map>[];
    final status = prescription['status']?.toString() ?? 'ACTIVE';
    final statusPresentation = _status(status);
    final title = prescription['title']?.toString().trim();

    return Card(
      child: ExpansionTile(
        tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        leading: Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            color: const Color(0xFFE8F4F1),
            borderRadius: BorderRadius.circular(14),
          ),
          child:
              const Icon(Icons.receipt_long_outlined, color: Color(0xFF087E79)),
        ),
        title: Text(
          title == null || title.isEmpty
              ? 'Đơn thuốc #${prescription['id']}'
              : title,
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        subtitle: Text(
          [
            member?['full_name']?.toString() ?? 'Thành viên',
            if (prescription['issued_at'] != null)
              'Ngày ${prescription['issued_at']}',
            '${items.length} thuốc',
          ].join(' · '),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: _StatusChip(
          label: statusPresentation.$1,
          color: statusPresentation.$2,
        ),
        children: [
          if (prescription['doctor_name'] != null ||
              prescription['facility_name'] != null)
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                [
                  prescription['doctor_name'],
                  prescription['facility_name'],
                ]
                    .whereType<String>()
                    .where((value) => value.isNotEmpty)
                    .join(' · '),
                style: const TextStyle(color: Color(0xFF687875), fontSize: 13),
              ),
            ),
          if (items.isEmpty)
            const Padding(
              padding: EdgeInsets.only(top: 12),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text('Đơn này chưa có thuốc.'),
              ),
            )
          else
            ...items.map((item) => _PrescriptionItemTile(item: item)),
          if (prescription['notes'] != null) ...[
            const Divider(height: 24),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                prescription['notes'].toString(),
                style: const TextStyle(color: Color(0xFF687875)),
              ),
            ),
          ],
        ],
      ),
    );
  }

  static (String, Color) _status(String status) => switch (status) {
        'DRAFT' => ('Bản nháp', const Color(0xFF6F7782)),
        'COMPLETED' => ('Hoàn thành', const Color(0xFF356D9B)),
        'ARCHIVED' => ('Lưu trữ', const Color(0xFF8A6A48)),
        _ => ('Đang dùng', const Color(0xFF24734F)),
      };
}

class _PrescriptionItemTile extends StatelessWidget {
  const _PrescriptionItemTile({required this.item});

  final Map item;

  @override
  Widget build(BuildContext context) {
    final medication = item['medication'] as Map?;
    final dose = [item['dose_amount'], _doseUnit(item['dose_unit'])]
        .where((value) => value != null && value.toString().isNotEmpty)
        .join(' ');
    final frequency = item['frequency_text']?.toString().trim();
    final perDay = item['frequency_per_day'];
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(top: 2),
            child: Icon(Icons.medication_outlined,
                size: 20, color: Color(0xFFB66A19)),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  medication?['name']?.toString() ?? 'Thuốc',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                Text(
                  [
                    medication?['strength'],
                    if (dose.isNotEmpty) dose,
                    if (frequency != null && frequency.isNotEmpty)
                      frequency
                    else if (perDay != null)
                      '$perDay lần/ngày',
                  ]
                      .whereType<Object>()
                      .map((value) => value.toString())
                      .join(' · '),
                  style:
                      const TextStyle(color: Color(0xFF687875), fontSize: 13),
                ),
                if (item['instructions'] != null)
                  Text(
                    item['instructions'].toString(),
                    style: const TextStyle(fontSize: 12),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  static String? _doseUnit(dynamic value) => const {
        'TABLET': 'viên',
        'CAPSULE': 'viên nang',
        'ML': 'ml',
        'BOTTLE': 'chai',
        'BOX': 'hộp',
        'SACHET': 'gói',
        'VIAL': 'lọ',
        'AMPULE': 'ống',
        'DROP': 'giọt',
        'PUFF': 'nhát',
        'PATCH': 'miếng',
        'OTHER': 'đơn vị',
      }[value?.toString()];
}

class _CreatePrescriptionDialog extends StatefulWidget {
  const _CreatePrescriptionDialog({
    required this.members,
    required this.medications,
  });

  final List<Map<String, dynamic>> members;
  final List<Map<String, dynamic>> medications;

  @override
  State<_CreatePrescriptionDialog> createState() =>
      _CreatePrescriptionDialogState();
}

class _CreatePrescriptionDialogState extends State<_CreatePrescriptionDialog> {
  final _formKey = GlobalKey<FormState>();
  final _title = TextEditingController();
  final _doctor = TextEditingController();
  final _facility = TextEditingController();
  final _notes = TextEditingController();
  final _dose = TextEditingController(text: '1');
  final _frequency = TextEditingController(text: '1');
  final _frequencyText = TextEditingController();
  final _instructions = TextEditingController();

  late int _memberId;
  late int _medicationId;
  String _doseUnit = 'TABLET';
  String _route = 'ORAL';

  @override
  void initState() {
    super.initState();
    _memberId = widget.members.first['id'] as int;
    _medicationId = widget.medications.first['id'] as int;
  }

  @override
  void dispose() {
    _title.dispose();
    _doctor.dispose();
    _facility.dispose();
    _notes.dispose();
    _dose.dispose();
    _frequency.dispose();
    _frequencyText.dispose();
    _instructions.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.pop(
      context,
      _PrescriptionDraft(
        memberId: _memberId,
        medicationId: _medicationId,
        title: _title.text,
        doctorName: _doctor.text,
        facilityName: _facility.text,
        notes: _notes.text,
        doseAmount: double.parse(_dose.text.trim()),
        doseUnit: _doseUnit,
        frequencyPerDay: double.parse(_frequency.text.trim()),
        frequencyText: _frequencyText.text,
        route: _route,
        instructions: _instructions.text,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      scrollable: true,
      title: const Text('Tạo đơn thuốc mới'),
      content: SizedBox(
        width: 520,
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const _FormSectionTitle('Thông tin đơn thuốc'),
              DropdownButtonFormField<int>(
                initialValue: _memberId,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Thành viên *'),
                items: widget.members
                    .map(
                      (member) => DropdownMenuItem<int>(
                        value: member['id'] as int,
                        child: Text(
                          member['full_name']?.toString() ?? 'Thành viên',
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  if (value != null) setState(() => _memberId = value);
                },
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _title,
                maxLength: 200,
                decoration: const InputDecoration(labelText: 'Tên đơn thuốc'),
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _doctor,
                maxLength: 150,
                decoration: const InputDecoration(labelText: 'Bác sĩ'),
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _facility,
                maxLength: 200,
                decoration:
                    const InputDecoration(labelText: 'Cơ sở khám chữa bệnh'),
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _notes,
                maxLines: 2,
                decoration:
                    const InputDecoration(labelText: 'Ghi chú đơn thuốc'),
              ),
              const SizedBox(height: 18),
              const _FormSectionTitle('Thuốc đầu tiên'),
              DropdownButtonFormField<int>(
                initialValue: _medicationId,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Thuốc *'),
                items: widget.medications
                    .map(
                      (medication) => DropdownMenuItem<int>(
                        value: medication['id'] as int,
                        child: Text(
                          _medicationLabel(medication),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  if (value != null) setState(() => _medicationId = value);
                },
              ),
              const SizedBox(height: 10),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _dose,
                      keyboardType:
                          const TextInputType.numberWithOptions(decimal: true),
                      decoration:
                          const InputDecoration(labelText: 'Liều mỗi lần *'),
                      validator: _positiveNumber,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _doseUnit,
                      isExpanded: true,
                      decoration:
                          const InputDecoration(labelText: 'Đơn vị liều *'),
                      items: _doseUnits.entries
                          .map(
                            (entry) => DropdownMenuItem(
                              value: entry.key,
                              child: Text(entry.value),
                            ),
                          )
                          .toList(),
                      onChanged: (value) {
                        if (value != null) setState(() => _doseUnit = value);
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _frequency,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration:
                    const InputDecoration(labelText: 'Số lần mỗi ngày *'),
                validator: _positiveNumber,
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _frequencyText,
                maxLength: 150,
                decoration: const InputDecoration(
                  labelText: 'Mô tả tần suất',
                  hintText: 'Ví dụ: sáng và tối sau ăn',
                ),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                initialValue: _route,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Đường dùng *'),
                items: _routes.entries
                    .map(
                      (entry) => DropdownMenuItem(
                        value: entry.key,
                        child: Text(entry.value),
                      ),
                    )
                    .toList(),
                onChanged: (value) {
                  if (value != null) setState(() => _route = value);
                },
              ),
              const SizedBox(height: 10),
              TextFormField(
                controller: _instructions,
                maxLines: 2,
                decoration: const InputDecoration(
                  labelText: 'Hướng dẫn sử dụng',
                  hintText: 'Ví dụ: uống sau ăn, không nhai viên',
                ),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Hủy'),
        ),
        FilledButton.icon(
          onPressed: _submit,
          icon: const Icon(Icons.check_rounded),
          label: const Text('Tạo đơn'),
        ),
      ],
    );
  }

  static String? _positiveNumber(String? value) {
    final number = double.tryParse(value?.trim() ?? '');
    if (number == null || number <= 0) return 'Nhập số lớn hơn 0';
    return null;
  }

  static String _medicationLabel(Map<String, dynamic> medication) {
    final catalog = medication['catalog'] as Map?;
    return [catalog?['name'] ?? 'Thuốc', catalog?['strength']]
        .whereType<Object>()
        .map((value) => value.toString())
        .where((value) => value.isNotEmpty)
        .join(' · ');
  }

  static const _doseUnits = <String, String>{
    'TABLET': 'Viên',
    'CAPSULE': 'Viên nang',
    'ML': 'ml',
    'BOTTLE': 'Chai',
    'BOX': 'Hộp',
    'SACHET': 'Gói',
    'VIAL': 'Lọ',
    'AMPULE': 'Ống',
    'DROP': 'Giọt',
    'PUFF': 'Nhát',
    'PATCH': 'Miếng dán',
    'OTHER': 'Khác',
  };

  static const _routes = <String, String>{
    'ORAL': 'Đường uống',
    'TOPICAL': 'Bôi ngoài da',
    'INHALATION': 'Đường hít',
    'INJECTION': 'Tiêm',
    'EYE': 'Nhỏ mắt',
    'EAR': 'Nhỏ tai',
    'NASAL': 'Đường mũi',
    'RECTAL': 'Đường trực tràng',
    'SUBLINGUAL': 'Ngậm dưới lưỡi',
    'TRANSDERMAL': 'Qua da',
    'OTHER': 'Khác',
  };
}

class _FormSectionTitle extends StatelessWidget {
  const _FormSectionTitle(this.title);
  final String title;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Text(
          title,
          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
        ),
      );
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.label, required this.color});
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
        decoration: BoxDecoration(
          color: color.withValues(alpha: .11),
          borderRadius: BorderRadius.circular(30),
        ),
        child: Text(
          label,
          style: TextStyle(
              color: color, fontSize: 10, fontWeight: FontWeight.w700),
        ),
      );
}

class _MessageCard extends StatelessWidget {
  const _MessageCard({
    required this.icon,
    required this.message,
    required this.color,
    required this.actionLabel,
    required this.onAction,
  });

  final IconData icon;
  final String message;
  final Color color;
  final String actionLabel;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            children: [
              Icon(icon, color: color, size: 34),
              const SizedBox(height: 10),
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: 8),
              TextButton(onPressed: onAction, child: Text(actionLabel)),
            ],
          ),
        ),
      );
}

class _PrescriptionDraft {
  const _PrescriptionDraft({
    required this.memberId,
    required this.medicationId,
    required this.title,
    required this.doctorName,
    required this.facilityName,
    required this.notes,
    required this.doseAmount,
    required this.doseUnit,
    required this.frequencyPerDay,
    required this.frequencyText,
    required this.route,
    required this.instructions,
  });

  final int memberId;
  final int medicationId;
  final String title;
  final String doctorName;
  final String facilityName;
  final String notes;
  final double doseAmount;
  final String doseUnit;
  final double frequencyPerDay;
  final String frequencyText;
  final String route;
  final String instructions;
}
