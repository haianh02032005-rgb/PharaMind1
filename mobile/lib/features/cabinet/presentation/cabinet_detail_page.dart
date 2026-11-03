import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';

class CabinetDetailPage extends StatefulWidget {
  const CabinetDetailPage({
    required this.api,
    required this.familyId,
    this.cabinet,
    this.cabinetId,
    super.key,
  }) : assert(cabinet != null || cabinetId != null);

  final ApiClient api;
  final int familyId;
  final Map<String, dynamic>? cabinet;
  final int? cabinetId;

  @override
  State<CabinetDetailPage> createState() => _CabinetDetailPageState();
}

class _CabinetDetailPageState extends State<CabinetDetailPage>
    with WidgetsBindingObserver {
  Map<String, dynamic>? _digitalTwin;
  bool _loading = true;
  bool _refreshing = false;
  String? _error;
  int? _changingPosition;
  int? _selectedPosition;

  int get _cabinetId {
    final raw = widget.cabinetId ?? widget.cabinet?['id'];
    if (raw is int) return raw;
    if (raw is num) return raw.toInt();
    return int.parse(raw.toString());
  }

  Map<String, dynamic> get _cabinetHeader {
    final header = _digitalTwin?['cabinet'];
    if (header is Map) return Map<String, dynamic>.from(header);
    return widget.cabinet ?? <String, dynamic>{};
  }

  List<Map<String, dynamic>> get _compartments {
    final raw = _digitalTwin?['compartments'];
    final loaded = raw is List
        ? raw
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList()
        : <Map<String, dynamic>>[];
    loaded.sort((a, b) => _position(a).compareTo(_position(b)));
    final byPosition = <int, Map<String, dynamic>>{
      for (final item in loaded) _position(item): item,
    };
    return List.generate(
      9,
      (index) =>
          byPosition[index + 1] ??
          <String, dynamic>{
            'position': index + 1,
            'object_id': 'drawer_${(index + 1).toString().padLeft(2, '0')}',
            'status': 'EMPTY',
            'is_open': false,
          },
    );
  }

  static int _position(Map<String, dynamic> item) {
    final value = item['position'];
    if (value is int) return value;
    if (value is num) return value.toInt();
    return int.tryParse(value?.toString() ?? '') ?? 0;
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _load();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _load(background: true);
    }
  }

  Future<void> _load({bool background = false}) async {
    if (!mounted) return;
    setState(() {
      if (background && _digitalTwin != null) {
        _refreshing = true;
      } else {
        _loading = true;
      }
      _error = null;
    });
    try {
      final response = await widget.api.dio.get(
        '/families/${widget.familyId}/cabinets/$_cabinetId/digital-twin',
      );
      if (response.data is! Map) {
        throw StateError('Dữ liệu tủ thuốc không hợp lệ.');
      }
      if (!mounted) return;
      setState(() {
        _digitalTwin = Map<String, dynamic>.from(response.data as Map);
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = widget.api.messageFor(error));
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
          _refreshing = false;
        });
      }
    }
  }

  Future<bool> _setCompartmentOpen(
    Map<String, dynamic> compartment,
    bool shouldOpen,
  ) async {
    final position = _position(compartment);
    if (_changingPosition != null || position <= 0) return false;
    setState(() => _changingPosition = position);
    try {
      await widget.api.dio.post(
        '/families/${widget.familyId}/cabinets/$_cabinetId/'
        'compartments/$position/${shouldOpen ? 'open' : 'close'}',
      );
      await _load(background: true);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              shouldOpen ? 'Đã mở ngăn $position.' : 'Đã đóng ngăn $position.',
            ),
          ),
        );
      }
      return true;
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(widget.api.messageFor(error))),
        );
      }
      return false;
    } finally {
      if (mounted) setState(() => _changingPosition = null);
    }
  }

  Future<void> _showCompartment(Map<String, dynamic> compartment) async {
    final position = _position(compartment);
    setState(() => _selectedPosition = position);
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (sheetContext) => _CompartmentSheet(
        compartment: compartment,
        changing: _changingPosition == position,
        onToggle: () async {
          final isOpen = compartment['is_open'] == true;
          final changed = await _setCompartmentOpen(compartment, !isOpen);
          if (changed && sheetContext.mounted) Navigator.pop(sheetContext);
        },
      ),
    );
    if (mounted) setState(() => _selectedPosition = null);
  }

  @override
  Widget build(BuildContext context) {
    final cabinet = _cabinetHeader;
    final online = cabinet['status']?.toString().toUpperCase() == 'ONLINE';
    final title = cabinet['name']?.toString() ?? 'Tủ thuốc';

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
            Text(
              cabinet['device_code']?.toString() ?? 'Digital Twin',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w400),
            ),
          ],
        ),
        actions: [
          if (_refreshing)
            const Padding(
              padding: EdgeInsets.all(16),
              child: SizedBox.square(
                dimension: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            )
          else
            IconButton(
              tooltip: 'Tải lại trạng thái',
              onPressed: () => _load(background: true),
              icon: const Icon(Icons.refresh_rounded),
            ),
        ],
      ),
      body: _loading && _digitalTwin == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () => _load(background: true),
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
                children: [
                  if (_error != null) ...[
                    _ErrorCard(
                      message: _error!,
                      onRetry: () => _load(background: true),
                    ),
                    const SizedBox(height: 14),
                  ],
                  _CabinetStatusCard(cabinet: cabinet, online: online),
                  const SizedBox(height: 22),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'Sơ đồ 9 ngăn',
                          style: Theme.of(context)
                              .textTheme
                              .titleLarge
                              ?.copyWith(fontWeight: FontWeight.w800),
                        ),
                      ),
                      const Text(
                        'Chạm để xem chi tiết',
                        style:
                            TextStyle(color: Color(0xFF6F7E7B), fontSize: 12),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: 9,
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3,
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                      childAspectRatio: .92,
                    ),
                    itemBuilder: (context, index) {
                      final compartment = _compartments[index];
                      return _CompartmentCell(
                        compartment: compartment,
                        selected: _selectedPosition == _position(compartment),
                        changing: _changingPosition == _position(compartment),
                        onTap: () => _showCompartment(compartment),
                      );
                    },
                  ),
                  const SizedBox(height: 18),
                  const _Legend(),
                ],
              ),
            ),
    );
  }
}

class _CabinetStatusCard extends StatelessWidget {
  const _CabinetStatusCard({required this.cabinet, required this.online});

  final Map<String, dynamic> cabinet;
  final bool online;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Row(
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: const Color(0xFFE8F3F0),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(
                Icons.inventory_2_outlined,
                color: Color(0xFF087E79),
              ),
            ),
            const SizedBox(width: 13),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    online ? 'Tủ đang kết nối' : 'Tủ đang ngoại tuyến',
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    cabinet['hardware_mode']?.toString() ?? 'Không rõ chế độ',
                    style: const TextStyle(color: Color(0xFF6F7E7B)),
                  ),
                ],
              ),
            ),
            Container(
              width: 11,
              height: 11,
              decoration: BoxDecoration(
                color:
                    online ? const Color(0xFF36A16B) : const Color(0xFFE08445),
                shape: BoxShape.circle,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CompartmentCell extends StatelessWidget {
  const _CompartmentCell({
    required this.compartment,
    required this.selected,
    required this.changing,
    required this.onTap,
  });

  final Map<String, dynamic> compartment;
  final bool selected;
  final bool changing;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final position = _CabinetDetailPageState._position(compartment);
    final medication = compartment['medication'] is Map
        ? Map<String, dynamic>.from(compartment['medication'] as Map)
        : null;
    final hasMedication = medication != null;
    final isOpen = compartment['is_open'] == true;
    final background = isOpen
        ? const Color(0xFFFFF0E3)
        : hasMedication
            ? const Color(0xFFE7F4EF)
            : const Color(0xFFF3F6F5);

    return Material(
      color: background,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(17),
        side: BorderSide(
          color: selected
              ? const Color(0xFF087E79)
              : isOpen
                  ? const Color(0xFFE2A16E)
                  : hasMedication
                      ? const Color(0xFFBFDCCF)
                      : const Color(0xFFE2E9E6),
          width: selected ? 2 : 1,
        ),
      ),
      child: InkWell(
        onTap: changing ? null : onTap,
        borderRadius: BorderRadius.circular(17),
        child: Padding(
          padding: const EdgeInsets.all(11),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(
                    'NGĂN ${position.toString().padLeft(2, '0')}',
                    style: const TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF657572),
                      letterSpacing: .5,
                    ),
                  ),
                  const Spacer(),
                  if (changing)
                    const SizedBox.square(
                      dimension: 13,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  else
                    Icon(
                      isOpen
                          ? Icons.lock_open_rounded
                          : Icons.lock_outline_rounded,
                      size: 15,
                      color: isOpen
                          ? const Color(0xFFB4642E)
                          : const Color(0xFF60716D),
                    ),
                ],
              ),
              const Spacer(),
              Icon(
                hasMedication ? Icons.medication_rounded : Icons.inbox_outlined,
                size: 24,
                color: hasMedication
                    ? const Color(0xFF087E79)
                    : const Color(0xFF8A9794),
              ),
              const SizedBox(height: 5),
              Text(
                hasMedication
                    ? medication['name']?.toString() ?? 'Thuốc'
                    : 'Trống',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 11,
                  height: 1.1,
                  fontWeight: hasMedication ? FontWeight.w700 : FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CompartmentSheet extends StatelessWidget {
  const _CompartmentSheet({
    required this.compartment,
    required this.changing,
    required this.onToggle,
  });

  final Map<String, dynamic> compartment;
  final bool changing;
  final Future<void> Function() onToggle;

  static List<Map<String, dynamic>> _maps(Object? value) {
    if (value is! List) return [];
    return value
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final position = _CabinetDetailPageState._position(compartment);
    final medication = compartment['medication'] is Map
        ? Map<String, dynamic>.from(compartment['medication'] as Map)
        : null;
    final members = _maps(compartment['members']);
    final allergyAlerts = _maps(compartment['allergy_alerts']);
    final warningCodes = compartment['warnings'] is List
        ? List<Object?>.from(compartment['warnings'] as List)
        : <Object?>[];
    final isOpen = compartment['is_open'] == true;

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: .72,
      minChildSize: .42,
      maxChildSize: .94,
      builder: (context, controller) => SafeArea(
        top: false,
        child: ListView(
          controller: controller,
          padding: const EdgeInsets.fromLTRB(22, 4, 22, 24),
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Ngăn ${position.toString().padLeft(2, '0')}',
                    style: Theme.of(context)
                        .textTheme
                        .headlineSmall
                        ?.copyWith(fontWeight: FontWeight.w800),
                  ),
                ),
                _StateBadge(isOpen: isOpen),
              ],
            ),
            const SizedBox(height: 18),
            if (medication == null)
              const _InfoCard(
                icon: Icons.inbox_outlined,
                title: 'Ngăn đang trống',
                subtitle: 'Chưa có thuốc được gán vào ngăn này.',
              )
            else
              _MedicationCard(medication: medication),
            const SizedBox(height: 18),
            const _SheetTitle(
                icon: Icons.people_outline, label: 'Thành viên sử dụng'),
            const SizedBox(height: 8),
            if (members.isEmpty)
              const Text('Chưa gán thành viên hoặc lịch uống cho ngăn này.')
            else
              ...members.map((member) => _MemberScheduleCard(member: member)),
            const SizedBox(height: 18),
            const _SheetTitle(
                icon: Icons.warning_amber_rounded, label: 'Cảnh báo'),
            const SizedBox(height: 8),
            if (warningCodes.isEmpty && allergyAlerts.isEmpty)
              const Text('Không có cảnh báo cho ngăn này.')
            else ...[
              ...warningCodes.map(
                (warning) =>
                    _WarningTile(message: _warningLabel(warning.toString())),
              ),
              ...allergyAlerts.map(
                (alert) => _WarningTile(
                  message:
                      alert['message']?.toString() ?? 'Cảnh báo dị ứng thuốc',
                  severe: true,
                ),
              ),
            ],
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: changing ? null : onToggle,
              icon: changing
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(isOpen ? Icons.lock_rounded : Icons.lock_open_rounded),
              label: Text(isOpen ? 'Đóng ngăn' : 'Mở ngăn'),
              style: FilledButton.styleFrom(
                minimumSize: const Size.fromHeight(52),
              ),
            ),
          ],
        ),
      ),
    );
  }

  static String _warningLabel(String code) => switch (code) {
        'LOW_STOCK' => 'Thuốc trong ngăn sắp hết.',
        'EXPIRED' => 'Thuốc trong ngăn đã hết hạn.',
        'EXPIRING_SOON' => 'Thuốc trong ngăn sắp hết hạn.',
        _ => code.replaceAll('_', ' '),
      };
}

class _MedicationCard extends StatelessWidget {
  const _MedicationCard({required this.medication});

  final Map<String, dynamic> medication;

  @override
  Widget build(BuildContext context) {
    final details = <String>[
      if (medication['strength'] != null) medication['strength'].toString(),
      if (medication['active_ingredient'] != null)
        medication['active_ingredient'].toString(),
      if (medication['quantity'] != null)
        'Còn ${medication['quantity']} ${medication['unit'] ?? 'đơn vị'}',
      if (medication['expiration_date'] != null)
        'HSD ${medication['expiration_date']}',
    ];
    return _InfoCard(
      icon: Icons.medication_rounded,
      title: medication['name']?.toString() ?? 'Thuốc',
      subtitle:
          details.isEmpty ? 'Chưa có thông tin chi tiết.' : details.join(' · '),
    );
  }
}

class _MemberScheduleCard extends StatelessWidget {
  const _MemberScheduleCard({required this.member});

  final Map<String, dynamic> member;

  @override
  Widget build(BuildContext context) {
    final schedules = _CompartmentSheet._maps(member['schedules']);
    final scheduleText = schedules.expand((schedule) {
      final times = schedule['times'];
      if (times is List && times.isNotEmpty) {
        return [
          '${times.join(', ')} · ${schedule['dose_amount'] ?? ''} ${schedule['dose_unit'] ?? ''}'
              .trim()
        ];
      }
      return <String>[];
    }).join('\n');
    final next = member['next_schedule']?.toString();

    return Card(
      child: ListTile(
        leading: const CircleAvatar(child: Icon(Icons.person_outline)),
        title: Text(
          member['full_name']?.toString() ?? 'Thành viên',
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        subtitle: Text(
          [
            member['relationship_label']?.toString(),
            if (scheduleText.isNotEmpty) scheduleText,
            if (next != null && next.isNotEmpty) 'Liều tiếp theo: $next',
          ].whereType<String>().where((item) => item.isNotEmpty).join('\n'),
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFFEAF4F1),
          borderRadius: BorderRadius.circular(18),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: const Color(0xFF087E79), size: 28),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 4),
                  Text(subtitle,
                      style: const TextStyle(color: Color(0xFF60716D))),
                ],
              ),
            ),
          ],
        ),
      );
}

class _SheetTitle extends StatelessWidget {
  const _SheetTitle({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) => Row(
        children: [
          Icon(icon, size: 20, color: const Color(0xFF087E79)),
          const SizedBox(width: 8),
          Text(label, style: const TextStyle(fontWeight: FontWeight.w800)),
        ],
      );
}

class _WarningTile extends StatelessWidget {
  const _WarningTile({required this.message, this.severe = false});

  final String message;
  final bool severe;

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: severe ? const Color(0xFFFFE9E6) : const Color(0xFFFFF3E3),
          borderRadius: BorderRadius.circular(13),
        ),
        child: Row(
          children: [
            Icon(
              severe ? Icons.dangerous_outlined : Icons.warning_amber_rounded,
              color: severe ? const Color(0xFFB43B32) : const Color(0xFFB76B22),
            ),
            const SizedBox(width: 9),
            Expanded(child: Text(message)),
          ],
        ),
      );
}

class _StateBadge extends StatelessWidget {
  const _StateBadge({required this.isOpen});

  final bool isOpen;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
        decoration: BoxDecoration(
          color: isOpen ? const Color(0xFFFFEAD9) : const Color(0xFFE6F3ED),
          borderRadius: BorderRadius.circular(30),
        ),
        child: Text(
          isOpen ? 'Đang mở' : 'Đang đóng',
          style: TextStyle(
            color: isOpen ? const Color(0xFFA75A24) : const Color(0xFF287451),
            fontWeight: FontWeight.w700,
            fontSize: 12,
          ),
        ),
      );
}

class _Legend extends StatelessWidget {
  const _Legend();

  @override
  Widget build(BuildContext context) => const Wrap(
        spacing: 14,
        runSpacing: 8,
        children: [
          _LegendItem(color: Color(0xFFE7F4EF), label: 'Có thuốc'),
          _LegendItem(color: Color(0xFFFFF0E3), label: 'Đang mở'),
          _LegendItem(color: Color(0xFFF3F6F5), label: 'Trống'),
        ],
      );
}

class _LegendItem extends StatelessWidget {
  const _LegendItem({required this.color, required this.label});

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 13,
            height: 13,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: const Color(0xFFD4DEDA)),
            ),
          ),
          const SizedBox(width: 6),
          Text(label, style: const TextStyle(fontSize: 12)),
        ],
      );
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Card(
        color: const Color(0xFFFFECE9),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              const Icon(Icons.error_outline, color: Color(0xFFB43B32)),
              const SizedBox(width: 10),
              Expanded(child: Text(message)),
              TextButton(
                onPressed: onRetry,
                child: const Text('Thử lại'),
              ),
            ],
          ),
        ),
      );
}
