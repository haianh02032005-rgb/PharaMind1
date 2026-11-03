Map<String, dynamic> _mapOf(dynamic value) {
  if (value is! Map) return <String, dynamic>{};
  return value.map((key, item) => MapEntry(key.toString(), item));
}

List<Map<String, dynamic>> _mapsOf(dynamic value) {
  if (value is! List) return <Map<String, dynamic>>[];
  return value.whereType<Map>().map(_mapOf).toList(growable: false);
}

class ImportValidationIssue {
  const ImportValidationIssue({
    required this.id,
    required this.severity,
    required this.code,
    required this.fieldPath,
    required this.message,
    required this.isResolved,
    this.suggestedFix,
  });

  factory ImportValidationIssue.fromJson(dynamic value) {
    final json = _mapOf(value);
    return ImportValidationIssue(
      id: (json['id'] as num?)?.toInt() ?? 0,
      severity: json['severity']?.toString() ?? 'INFO',
      code: json['code']?.toString() ?? 'UNKNOWN',
      fieldPath: json['field_path']?.toString() ?? '',
      message: json['message']?.toString() ?? 'Cần kiểm tra lại dữ liệu.',
      suggestedFix: json['suggested_fix']?.toString(),
      isResolved: json['is_resolved'] == true,
    );
  }

  final int id;
  final String severity;
  final String code;
  final String fieldPath;
  final String message;
  final String? suggestedFix;
  final bool isResolved;

  bool get isBlocking =>
      !isResolved && (severity == 'BLOCKING' || severity == 'ERROR');
}

class ImportSessionData {
  const ImportSessionData({required this.json});

  factory ImportSessionData.fromJson(dynamic value) =>
      ImportSessionData(json: _mapOf(value));

  final Map<String, dynamic> json;

  int get id => (json['id'] as num?)?.toInt() ?? 0;
  int get familyId => (json['family_id'] as num?)?.toInt() ?? 0;
  int get memberId => (json['member_id'] as num?)?.toInt() ?? 0;
  String get sourceType => json['source_type']?.toString() ?? '';
  String get sourceFilename => json['source_filename']?.toString() ?? '';
  String get status => json['status']?.toString() ?? 'UPLOADED';
  String get importMode =>
      json['import_mode']?.toString() ?? 'CREATE_NEW_PRESCRIPTION';
  double? get overallConfidence =>
      (json['overall_confidence'] as num?)?.toDouble();
  bool get isDuplicate => json['is_duplicate'] == true;
  bool get isOcr => sourceType == 'OCR_IMAGE' || sourceType == 'OCR_PDF';
  bool get isCommitted => status == 'COMMITTED';
  bool get isTerminal => status == 'COMMITTED' || status == 'REJECTED';

  Map<String, dynamic> get reviewPayload => _mapOf(json['review_payload']);
  Map<String, dynamic> get prescription =>
      _mapOf(reviewPayload['prescription']);
  Map<String, dynamic> get healthUpdates =>
      _mapOf(reviewPayload['health_updates']);
  List<Map<String, dynamic>> get medicationItems =>
      _mapsOf(reviewPayload['items']);
  Map<String, dynamic> get memberResolution =>
      _mapOf(reviewPayload['member_resolution']);
  Map<String, dynamic> get commitSummary => _mapOf(json['commit_summary']);

  List<ImportValidationIssue> get issues {
    final raw = json['validation_issues'];
    if (raw is! List) return const <ImportValidationIssue>[];
    return raw.map(ImportValidationIssue.fromJson).toList(growable: false);
  }

  List<ImportValidationIssue> get unresolvedIssues =>
      issues.where((issue) => !issue.isResolved).toList(growable: false);
  List<ImportValidationIssue> get blockingIssues =>
      issues.where((issue) => issue.isBlocking).toList(growable: false);

  bool hasIssue(String code) =>
      unresolvedIssues.any((issue) => issue.code == code);
}

String? inferImportSourceType(String filename) {
  final dot = filename.lastIndexOf('.');
  final extension = dot < 0 ? '' : filename.substring(dot + 1).toLowerCase();
  switch (extension) {
    case 'jpg':
    case 'jpeg':
    case 'png':
      return 'OCR_IMAGE';
    case 'pdf':
      return 'OCR_PDF';
    case 'xlsx':
      return 'EXCEL_XLSX';
    case 'csv':
      return 'CSV';
    default:
      return null;
  }
}

int importFileLimitBytes(String filename) =>
    filename.toLowerCase().endsWith('.pdf')
        ? 20 * 1024 * 1024
        : 10 * 1024 * 1024;
