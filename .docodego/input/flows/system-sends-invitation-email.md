# System Sends Invitation Email

## Trigger

When an organization admin invites a new member, Better Auth creates an invitation record with a 7-day expiration window and fires the email callback. The callback receives the invitee's email address, the invitation token, and organization details needed to compose the message.

## Email Delivery

The invitation email is processed through the same `IEmailService` interface used by OTP emails. In development, the email content — including the invitation link — is logged to the console for easy testing. In production, the email is delivered through whichever transport is configured (Resend, SES, or another provider). The email contains a link the recipient can follow to accept or reject the invitation. This link routes to the web application where the user is presented with the accept/reject decision.

## Template and Localization

The email HTML is built from its template within `src/email/templates/` and uses the shared `email-layout.tsx` for consistent table-based HTML structure across all email types. Subject and body text are localized using the i18n `email` namespace, with the locale determined by the request's `Accept-Language` header at the time the admin triggered the invitation. The invitation email includes the organization name, the role being offered, and clear calls to action for accepting or declining.
