import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';

class MemberDetailPage extends StatefulWidget {
  const MemberDetailPage({
    required this.api,
    required this.familyId,
    required this.member,
    super.key,
  });

  final ApiClient api;
  final int familyId;
  final Map<String, dynamic> member;

  @override
  State<MemberDetailPage> createState() => _MemberDetailPageState();
}

class _MemberDetailPageState extends State<MemberDetailPage> {
  bool _loading = true;
  bool _saving = false;
  String? _error;
  late Map<String, dynamic> _member;
  Map<String, dynamic> _health = {};
  List<Map<String, dynamic>> _conditions = [];
  List<Map<String, dynamic>> _allergies = [];
  List<Map<String, dynamic>> _reactions = [];
  List<Map<String, dynamic>> _contacts = [];
  List<Map<String, dynamic>> _schedules = [];

  int get _memberId => (widget.member['id'] as num).toInt();
  String get _basePath => '/families/${widget.familyId}/members/$_memberId';

  @override
  void initState() {
    super.initState();
    _member = Map<String, dynamic>.from(widget.member);
    _load();
  }

  @override
  void didUpdateWidget(covariant MemberDetailPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.familyId != widget.familyId ||
        oldWidget.member['id'] != widget.member['id']) {
      _member = Map<String, dynamic>.from(widget.member);
      _load();
    }
  }

  static List<Map<String, dynamic>> _items(dynamic response) {
    final raw = response is Map ? response['items'] : null;
    if (raw is! List) return [];
    return raw
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  static Map<String, dynamic> _map(dynamic response) {
    if (response is! Map) return {};
    return Map<String, dynamic>.from(response);
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final responses = await Future.wait([
        widget.api.dio.get(_basePath),
        widget.api.dio.get('$_basePath/health-profile'),
        widget.api.dio.get('$_basePath/conditions'),
        widget.api.dio.get('$_basePath/allergies'),
        widget.api.dio.get('$_basePath/drug-reactions'),
        widget.api.dio.get('$_basePath/emergency-contacts'),
        widget.api.dio.get('$_basePath/schedules'),
      ]);
      if (!mounted) return;
      setState(() {
        _member = _map(responses[0].data);
        _health = _map(responses[1].data);
        _conditions = _items(responses[2].data);
        _allergies = _items(responses[3].data);
        _reactions = _items(responses[4].data);
        _contacts = _items(responses[5].data);
        _schedules = _items(responses[6].data);
      });
    } catch (error) {
      if (mounted) setState(() => _error = widget.api.messageFor(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _editHealthProfile() async {
    final update = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => _HealthProfileDialog(profile: _health),
    );
    if (update == null || !mounted) return;

    setState(() => _saving = true);
    try {
      final response = await widget.api.dio.patch(
        '$_basePath/health-profile',
        data: update,
      );
      if (!mounted) return;
      setState(() => _health = _map(response.data));
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đã cập nhật hồ sơ sức khỏe.')),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(widget.api.messageFor(error))),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final name = _member['full_name']?.toString() ?? 'Thành viên';
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text(name),
          actions: [
            IconButton(
              tooltip: 'Tải lại',
              onPressed: _loading ? null : _load,
              icon: const Icon(Icons.refresh_rounded),
            ),
          ],
          bottom: const TabBar(
            isScrollable: true,
            tabs: [
              Tab(icon: Icon(Icons.person_outline), text: 'Tổng quan'),
              Tab(icon: Icon(Icons.monitor_heart_outlined), text: 'Sức khỏe'),
              Tab(
                  icon: Icon(Icons.calendar_month_outlined),
                  text: 'Lịch thuốc'),
            ],
          ),
        ),
        body: Stack(
          children: [
            if (_loading)
              const Center(child: CircularProgressIndicator())
            else if (_error != null)
              _ErrorState(message: _error!, onRetry: _load)
            else
              TabBarView(
                children: [
                  _refreshable(_OverviewTab(
                    member: _member,
                    health: _health,
                    conditions: _conditions,
                    allergies: _allergies,
                    contacts: _contacts,
                  )),
                  _refreshable(_HealthTab(
                    health: _health,
                    conditions: _conditions,
                    allergies: _allergies,
                    reactions: _reactions,
                    onEdit: _saving ? null : _editHealthProfile,
                  )),
                  _refreshable(_ScheduleTab(schedules: _schedules)),
                ],
              ),
            if (_saving)
              Positioned.fill(
                child: ColoredBox(
                  color: Colors.black.withValues(alpha: .08),
                  child: const Center(child: CircularProgressIndicator()),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _refreshable(Widget child) => RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 36),
          children: [child],
        ),
      );
}

class _OverviewTab extends StatelessWidget {
  const _OverviewTab({
    required this.member,
    required this.health,
    required this.conditions,
    required this.allergies,
    required this.contacts,
  });

  final Map<String, dynamic> member;
  final Map<String, dynamic> health;
  final List<Map<String, dynamic>> conditions;
  final List<Map<String, dynamic>> allergies;
  final List<Map<String, dynamic>> contacts;

  @override
  Widget build(BuildContext context) {
    final name = member['full_name']?.toString() ?? 'Thành viên';
    final activeConditions =
        conditions.where((condition) => condition['status'] == 'ACTIVE').length;
    final severeAllergies =
        allergies.where((allergy) => allergy['severity'] == 'SEVERE').length;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 34,
                  backgroundColor: const Color(0xFFE7F3F0),
                  child: Text(
                    _initial(name),
                    style: const TextStyle(
                      color: Color(0xFF087E79),
                      fontSize: 25,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                const SizedBox(width: 15),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        name,
                        style: Theme.of(context)
                            .textTheme
                            .titleLarge
                            ?.copyWith(fontWeight: FontWeight.w800),
                      ),
                      Text(
                        member['relationship_label']?.toString() ??
                            'Thành viên gia đình',
                        style: const TextStyle(color: Color(0xFF687875)),
                      ),
                      const SizedBox(height: 5),
                      Wrap(
                        spacing: 10,
                        runSpacing: 4,
                        children: [
                          if (member['date_of_birth'] != null)
                            _InlineInfo(
                              icon: Icons.cake_outlined,
                              text: member['date_of_birth'].toString(),
                            ),
                          if (member['gender'] != null)
                            _InlineInfo(
                              icon: Icons.badge_outlined,
                              text: _gender(member['gender'].toString()),
                            ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 14),
        LayoutBuilder(
          builder: (context, constraints) {
            final count = constraints.maxWidth >= 660 ? 4 : 2;
            return GridView.count(
              crossAxisCount: count,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 10,
              crossAxisSpacing: 10,
              childAspectRatio: constraints.maxWidth >= 660 ? 1.55 : 1.35,
              children: [
                _MetricCard(
                  icon: Icons.bloodtype_outlined,
                  value: _bloodType(health['blood_type']),
                  label: 'Nhóm máu',
                ),
                _MetricCard(
                  icon: Icons.monitor_weight_outlined,
                  value: _numberUnit(health['weight_kg'], 'kg'),
                  label: 'Cân nặng',
                ),
                _MetricCard(
                  icon: Icons.height_rounded,
                  value: _numberUnit(health['height_cm'], 'cm'),
                  label: 'Chiều cao',
                ),
                _MetricCard(
                  icon: Icons.calculate_outlined,
                  value: health['bmi']?.toString() ?? '—',
                  label: 'BMI',
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 20),
        const _SectionTitle('Tổng quan an toàn'),
        const SizedBox(height: 9),
        Row(
          children: [
            Expanded(
              child: _SummaryCard(
                count: activeConditions,
                label: 'Bệnh nền đang theo dõi',
                icon: Icons.monitor_heart_outlined,
                alert: false,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _SummaryCard(
                count: allergies.length,
                label: severeAllergies > 0
                    ? '$severeAllergies dị ứng nghiêm trọng'
                    : 'Dị ứng đã ghi nhận',
                icon: Icons.warning_amber_rounded,
                alert: severeAllergies > 0,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        const _SectionTitle('Liên hệ khẩn cấp'),
        const SizedBox(height: 9),
        if (contacts.isEmpty)
          const _EmptyCard(
            icon: Icons.contact_emergency_outlined,
            text: 'Chưa có liên hệ khẩn cấp.',
          )
        else
          ...contacts.map(
            (contact) => Card(
              child: ListTile(
                leading: const CircleAvatar(
                  child: Icon(Icons.phone_outlined),
                ),
                title: Text(
                  contact['name']?.toString() ?? 'Người liên hệ',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                subtitle: Text(
                  [contact['relationship'], contact['phone']]
                      .whereType<String>()
                      .where((value) => value.isNotEmpty)
                      .join(' · '),
                ),
                trailing: contact['is_primary'] == true
                    ? const Tooltip(
                        message: 'Liên hệ chính',
                        child:
                            Icon(Icons.star_rounded, color: Color(0xFFB66A19)),
                      )
                    : null,
              ),
            ),
          ),
      ],
    );
  }
}

class _HealthTab extends StatelessWidget {
  const _HealthTab({
    required this.health,
    required this.conditions,
    required this.allergies,
    required this.reactions,
    required this.onEdit,
  });

  final Map<String, dynamic> health;
  final List<Map<String, dynamic>> conditions;
  final List<Map<String, dynamic>> allergies;
  final List<Map<String, dynamic>> reactions;
  final VoidCallback? onEdit;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            const Expanded(child: _SectionTitle('Hồ sơ sức khỏe')),
            FilledButton.tonalIcon(
              onPressed: onEdit,
              icon: const Icon(Icons.edit_outlined, size: 18),
              label: const Text('Chỉnh sửa'),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 24,
                  runSpacing: 12,
                  children: [
                    _LabelValue('Nhóm máu', _bloodType(health['blood_type'])),
                    _LabelValue(
                      'Chiều cao',
                      _numberUnit(health['height_cm'], 'cm'),
                    ),
                    _LabelValue(
                      'Cân nặng',
                      _numberUnit(health['weight_kg'], 'kg'),
                    ),
                    _LabelValue('BMI', health['bmi']?.toString() ?? '—'),
                  ],
                ),
                if (health['general_notes'] != null) ...[
                  const Divider(height: 26),
                  Text(
                    health['general_notes'].toString(),
                    style: const TextStyle(color: Color(0xFF5E6D69)),
                  ),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        const _SectionTitle('Bệnh nền'),
        const SizedBox(height: 8),
        if (conditions.isEmpty)
          const _EmptyCard(
            icon: Icons.monitor_heart_outlined,
            text: 'Chưa ghi nhận bệnh nền.',
          )
        else
          ...conditions.map(
            (condition) => _HealthListCard(
              icon: Icons.monitor_heart_outlined,
              title: condition['name']?.toString() ?? 'Bệnh nền',
              subtitle: [
                if (condition['diagnosed_at'] != null)
                  'Chẩn đoán ${condition['diagnosed_at']}',
                if (condition['notes'] != null) condition['notes'],
              ]
                  .whereType<Object>()
                  .map((value) => value.toString())
                  .join(' · '),
              badge: _conditionStatus(condition['status']?.toString()),
            ),
          ),
        const SizedBox(height: 20),
        const _SectionTitle('Dị ứng'),
        const SizedBox(height: 8),
        if (allergies.isEmpty)
          const _EmptyCard(
            icon: Icons.health_and_safety_outlined,
            text: 'Chưa ghi nhận dị ứng.',
          )
        else
          ...allergies.map(
            (allergy) => _HealthListCard(
              icon: Icons.warning_amber_rounded,
              title: allergy['allergen']?.toString() ?? 'Dị ứng',
              subtitle: [
                _allergyType(allergy['allergy_type']?.toString()),
                allergy['reaction_description'],
              ]
                  .whereType<Object>()
                  .map((value) => value.toString())
                  .join(' · '),
              badge: _severity(allergy['severity']?.toString()),
              danger: allergy['severity'] == 'SEVERE',
            ),
          ),
        const SizedBox(height: 20),
        const _SectionTitle('Phản ứng thuốc'),
        const SizedBox(height: 8),
        if (reactions.isEmpty)
          const _EmptyCard(
            icon: Icons.medication_outlined,
            text: 'Chưa ghi nhận phản ứng thuốc.',
          )
        else
          ...reactions.map(
            (reaction) => _HealthListCard(
              icon: Icons.medication_outlined,
              title: reaction['drug_name']?.toString() ?? 'Thuốc',
              subtitle: reaction['reaction']?.toString() ?? '',
              badge: _severity(reaction['severity']?.toString()),
              danger: reaction['severity'] == 'SEVERE',
            ),
          ),
      ],
    );
  }
}

class _ScheduleTab extends StatelessWidget {
  const _ScheduleTab({required this.schedules});
  final List<Map<String, dynamic>> schedules;

  @override
  Widget build(BuildContext context) {
    final ordered = [...schedules]..sort((a, b) {
        final aTime = _firstTime(a);
        final bTime = _firstTime(b);
        return aTime.compareTo(bTime);
      });
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const _SectionTitle('Lịch dùng thuốc'),
        const SizedBox(height: 6),
        const Text(
          'Các lịch đang được đồng bộ từ hệ thống PharmaMind.',
          style: TextStyle(color: Color(0xFF687875)),
        ),
        const SizedBox(height: 14),
        if (ordered.isEmpty)
          const _EmptyCard(
            icon: Icons.event_busy_outlined,
            text: 'Thành viên chưa có lịch dùng thuốc.',
          )
        else
          ...ordered.map((schedule) {
            final medication = schedule['medication'] as Map?;
            final times = schedule['times'] is List
                ? (schedule['times'] as List)
                    .map((value) => value.toString())
                    .toList()
                : <String>[];
            return Card(
              child: Padding(
                padding: const EdgeInsets.all(15),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFF3E2),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: const Icon(
                        Icons.medication_outlined,
                        color: Color(0xFFB66A19),
                      ),
                    ),
                    const SizedBox(width: 12),
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
                              if (schedule['dose_amount'] != null)
                                '${schedule['dose_amount']} ${_doseUnit(schedule['dose_unit'])}',
                            ]
                                .whereType<Object>()
                                .map((value) => value.toString())
                                .join(' · '),
                            style: const TextStyle(
                              color: Color(0xFF687875),
                              fontSize: 13,
                            ),
                          ),
                          const SizedBox(height: 7),
                          Wrap(
                            spacing: 6,
                            runSpacing: 6,
                            children: times
                                .map(
                                  (time) => Chip(
                                    visualDensity: VisualDensity.compact,
                                    avatar:
                                        const Icon(Icons.schedule, size: 15),
                                    label: Text(time),
                                  ),
                                )
                                .toList(),
                          ),
                        ],
                      ),
                    ),
                    _Badge(
                      label: _scheduleStatus(schedule['status']?.toString()),
                      danger: schedule['status'] == 'PAUSED',
                    ),
                  ],
                ),
              ),
            );
          }),
      ],
    );
  }

  static String _firstTime(Map<String, dynamic> schedule) {
    final times = schedule['times'];
    return times is List && times.isNotEmpty ? times.first.toString() : '99:99';
  }
}

class _HealthProfileDialog extends StatefulWidget {
  const _HealthProfileDialog({required this.profile});
  final Map<String, dynamic> profile;

  @override
  State<_HealthProfileDialog> createState() => _HealthProfileDialogState();
}

class _HealthProfileDialogState extends State<_HealthProfileDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _height;
  late final TextEditingController _weight;
  late final TextEditingController _notes;
  String? _bloodType;

  @override
  void initState() {
    super.initState();
    _bloodType = widget.profile['blood_type']?.toString();
    _height =
        TextEditingController(text: _numberText(widget.profile['height_cm']));
    _weight =
        TextEditingController(text: _numberText(widget.profile['weight_kg']));
    _notes = TextEditingController(
      text: widget.profile['general_notes']?.toString() ?? '',
    );
  }

  @override
  void dispose() {
    _height.dispose();
    _weight.dispose();
    _notes.dispose();
    super.dispose();
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) return;
    Navigator.pop(context, {
      'blood_type': _bloodType,
      'height_cm': _nullableDouble(_height.text),
      'weight_kg': _nullableDouble(_weight.text),
      'general_notes': _notes.text.trim().isEmpty ? null : _notes.text.trim(),
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      scrollable: true,
      title: const Text('Cập nhật hồ sơ sức khỏe'),
      content: SizedBox(
        width: 460,
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              DropdownButtonFormField<String?>(
                initialValue: _bloodType,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Nhóm máu'),
                items: const [
                  DropdownMenuItem<String?>(
                    value: null,
                    child: Text('Chưa xác định'),
                  ),
                  DropdownMenuItem(value: 'A+', child: Text('A+')),
                  DropdownMenuItem(value: 'A-', child: Text('A-')),
                  DropdownMenuItem(value: 'B+', child: Text('B+')),
                  DropdownMenuItem(value: 'B-', child: Text('B-')),
                  DropdownMenuItem(value: 'AB+', child: Text('AB+')),
                  DropdownMenuItem(value: 'AB-', child: Text('AB-')),
                  DropdownMenuItem(value: 'O+', child: Text('O+')),
                  DropdownMenuItem(value: 'O-', child: Text('O-')),
                  DropdownMenuItem(value: 'UNKNOWN', child: Text('Không rõ')),
                ],
                onChanged: (value) => setState(() => _bloodType = value),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _height,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Chiều cao (cm)',
                  prefixIcon: Icon(Icons.height_rounded),
                ),
                validator: (value) => _numberRange(value, max: 300),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _weight,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Cân nặng (kg)',
                  prefixIcon: Icon(Icons.monitor_weight_outlined),
                ),
                validator: (value) => _numberRange(value, max: 500),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _notes,
                minLines: 3,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: 'Ghi chú sức khỏe chung',
                  alignLabelWithHint: true,
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
          icon: const Icon(Icons.save_outlined),
          label: const Text('Lưu'),
        ),
      ],
    );
  }

  static String _numberText(dynamic value) {
    if (value == null) return '';
    final number =
        value is num ? value.toDouble() : double.tryParse(value.toString());
    if (number == null) return '';
    return number == number.roundToDouble()
        ? number.toInt().toString()
        : number.toString();
  }

  static double? _nullableDouble(String raw) {
    final value = raw.trim();
    return value.isEmpty ? null : double.parse(value);
  }

  static String? _numberRange(String? raw, {required double max}) {
    final value = raw?.trim() ?? '';
    if (value.isEmpty) return null;
    final number = double.tryParse(value);
    if (number == null || number <= 0 || number > max) {
      return 'Nhập số lớn hơn 0 và không quá ${max.toInt()}';
    }
    return null;
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.icon,
    required this.value,
    required this.label,
  });
  final IconData icon;
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: const Color(0xFF087E79)),
              const SizedBox(height: 7),
              Text(
                value,
                style:
                    const TextStyle(fontSize: 19, fontWeight: FontWeight.w800),
              ),
              Text(
                label,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Color(0xFF687875), fontSize: 11),
              ),
            ],
          ),
        ),
      );
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({
    required this.count,
    required this.label,
    required this.icon,
    required this.alert,
  });
  final int count;
  final String label;
  final IconData icon;
  final bool alert;

  @override
  Widget build(BuildContext context) => Card(
        color: alert ? const Color(0xFFFFEFED) : null,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                icon,
                color:
                    alert ? const Color(0xFFB34338) : const Color(0xFF087E79),
              ),
              const SizedBox(height: 8),
              Text(
                '$count',
                style:
                    const TextStyle(fontSize: 23, fontWeight: FontWeight.w800),
              ),
              Text(
                label,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: Color(0xFF687875), fontSize: 12),
              ),
            ],
          ),
        ),
      );
}

class _HealthListCard extends StatelessWidget {
  const _HealthListCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.badge,
    this.danger = false,
  });
  final IconData icon;
  final String title;
  final String subtitle;
  final String badge;
  final bool danger;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: Icon(
            icon,
            color: danger ? const Color(0xFFB34338) : const Color(0xFF087E79),
          ),
          title:
              Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
          subtitle: subtitle.isEmpty ? null : Text(subtitle),
          trailing: _Badge(label: badge, danger: danger),
        ),
      );
}

class _Badge extends StatelessWidget {
  const _Badge({required this.label, this.danger = false});
  final String label;
  final bool danger;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
        decoration: BoxDecoration(
          color: danger ? const Color(0xFFFFE2DE) : const Color(0xFFE7F3F0),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: danger ? const Color(0xFF9B352D) : const Color(0xFF24734F),
            fontSize: 10,
            fontWeight: FontWeight.w700,
          ),
        ),
      );
}

class _LabelValue extends StatelessWidget {
  const _LabelValue(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => SizedBox(
        width: 115,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: const TextStyle(color: Color(0xFF687875), fontSize: 12),
            ),
            const SizedBox(height: 2),
            Text(value, style: const TextStyle(fontWeight: FontWeight.w700)),
          ],
        ),
      );
}

class _InlineInfo extends StatelessWidget {
  const _InlineInfo({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: const Color(0xFF71807D)),
          const SizedBox(width: 4),
          Text(
            text,
            style: const TextStyle(color: Color(0xFF71807D), fontSize: 12),
          ),
        ],
      );
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.title);
  final String title;

  @override
  Widget build(BuildContext context) => Text(
        title,
        style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800),
      );
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(17),
          child: Row(
            children: [
              Icon(icon, color: const Color(0xFF71807D)),
              const SizedBox(width: 11),
              Expanded(
                child: Text(
                  text,
                  style: const TextStyle(color: Color(0xFF687875)),
                ),
              ),
            ],
          ),
        ),
      );
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.wifi_off_rounded,
                color: Color(0xFFB34338),
                size: 42,
              ),
              const SizedBox(height: 12),
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: 10),
              FilledButton.tonalIcon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Thử lại'),
              ),
            ],
          ),
        ),
      );
}

String _initial(String name) {
  final trimmed = name.trim();
  return trimmed.isEmpty
      ? 'T'
      : String.fromCharCode(trimmed.runes.first).toUpperCase();
}

String _bloodType(dynamic value) {
  if (value == null || value.toString() == 'UNKNOWN') return 'Chưa rõ';
  return value.toString();
}

String _numberUnit(dynamic value, String unit) =>
    value == null ? '—' : '$value $unit';

String _gender(String value) => switch (value) {
      'MALE' => 'Nam',
      'FEMALE' => 'Nữ',
      'OTHER' => 'Khác',
      _ => 'Chưa xác định',
    };

String _conditionStatus(String? value) => switch (value) {
      'RESOLVED' => 'Đã ổn định',
      'UNKNOWN' => 'Chưa rõ',
      _ => 'Đang theo dõi',
    };

String _allergyType(String? value) => switch (value) {
      'DRUG' => 'Dị ứng thuốc',
      'FOOD' => 'Dị ứng thực phẩm',
      'ENVIRONMENT' => 'Dị ứng môi trường',
      _ => 'Dị ứng khác',
    };

String _severity(String? value) => switch (value) {
      'MILD' => 'Nhẹ',
      'MODERATE' => 'Trung bình',
      'SEVERE' => 'Nghiêm trọng',
      _ => 'Chưa rõ',
    };

String _scheduleStatus(String? value) => switch (value) {
      'PAUSED' => 'Tạm dừng',
      'COMPLETED' => 'Hoàn thành',
      'ARCHIVED' => 'Lưu trữ',
      _ => 'Đang dùng',
    };

String _doseUnit(dynamic value) =>
    const {
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
    }[value?.toString()] ??
    '';
