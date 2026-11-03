import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pharmamind/core/network/api_client.dart';
import 'package:pharmamind/features/auth/presentation/login_page.dart';

void main() {
  testWidgets('login screen exposes normal and demo entry points',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: LoginPage(
          api: ApiClient.instance,
          onAuthenticated: () {},
        ),
      ),
    );

    expect(find.text('Đăng nhập'), findsOneWidget);
    expect(find.text('Dùng thử với tài khoản demo'), findsOneWidget);
    expect(find.byType(TextFormField), findsNWidgets(2));
  });
}
