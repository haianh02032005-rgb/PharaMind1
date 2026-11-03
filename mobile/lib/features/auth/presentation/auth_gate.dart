import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../home/presentation/home_shell.dart';
import 'login_page.dart';

class AuthGate extends StatefulWidget {
  const AuthGate({required this.api, super.key});
  final ApiClient api;

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    widget.api
        .initialize()
        .then((_) => widget.api.restoreSession())
        .catchError((_) async {
      await widget.api.logout();
    }).then((_) {
      if (mounted) setState(() => _loading = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return widget.api.accessToken == null
        ? LoginPage(api: widget.api, onAuthenticated: () => setState(() {}))
        : HomeShell(api: widget.api, onLogout: () => setState(() {}));
  }
}
