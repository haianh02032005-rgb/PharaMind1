import 'package:flutter_test/flutter_test.dart';
import 'package:pharmamind/core/network/api_client.dart';

void main() {
  test('reads a string FastAPI error detail', () {
    expect(
      fastApiDetailMessage({'detail': 'Không tìm thấy dữ liệu'}),
      'Không tìm thấy dữ liệu',
    );
  });

  test('combines FastAPI validation errors with field paths', () {
    final message = fastApiDetailMessage({
      'detail': [
        {
          'loc': ['body', 'email'],
          'msg': 'Invalid email address',
        },
        {
          'loc': ['body', 'password'],
          'msg': 'Field required',
        },
      ],
    });

    expect(message, 'email: Invalid email address; password: Field required');
  });

  test('returns null for an unsupported error body', () {
    expect(fastApiDetailMessage({'message': 'unknown'}), isNull);
  });
}
