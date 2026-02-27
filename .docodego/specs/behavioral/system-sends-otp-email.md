---
id: SPEC-2026-086
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [System, User]
---

[← Back to Roadmap](../ROADMAP.md)

# System Sends OTP Email

## Intent

This spec defines how the system generates and delivers a one-time password (OTP) verification email when a user requests email OTP sign-in. Better Auth generates a 6-digit verification code, stores it in the `verification` table with an expiration timestamp, and fires the `sendVerificationOTP` callback with the code, email address, and verification type. The `IEmailService` interface receives the send request and routes it through the configured transport — in development the service logs the OTP code directly to the console terminal for local testing without real email delivery, and in production the service delivers the email through a pluggable transport such as Resend, SES, or any provider implementing the interface. The email HTML is rendered from the `otp-email.tsx` template using the shared `email-layout.tsx` for table-based HTML structure compatible with email clients. Subject line and body content are localized through the @repo/i18n `email` namespace using the locale resolved from the request's `Accept-Language` header, with RTL rendering for Arabic locales. A development-only preview route at `GET /api/dev/emails/otp` renders the OTP template with sample data for browser preview and returns HTTP 404 in production.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth OTP generation (authentication framework component that generates a 6-digit numeric verification code, stores the code in the `verification` database table with an expiration timestamp, and fires the `sendVerificationOTP` callback) | write | When a user submits their email address on the sign-in form requesting email OTP authentication and Better Auth processes the request by generating the code and persisting it to the verification table before invoking the send callback | The verification table write fails because the D1 database is unreachable or the write operation times out — Better Auth returns an error response to the sign-in request and the OTP email is not sent because the callback is never fired |
| `IEmailService` interface (application email abstraction layer that receives send requests from Better Auth callbacks and routes them through the configured transport — console logging in development, pluggable provider such as Resend or SES in production) | write | When the `sendVerificationOTP` callback fires and passes the 6-digit code, recipient email address, and verification type to the email service interface for delivery through the active transport | The email service transport fails because the production provider (Resend, SES) returns an API error or the network connection to the provider times out — the service logs the delivery failure and returns an error to the callback indicating the OTP email was not delivered |
| OTP email template `otp-email.tsx` (React component that renders the OTP verification email HTML using the shared `email-layout.tsx` for table-based structure, displaying a localized greeting, the 6-digit code in a prominent styled block, and an expiration notice) | read | When the email service prepares the email body by rendering the OTP template component with the generated code, recipient email address, and resolved locale to produce the final HTML string for delivery | The template rendering fails because the component throws a runtime error during JSX evaluation or the shared `email-layout.tsx` dependency is missing — the email service catches the render error and logs the failure details without sending a malformed email to the recipient |
| @repo/i18n `email` namespace (internationalization translations for email subject lines and body content, resolved against the locale derived from the request's `Accept-Language` header, supporting LTR and RTL rendering for Arabic locales) | read | When the OTP email template resolves translation keys for the subject line, greeting text, code label, and expiration notice using the locale determined from the sign-in request's `Accept-Language` header | The translation lookup fails because the `email` namespace is missing keys for the resolved locale — the i18n framework falls back to the English default translations and the email is sent with English text instead of the user's preferred locale |
| Development preview route `GET /api/dev/emails/otp` (Hono route handler that renders the OTP email template with hardcoded sample data and returns the HTML response for browser-based visual preview during local development, disabled in production) | read | When a developer navigates to `GET /api/dev/emails/otp` in their browser during local development to preview the OTP email template appearance without triggering an actual sign-in flow or email delivery | The route is accessed in production and returns HTTP 404 because the route handler checks the environment and rejects requests outside the development environment — the developer must use the local development server to access the preview |
| `verification` table in D1 database (SQLite-based Cloudflare D1 database table that stores the generated OTP code alongside the recipient email address, verification type, and expiration timestamp for later validation during the sign-in completion step) | write | When Better Auth generates the 6-digit OTP code and persists the verification record to the database before firing the `sendVerificationOTP` callback to ensure the code exists in storage before the email is sent | The D1 database write fails because the database instance is unavailable or the table schema is corrupted — Better Auth returns an error response to the client and the `sendVerificationOTP` callback is not invoked because the code was not persisted |

## Behavioral Flow

1. **[User]** submits their email address on the sign-in form requesting email OTP authentication, sending a POST request to the Better Auth email OTP endpoint on the Hono API running on Cloudflare Workers

2. **[Better Auth]** receives the sign-in request, generates a 6-digit numeric verification code, and stores the code in the `verification` table in the D1 database with the recipient email address, verification type, and an expiration timestamp

3. **[Better Auth]** fires the `sendVerificationOTP` callback, passing the 6-digit code, the recipient email address, and the verification type to the application's `IEmailService` interface for email delivery

4. **[IEmailService]** receives the send request and determines the active transport based on the environment — in development the service logs the OTP code, recipient email, and verification type directly to the console terminal output for local testing

5. **[IEmailService]** in production, resolves the locale from the original request's `Accept-Language` header and renders the OTP email HTML by invoking the `otp-email.tsx` template component with the 6-digit code, recipient email, and resolved locale as input parameters

6. **[otp-email.tsx]** renders the email HTML using the shared `email-layout.tsx` for table-based structure compatible with email clients, resolving all text content through the @repo/i18n `email` namespace translation keys including the subject line, greeting, code display block, and expiration notice

7. **[IEmailService]** in production, delivers the rendered HTML email to the recipient through the configured transport provider (Resend, SES, or another provider implementing the `IEmailService` interface) and returns the delivery status to the callback

8. **[System]** when the locale resolved from `Accept-Language` is Arabic, the email subject line and body content render in RTL direction — for example the Arabic verification code subject line reads as the localized equivalent of the English subject

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | otp_generated | The user submits their email address on the sign-in form and Better Auth generates a 6-digit verification code and persists it to the `verification` table in D1 with an expiration timestamp | The email address is a valid format, the D1 database write completes without errors, and the verification record is persisted with the generated code and expiration timestamp |
| otp_generated | callback_fired | Better Auth invokes the `sendVerificationOTP` callback with the 6-digit code, recipient email address, and verification type after the verification record is persisted in the database | The verification record exists in the database and Better Auth passes all three parameters (code, email, verification type) to the callback without modification |
| callback_fired | email_logged_to_console | The `IEmailService` receives the callback parameters and the current environment is development, so the service logs the OTP code and recipient email directly to the console terminal output | The environment variable or configuration flag indicates the development environment and the console logging completes without errors |
| callback_fired | email_rendered | The `IEmailService` receives the callback parameters and the current environment is production, so the service resolves the locale and invokes the `otp-email.tsx` template to render the email HTML | The environment is production, the locale is resolved from the `Accept-Language` header, and the template component renders without throwing a runtime error |
| email_rendered | email_delivered | The `IEmailService` sends the rendered HTML email to the recipient through the configured production transport provider and receives a delivery confirmation response from the provider | The transport provider accepts the email, returns a delivery confirmation with a message ID, and the HTTP response status from the provider indicates acceptance |
| email_rendered | email_delivery_failed | The `IEmailService` attempts to send the rendered HTML email through the production transport provider but the provider returns an error or the request times out before receiving a response | The transport provider returns an HTTP error status or the delivery request exceeds the configured timeout threshold and the service catches the failure |

## Business Rules

- **Rule otp-code-six-digits:** IF Better Auth generates a verification code for email OTP sign-in THEN the code is exactly 6 numeric digits — the count of digits in the generated code equals 6 and the code contains only characters in the range 0 through 9
- **Rule verification-record-persisted-before-send:** IF the `sendVerificationOTP` callback is fired THEN the verification record with the code, email, and expiration timestamp already exists in the `verification` table — the count of verification records in the database for the email at callback time equals 1 or more
- **Rule development-logs-to-console:** IF the environment is development THEN the `IEmailService` logs the OTP code and recipient email to the console terminal and does not invoke any production email transport — the count of production email API calls in development equals 0
- **Rule production-uses-pluggable-transport:** IF the environment is production THEN the `IEmailService` delivers the email through the configured transport provider (Resend, SES, or another implementing provider) — the count of console-only OTP deliveries in production equals 0
- **Rule locale-resolved-from-accept-language:** IF the email is rendered in production THEN the locale is resolved from the original sign-in request's `Accept-Language` header and all translation keys are resolved against that locale — the locale used for rendering matches the primary locale from the `Accept-Language` header
- **Rule arabic-renders-rtl:** IF the resolved locale is Arabic (ar) THEN the email subject line and body content render with RTL text direction — the `dir` attribute on the email body element equals `rtl` for Arabic locale emails
- **Rule dev-preview-disabled-in-production:** IF a request is made to `GET /api/dev/emails/otp` in production THEN the endpoint returns HTTP 404 — the HTTP response status code equals 404 for production requests to the dev preview route
- **Rule transport-is-swappable:** IF the production email transport is changed from one provider to another (for example from Resend to SES) THEN zero changes are required in the calling code that invokes `IEmailService` — the count of code changes outside the transport implementation equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| System (the server-side application components including Better Auth, `IEmailService`, email templates, and the Hono API that collectively generate, render, and deliver the OTP verification email without manual intervention) | Generate the 6-digit OTP code and persist it to the `verification` table; fire the `sendVerificationOTP` callback; resolve the locale from `Accept-Language`; render the email template; deliver the email through the configured transport; log OTP details to console in development | Cannot modify the OTP code after it is persisted to the verification table, cannot send the email before the verification record is written to the database, cannot bypass the environment check that determines console logging versus production transport delivery | The system has visibility into the generated OTP code, the recipient email address, the verification type, the resolved locale, and the transport delivery status — the system does not expose the OTP code in any client-facing API response |
| User (the person who submitted their email address requesting email OTP sign-in and who receives the OTP verification email in their inbox or views the logged code in the development console output) | Submit their email address to request OTP sign-in; receive the OTP email in their inbox; view the 6-digit code in the email body; use the code to complete the sign-in verification step on the client-side form | Cannot request the system to resend the OTP without submitting a new sign-in request, cannot view the OTP code through any API response or client-side state other than the delivered email, cannot modify the expiration timestamp of the stored verification record | The user sees only the rendered email in their inbox containing the 6-digit code, greeting, and expiration notice — the user does not see internal delivery logs, transport provider responses, or the verification record stored in the database |

## Constraints

- The 6-digit OTP code is stored in the `verification` table with an expiration timestamp that is exactly 300 seconds (5 minutes) from the generation time — the count of seconds from code generation to expiration equals 300.
- The email template rendering completes within 500 ms of the `IEmailService` receiving the callback parameters — the count of milliseconds from callback receipt to rendered HTML output equals 500 or fewer.
- The production email transport delivery completes within 5000 ms of the rendered HTML being passed to the provider API — the count of milliseconds from transport send to provider response equals 5000 or fewer.
- The OTP email HTML body size is 50 KB or less after rendering — the count of kilobytes in the rendered email HTML string equals 50 or fewer.
- The development console log output for each OTP includes the 6-digit code, recipient email address, and verification type on a single log entry — the count of log entries per OTP in development equals 1.
- The development preview route at `GET /api/dev/emails/otp` returns the rendered HTML response within 1000 ms — the count of milliseconds from request to response equals 1000 or fewer.

## Acceptance Criteria

- [ ] Better Auth generates a 6-digit numeric OTP code when the user requests email OTP sign-in — the generated code length equals 6 and contains only digits 0 through 9
- [ ] The verification record is persisted to the `verification` table in D1 before the `sendVerificationOTP` callback fires — the record is present in the database when the callback begins execution
- [ ] The stored verification record includes the OTP code, recipient email, verification type, and expiration timestamp set to 300 seconds from generation — the expiration offset equals 300 seconds
- [ ] In development the `IEmailService` logs the OTP code and recipient email to the console without invoking a production transport — the console output contains the 6-digit code and the count of production API calls equals 0
- [ ] In production the email HTML is rendered from `otp-email.tsx` using the shared `email-layout.tsx` template — the count of `<table>` elements in the rendered HTML equals 1 or more confirming table-based layout
- [ ] The email subject line and body content are localized via @repo/i18n `email` namespace using the locale from the `Accept-Language` header — the count of hardcoded English strings in the rendered email equals 0
- [ ] When the resolved locale is Arabic the email renders with RTL direction — the `dir` attribute value on the email body element equals `rtl` and is present in the rendered HTML
- [ ] The production transport delivers the email through the configured provider and returns a delivery confirmation — the transport response contains a non-empty message ID
- [ ] The development preview route at `GET /api/dev/emails/otp` returns rendered HTML with sample data and HTTP 200 in development — the response status equals 200 and the body is non-empty
- [ ] The development preview route at `GET /api/dev/emails/otp` returns HTTP 404 in production — the response status equals 404
- [ ] Swapping the production transport provider from one implementation to another requires zero changes to the calling code — the count of modified files outside the transport module equals 0
- [ ] The email template rendering completes within 500 ms of callback receipt — the count of milliseconds from callback to rendered output equals 500 or fewer

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user submits an email address that is syntactically valid but does not correspond to any existing mailbox on the recipient's mail server, resulting in the transport provider accepting the email but the mail server bouncing it later | The `IEmailService` delivers the email to the transport provider which accepts it and returns a delivery confirmation — the bounce notification arrives asynchronously and is handled by the transport provider's webhook or bounce handling mechanism outside the scope of this flow | The transport provider returns a delivery confirmation with a non-empty message ID and the immediate send operation completes without errors despite the eventual bounce |
| The user's `Accept-Language` header contains a locale that has no translations in the @repo/i18n `email` namespace, such as a rare locale variant that was never added to the translation files | The i18n framework falls back to the English default translations for all email content including the subject line, greeting, code label, and expiration notice — the email is rendered entirely in English as the fallback locale | The rendered email HTML contains English text for all translation keys and the count of blank or missing text placeholders in the email equals 0 |
| Two sign-in requests for the same email address arrive within milliseconds of each other, causing Better Auth to generate two separate OTP codes and fire two `sendVerificationOTP` callbacks in rapid succession | Better Auth generates two distinct 6-digit codes and stores two separate verification records in the `verification` table, and the `IEmailService` sends two separate OTP emails — the user receives both emails and can use either valid code to complete sign-in | The count of verification records in the database for the email address equals 2 and both OTP emails are delivered or logged with distinct 6-digit codes |
| The production email transport provider is temporarily rate-limiting requests and returns HTTP 429 when the `IEmailService` attempts to deliver the OTP email through the provider API | The `IEmailService` catches the HTTP 429 response from the provider, logs the rate-limit error with the retry-after header value if present, and returns a delivery failure to the callback — the user does not receive the OTP email for this attempt | The delivery failure log entry contains the HTTP 429 status code and the callback receives an error response indicating the email was not delivered |
| A developer navigates to `GET /api/dev/emails/otp` with a query parameter specifying the Arabic locale to preview the RTL rendering of the OTP email template with sample data in their local browser | The preview route renders the OTP email template with the Arabic locale applied, producing an HTML response with RTL text direction and Arabic translation keys resolved from the `email` namespace sample data | The rendered HTML response contains `dir="rtl"` on the body element and the text content displays Arabic characters from the email namespace translations |

## Failure Modes

- **D1 database write fails when Better Auth attempts to persist the verification record containing the generated OTP code and expiration timestamp**
    - **What happens:** Better Auth generates the 6-digit OTP code and attempts to write the verification record to the `verification` table in D1, but the database write fails because the D1 instance is unreachable, the database is in a read-only state, or the write exceeds the D1 row size limit.
    - **Source:** A Cloudflare D1 regional outage, a database migration that left the table in a locked or read-only state, or a corrupted database instance that rejects new writes to the verification table.
    - **Consequence:** The verification record is not persisted and the `sendVerificationOTP` callback is never fired — the user does not receive the OTP email and the sign-in request returns an error response to the client indicating the OTP could not be generated.
    - **Recovery:** Better Auth returns an HTTP 500 error to the client and the sign-in form displays a localized error message — the user retries the sign-in request and the system logs the D1 write failure with the database error details for the operations team to investigate.

- **Production email transport provider rejects the delivery request or returns an API error when the `IEmailService` attempts to send the rendered OTP email**
    - **What happens:** The `IEmailService` renders the OTP email HTML and sends it to the configured transport provider (Resend, SES, or another provider), but the provider returns an API error such as HTTP 400 (invalid parameters), HTTP 429 (rate limited), or HTTP 500 (provider internal error) and the email is not accepted for delivery.
    - **Source:** The transport provider's API is experiencing an outage, the API key or credentials for the provider are expired or revoked, the sender email address is not verified with the provider, or the provider is rate-limiting requests from the account.
    - **Consequence:** The OTP email is not delivered to the user's inbox and the user cannot complete the sign-in flow with the generated code — the verification record exists in the database with a valid code that the user has no way to access.
    - **Recovery:** The `IEmailService` logs the transport error with the provider response status and error message, and returns an error to the callback — the user retries the sign-in request which generates a new OTP code and attempts delivery again through the same transport provider.

- **OTP email template rendering fails due to a runtime error in the `otp-email.tsx` component or the shared `email-layout.tsx` dependency during HTML generation**
    - **What happens:** The `IEmailService` invokes the `otp-email.tsx` template component to render the email HTML, but the component throws a runtime error during JSX evaluation because a required prop is undefined, the shared `email-layout.tsx` is not found, or a translation key resolution throws an exception.
    - **Source:** A code change to the email template introduced a runtime error, the shared layout component was renamed or moved without updating the import path, or the i18n `email` namespace initialization fails for the resolved locale.
    - **Consequence:** The email HTML is not rendered and the `IEmailService` cannot deliver the email — the user does not receive the OTP code in their inbox and the sign-in flow is blocked until the template error is resolved.
    - **Recovery:** The `IEmailService` catches the template rendering error, logs the error stack trace and the input parameters that caused the failure, and returns an error to the callback — the user retries the sign-in request and the development team alerts on the rendering failure to fix the template.

## Declared Omissions

- This specification does not define the OTP verification step where the user enters the 6-digit code on the sign-in form and Better Auth validates it against the stored record — that behavior is covered by the user-signs-in-with-email-otp specification
- This specification does not cover the email transport provider configuration, API key management, or sender domain verification required to set up Resend, SES, or other providers — those are infrastructure concerns outside the behavioral flow
- This specification does not define the `IEmailService` interface contract, method signatures, or provider implementation details — the interface is an application architecture concern that this specification references for behavioral context only
- This specification does not address email deliverability, spam filtering, DKIM signing, or SPF record configuration that affects whether the OTP email reaches the user's inbox versus their spam folder — those concerns are handled at the DNS and transport provider configuration level
- This specification does not cover the OTP expiration validation logic that rejects expired codes during the sign-in completion step — expiration enforcement is part of the sign-in verification flow specification

## Related Specifications

- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md)
    — defines the complete email OTP sign-in flow including the user
    submitting their email, receiving the OTP, and entering the code
    to complete authentication which triggers this email send flow
- [system-sends-invitation-email](system-sends-invitation-email.md)
    — defines the invitation email send flow that uses the same
    `IEmailService` interface and shared `email-layout.tsx` template
    structure as the OTP email but delivers an organization invitation
    link instead of a verification code
- [session-lifecycle](session-lifecycle.md) — defines the session
    creation behavior that begins after the user successfully verifies
    the OTP code delivered by this email flow and Better Auth
    establishes the authenticated session
- [user-changes-language](user-changes-language.md) — defines the
    language preference mechanism that determines the locale used for
    resolving @repo/i18n translation keys in the OTP email template
    subject line and body content
