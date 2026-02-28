[← Back to Index](README.md)

# User Syncs Locale Preference

## Trigger

When the user changes their language on any platform — [web](user-changes-language.md), [mobile](user-changes-language-on-mobile.md), desktop, or browser extension — the new preference is persisted not only locally but also to the server. The client makes an API call that sets the `user.preferredLocale` field in the database to the selected locale code.

## Server-Side Storage

The `user.preferredLocale` field is a nullable column on the user record. When set, it stores the user's explicit language choice (e.g., `en` or `ar`). When null, it indicates the user has never made an explicit choice and the system should fall back to the standard [locale detection chain](system-detects-locale.md) for each platform — `Accept-Language` header on the API side, localStorage or `navigator.language` on the web, and device locale via `expo-localization` on mobile.

## Cross-Device Consistency

Because the preference lives in the database, it follows the user across every device and platform. When the user signs in on a new device, the client reads `user.preferredLocale` during initialization. If the field is set, the client applies that locale immediately rather than relying on device or browser settings. This means a user who selects Arabic on their phone will see Arabic when they next open the web app on their laptop, without needing to change the setting again.

## Server-Rendered Content

The server uses `user.preferredLocale` to determine the locale for all server-generated content directed at the user. When composing transactional emails — [OTP verification emails](system-sends-otp-email.md), [invitation emails](system-sends-invitation-email.md) — the email service resolves the recipient's preferred locale from this field. If `preferredLocale` is set, it takes priority over the `Accept-Language` header that was present on the original request. This ensures the user receives emails in their chosen language regardless of which device or browser triggered the action.

## Fallback Behavior

If `user.preferredLocale` is null, the system falls back to the standard detection mechanisms described in [System Detects Locale](system-detects-locale.md). The API side parses the `Accept-Language` header, the web side checks localStorage and then `navigator.language`, and the mobile side reads the device locale via `expo-localization`. The `preferredLocale` field only overrides these defaults when the user has made an explicit choice.
