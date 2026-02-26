[← Back to Index](README.md)

# Mobile Handles Deep Link

## The User Taps a Link

The user encounters a `docodego://` link somewhere on their device — in a push notification, an email, a chat message, or another app. When they tap it, the operating system recognizes the custom URL scheme registered by the Expo app and hands the URL to the DoCodeGo mobile application. If the app is not already running, the OS launches it with the deep link URL as the initial route.

## Expo Router Resolves the Path

Expo Router v6 intercepts the incoming URL and extracts the path portion — for example, `docodego://app/acme-corp/members` resolves to the `/app/acme-corp/members` route. The router matches this path against its file-based route definitions, the same typed routes described in [User Navigates Mobile App](user-navigates-mobile-app.md). If the path matches a valid route, navigation proceeds. If the path does not match any known route, the app falls back to the default screen rather than showing an error.

## Authenticated User — Direct Navigation

If the user is already authenticated — meaning a valid session token exists in `expo-secure-store` as established during [sign-in on mobile](user-signs-in-on-mobile.md) — the app navigates directly to the target screen. The user sees the linked content load with all expected data. If the deep link points to a resource within a different organization than the user's current active org, the app switches the active organization context before rendering the target screen.

## Unauthenticated User — Sign-In Detour

If the user is not authenticated, or if their stored session token has expired, the app cannot load the target screen. Instead, the app redirects to the sign-in screen. Before redirecting, it preserves the deep link target path in memory so it is not lost during the authentication flow. The user signs in through any of the available mobile methods — [email OTP or SSO](user-signs-in-on-mobile.md). After successful authentication and session establishment, the app retrieves the preserved deep link target and navigates there automatically. The user arrives at the screen they originally intended to reach, without needing to tap the link again.

## Cold Start vs. Warm Start

When the app is already running in the foreground or background (warm start), the deep link is received by the existing Expo Router instance and navigation happens immediately within the current navigation stack. When the app is launched from a terminated state (cold start), the deep link URL is passed as the initial URL during app initialization. Expo Router reads this URL during startup and uses it as the initial route, so the user lands directly on the target screen after the app finishes loading — provided they are authenticated. The behavior is identical from the user's perspective regardless of whether the app was already running.
