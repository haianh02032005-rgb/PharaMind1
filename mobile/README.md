# PharmaMind AI Mobile

Flutter app for Android and iOS. The app talks directly to the existing FastAPI backend; the backend remains the source of truth.

## Requirements

- Flutter stable (Dart SDK constraint is declared in `pubspec.yaml`)
- Android Studio / Xcode for native builds
- A reachable PharmaMind API

## Setup

Generate the native platform folders from a separate scaffold so the existing app source and `pubspec.yaml` stay intact. From this directory:

```powershell
flutter create --org ai.pharmamind --project-name pharmamind --platforms android,ios native_scaffold
Copy-Item -Recurse native_scaffold\android .
Copy-Item -Recurse native_scaffold\ios .
Remove-Item -Recurse native_scaffold
```

Then run:

```sh
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

For a physical device, set `API_BASE_URL` to the development machine's LAN IP. For iOS simulator use `http://127.0.0.1:8000`. Production must use HTTPS.

## Current MVP

- Email/password login and registration against `/auth`
- Short-lived access token in memory; refresh token in Keychain/Keystore using `flutter_secure_storage`
- Automatic single-flight token refresh on 401, then sign out if refresh is rejected
- Create/select family, add members, member list, today's member schedule, medication list, and cabinet overview
- Responsive Flutter Material 3 shell with large touch targets and Vietnamese labels

Screens for OCR/Excel, push notifications, AI chat, 3D Digital Twin and offline cache need the related backend/mobile integrations and are not represented by mock health data yet.

## API settings

`API_BASE_URL` can be supplied with `--dart-define`. Defaults to Android emulator host `http://10.0.2.2:8000`. API paths match the current backend routers. Android's generated debug manifest may permit local HTTP during development; configure HTTPS and platform transport security before release.
