import 'package:flutter_test/flutter_test.dart';
import 'package:pharmamind/app/app_config.dart';

void main() {
  test('normalizes trailing slashes in API base URL', () {
    final uri = AppConfig.validatedApiBaseUrl(
      'https://example.com///',
      environment: 'production',
    );
    expect(uri.toString(), 'https://example.com');
  });

  test('production rejects an insecure API URL', () {
    expect(
      () => AppConfig.validatedApiBaseUrl(
        'http://example.com',
        environment: 'production',
      ),
      throwsStateError,
    );
  });

  test('development allows the Android emulator HTTP address', () {
    final uri = AppConfig.validatedApiBaseUrl(
      'http://10.0.2.2:8000',
      environment: 'development',
    );
    expect(uri.host, '10.0.2.2');
  });
}
