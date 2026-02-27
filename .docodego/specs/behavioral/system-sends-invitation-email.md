---
id: SPEC-2026-087
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [System, Org Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# System Sends Invitation Email

## Intent

This spec defines how the system generates and delivers an organization invitation email when an organization admin invites a new member. Better Auth creates an invitation record with a 7-day expiration window and fires the email callback with the invitee's email address, the invitation token, and organization details. The email is processed through the same `IEmailService` interface used by OTP emails — in development the email content including the invitation link is logged to the console for testing, and in production the email is delivered through the configured pluggable transport (Resend, SES, or another provider). The email HTML is built from a template within `src/email/templates/` using the shared `email-layout.tsx` for consistent table-based structure across all email types. Subject and body text are localized using the @repo/i18n `email` namespace with the locale determined from the request's `Accept-Language` header at the time the admin triggered the invitation. The email includes the organization name, the role being offered, and clear calls to action for accepting or declining the invitation through a link that routes to the web application.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth invitation system (authentication framework component that creates an invitation record in the database with a unique token, the invitee's email address, the assigned role, organization ID, and a 7-day expiration timestamp, then fires the email callback) | write | When an organization admin submits the invite member form and Better Auth processes the request by creating the invitation record in the database and invoking the email callback with the token, email, and organization details | The invitation record write fails because the D1 database is unreachable or the write operation encounters a constraint violation — Better Auth returns an error to the admin and the email callback is never fired because the invitation was not persisted |
| `IEmailService` interface (application email abstraction layer that receives send requests from Better Auth callbacks and routes them through the configured transport — console logging in development, pluggable provider such as Resend or SES in production) | write | When Better Auth fires the invitation email callback and passes the invitee email address, invitation token, organization name, assigned role, and related details to the email service for rendering and delivery | The email service transport fails because the production provider returns an API error or the network connection to the provider times out — the service logs the delivery failure and returns an error indicating the invitation email was not delivered to the invitee |
| Invitation email template (React component within `src/email/templates/` that renders the invitation email HTML using the shared `email-layout.tsx` for table-based structure, displaying the organization name, offered role, and accept/decline action links) | read | When the email service prepares the invitation email body by rendering the template component with the organization name, assigned role, invitation token, invitee email, and resolved locale to produce the final HTML | The template rendering fails because the component throws a runtime error during JSX evaluation or the shared `email-layout.tsx` dependency cannot be resolved — the email service catches the render error and logs the failure without sending a malformed email |
| @repo/i18n `email` namespace (internationalization translations for email subject lines and body content, resolved against the locale derived from the admin's request `Accept-Language` header at the time the invitation was triggered) | read | When the invitation email template resolves translation keys for the subject line, greeting text, organization name label, role description, and accept/decline button text using the locale from the admin's request | The translation lookup fails because the `email` namespace is missing keys for the resolved locale — the i18n framework falls back to the English default translations and the email is sent with English text instead of the locale matching the admin's language preference |
| Web application invitation acceptance route (client-side route in the SPA that receives the invitation link click from the email recipient, validates the invitation token, and presents the accept or decline decision UI to the invitee) | read | When the email recipient clicks the accept or decline link in the invitation email and their browser navigates to the web application URL containing the invitation token as a route parameter | The web application is unreachable because the hosting infrastructure is down — the invitee's browser displays a connection error and the invitee retries clicking the link later when the application becomes accessible again |
| D1 database invitation table (Cloudflare D1 database table that stores the invitation record including the unique token, invitee email, organization ID, assigned role, inviting admin ID, and 7-day expiration timestamp) | write | When Better Auth processes the admin's invite request and persists the invitation record to the database before firing the email callback to ensure the token is valid and stored before the email is sent to the invitee | The D1 database is unavailable or the write fails due to a constraint violation such as a duplicate invitation for the same email and organization — Better Auth returns an error to the admin and the invitation email is not sent |

## Behavioral Flow

1. **[Org Admin]** submits the invite member form specifying the invitee's email address and the role to assign, sending a request to the Better Auth invitation endpoint on the Hono API running on Cloudflare Workers

2. **[Better Auth]** receives the invitation request, validates the admin's permission to invite members, creates an invitation record in the D1 database with a unique token, the invitee email address, the assigned role, the organization ID, the inviting admin's user ID, and a 7-day expiration timestamp

3. **[Better Auth]** fires the invitation email callback, passing the invitee's email address, the invitation token, the organization name, the assigned role, and the inviting admin's name to the application's `IEmailService` interface

4. **[IEmailService]** receives the callback parameters and determines the active transport based on the environment — in development the service logs the invitation details including the invitation link, invitee email, organization name, and role directly to the console terminal

5. **[IEmailService]** in production, resolves the locale from the admin's original request `Accept-Language` header and renders the invitation email HTML by invoking the template component with the organization name, assigned role, invitation token, and resolved locale

6. **[Template]** renders the email HTML using the shared `email-layout.tsx` for table-based structure compatible with email clients, displaying the organization name, the role being offered, and localized accept and decline action links that route to the web application with the invitation token embedded in the URL

7. **[IEmailService]** in production, delivers the rendered HTML email to the invitee through the configured transport provider (Resend, SES, or another provider implementing the `IEmailService` interface) and returns the delivery status to the callback

8. **[Invitee]** receives the email in their inbox, views the organization name and offered role, and clicks the accept or decline link which opens the web application at the invitation route with the token for processing

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | invitation_created | The org admin submits the invite member form and Better Auth validates the admin's permission and creates the invitation record in the D1 database with a unique token and 7-day expiration | The admin has the `invite_member` permission for the organization, the invitee email is not already a member, and the D1 database write completes without constraint violations |
| invitation_created | callback_fired | Better Auth fires the invitation email callback with the invitee email, invitation token, organization name, assigned role, and admin name after the invitation record is persisted in the database | The invitation record exists in the database with a valid token and the callback receives all required parameters including the invitee email and invitation token |
| callback_fired | email_logged_to_console | The `IEmailService` receives the callback parameters and the current environment is development, so the service logs the invitation link, invitee email, organization name, and role to the console | The environment configuration indicates development mode and the console logging operation completes without errors writing the invitation details to the terminal |
| callback_fired | email_rendered | The `IEmailService` receives the callback parameters and the current environment is production, so the service resolves the locale and invokes the invitation template to render the email HTML | The environment is production, the locale is resolved from the admin's `Accept-Language` header, and the template renders without throwing a runtime error during HTML generation |
| email_rendered | email_delivered | The `IEmailService` sends the rendered HTML email to the invitee through the configured production transport provider and receives a delivery confirmation response from the provider | The transport provider accepts the email and returns a delivery confirmation containing a non-empty message ID indicating the email was accepted for delivery to the invitee |
| email_rendered | email_delivery_failed | The `IEmailService` attempts to send the rendered HTML email through the production transport provider but the provider returns an error response or the delivery request times out | The transport provider returns an HTTP error status code or the delivery request exceeds the configured timeout threshold and the service catches the delivery failure |

## Business Rules

- **Rule invitation-expires-in-seven-days:** IF Better Auth creates an invitation record THEN the expiration timestamp is set to exactly 7 days (604800 seconds) from the creation time — the count of seconds from creation to expiration equals 604800
- **Rule invitation-persisted-before-email:** IF the invitation email callback is fired THEN the invitation record with the token, email, role, and expiration already exists in the D1 database — the count of invitation records for the token at callback time equals 1
- **Rule development-logs-to-console:** IF the environment is development THEN the `IEmailService` logs the invitation link, invitee email, organization name, and role to the console terminal without invoking a production transport — the count of production email API calls in development equals 0
- **Rule production-uses-pluggable-transport:** IF the environment is production THEN the `IEmailService` delivers the invitation email through the configured transport provider — the count of console-only invitation deliveries in production equals 0
- **Rule locale-from-admin-request:** IF the invitation email is rendered in production THEN the locale is resolved from the admin's original request `Accept-Language` header at the time the invitation was triggered — the locale used for rendering matches the primary locale from the admin's request header
- **Rule email-includes-org-name-and-role:** IF the invitation email is rendered THEN the email body contains the organization name and the role being offered to the invitee — the count of invitation emails missing the organization name or role equals 0
- **Rule email-includes-accept-decline-links:** IF the invitation email is rendered THEN the email body contains distinct accept and decline action links that route to the web application with the invitation token — the count of action links in the email body equals 2

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| System (the server-side application components including Better Auth, `IEmailService`, email templates, and the Hono API that collectively create the invitation record, render the email, and deliver it to the invitee through the configured transport) | Create the invitation record in the D1 database with a unique token and 7-day expiration; fire the email callback; resolve the locale from the admin's `Accept-Language` header; render the email template; deliver the email through the configured transport; log invitation details to console in development | Cannot modify the invitation token or expiration after the record is persisted, cannot send the email before the invitation record is written to the database, cannot bypass the environment check that determines console logging versus production transport | The system has visibility into the invitation token, invitee email, organization details, assigned role, admin identity, resolved locale, and transport delivery status — the system does not expose the invitation token in any API response other than the admin-facing invitation list |
| Org Admin (the organization administrator who initiates the invitation by submitting the invite member form with the invitee's email address and the role to assign, triggering the system to create the invitation and send the email) | Submit the invite member form with the invitee's email and role; view the invitation status in the organization's invitation list; cancel the invitation before it is accepted or before it expires; re-send the invitation email by triggering a new invitation | Cannot modify the invitation token or expiration timestamp after creation, cannot change the invitee's email address on an existing invitation record, cannot send invitations to users who are already members of the organization, cannot bypass the permission check for the invite action | The admin sees the invitation status (pending, accepted, declined, expired) in the organization member management UI — the admin does not see the email delivery logs, transport provider responses, or the internal invitation token value used in the email link |

## Constraints

- The invitation record is stored with an expiration timestamp exactly 604800 seconds (7 days) from creation time — the count of seconds from record creation to expiration equals 604800.
- The email template rendering completes within 500 ms of the `IEmailService` receiving the callback parameters — the count of milliseconds from callback receipt to rendered HTML output equals 500 or fewer.
- The production email transport delivery completes within 5000 ms of the rendered HTML being passed to the provider API — the count of milliseconds from transport send to provider response equals 5000 or fewer.
- The invitation email HTML body size is 50 KB or less after rendering — the count of kilobytes in the rendered email HTML string equals 50 or fewer.
- The invitation link URL embedded in the email is 2048 characters or fewer including the token parameter — the count of characters in the invitation link URL equals 2048 or fewer.
- All user-facing text in the invitation email uses @repo/i18n `email` namespace translation keys with zero hardcoded English strings — the count of hardcoded strings in the rendered email equals 0.

## Acceptance Criteria

- [ ] Better Auth creates an invitation record with a unique token and 7-day expiration when the admin submits the invite form — the invitation record is present in the database with an expiration offset of 604800 seconds
- [ ] The invitation record is persisted to the D1 database before the email callback fires — the count of invitation records for the token in the database equals 1 when the callback execution begins
- [ ] In development the `IEmailService` logs the invitation link, invitee email, organization name, and role to the console — the console output contains all four values and the count of production API calls equals 0
- [ ] In production the email HTML is rendered from the invitation template using the shared `email-layout.tsx` — the count of `<table>` elements in the rendered HTML equals 1 or more confirming table-based layout
- [ ] The email subject and body are localized via @repo/i18n `email` namespace using the locale from the admin's `Accept-Language` header — the count of hardcoded English strings in the rendered email equals 0
- [ ] The rendered email body contains the organization name and the role being offered to the invitee — both values are present in the email HTML content
- [ ] The rendered email contains accept and decline action links routing to the web application with the invitation token — the count of action links in the email equals 2 and both contain the token
- [ ] The production transport delivers the email through the configured provider and returns a delivery confirmation — the transport response contains a non-empty message ID
- [ ] The email template rendering completes within 500 ms of callback receipt — the count of milliseconds from callback to rendered output equals 500 or fewer
- [ ] The invitation link URL in the email is 2048 characters or fewer — the count of characters in the link URL equals 2048 or fewer
- [ ] Swapping the production transport provider requires zero changes to the calling code — the count of modified files outside the transport module equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The admin invites an email address that already has a pending unexpired invitation for the same organization, creating a duplicate invitation request for the same invitee and organization pair | Better Auth detects the existing pending invitation and either rejects the duplicate with an error indicating a pending invitation exists for this email, or replaces the existing invitation with a new token and resets the 7-day expiration window depending on the configured duplicate handling strategy | The admin receives a response indicating the duplicate state and the count of active invitation records for the same email and organization pair equals 1 after the operation |
| The admin triggers the invitation while their browser sends an `Accept-Language` header with a locale that has no translations in the @repo/i18n `email` namespace, such as an unsupported language variant | The i18n framework falls back to the English default translations for all invitation email content including the subject line, greeting, organization name label, role description, and action button text — the email is delivered in English as the fallback | The rendered email contains English text for all translation keys and the count of blank or missing text placeholders in the email equals 0 |
| The invitee's email server is temporarily unavailable and the transport provider accepts the email but cannot deliver it, resulting in a delayed delivery or bounce after the initial acceptance by the provider | The `IEmailService` receives a delivery confirmation from the transport provider because the provider accepted the email for delivery — the bounce or delayed delivery notification arrives asynchronously through the provider's webhook and is outside the scope of the immediate send flow | The transport provider returns a non-empty message ID and the immediate send operation completes without error despite the eventual delivery failure at the destination server |
| The admin invites a user whose email address is already an existing member of the organization, attempting to send an invitation to someone who already has membership access | Better Auth validates the invitee email against the current organization membership list and rejects the invitation with an error indicating the user is already a member — the invitation record is not created and the email callback is not fired | The admin receives an error response indicating the email belongs to an existing member and the count of new invitation records created equals 0 |
| The production email transport provider is experiencing an outage and returns HTTP 503 for all delivery requests when the `IEmailService` attempts to send the invitation email | The `IEmailService` catches the HTTP 503 response from the provider, logs the service unavailable error with the response details, and returns a delivery failure to the callback — the invitation record remains in the database with a pending status but the email is not delivered | The delivery failure log contains the HTTP 503 status and the invitation record status in the database remains pending because the email was not delivered |

## Failure Modes

- **D1 database write fails when Better Auth attempts to create the invitation record with the unique token, assigned role, and expiration timestamp**
    - **What happens:** Better Auth validates the admin's permissions and attempts to write the invitation record to the D1 database, but the write fails because the D1 instance is unreachable, the table has a constraint violation (such as a unique index on email and organization), or the write exceeds a storage limit.
    - **Source:** A Cloudflare D1 regional outage, a database migration that introduced a new constraint conflicting with the invitation data, or the database storage quota is exhausted preventing new rows from being written.
    - **Consequence:** The invitation record is not persisted and the email callback is never fired — the invitee does not receive the invitation email and the admin sees an error response indicating the invitation could not be created.
    - **Recovery:** Better Auth returns an HTTP 500 error to the admin's client and the admin form displays a localized error message — the admin retries the invitation and the system logs the D1 write failure for the operations team to investigate and resolve.

- **Production email transport provider rejects the delivery request or returns an API error when the `IEmailService` attempts to send the rendered invitation email**
    - **What happens:** The `IEmailService` renders the invitation email HTML and sends it to the configured transport provider, but the provider returns an API error such as HTTP 400 (invalid recipient), HTTP 429 (rate limited), or HTTP 503 (service unavailable) and the email is not accepted for delivery.
    - **Source:** The transport provider's API is experiencing an outage, the API credentials are expired, the sender domain is not verified with the provider, or the provider is rate-limiting requests from the account due to high send volume.
    - **Consequence:** The invitation email is not delivered to the invitee's inbox and the invitee has no way to access the invitation link — the invitation record exists in the database with a valid token but the invitee cannot act on it without receiving the email.
    - **Recovery:** The `IEmailService` logs the transport error with the provider response details and returns an error to the callback — the admin retries by re-sending the invitation which triggers a new email delivery attempt through the transport provider.

- **Invitation email template rendering fails due to a runtime error in the template component or the shared `email-layout.tsx` dependency during HTML generation**
    - **What happens:** The `IEmailService` invokes the invitation template component to render the email HTML, but the component throws a runtime error because a required prop such as the organization name is undefined, the shared `email-layout.tsx` import path is broken, or a translation key resolution throws an exception during rendering.
    - **Source:** A code change to the email template introduced a prop validation error, the shared layout component was refactored and its export name changed, or the i18n `email` namespace fails to initialize for the resolved locale causing translation key lookups to throw.
    - **Consequence:** The email HTML is not rendered and the `IEmailService` cannot deliver the invitation email — the invitee does not receive the invitation and the invitation record remains in the database with a pending status that the invitee cannot act on.
    - **Recovery:** The `IEmailService` catches the template rendering error, logs the error stack trace and the input parameters, and returns an error to the callback — the admin retries the invitation and the development team alerts on the rendering failure to deploy a fix.

## Declared Omissions

- This specification does not define the invitation acceptance or decline flow that executes when the invitee clicks the accept or decline link in the email — those behaviors are covered by the user-accepts-an-invitation and user-declines-an-invitation specifications
- This specification does not cover the admin's invitation management UI including the invitation list, status tracking, cancellation, or re-send functionality — those interactions are covered by the org-admin-invites-a-member and org-admin-cancels-an-invitation specifications
- This specification does not define the `IEmailService` interface contract, method signatures, or transport provider implementation details — the interface is an application architecture concern referenced here for behavioral context
- This specification does not address email deliverability, spam filtering, DKIM signing, or SPF record configuration that affects whether the invitation email reaches the invitee's inbox versus their spam folder
- This specification does not cover the invitation expiration enforcement logic that rejects invitation tokens after the 7-day window — that validation is part of the invitation acceptance flow specification

## Related Specifications

- [org-admin-invites-a-member](org-admin-invites-a-member.md) — defines
    the admin-side invitation flow including the invite form submission,
    permission validation, and invitation list management that triggers
    the system to create the invitation record and send this email
- [user-accepts-an-invitation](user-accepts-an-invitation.md) — defines
    the invitee-side acceptance flow that executes when the recipient
    clicks the accept link in the invitation email delivered by this
    specification's send flow
- [user-declines-an-invitation](user-declines-an-invitation.md) — defines
    the invitee-side decline flow that executes when the recipient clicks
    the decline link in the invitation email delivered by this
    specification's send flow
- [system-sends-otp-email](system-sends-otp-email.md) — defines the
    OTP verification email send flow that uses the same `IEmailService`
    interface and shared `email-layout.tsx` template structure as the
    invitation email but delivers a verification code instead of an
    invitation link
- [user-changes-language](user-changes-language.md) — defines the
    language preference mechanism that determines the admin's locale
    used for resolving @repo/i18n translation keys in the invitation
    email subject line and body content
