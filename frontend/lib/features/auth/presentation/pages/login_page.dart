import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/theme/app_theme.dart';
import '../../application/auth_providers.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  late final TextEditingController _userController;
  late final TextEditingController _passwordController;
  bool _tokenSelected = false;
  int _selectedNavIndex = 0;

  @override
  void initState() {
    super.initState();
    _userController = TextEditingController();
    _passwordController = TextEditingController();
  }

  @override
  void dispose() {
    _userController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    final mediaQuery = MediaQuery.of(context);
    final size = mediaQuery.size;
    final platform = Theme.of(context).platform;
    final isIOS = platform == TargetPlatform.iOS || platform == TargetPlatform.macOS;
    final headerHeight = size.height * 0.15;

    return Scaffold(
      backgroundColor: BankingThemeTokens.pageBackground,
      body: Column(
        children: [
          Expanded(
            child: Stack(
              children: [
                Column(
                  children: [
                    Container(
                      height: headerHeight + mediaQuery.padding.top,
                      color: BankingThemeTokens.headerRed,
                      child: Padding(
                        padding: EdgeInsets.only(
                          top: mediaQuery.padding.top + (isIOS ? 6 : 4),
                          left: 18,
                          right: 18,
                          bottom: 12,
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            _StatusBar(isIOS: isIOS),
                            const Spacer(),
                            const _BacLogo(),
                            const SizedBox(height: 8),
                          ],
                        ),
                      ),
                    ),
                    const Expanded(child: SizedBox.shrink()),
                  ],
                ),
                Positioned.fill(
                  child: SingleChildScrollView(
                    padding: EdgeInsets.fromLTRB(
                      16,
                      headerHeight + mediaQuery.padding.top - 28,
                      16,
                      isIOS ? 130 : 118,
                    ),
                    child: Column(
                      children: [
                        _MainLoginCard(
                          userController: _userController,
                          passwordController: _passwordController,
                          tokenSelected: _tokenSelected,
                          onTokenToggle: (value) => setState(() => _tokenSelected = value ?? false),
                          onLoginPressed: () =>
                              ref.read(authControllerProvider.notifier).signInPlaceholder(),
                          errorMessage: authState.errorMessage,
                        ),
                        const SizedBox(height: 14),
                        const _SecondaryActionCard(),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          _BottomNavigationBar(
            isIOS: isIOS,
            selectedIndex: _selectedNavIndex,
            onSelect: (index) => setState(() => _selectedNavIndex = index),
            onCenterTap: () => _showComingSoon(context),
          ),
        ],
      ),
    );
  }

  void _showComingSoon(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Función disponible próximamente')),
    );
  }
}

class _MainLoginCard extends StatelessWidget {
  const _MainLoginCard({
    required this.userController,
    required this.passwordController,
    required this.tokenSelected,
    required this.onTokenToggle,
    required this.onLoginPressed,
    this.errorMessage,
  });

  final TextEditingController userController;
  final TextEditingController passwordController;
  final bool tokenSelected;
  final ValueChanged<bool?> onTokenToggle;
  final VoidCallback onLoginPressed;
  final String? errorMessage;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: BankingThemeTokens.surface,
        borderRadius: BorderRadius.circular(BankingThemeTokens.cardRadius),
        boxShadow: BankingThemeTokens.surfaceShadow,
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 18, 18, 22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const _GreetingSection(),
            const SizedBox(height: 20),
            _InputSection(
              label: 'Usuario',
              controller: userController,
              placeholder: 'santty19',
            ),
            const SizedBox(height: 12),
            _InputSection(
              label: 'Contraseña',
              controller: passwordController,
              placeholder: 'Digite su contraseña',
              obscureText: true,
            ),
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Recuperación de acceso próximamente')),
                  );
                },
                style: TextButton.styleFrom(
                  padding: EdgeInsets.zero,
                  foregroundColor: BankingThemeTokens.accentBlue,
                ),
                child: const Text('¿No puede ingresar?'),
              ),
            ),
            Row(
              children: [
                Checkbox.adaptive(
                  value: tokenSelected,
                  onChanged: onTokenToggle,
                  visualDensity: VisualDensity.compact,
                ),
                const Text(
                  'Ingresar token',
                  style: TextStyle(color: BankingThemeTokens.subtleText),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const _FaceIdSection(),
            const SizedBox(height: 16),
            SizedBox(
              height: 52,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: BankingThemeTokens.primaryBlue,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  elevation: 2,
                ),
                onPressed: onLoginPressed,
                child: const Text(
                  'Ingresar',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                ),
              ),
            ),
            if (errorMessage != null) ...[
              const SizedBox(height: 12),
              Text(
                errorMessage!,
                style: const TextStyle(color: Colors.red),
                textAlign: TextAlign.center,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _GreetingSection extends StatelessWidget {
  const _GreetingSection();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(
          width: 28,
          height: 24,
          child: Stack(
            children: const [
              Positioned(
                left: 0,
                top: 0,
                child: Icon(Icons.wb_sunny_rounded, size: 14, color: Color(0xFFFFB547)),
              ),
              Positioned(
                right: 0,
                bottom: 0,
                child: Icon(Icons.cloud_rounded, size: 18, color: Color(0xFFB4BFCE)),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        const Text(
          'Buenas noches, Santiago',
          style: TextStyle(
            color: BankingThemeTokens.subtleText,
            fontSize: 15,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}

class _InputSection extends StatelessWidget {
  const _InputSection({
    required this.label,
    required this.controller,
    this.placeholder,
    this.obscureText = false,
  });

  final String label;
  final TextEditingController controller;
  final String? placeholder;
  final bool obscureText;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(BankingThemeTokens.fieldRadius),
        border: Border.all(color: BankingThemeTokens.inputBorder),
      ),
      padding: const EdgeInsets.fromLTRB(14, 10, 14, 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: BankingThemeTokens.darkText,
              fontWeight: FontWeight.w700,
            ),
          ),
          TextField(
            controller: controller,
            obscureText: obscureText,
            decoration: InputDecoration(
              isDense: true,
              hintText: placeholder,
              hintStyle: const TextStyle(color: BankingThemeTokens.subtleText),
              border: InputBorder.none,
              enabledBorder: InputBorder.none,
              focusedBorder: InputBorder.none,
              contentPadding: const EdgeInsets.only(top: 8),
            ),
          ),
        ],
      ),
    );
  }
}

class _FaceIdSection extends StatelessWidget {
  const _FaceIdSection();

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Autenticación FaceID próximamente')),
        );
      },
      child: Column(
        children: [
          Container(
            width: 168,
            height: 168,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: BankingThemeTokens.glowBlue.withValues(alpha: 0.7),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x77CDEFFF),
                  blurRadius: 34,
                  spreadRadius: 6,
                ),
                BoxShadow(
                  color: Color(0x337AC8FF),
                  blurRadius: 56,
                  spreadRadius: 14,
                ),
              ],
            ),
            child: Center(
              child: Container(
                width: 130,
                height: 130,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: const Color(0x66FFFFFF), width: 2),
                  gradient: const RadialGradient(
                    colors: [Color(0xFFE8F8FF), Color(0xFFCDEFFF)],
                  ),
                ),
                child: const Center(
                  child: Icon(
                    Icons.face_rounded,
                    size: 74,
                    color: Color(0xFF4C5A6E),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            'o ingrese con FaceID',
            style: TextStyle(
              color: BankingThemeTokens.accentBlue,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _SecondaryActionCard extends StatelessWidget {
  const _SecondaryActionCard();

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(BankingThemeTokens.actionRadius),
        onTap: () {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Registro de cliente próximamente')),
          );
        },
        child: Container(
          width: double.infinity,
          decoration: BoxDecoration(
            color: BankingThemeTokens.surface,
            borderRadius: BorderRadius.circular(BankingThemeTokens.actionRadius),
            boxShadow: BankingThemeTokens.surfaceShadow,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: const [
              Icon(Icons.groups_rounded, color: BankingThemeTokens.primaryBlue),
              SizedBox(width: 2),
              Icon(Icons.arrow_forward_rounded, color: BankingThemeTokens.primaryBlue, size: 20),
              SizedBox(width: 10),
              Expanded(
                child: Text(
                  '¿Quiere ser cliente o crear usuario?',
                  style: TextStyle(
                    color: BankingThemeTokens.darkText,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: BankingThemeTokens.subtleText),
            ],
          ),
        ),
      ),
    );
  }
}

class _BottomNavigationBar extends StatelessWidget {
  const _BottomNavigationBar({
    required this.isIOS,
    required this.selectedIndex,
    required this.onSelect,
    required this.onCenterTap,
  });

  final bool isIOS;
  final int selectedIndex;
  final ValueChanged<int> onSelect;
  final VoidCallback onCenterTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      padding: EdgeInsets.fromLTRB(8, isIOS ? 6 : 4, 8, isIOS ? 18 : 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          _NavItem(
            icon: Icons.home_rounded,
            label: 'Inicio',
            active: selectedIndex == 0,
            onTap: () => onSelect(0),
          ),
          _NavItem(
            icon: Icons.calendar_month_rounded,
            label: 'Centro de pagos',
            active: selectedIndex == 1,
            onTap: () => onSelect(1),
          ),
          _CenterNavItem(onTap: onCenterTap),
          _NavItem(
            icon: Icons.tune_rounded,
            label: 'Solicitudes',
            active: selectedIndex == 2,
            onTap: () => onSelect(2),
          ),
          _NavItem(
            icon: Icons.menu_rounded,
            label: 'Más',
            active: selectedIndex == 3,
            onTap: () => onSelect(3),
          ),
        ],
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.icon,
    required this.label,
    required this.onTap,
    this.active = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool active;

  @override
  Widget build(BuildContext context) {
    final color = active ? BankingThemeTokens.headerRed : BankingThemeTokens.subtleText;
    return Expanded(
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 22, color: color),
            const SizedBox(height: 2),
            Text(
              label,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 11,
                fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CenterNavItem extends StatelessWidget {
  const _CenterNavItem({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: InkWell(
        borderRadius: BorderRadius.circular(28),
        onTap: onTap,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 54,
              height: 54,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: BankingThemeTokens.primaryBlue,
                boxShadow: [
                  BoxShadow(
                    color: Color(0x33004C8C),
                    blurRadius: 14,
                    offset: Offset(0, 5),
                  ),
                ],
              ),
              child: const Icon(Icons.compare_arrows_rounded, color: Colors.white),
            ),
            const SizedBox(height: 4),
            const Text(
              'Transferir o pagar',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 10,
                color: BankingThemeTokens.darkText,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusBar extends StatelessWidget {
  const _StatusBar({required this.isIOS});

  final bool isIOS;

  @override
  Widget build(BuildContext context) {
    if (isIOS) {
      return const Row(
        children: [
          Text(
            '11:51',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
          ),
          Spacer(),
          Icon(Icons.signal_cellular_alt_rounded, color: Colors.white, size: 16),
          SizedBox(width: 5),
          Icon(Icons.wifi_rounded, color: Colors.white, size: 16),
          SizedBox(width: 5),
          _BatteryBadge(),
        ],
      );
    }

    return const Row(
      children: [
        Text(
          '11:51',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w500),
        ),
        Spacer(),
        Icon(Icons.signal_cellular_alt_rounded, color: Colors.white, size: 14),
        SizedBox(width: 4),
        Icon(Icons.wifi_rounded, color: Colors.white, size: 14),
        SizedBox(width: 4),
        _BatteryBadge(compact: true),
      ],
    );
  }
}

class _BatteryBadge extends StatelessWidget {
  const _BatteryBadge({this.compact = false});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: compact ? 4 : 6, vertical: 2),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white.withValues(alpha: 0.7), width: 0.8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.battery_5_bar_rounded, size: 14, color: Color(0xFFFFDF6B)),
          const SizedBox(width: 2),
          Text(
            '67%',
            style: TextStyle(
              color: const Color(0xFFFFDF6B),
              fontSize: compact ? 10 : 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _BacLogo extends StatelessWidget {
  const _BacLogo();

  @override
  Widget build(BuildContext context) {
    return const Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.pets_rounded, color: Colors.white, size: 28),
        SizedBox(width: 8),
        Text(
          'BAC',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w800,
            fontSize: 28,
            letterSpacing: 1.2,
          ),
        ),
      ],
    );
  }
}
