import 'package:flutter/material.dart';

import '../../../app/app_config.dart';
import '../../../core/network/api_client.dart';

class LoginPage extends StatefulWidget {
  const LoginPage(
      {required this.api, required this.onAuthenticated, super.key});
  final ApiClient api;
  final VoidCallback onAuthenticated;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _form = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _register = false;
  bool _busy = false;
  bool _showPassword = false;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _runAuthentication(Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action();
      if (mounted) widget.onAuthenticated();
    } catch (error) {
      if (mounted) setState(() => _error = widget.api.messageFor(error));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    await _runAuthentication(() async {
      if (_register) {
        await widget.api.register(
          name: _name.text,
          email: _email.text,
          password: _password.text,
        );
      } else {
        await widget.api.login(_email.text, _password.text);
      }
    });
  }

  Future<void> _loginDemo() async {
    _email.text = AppConfig.demoEmail;
    _password.text = AppConfig.demoPassword;
    await _runAuthentication(
      () => widget.api.login(AppConfig.demoEmail, AppConfig.demoPassword),
    );
  }

  Future<void> _configureServer() async {
    final controller = TextEditingController(text: widget.api.apiBaseUrl);
    String? dialogError;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Cấu hình máy chủ'),
          content: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Nhập địa chỉ HTTPS của PharmaMind API. Với Cloudflare '
                  'Quick Tunnel, bạn có thể thay URL mới tại đây mà không '
                  'cần cài lại ứng dụng.',
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: controller,
                  keyboardType: TextInputType.url,
                  autocorrect: false,
                  decoration: const InputDecoration(
                    labelText: 'Địa chỉ API',
                    hintText: 'https://example.trycloudflare.com',
                    prefixIcon: Icon(Icons.dns_outlined),
                  ),
                ),
                if (dialogError != null) ...[
                  const SizedBox(height: 10),
                  Text(
                    dialogError!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () async {
                await widget.api.resetApiBaseUrl();
                if (!dialogContext.mounted) return;
                Navigator.of(dialogContext).pop();
                if (mounted) setState(() => _error = null);
              },
              child: const Text('Dùng mặc định'),
            ),
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Hủy'),
            ),
            FilledButton(
              onPressed: () async {
                try {
                  await widget.api.updateApiBaseUrl(controller.text);
                  if (!dialogContext.mounted) return;
                  Navigator.of(dialogContext).pop();
                  if (mounted) setState(() => _error = null);
                } on StateError catch (error) {
                  setDialogState(() => dialogError = error.message);
                }
              },
              child: const Text('Lưu'),
            ),
          ],
        ),
      ),
    );
    controller.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Form(
                key: _form,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Container(
                      width: 72,
                      height: 72,
                      decoration: BoxDecoration(
                        color: colors.primary,
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: const Icon(
                        Icons.health_and_safety_rounded,
                        color: Colors.white,
                        size: 38,
                      ),
                    ),
                    const SizedBox(height: 28),
                    Text(
                      _register
                          ? 'Tạo tài khoản'
                          : 'Chăm sóc sức khỏe\ncả gia đình',
                      style:
                          Theme.of(context).textTheme.headlineMedium?.copyWith(
                                fontWeight: FontWeight.w800,
                                height: 1.12,
                              ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      _register
                          ? 'Bắt đầu quản lý thuốc và lịch uống cùng PharmaMind.'
                          : 'Đăng nhập để xem lịch thuốc và thông tin gia đình.',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            color: colors.onSurfaceVariant,
                          ),
                    ),
                    const SizedBox(height: 30),
                    if (_register) ...[
                      TextFormField(
                        controller: _name,
                        textCapitalization: TextCapitalization.words,
                        decoration: const InputDecoration(
                          labelText: 'Họ và tên',
                          prefixIcon: Icon(Icons.person_outline),
                        ),
                        validator: (value) =>
                            value == null || value.trim().isEmpty
                                ? 'Nhập họ tên của bạn'
                                : null,
                      ),
                      const SizedBox(height: 14),
                    ],
                    TextFormField(
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      autofillHints: const [AutofillHints.email],
                      decoration: const InputDecoration(
                        labelText: 'Email',
                        prefixIcon: Icon(Icons.mail_outline),
                      ),
                      validator: (value) =>
                          value == null || !value.contains('@')
                              ? 'Nhập email hợp lệ'
                              : null,
                    ),
                    const SizedBox(height: 14),
                    TextFormField(
                      controller: _password,
                      obscureText: !_showPassword,
                      autofillHints: const [AutofillHints.password],
                      decoration: InputDecoration(
                        labelText: 'Mật khẩu',
                        prefixIcon: const Icon(Icons.lock_outline),
                        suffixIcon: IconButton(
                          onPressed: () => setState(
                            () => _showPassword = !_showPassword,
                          ),
                          icon: Icon(
                            _showPassword
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                          ),
                        ),
                      ),
                      validator: (value) =>
                          value == null || value.length < (_register ? 8 : 1)
                              ? (_register
                                  ? 'Mật khẩu cần ít nhất 8 ký tự'
                                  : 'Nhập mật khẩu')
                              : null,
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 14),
                      Text(_error!, style: TextStyle(color: colors.error)),
                    ],
                    const SizedBox(height: 22),
                    FilledButton(
                      onPressed: _busy ? null : _submit,
                      style: FilledButton.styleFrom(
                        minimumSize: const Size.fromHeight(54),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      child: _busy
                          ? const SizedBox(
                              width: 22,
                              height: 22,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(
                              _register ? 'Tạo tài khoản' : 'Đăng nhập',
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                    ),
                    if (!_register && AppConfig.enableDemoLogin) ...[
                      const SizedBox(height: 12),
                      OutlinedButton.icon(
                        onPressed: _busy ? null : _loginDemo,
                        icon: const Icon(Icons.auto_awesome_outlined),
                        label: const Text('Dùng thử với tài khoản demo'),
                        style: OutlinedButton.styleFrom(
                          minimumSize: const Size.fromHeight(52),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Tài khoản demo luôn bắt đầu trống. Dữ liệu sẽ được xóa '
                        'khi đăng nhập lại.',
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: colors.onSurfaceVariant,
                            ),
                      ),
                    ],
                    if (AppConfig.enableRegistration) ...[
                      const SizedBox(height: 12),
                      TextButton(
                        onPressed: _busy
                            ? null
                            : () => setState(() {
                                  _register = !_register;
                                  _error = null;
                                }),
                        child: Text(
                          _register
                              ? 'Đã có tài khoản? Đăng nhập'
                              : 'Chưa có tài khoản? Đăng ký',
                        ),
                      ),
                    ],
                    const SizedBox(height: 8),
                    TextButton.icon(
                      onPressed: _busy ? null : _configureServer,
                      icon: const Icon(Icons.settings_ethernet_outlined),
                      label: Text(
                        'Máy chủ: ${Uri.parse(widget.api.apiBaseUrl).host}',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
