# ⚠️ Frontend incompleto — no forma parte de la entrega evaluada

Este proyecto de Flutter se inició en un solo commit ("Primer commit") y nunca se continuó. Antes de asumir que es una app funcional, ten esto en cuenta:

## Qué sí existe

- Un flujo de autenticación (`lib/features/auth/`) con arquitectura limpia real: `domain/`, `data/`, `application/`, `presentation/` — incluye páginas de login, splash y home.
- Soporte planeado (pero no confirmado funcional) para autenticación biométrica (`lib/core/security/biometric_auth_contract.dart`).
- Manejo de distintos entornos (`main_development.dart`, `main_staging.dart`, `main_production.dart`).

## Qué falta

- Las carpetas `lib/features/session/` y `lib/features/dashboard/` existen pero están **vacías** — no hay gestión de sesión ni pantalla principal bancaria.
- No conecta con el resto de la funcionalidad del banco: aunque compilara, no hay a dónde navegar después del login.
- **Nadie ha compilado ni corrido esta app** desde que se creó en ese primer commit. No hay garantía de que `flutter pub get` / `flutter run` funcionen hoy sin ajustes.

## Qué usar en su lugar

La aplicación real y funcional de este proyecto es la web app de Flask documentada en el [`README.md`](../README.md) de la raíz del repositorio, con su guía de instalación en [`SETUP.md`](../SETUP.md).

Si en el futuro se retoma este frontend, la feature de `auth/` puede servir como referencia de la arquitectura a seguir para las demás.
