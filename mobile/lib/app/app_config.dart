class AppConfig {
  AppConfig._();

  static const environment = String.fromEnvironment(
    'APP_ENV',
    defaultValue: 'development',
  );

  static const _configuredApiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const enableRegistration = bool.fromEnvironment(
    'ENABLE_REGISTRATION',
    defaultValue: true,
  );

  static const enableDemoLogin = bool.fromEnvironment(
    'ENABLE_DEMO_LOGIN',
    defaultValue: true,
  );

  static const enableCabinetRealtime = bool.fromEnvironment(
    'ENABLE_CABINET_REALTIME',
    defaultValue: true,
  );

  // These credentials are intentionally public and only belong to the shared
  // trial account. The backend clears that account on every successful login.
  static const demoEmail = 'demo@pharmamind.vn';
  static const demoPassword = 'DemoPass123!';

  static String get apiBaseUrl => validatedApiBaseUrl(
        _configuredApiBaseUrl,
        environment: environment,
      ).toString();

  static bool get isProduction =>
      environment.trim().toLowerCase() == 'production';

  static Uri validatedApiBaseUrl(
    String value, {
    required String environment,
  }) {
    final normalized = value.trim().replaceAll(RegExp(r'/+$'), '');
    final uri = Uri.tryParse(normalized);
    if (uri == null ||
        !uri.hasScheme ||
        uri.host.isEmpty ||
        (uri.scheme != 'http' && uri.scheme != 'https')) {
      throw StateError('API_BASE_URL phải là một địa chỉ HTTP(S) hợp lệ.');
    }
    if (environment.trim().toLowerCase() == 'production' &&
        uri.scheme != 'https') {
      throw StateError(
          'Bản production bắt buộc sử dụng API_BASE_URL qua HTTPS.');
    }
    return uri;
  }
}
