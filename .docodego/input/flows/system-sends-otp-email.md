# System Sends OTP Email

## Trigger

When a user requests email OTP sign-in, Better Auth generates a 6-digit verification code and stores it in the `verification` table with an expiration timestamp. This fires the `sendVerificationOTP` callback, passing the code, email address, and verification type to the application's email layer.

## Email Processing

The `IEmailService` interface receives the send request and routes it through the appropriate transport. In development, the service logs the code directly to the console — the OTP is visible in the terminal output, so no real email delivery is needed during local development. In production, the interface is backed by a pluggable transport such as Resend, SES, or any provider that implements the interface. Swapping providers requires no changes to the calling code.

## Template Rendering and Localization

The email HTML is rendered from `src/email/templates/otp-email.tsx`, which uses the shared `email-layout.tsx` for its table-based HTML structure. The subject line and body content are localized through the i18n `email` namespace, using the locale resolved from the request's `Accept-Language` header. When the locale is Arabic, the subject line renders correctly in RTL — for example, the Arabic verification code subject line reads "رمز التحقق الخاص بك". The shared email layout handles the structural markup (table-based for email client compatibility), and the OTP template slots in the localized greeting, code display, and expiration notice.

## Developer Preview

A development-only route at `GET /api/dev/emails/otp` renders the OTP email template with sample data, allowing developers to preview the email's appearance in a browser without triggering an actual sign-in flow. This endpoint is disabled in production and returns a 404.
