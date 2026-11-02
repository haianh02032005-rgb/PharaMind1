import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const _refreshKey = 'pharmamind_refresh_token';

class ApiClient {
  ApiClient._() {
    dio = Dio(BaseOptions(
      baseUrl: const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://10.0.2.2:8000',
      ),
      connectTimeout: const Duration(seconds: 12),
      receiveTimeout: const Duration(seconds: 20),
      headers: {'Accept': 'application/json'},
    ));
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = accessToken;
        if (token != null) options.headers['Authorization'] = 'Bearer $token';
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode != 401 ||
            error.requestOptions.extra['retried'] == true ||
            error.requestOptions.path.endsWith('/auth/refresh') ||
            error.requestOptions.path.endsWith('/auth/login')) {
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

  Future<void> restoreSession() async {
    final refreshToken = await _storage.read(key: _refreshKey);
    if (refreshToken == null) return;
    accessToken = await refresh();
  }

  Future<void> login(String email, String password) async {
    final response = await dio.post('/auth/login', data: {
      'email': email.trim(),
      'password': password,
    });
    await _saveTokens(response.data as Map<String, dynamic>);
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
    if (refreshToken == null) return null;
    try {
      final response = await dio.post('/auth/refresh', data: {
        'refresh_token': refreshToken,
      });
      final data = response.data as Map<String, dynamic>;
      accessToken = data['access_token'] as String?;
      return accessToken;
    } on DioException {
      await logout();
      return null;
    }
  }

  Future<void> _saveTokens(Map<String, dynamic> data) async {
    accessToken = data['access_token'] as String?;
    final refreshToken = data['refresh_token'] as String?;
    if (refreshToken != null) {
      await _storage.write(key: _refreshKey, value: refreshToken);
    }
  }

  Future<void> logout() async {
    accessToken = null;
    await _storage.delete(key: _refreshKey);
  }

  String messageFor(Object error) {
    if (error is DioException) {
      if (error.response?.statusCode == 401) return 'Email hoặc mật khẩu chưa đúng.';
      if (error.response == null) return 'Không kết nối được máy chủ. Hãy kiểm tra mạng và địa chỉ API.';
      final detail = error.response?.data;
      if (detail is Map && detail['detail'] is String) return detail['detail'] as String;
      return 'Máy chủ chưa thể xử lý yêu cầu (${error.response?.statusCode ?? 'lỗi'}).';
    }
    return 'Đã xảy ra lỗi. Vui lòng thử lại.';
  }
}
