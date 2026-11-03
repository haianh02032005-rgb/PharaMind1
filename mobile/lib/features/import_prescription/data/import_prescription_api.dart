import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import '../domain/import_session.dart';

class ImportPrescriptionApi {
  const ImportPrescriptionApi(this.api);

  final ApiClient api;

  String _base(int familyId, int memberId) =>
      '/families/$familyId/members/$memberId/imports';

  Future<ImportSessionData> upload({
    required int familyId,
    required int memberId,
    required String filename,
    required Uint8List bytes,
    required String sourceType,
    String importMode = 'CREATE_NEW_PRESCRIPTION',
  }) async {
    final form = FormData.fromMap(<String, dynamic>{
      'file': MultipartFile.fromBytes(bytes, filename: filename),
      'source_type': sourceType,
      'import_mode': importMode,
    });
    final response = await api.dio.post(
      _base(familyId, memberId),
      data: form,
      options: Options(contentType: 'multipart/form-data'),
    );
    return ImportSessionData.fromJson(response.data);
  }

  Future<ImportSessionData> updateDraft({
    required ImportSessionData session,
    required Map<String, dynamic> payload,
  }) async {
    final response = await api.dio.patch(
      '${_base(session.familyId, session.memberId)}/${session.id}/draft',
      data: payload,
    );
    return ImportSessionData.fromJson(response.data);
  }

  Future<ImportSessionData> validate(ImportSessionData session) async {
    final response = await api.dio.post(
      '${_base(session.familyId, session.memberId)}/${session.id}/validate',
    );
    return ImportSessionData.fromJson(response.data);
  }

  Future<ImportSessionData> commit({
    required ImportSessionData session,
    required bool confirmScheduleCreation,
    required bool confirmHealthUpdates,
    required bool confirmOcrReview,
  }) async {
    final response = await api.dio.post(
      '${_base(session.familyId, session.memberId)}/${session.id}/commit',
      data: <String, dynamic>{
        'confirm_member_id': session.memberId,
        'confirm_import_mode': session.importMode,
        'confirm_schedule_creation': confirmScheduleCreation,
        'confirm_health_updates': confirmHealthUpdates,
        'confirm_ocr_review': confirmOcrReview,
      },
    );
    return ImportSessionData.fromJson(response.data);
  }

  Future<ImportSessionData> reject(ImportSessionData session) async {
    final response = await api.dio.post(
      '${_base(session.familyId, session.memberId)}/${session.id}/reject',
      data: const <String, dynamic>{
        'reason': 'Người dùng hủy trên ứng dụng mobile'
      },
    );
    return ImportSessionData.fromJson(response.data);
  }
}
