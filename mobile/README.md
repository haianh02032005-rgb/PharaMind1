# PharmaMind AI Mobile

Flutter app for Android and iOS. The app talks directly to the existing FastAPI backend; the backend remains the source of truth.

## Requirements

- Flutter stable 3.47 or newer
- Android SDK 36 + JDK 17 for Android builds
- macOS + Xcode for iOS signing/builds
- A reachable PharmaMind API

## Setup

The Android and iOS native projects are already included. From this directory:

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

For a physical device, set `API_BASE_URL` to the development machine's LAN IP. For iOS simulator use `http://127.0.0.1:8000`. Production must use HTTPS.

## Current MVP

- Email/password login and registration against `/auth`
- Short-lived access token in memory; refresh token in Keychain/Keystore using `flutter_secure_storage`
- Automatic single-flight token refresh on 401, then sign out if refresh is rejected
- Empty-account onboarding, create/select family, and add/select members
- Member health overview with conditions, allergies, drug reactions, emergency contacts and health profile editing
- Medication list, today's schedule and prescription history
- Manual prescription creation with the first medication item
- Prescription import from camera, gallery, PDF, XLSX or CSV with review, validation and commit
- Interactive 3x3 smart-cabinet view with compartment details and open/close actions
- Responsive Flutter Material 3 shell with large touch targets and Vietnamese labels
- One-tap login for the shared empty demo account
- Runtime API server settings on the login screen, so a changed Cloudflare
  Quick Tunnel URL does not require rebuilding or reinstalling the app

Push notifications, AI chat, realtime WebSocket sync, full 3D rendering and offline write synchronization remain later phases. The current cabinet screen uses the backend Digital Twin state in a mobile-first 3x3 layout.

## API settings

Build-time settings are supplied with `--dart-define`:

```text
APP_ENV=development|production
API_BASE_URL=https://your-api.example.com
ENABLE_REGISTRATION=true|false
ENABLE_DEMO_LOGIN=true|false
ENABLE_CABINET_REALTIME=true|false
```

`API_BASE_URL` defaults to the Android emulator host `http://10.0.2.2:8000`. `APP_ENV=production` rejects non-HTTPS URLs.
The login screen can override this value at runtime. Changing servers clears
the current authentication session, and the chosen URL is stored securely on
the device.

## Validate and build

```bash
flutter analyze
flutter test
flutter build apk --release \
  --dart-define=APP_ENV=production \
  --dart-define=API_BASE_URL=https://your-api.example.com
```

The generated Android project currently uses the debug signing key for local trial builds. Configure a private upload/release keystore before publishing to Google Play. Build and sign the iOS target on macOS with Xcode and an Apple Developer account.
