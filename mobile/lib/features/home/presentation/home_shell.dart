import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({required this.api, required this.onLogout, super.key});
  final ApiClient api;
  final VoidCallback onLogout;

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _tab = 0;
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _families = [];
  List<Map<String, dynamic>> _members = [];
  List<Map<String, dynamic>> _schedule = [];
  List<Map<String, dynamic>> _medications = [];
  List<Map<String, dynamic>> _cabinets = [];
  int? _familyId;
  int? _memberId;
  String _familyName = '';
  String _memberName = '';

  static List<Map<String, dynamic>> _items(dynamic response) {
    final body = response is Map ? response['items'] : null;
    if (body is! List) return [];
    return body.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
  }

  @override
  void initState() {
    super.initState();
    _loadFamilies();
  }

  Future<void> _loadFamilies() async {
    setState(() { _loading = true; _error = null; });
    try {
      final response = await widget.api.dio.get('/families');
      _families = _items(response.data);
      if (_families.isNotEmpty) {
        final family = _families.firstWhere(
          (f) => f['id'] == _familyId,
          orElse: () => _families.first,
        );
        await _selectFamily(family, showLoading: false);
      } else {
        _familyId = null;
      }
    } catch (error) {
      _error = widget.api.messageFor(error);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _selectFamily(Map<String, dynamic> family, {bool showLoading = true}) async {
    _familyId = family['id'] as int?;
    _familyName = family['name'] as String? ?? 'Gia đình';
    _memberId = null;
    _memberName = '';
    _members = [];
    _schedule = [];
    _medications = [];
    _cabinets = [];
    if (showLoading) setState(() { _loading = true; _error = null; });
    try {
      final id = _familyId;
      if (id == null) return;
      final results = await Future.wait([
        widget.api.dio.get('/families/$id/members'),
        widget.api.dio.get('/families/$id/medications'),
        widget.api.dio.get('/families/$id/cabinets'),
      ]);
      _members = _items(results[0].data);
      _medications = _items(results[1].data);
      _cabinets = _items(results[2].data);
      if (_members.isNotEmpty) {
        await _selectMember(_members.first, showLoading: false);
      } else {
        _schedule = [];
      }
    } catch (error) {
      _error = widget.api.messageFor(error);
    } finally {
      if (mounted && showLoading) setState(() => _loading = false);
    }
    if (mounted && !showLoading) setState(() {});
  }

  Future<void> _selectMember(Map<String, dynamic> member, {bool showLoading = true}) async {
    _memberId = member['id'] as int?;
    _memberName = member['full_name'] as String? ?? 'Thành viên';
    final familyId = _familyId;
    final memberId = _memberId;
    if (familyId == null || memberId == null) return;
    if (showLoading) setState(() { _loading = true; _error = null; });
    try {
      final now = DateTime.now();
      final date = '${now.year.toString().padLeft(4, '0')}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
      final response = await widget.api.dio.get('/families/$familyId/members/$memberId/schedule-day', queryParameters: {'date': date});
      _schedule = _items(response.data);
    } on DioException catch (error) {
      _schedule = [];
      _error = widget.api.messageFor(error);
    } finally {
      if (mounted && showLoading) setState(() => _loading = false);
    }
    if (mounted && !showLoading) setState(() {});
  }

  Future<void> _logout() async {
    await widget.api.logout();
    if (mounted) widget.onLogout();
  }

  Future<void> _createFamily() async {
    final nameController = TextEditingController();
    final descriptionController = TextEditingController();
    final formKey = GlobalKey<FormState>();
    final created = await showDialog<bool>(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('Tạo gia đình'),
      content: Form(key: formKey, child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextFormField(controller: nameController, autofocus: true, decoration: const InputDecoration(labelText: 'Tên gia đình'),
          validator: (value) => (value == null || value.trim().isEmpty) ? 'Nhập tên gia đình' : null),
        const SizedBox(height: 12),
        TextField(controller: descriptionController, decoration: const InputDecoration(labelText: 'Mô tả (không bắt buộc)')),
      ])),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Để sau')),
        FilledButton(onPressed: () { if (formKey.currentState!.validate()) Navigator.pop(dialogContext, true); }, child: const Text('Tạo'))],
    ));
    if (created == true) {
      try {
        await widget.api.dio.post('/families', data: {
          'name': nameController.text.trim(),
          'description': descriptionController.text.trim().isEmpty ? null : descriptionController.text.trim(),
        });
        if (mounted) {
          await _loadFamilies();
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Đã tạo gia đình.')));
        }
      } catch (error) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(widget.api.messageFor(error))));
      }
    }
    nameController.dispose();
    descriptionController.dispose();
  }

  Future<void> _createMember() async {
    final name = TextEditingController();
    final relationship = TextEditingController();
    final formKey = GlobalKey<FormState>();
    final result = await showDialog<bool>(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('Thêm thành viên'),
      content: Form(key: formKey, child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextFormField(controller: name, autofocus: true, decoration: const InputDecoration(labelText: 'Họ và tên'),
          validator: (value) => (value == null || value.trim().isEmpty) ? 'Nhập họ tên thành viên' : null),
        const SizedBox(height: 12),
        TextField(controller: relationship, decoration: const InputDecoration(labelText: 'Quan hệ (không bắt buộc)')),
      ])),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Hủy')),
        FilledButton(onPressed: () { if (formKey.currentState!.validate()) Navigator.pop(dialogContext, true); }, child: const Text('Thêm'))],
    ));
    if (result == true && _familyId != null) {
      try {
        await widget.api.dio.post('/families/$_familyId/members', data: {
          'full_name': name.text.trim(),
          'relationship_label': relationship.text.trim().isEmpty ? null : relationship.text.trim(),
        });
        if (mounted) await _selectFamily({'id': _familyId, 'name': _familyName});
      } catch (error) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(widget.api.messageFor(error))));
      }
    }
    name.dispose();
    relationship.dispose();
  }

  Future<void> _chooseFamily() async {
    if (_families.isEmpty) return;
    final selected = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(child: Column(mainAxisSize: MainAxisSize.min, children: [
        const ListTile(title: Text('Chọn gia đình', style: TextStyle(fontWeight: FontWeight.bold))),
        ..._families.map((f) => ListTile(
          leading: const CircleAvatar(child: Icon(Icons.home_rounded)),
          title: Text(f['name']?.toString() ?? 'Gia đình'),
          subtitle: Text(f['my_role']?.toString() ?? ''),
          trailing: f['id'] == _familyId ? const Icon(Icons.check_circle, color: Color(0xFF087E79)) : null,
          onTap: () => Navigator.pop(context, f),
        )),
        const SizedBox(height: 12),
      ])),
    );
    if (selected != null) await _selectFamily(selected);
  }

  Future<void> _chooseMember() async {
    if (_members.isEmpty) return;
    final selected = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(child: Column(mainAxisSize: MainAxisSize.min, children: [
        const ListTile(title: Text('Chọn thành viên', style: TextStyle(fontWeight: FontWeight.bold))),
        ..._members.map((m) => ListTile(
          leading: CircleAvatar(child: Text(_initial(m['full_name']))),
          title: Text(m['full_name']?.toString() ?? 'Thành viên'),
          subtitle: Text(m['relationship_label']?.toString() ?? ''),
          trailing: m['id'] == _memberId ? const Icon(Icons.check_circle, color: Color(0xFF087E79)) : null,
          onTap: () => Navigator.pop(context, m),
        )),
        const SizedBox(height: 12),
      ])),
    );
    if (selected != null) await _selectMember(selected);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          Container(width: 34, height: 34, decoration: BoxDecoration(color: Theme.of(context).colorScheme.primary, borderRadius: BorderRadius.circular(11)),
            child: const Icon(Icons.health_and_safety_rounded, color: Colors.white, size: 21)),
          const SizedBox(width: 10),
          Text('PharmaMind', style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800, letterSpacing: -.4)),
        ]),
        actions: [
          IconButton(tooltip: 'Tải lại', onPressed: _loadFamilies, icon: const Icon(Icons.refresh_rounded)),
          PopupMenuButton<String>(onSelected: (v) { if (v == 'logout') _logout(); }, itemBuilder: (_) => const [PopupMenuItem(value: 'logout', child: Text('Đăng xuất'))]),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(onRefresh: _loadFamilies, child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
              children: [
                if (_error != null) _ErrorBanner(message: _error!, onRetry: _loadFamilies),
                if (_families.isEmpty) _EmptyFamilies(onRetry: _loadFamilies, onCreate: _createFamily),
                if (_families.isNotEmpty) ...[
                  Row(children: [
                    Expanded(child: _PickerChip(icon: Icons.home_outlined, label: _familyName, onTap: _chooseFamily)),
                    if (_members.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      Expanded(child: _PickerChip(icon: Icons.person_outline, label: _memberName, onTap: _chooseMember)),
                    ],
                  ]),
                  const SizedBox(height: 20),
                  if (_tab == 0) _Dashboard(familyName: _familyName, memberName: _memberName, members: _members,
                    schedule: _schedule, medications: _medications, cabinets: _cabinets,
                    onMembers: () => setState(() => _tab = 1), onMedications: () => setState(() => _tab = 2), onSchedule: () => setState(() => _tab = 3), onCabinet: () => setState(() => _tab = 4)),
                  if (_tab == 1) _FamilyPage(members: _members, onSelect: _selectMember, onAdd: _createMember, selectedId: _memberId),
                  if (_tab == 2) _MedicationPage(medications: _medications),
                  if (_tab == 3) _SchedulePage(memberName: _memberName, schedule: _schedule),
                  if (_tab == 4) _CabinetPage(cabinets: _cabinets),
                ],
              ],
            )),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (index) => setState(() => _tab = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.grid_view_rounded), label: 'Tổng quan'),
          NavigationDestination(icon: Icon(Icons.people_alt_outlined), label: 'Gia đình'),
          NavigationDestination(icon: Icon(Icons.medication_outlined), label: 'Thuốc'),
          NavigationDestination(icon: Icon(Icons.calendar_month_outlined), label: 'Lịch thuốc'),
          NavigationDestination(icon: Icon(Icons.medication_outlined), label: 'Tủ thuốc'),
        ],
      ),
    );
  }
}

class _Dashboard extends StatelessWidget {
  const _Dashboard({required this.familyName, required this.memberName, required this.members, required this.schedule,
    required this.medications, required this.cabinets, required this.onMembers, required this.onMedications, required this.onSchedule, required this.onCabinet});
  final String familyName, memberName;
  final List<Map<String, dynamic>> members, schedule, medications, cabinets;
  final VoidCallback onMembers, onMedications, onSchedule, onCabinet;

  @override
  Widget build(BuildContext context) {
    final next = schedule.where((e) => e['status'] == 'SCHEDULED').toList()
      ..sort((a, b) => (a['time']?.toString() ?? '').compareTo(b['time']?.toString() ?? ''));
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Xin chào 👋', style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: const Color(0xFF687875))),
      const SizedBox(height: 4),
      Text(familyName, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
      const SizedBox(height: 18),
      Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF087E79), Color(0xFF075C62)], begin: Alignment.topLeft, end: Alignment.bottomRight), borderRadius: BorderRadius.circular(24)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [const Icon(Icons.wb_sunny_outlined, color: Colors.white70, size: 18), const SizedBox(width: 7),
            Text('LỊCH UỐNG HÔM NAY', style: TextStyle(color: Colors.white.withValues(alpha: .78), fontWeight: FontWeight.w700, letterSpacing: .8, fontSize: 11))]),
          const SizedBox(height: 14),
          Text('${schedule.length}', style: const TextStyle(color: Colors.white, fontSize: 38, height: 1, fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          Text('liều thuốc${schedule.length == 1 ? '' : ''} · $memberName', style: const TextStyle(color: Colors.white, fontSize: 15)),
          const SizedBox(height: 18),
          Container(height: 1, color: Colors.white.withValues(alpha: .22)),
          const SizedBox(height: 14),
          Row(children: [const Icon(Icons.schedule_rounded, color: Colors.white, size: 18), const SizedBox(width: 7),
            Expanded(child: Text(next.isEmpty ? 'Chưa có lịch uống trong hôm nay' : 'Liều tiếp theo lúc ${next.first['time'] ?? '--:--'}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600))),
            Icon(Icons.arrow_forward_rounded, color: Colors.white.withValues(alpha: .85), size: 18)]),
        ]),
      ),
      const SizedBox(height: 18),
      Row(children: [
        Expanded(child: _StatCard(icon: Icons.people_alt_outlined, value: '${members.length}', label: 'Thành viên', tint: const Color(0xFFE8F4F1), onTap: onMembers)),
        const SizedBox(width: 10),
        Expanded(child: _StatCard(icon: Icons.medication_outlined, value: '${medications.length}', label: 'Thuốc đang có', tint: const Color(0xFFFFF2E3), onTap: onMedications)),
      ]),
      const SizedBox(height: 24),
      _SectionHeader(title: 'Liều uống hôm nay', action: 'Xem lịch', onTap: onSchedule),
      const SizedBox(height: 10),
      if (schedule.isEmpty) const _EmptyCard(icon: Icons.event_available_outlined, text: 'Chưa có lịch uống thuốc hôm nay.'),
      ...schedule.take(5).map((dose) => _DoseTile(dose: dose)),
      const SizedBox(height: 20),
      _SectionHeader(title: 'Tủ thuốc thông minh', action: 'Mở tủ', onTap: onCabinet),
      const SizedBox(height: 10),
      if (cabinets.isEmpty) const _EmptyCard(icon: Icons.inventory_2_outlined, text: 'Gia đình chưa kết nối tủ thuốc.'),
      ...cabinets.take(2).map((cabinet) => _CabinetTile(cabinet: cabinet)),
      const SizedBox(height: 16),
      const Text('Thông tin được đồng bộ trực tiếp từ hệ thống PharmaMind.', style: TextStyle(color: Color(0xFF71807D), fontSize: 12)),
    ]);
  }
}

class _FamilyPage extends StatelessWidget {
  const _FamilyPage({required this.members, required this.onSelect, required this.onAdd, required this.selectedId});
  final List<Map<String, dynamic>> members;
  final Future<void> Function(Map<String, dynamic>) onSelect;
  final VoidCallback onAdd;
  final int? selectedId;

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Row(children: [Expanded(child: Text('Thành viên gia đình', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800))), IconButton.filledTonal(tooltip: 'Thêm thành viên', onPressed: onAdd, icon: const Icon(Icons.person_add_alt_1))]),
    const SizedBox(height: 8), const Text('Chọn một thành viên để xem lịch uống thuốc của họ.'),
    const SizedBox(height: 16),
    if (members.isEmpty) const _EmptyCard(icon: Icons.person_add_alt_1, text: 'Gia đình chưa có thành viên.'),
    ...members.map((member) => Card(child: ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: CircleAvatar(radius: 24, backgroundColor: const Color(0xFFE7F3F0), child: Text(_initial(member['full_name']), style: const TextStyle(color: Color(0xFF087E79), fontWeight: FontWeight.bold))),
      title: Text(member['full_name']?.toString() ?? 'Thành viên', style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Text(member['relationship_label']?.toString() ?? 'Thành viên gia đình'),
      trailing: member['id'] == selectedId ? const Icon(Icons.check_circle, color: Color(0xFF087E79)) : const Icon(Icons.chevron_right),
      onTap: () => onSelect(member),
    ))),
  ]);
}

String _initial(dynamic value) {
  final name = value?.toString().trim() ?? '';
  return name.isEmpty ? 'T' : String.fromCharCode(name.runes.first).toUpperCase();
}

class _SchedulePage extends StatelessWidget {
  const _SchedulePage({required this.memberName, required this.schedule});
  final String memberName;
  final List<Map<String, dynamic>> schedule;

  @override
  Widget build(BuildContext context) {
    final doses = [...schedule]..sort((a, b) => (a['time']?.toString() ?? '').compareTo(b['time']?.toString() ?? ''));
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Lịch thuốc hôm nay', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
      const SizedBox(height: 4), Text(memberName), const SizedBox(height: 18),
      if (doses.isEmpty) const _EmptyCard(icon: Icons.event_busy_outlined, text: 'Chưa có lịch uống thuốc cho hôm nay.'),
      ...doses.map((dose) => _DoseTile(dose: dose, large: true)),
      const SizedBox(height: 8),
      const Text('Lịch hiển thị theo dữ liệu hiện có trên máy chủ.', style: TextStyle(color: Color(0xFF71807D), fontSize: 12)),
    ]);
  }
}

class _MedicationPage extends StatelessWidget {
  const _MedicationPage({required this.medications});
  final List<Map<String, dynamic>> medications;

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text('Thuốc của gia đình', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
    const SizedBox(height: 6), const Text('Danh sách thuốc được lưu trên hệ thống.'),
    const SizedBox(height: 16),
    if (medications.isEmpty) const _EmptyCard(icon: Icons.medication_outlined, text: 'Chưa có thuốc nào trong danh sách gia đình.'),
    ...medications.map((medication) {
      final quantity = medication['quantity'];
      final unit = medication['unit']?.toString() ?? 'đơn vị';
      final status = medication['status']?.toString() ?? 'ACTIVE';
      final catalog = medication['catalog'] as Map?;
      return Card(child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
        leading: Container(width: 46, height: 46, decoration: BoxDecoration(color: const Color(0xFFFFF3E2), borderRadius: BorderRadius.circular(14)), child: const Icon(Icons.medication_outlined, color: Color(0xFFB66A19))),
        title: Text(catalog?['name']?.toString() ?? 'Thuốc', style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text([catalog?['strength'], if (quantity != null) 'Còn $quantity $unit', medication['expiration_date'] == null ? null : 'HSD ${medication['expiration_date']}'].whereType<Object>().map((e) => e.toString()).where((e) => e.isNotEmpty).join(' · ')),
        trailing: Text(status == 'ACTIVE' ? 'Đang dùng' : status, style: const TextStyle(fontSize: 11, color: Color(0xFF687875))),
      ));
    }),
  ]);
}

class _CabinetPage extends StatelessWidget {
  const _CabinetPage({required this.cabinets});
  final List<Map<String, dynamic>> cabinets;

  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text('Tủ thuốc', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800)),
    const SizedBox(height: 6), const Text('Trạng thái tủ và sơ đồ 9 ngăn.'),
    const SizedBox(height: 16),
    if (cabinets.isEmpty) const _EmptyCard(icon: Icons.inventory_2_outlined, text: 'Chưa có tủ thuốc được kết nối với gia đình.'),
    ...cabinets.map((cabinet) => _CabinetTile(cabinet: cabinet, expanded: true)),
  ]);
}

class _CabinetTile extends StatelessWidget {
  const _CabinetTile({required this.cabinet, this.expanded = false});
  final Map<String, dynamic> cabinet;
  final bool expanded;

  @override
  Widget build(BuildContext context) {
    final compartments = (cabinet['compartments'] as List?)?.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList() ?? [];
    final online = cabinet['status']?.toString().toUpperCase() == 'ONLINE';
    return Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Container(width: 46, height: 46, decoration: BoxDecoration(color: const Color(0xFFEAF3F1), borderRadius: BorderRadius.circular(14)), child: const Icon(Icons.inventory_2_outlined, color: Color(0xFF087E79))),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(cabinet['name']?.toString() ?? 'Tủ thuốc', style: const TextStyle(fontWeight: FontWeight.w700)), Text(cabinet['device_code']?.toString() ?? 'Thiết bị', style: const TextStyle(color: Color(0xFF73817E), fontSize: 12))])),
        _StatusPill(label: online ? 'Đang kết nối' : 'Ngoại tuyến', online: online),
      ]),
      if (expanded) ...[
        const SizedBox(height: 16),
        GridView.builder(shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), itemCount: compartments.isEmpty ? 9 : compartments.length,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 3, crossAxisSpacing: 8, mainAxisSpacing: 8, childAspectRatio: 1.35),
          itemBuilder: (context, index) {
            final comp = index < compartments.length ? compartments[index] : <String, dynamic>{'position': index + 1};
            final med = comp['medication'] as Map?;
            final filled = med != null;
            final isOpen = comp['is_open'] == true;
            return Container(padding: const EdgeInsets.all(9), decoration: BoxDecoration(color: filled ? const Color(0xFFE9F4F0) : const Color(0xFFF4F6F5), borderRadius: BorderRadius.circular(13), border: Border.all(color: filled ? const Color(0xFFCDE6DB) : const Color(0xFFE9EEEC))),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
                Text('NGĂN ${(comp['position'] ?? index + 1).toString().padLeft(2, '0')}', style: const TextStyle(fontSize: 9, color: Color(0xFF71807D), fontWeight: FontWeight.w700, letterSpacing: .5)),
                const SizedBox(height: 3),
                Text(med?['name']?.toString() ?? 'Trống', maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 12, fontWeight: filled ? FontWeight.w700 : FontWeight.w500)),
                if (isOpen) const Text('Đang mở', style: TextStyle(fontSize: 9, color: Color(0xFFB45C20))),
              ]));
          }),
      ],
    ])));
  }
}

class _DoseTile extends StatelessWidget {
  const _DoseTile({required this.dose, this.large = false});
  final Map<String, dynamic> dose;
  final bool large;

  @override
  Widget build(BuildContext context) {
    final medication = dose['medication'] as Map?;
    final status = dose['status']?.toString() ?? 'SCHEDULED';
    final color = status == 'TAKEN' ? const Color(0xFF087E79) : status == 'MISSED' ? Colors.red : const Color(0xFFB66A19);
    return Card(child: Padding(padding: EdgeInsets.all(large ? 16 : 12), child: Row(children: [
      Container(width: large ? 55 : 47, height: large ? 55 : 47, decoration: BoxDecoration(color: const Color(0xFFFFF3E2), borderRadius: BorderRadius.circular(15)), child: const Icon(Icons.medication_outlined, color: Color(0xFFB66A19))),
      const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(medication?['name']?.toString() ?? 'Thuốc', style: const TextStyle(fontWeight: FontWeight.w700)),
        Text('${dose['dose_amount'] ?? ''} ${dose['dose_unit'] ?? ''}'.trim(), style: const TextStyle(color: Color(0xFF71807D), fontSize: 13)),
      ])),
      Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
        Text(dose['time']?.toString() ?? '--:--', style: TextStyle(fontWeight: FontWeight.w800, fontSize: large ? 17 : 15)),
        Text(_status(status), style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600)),
      ]),
    ])));
  }

  String _status(String value) => switch (value) { 'TAKEN' => 'Đã uống', 'MISSED' => 'Đã bỏ lỡ', _ => 'Theo lịch' };
}

class _PickerChip extends StatelessWidget {
  const _PickerChip({required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Material(color: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: const BorderSide(color: Color(0xFFE7ECEA))), child: InkWell(borderRadius: BorderRadius.circular(14), onTap: onTap, child: Padding(padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 12), child: Row(children: [Icon(icon, size: 18, color: const Color(0xFF087E79)), const SizedBox(width: 8), Expanded(child: Text(label, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13))), const Icon(Icons.expand_more, size: 19)]))));
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.icon, required this.value, required this.label, required this.tint, required this.onTap});
  final IconData icon; final String value, label; final Color tint; final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Card(child: InkWell(borderRadius: BorderRadius.circular(20), onTap: onTap, child: Padding(padding: const EdgeInsets.all(15), child: Row(children: [Container(width: 42, height: 42, decoration: BoxDecoration(color: tint, borderRadius: BorderRadius.circular(13)), child: Icon(icon, color: const Color(0xFF087E79))), const SizedBox(width: 11), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)), Text(label, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 11, color: Color(0xFF71807D)))]))]))));
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.action, required this.onTap});
  final String title, action; final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Row(children: [Expanded(child: Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800))), TextButton(onPressed: onTap, child: Text(action))]);
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.icon, required this.text});
  final IconData icon; final String text;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 20), child: Row(children: [Icon(icon, color: const Color(0xFF71807D)), const SizedBox(width: 12), Expanded(child: Text(text, style: const TextStyle(color: Color(0xFF687875))))])));
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.label, required this.online});
  final String label; final bool online;
  @override
  Widget build(BuildContext context) => Container(padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6), decoration: BoxDecoration(color: online ? const Color(0xFFE7F4ED) : const Color(0xFFFFF1E8), borderRadius: BorderRadius.circular(30)), child: Row(mainAxisSize: MainAxisSize.min, children: [Container(width: 7, height: 7, decoration: BoxDecoration(color: online ? const Color(0xFF319567) : const Color(0xFFCC742D), shape: BoxShape.circle)), const SizedBox(width: 6), Text(label, style: TextStyle(fontSize: 10, color: online ? const Color(0xFF24734F) : const Color(0xFF995A27), fontWeight: FontWeight.w700))]));
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message, required this.onRetry});
  final String message; final VoidCallback onRetry;
  @override
  Widget build(BuildContext context) => Card(color: const Color(0xFFFFEFED), child: Padding(padding: const EdgeInsets.all(13), child: Row(children: [const Icon(Icons.wifi_off_rounded, color: Color(0xFFB34338)), const SizedBox(width: 10), Expanded(child: Text(message, style: const TextStyle(fontSize: 13))), TextButton(onPressed: onRetry, child: const Text('Thử lại'))])));
}

class _EmptyFamilies extends StatelessWidget {
  const _EmptyFamilies({required this.onRetry, required this.onCreate});
  final VoidCallback onRetry, onCreate;
  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(top: 64), child: Column(children: [Container(width: 74, height: 74, decoration: BoxDecoration(color: const Color(0xFFE7F3F0), borderRadius: BorderRadius.circular(24)), child: const Icon(Icons.home_work_outlined, color: Color(0xFF087E79), size: 36)), const SizedBox(height: 18), const Text('Bắt đầu với gia đình', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)), const SizedBox(height: 8), const Text('Tạo Family Workspace để quản lý thành viên và lịch dùng thuốc tại một nơi.', textAlign: TextAlign.center, style: TextStyle(color: Color(0xFF687875))), const SizedBox(height: 18), FilledButton.icon(onPressed: onCreate, icon: const Icon(Icons.add), label: const Text('Tạo gia đình')), TextButton.icon(onPressed: onRetry, icon: const Icon(Icons.refresh), label: const Text('Tải lại'))]));
}
