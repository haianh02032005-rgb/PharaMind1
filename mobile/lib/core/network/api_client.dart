import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../app/app_config.dart';

const _refreshKey = 'pharmamind_refresh_token';
const _apiBaseUrlKey = 'pharmamind_api_base_url';

String? fastApiDetailMessage(Object? responseData) {
  if (responseData is! Map) return null;
  final detail = responseData['detail'];
  if (detail is String && detail.trim().isNotEmpty) return detail.trim();
  if (detail is! List) return null;

  final messages = detail
      .map((item) {
        if (item is String) return item.trim();
        if (item is Map) {
          final message = item['msg'];
          if (message is! String || message.trim().isEmpty) return '';
          final location = item['loc'];
          if (location is List && location.isNotEmpty) {
            final field = location
                .where((part) => part != 'body')
                .map((part) => part.toString())
                .join('.');
            return field.isEmpty ? message.trim() : '$field: ${message.trim()}';
          }
          return message.trim();
        }
        return '';
      })
      .where((message) => message.isNotEmpty)
      .toList();

  return messages.isEmpty ? null : messages.join('; ');
}

class ApiClient {
  ApiClient._() {
    dio = Dio(BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 12),
      receiveTimeout: const Duration(seconds: 30),
      headers: const {'Accept': 'application/json'},
    ));
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = accessToken;
        if (token != null) options.headers['Authorization'] = 'Bearer $token';
        handler.next(options);
      },
      onError: (error, handler) async {
        final path = error.requestOptions.path;
        final isAuthEndpoint = path.endsWith('/auth/refresh') ||
            path.endsWith('/auth/login') ||
            path.endsWith('/auth/register');
        if (error.response?.statusCode != 401 ||
            error.requestOptions.extra['retried'] == true ||
            isAuthEndpoint) {
          handler.next(error);
          return;
        }
        try {
          final token = await refresh();
          if (token == null) {
            handler.next(error);
            return;
          }
          final options = error.requestOptions;
          options.extra['retried'] = true;
          options.headers['Authorization'] = 'Bearer $token';
          handler.resolve(await dio.fetch(options));
        } catch (_) {
          handler.next(error);
        }
      },
    ));
  }

  static final ApiClient instance = ApiClient._();
  static const FlutterSecureStorage _storage = FlutterSecureStorage();
  late final Dio dio;
  String? accessToken;
  Future<String?>? _refreshing;

  String get apiBaseUrl => dio.options.baseUrl;

  Future<void> initialize() async {
    final savedBaseUrl = await _storage.read(key: _apiBaseUrlKey);
    if (savedBaseUrl == null || savedBaseUrl.trim().isEmpty) return;
    try {
      dio.options.baseUrl = AppConfig.validatedApiBaseUrl(
        savedBaseUrl,
        environment: AppConfig.environment,
      ).toString();
    } on StateError {
      await _storage.delete(key: _apiBaseUrlKey);
    }
  }

  Future<void> updateApiBaseUrl(String value) async {
    final normalized = AppConfig.validatedApiBaseUrl(
      value,
      environment: AppConfig.environment,
    ).toString();
    if (normalized == dio.options.baseUrl) return;

    // Authentication tokens are scoped to the server that issued them.
    await logout();
    dio.options.baseUrl = normalized;
    await _storage.write(key: _apiBaseUrlKey, value: normalized);
  }

  Future<void> resetApiBaseUrl() async {
    await logout();
    dio.options.baseUrl = AppConfig.apiBaseUrl;
    await _storage.delete(key: _apiBaseUrlKey);
  }

  Future<void> restoreSession() async {
    final refreshToken = await _storage.read(key: _refreshKey);
    if (refreshToken == null || refreshToken.isEmpty) {
      await logout();
      return;
    }
    accessToken = await refresh();
  }

  Future<void> login(String email, String password) async {
    // Never let a newly authenticated account inherit another account's token.
    await logout();
    final response = await dio.post('/auth/login', data: {
      'email': email.trim(),
      'password': password,
    });
    await _saveTokens(Map<String, dynamic>.from(response.data as Map));
  }

  Future<void> register({
    required String name,
    required String email,
    required String password,
  }) async {
    await dio.post('/auth/register', data: {
      'full_name': name.trim(),
      'email': email.trim(),
      'password': password,
    });
    await login(email, password);
  }

  Future<String?> refresh() {
    return _refreshing ??= _doRefresh().whenComplete(() => _refreshing = null);
  }

  Future<String?> _doRefresh() async {
    final refreshToken = await _storage.read(key: _refreshKey);
    if (refreshToken == null || refreshToken.isEmpty) return null;
    try {
      final response = await dio.post('/auth/refresh', data: {
        'refresh_token': refreshToken,
      });
      final data = Map<String, dynamic>.from(response.data as Map);
      final newAccessToken = data['access_token'];
      if (newAccessToken is! String || newAccessToken.isEmpty) {
        await logout();
        return null;
      }
      accessToken = newAccessToken;
      return accessToken;
    } on DioException {
      await logout();
      return null;
    }
  }

  Future<void> _saveTokens(Map<String, dynamic> data) async {
    final newAccessToken = data['access_token'];
    final refreshToken = data['refresh_token'];
    if (newAccessToken is! String ||
        newAccessToken.isEmpty ||
        refreshToken is! String ||
        refreshToken.isEmpty) {
      await logout();
      throw StateError('Máy chủ không trả về phiên đăng nhập hợp lệ.');
    }
    await _storage.write(key: _refreshKey, value: refreshToken);
    accessToken = newAccessToken;
  }

  Future<void> logout() async {
    accessToken = null;
    await _storage.delete(key: _refreshKey);
  }

  String messageFor(Object error) {
    if (error is DioException) {
      if (error.response?.statusCode == 401) {
        return 'Email hoặc mật khẩu chưa đúng.';
      }
      if (error.response == null) {
        return 'Không kết nối được máy chủ. Hãy kiểm tra mạng và địa chỉ API.';
      }
      final detail = fastApiDetailMessage(error.response?.data);
      if (detail != null) return detail;
      return 'Máy chủ chưa thể xử lý yêu cầu '
          '(${error.response?.statusCode ?? 'lỗi'}).';
    }
    if (error is StateError) return error.message;
    return 'Đã xảy ra lỗi. Vui lòng thử lại.';
  }
}
