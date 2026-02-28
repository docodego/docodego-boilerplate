---
id: SPEC-2026-034
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [Invitee, User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Declines an Invitation

## Intent

This spec defines the invitation-decline flow for an invitee who receives an
email containing a tokenized link to join an organization. The invitee opens
the app via the link, views the localized acceptance screen showing the
organization name, logo, and offered role, then clicks the "Decline" button.
The client calls `authClient.organization.rejectInvitation()`, which marks the
invitation token as permanently rejected on the server. The invitee sees a
localized confirmation message, then navigates to their existing dashboard if
they belong to other organizations, or to the organization creation flow if
they have none. The declined invitation moves from the Pending tab to the
History tab on the admin's members page and displays a "rejected" badge with a
red accent color. The token is permanently invalidated — the admin must issue a
fresh invitation to re-invite the same person.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth organization plugin (`rejectInvitation`) | write | Client calls `authClient.organization.rejectInvitation()` after the invitee clicks the "Decline" button on the acceptance screen | The server returns HTTP 500 and the client falls back to displaying a localized error message on the acceptance screen while the invitation token remains in the pending state until the request succeeds |
| `invitation` table (D1) | read/write | Server reads the invitation record to validate the token and resolve the organization details, then updates the status to `rejected` upon a valid decline request | The database read or update fails, the server returns HTTP 500, and the client notifies the invitee with a localized error so the invitation token is not left in a partial or ambiguous state |
| `session` table (D1) | read | Server reads the active session to resolve the calling invitee's identity before marking the invitation as rejected and navigating away from the acceptance screen | The session lookup fails, the server returns HTTP 401, and the client redirects the invitee to `/signin` so they can re-authenticate before the decline request is retried |
| Astro client-side router | write | After a successful decline the client navigates the invitee to their existing organization dashboard or to the organization creation flow depending on remaining membership count | Navigation falls back to a full page reload via `window.location.assign` if the client router is unavailable, delivering the correct destination URL without a client-side transition |
| `@repo/i18n` | read | All acceptance screen text, button labels, confirmation messages, and error messages in the decline flow are rendered via i18n translation keys | Translation function falls back to default English locale strings so the acceptance screen remains functional but untranslated for non-English invitees during a localization service failure |

## Behavioral Flow

1. **[Invitee]** receives an email containing a tokenized link to join an
    organization — the link points to the application and carries the
    invitation token as a query parameter or path segment

2. **[Invitee]** clicks the link, which opens the application and triggers the
    client to call the server and resolve the invitation details — the server
    reads the `invitation` table and returns the organization name, logo URL,
    and the role being offered to the invitee

3. **[Branch — invitee is not yet signed in]** The client detects that no
    active session exists and redirects the invitee through the
    `user-signs-in-with-email-otp` flow, preserving the invitation token in
    state, and returns the invitee to the acceptance screen once authenticated

4. **[Client]** renders the localized acceptance screen displaying the
    organization name, the organization logo, the offered role name, a primary
    "Accept" button, and a secondary "Decline" button — all text is rendered
    via i18n translation keys

5. **[Invitee]** reads the acceptance screen and clicks the localized "Decline"
    button to reject the invitation without joining the organization

6. **[Client]** disables the "Decline" button, displays a loading indicator,
    and calls `authClient.organization.rejectInvitation()` with the invitation
    token to request rejection on the server

7. **[Server]** receives the rejection request, reads the calling invitee's
    session to resolve their identity, validates that the invitation token
    exists in the `invitation` table and its status equals `pending`, and
    confirms the token belongs to the authenticated invitee's email address

8. **[Branch — token is invalid or already consumed]** The server rejects the
    request with HTTP 422 because the token does not exist, has already been
    accepted, or was previously declined — the client displays a localized
    error message explaining the invitation link is no longer valid

9. **[Server]** updates the invitation record status from `pending` to
    `rejected`, records the timestamp of rejection, and permanently invalidates
    the token so it cannot be accepted or declined again by any subsequent
    request

10. **[Server]** returns HTTP 200 confirming the successful rejection and the
    client removes the loading indicator and re-enables navigation

11. **[Client]** displays a localized confirmation message confirming that the
    invitation has been declined, visible on the acceptance screen until the
    navigation redirect completes

12. **[Branch — invitee belongs to other organizations]** The client navigates
    the invitee to their existing organization dashboard at
    `/app/{existingOrgSlug}/` so the invitee lands on an active workspace
    immediately after declining

13. **[Branch — invitee has no other organizations]** The client navigates the
    invitee to the organization creation flow so they can create a new
    organization and establish their own workspace context

14. **[Admin view update]** On the organization members page, the invitation
    moves from the Pending tab to the History tab, displaying the invitee's
    email, the date of rejection, and a "rejected" badge rendered in a red
    accent color — the count of pending invitation entries for this token
    equals 0

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| email_received | link_clicked | Invitee clicks the tokenized link in the email | Invitation token is present in the URL |
| link_clicked | unauthenticated_redirect | Client detects no active session | Session cookie is absent or expired |
| unauthenticated_redirect | acceptance_screen | Sign-in flow completes and returns invitee to the acceptance screen | Session is valid and invitation token is preserved |
| link_clicked | acceptance_screen | Client resolves invitation details from the server | Invitee is authenticated and invitation token status equals `pending` |
| acceptance_screen | decline_pending | Invitee clicks the "Decline" button | "Decline" button is not already in a loading state |
| decline_pending | declined | Server returns HTTP 200 | Invitation record status updated to `rejected` |
| decline_pending | decline_error | Server returns non-200 | HTTP response status does not equal 200 or request times out |
| decline_error | acceptance_screen | Client re-enables the "Decline" button for retry | Server error was transient and the invitation token status still equals `pending` |
| declined | existing_org_dashboard | Client navigates to existing org | Invitee has at least 1 existing organization membership |
| declined | org_creation_flow | Client navigates to org creation | Invitee has 0 existing organization memberships |

## Business Rules

- **Rule token-permanence:** IF the invitee calls `rejectInvitation()` and the
    server returns HTTP 200 THEN the invitation token status equals `rejected`
    and no subsequent call with the same token returns HTTP 200 — the count of
    successful accepts or declines for a rejected token equals 0
- **Rule pending-only-decline:** IF the invitation token status does not equal
    `pending` THEN the server rejects the `rejectInvitation()` call with HTTP
    422 and returns a localized error message — the count of status transitions
    from `accepted` or `rejected` back to any other state equals 0
- **Rule identity-match:** IF the `rejectInvitation()` request is processed
    THEN the server confirms that the authenticated session's email address
    matches the `invitee_email` field on the invitation record — any mismatch
    causes the server to return HTTP 403 and the invitation status remains
    unchanged
- **Rule redirect-to-existing-org:** IF the decline succeeds AND the invitee's
    session contains at least 1 existing organization membership THEN the
    client navigates to the dashboard of an existing organization and the count
    of seconds spent on a blank or broken route equals 0
- **Rule redirect-to-creation:** IF the decline succeeds AND the invitee's
    session contains 0 existing organization memberships THEN the client
    navigates to the organization creation flow and the count of organization
    memberships the invitee holds equals 0 at the time of navigation
- **Rule history-tab-visibility:** IF the invitation status equals `rejected`
    THEN the admin's members page moves the entry from the Pending tab to the
    History tab and the count of entries in the Pending tab for that token
    equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Invitee (authenticated, matching email) | View the acceptance screen, read the organization name and offered role, click the "Decline" button, trigger `rejectInvitation()`, receive the confirmation message, and be redirected after a successful decline | Accepting the invitation via this flow — this spec covers decline only; acceptance is covered by `user-accepts-an-invitation.md` | Sees the acceptance screen with the organization name, logo, offered role, and both the "Accept" and "Decline" buttons for the duration of the flow |
| Invitee (unauthenticated) | Click the invitation link and initiate the sign-in flow — the sign-in flow preserves the invitation token and returns the invitee to the acceptance screen upon successful authentication | Viewing the acceptance screen without authenticating first — the route guard redirects to the sign-in flow before rendering the acceptance screen | Does not see the acceptance screen until authentication completes; sees 0 instances of the acceptance screen UI before sign-in |
| Org Admin | View the History tab on the members page after a successful decline, see the "rejected" badge and rejection timestamp, and issue a fresh invitation if needed | Reversing the declined status — a declined invitation cannot be re-activated; the admin must create a new invitation via the invite flow | Sees the declined invitation in the History tab with a red accent "rejected" badge and the invitee's email and rejection date |
| Unauthenticated visitor (no invitation link) | None — requests to the invitation acceptance route without a valid token return HTTP 422 | Accessing the acceptance screen without a valid invitation token in the URL | Invitation acceptance screen is not rendered; the server returns HTTP 422 before any UI is visible to the unauthenticated visitor |

## Constraints

- The `rejectInvitation()` call is only valid when the invitation token status
    equals `pending` — the count of successful `rejected` status transitions
    from a non-pending token equals 0 because the server validates status before
    any update is committed
- The invitation token is permanently invalidated after a successful decline —
    the count of subsequent `rejectInvitation()` or `acceptInvitation()` calls
    that return HTTP 200 for the same token equals 0
- The server validates that the authenticated session's email matches the
    invitation's `invitee_email` field — the count of successful declines where
    the session email does not match the invitation email equals 0
- After a successful decline the invitation entry count in the Pending tab for
    that token equals 0 and the entry count in the History tab for that token
    equals 1, with a "rejected" badge rendered in a red accent color
- The redirect destination after decline is determined from the invitee's
    session membership count at the time the HTTP 200 response is received —
    the count of seconds the client spends on a broken or missing route after
    the decline completes equals 0

## Acceptance Criteria

- [ ] The acceptance screen is present and renders the organization name — the organization name text element is present in the DOM and non-empty within 500ms of the invitation link being opened
- [ ] The acceptance screen displays the offered role name — the role text element is present in the DOM and non-empty within 500ms of the invitation details being resolved
- [ ] The acceptance screen presents a "Decline" button — the decline button element is present in the DOM and its count equals 1
- [ ] Clicking the "Decline" button disables the button immediately — the disabled attribute is present on the decline button within 100ms of the click event
- [ ] Clicking the "Decline" button calls `authClient.organization.rejectInvitation()` — the method invocation is present and the count of calls equals 1 after the decline button is clicked
- [ ] A successful decline returns HTTP 200 — the response status equals 200 and the invitation record status equals `rejected` in the database after the call
- [ ] The invitation token status equals `rejected` in the database after a successful decline — the row count of `pending` invitation entries for the token equals 0 after HTTP 200 is returned
- [ ] A localized confirmation message is displayed after a successful decline — the confirmation message element is present in the DOM and non-empty within 300ms of receiving the HTTP 200 response
- [ ] After decline when existing organizations exist, the window location pathname changes to an existing org dashboard — the pathname equals a valid existing org slug path and the count of acceptance screen elements in the DOM equals 0 after navigation
- [ ] After decline when the invitee has no organizations, the window location pathname equals `/app/create-organization` — the pathname equals `/app/create-organization` within 1000ms of receiving the HTTP 200 response
- [ ] An already-rejected token returns HTTP 422 on a second decline attempt — the response status equals 422 and the invitation status in the database remains `rejected` after the second request
- [ ] The admin's members page History tab shows the declined invitation entry count equals 1 for the token — the history tab entry count for the declined token equals 1 and the pending tab entry count equals 0
- [ ] The declined invitation entry in the History tab displays a "rejected" badge — the badge element is present in the DOM and its count equals 1 per declined invitation row
- [ ] An unauthenticated invitee clicking the invitation link is redirected to sign-in before the acceptance screen renders — the sign-in page element count in the DOM equals 1 and the acceptance screen element count equals 0 before authentication completes
- [ ] All acceptance screen text and button labels are rendered via i18n translation keys — the count of hardcoded English string literals in the acceptance screen components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Invitee clicks the "Decline" button twice in rapid succession before the first request completes | The decline button is disabled on the first click, preventing duplicate rejection requests — the server receives exactly 1 `rejectInvitation()` call and the network log count equals 1 | The disabled attribute is present on the decline button within 100ms of the first click and the count of outbound requests to `rejectInvitation()` equals 1 |
| Invitee opens the invitation link after the token has already been accepted by a previous action | The server returns HTTP 422 because the token status does not equal `pending` — the client displays a localized error message and the count of acceptance screen interactive elements equals 0 | The HTTP response status equals 422 and the error message element is present in the DOM and non-empty within 300ms of the token resolution request |
| Invitee loses network connectivity after clicking "Decline" but before the server responds | The decline request times out on the client — the acceptance screen remains visible with a loading state and a localized error message appears so the invitee can retry once connectivity is restored | The error message element is present in the acceptance screen after the request timeout and the invitation token status remains `pending` in the database |
| Invitee declines an invitation for an organization they are already a member of via a separate path | The server returns HTTP 422 because the token status does not equal `pending` or the invitee's membership already exists — the client displays a localized error and performs no duplicate membership changes | The HTTP response status equals 422 and the count of duplicate `member` rows for the invitee in the organization equals 0 after the request |
| Org admin views the members page at the exact moment the invitee completes the decline | The History tab updates to include the newly declined entry — the count of pending entries for the token equals 0 and the count of history entries for the token equals 1 when the admin's page refreshes after the decline completes | The pending tab row count for the token equals 0 and the history tab row count equals 1 after the admin's page performs its next data refresh |
| Invitee attempts to decline an invitation token belonging to a different invitee's email address | The server returns HTTP 403 because the authenticated session email does not match the invitation's `invitee_email` field — the count of status changes to the invitation record equals 0 | The HTTP response status equals 403 and the invitation status in the database remains `pending` after the mismatched decline request |

## Failure Modes

- **Rejection request fails due to a transient D1 database error during the status update**
    - **What happens:** The client calls `authClient.organization.rejectInvitation()` and the server's UPDATE query against the `invitation` table fails due to a transient Cloudflare D1 error or Worker timeout, leaving the invitation token in the `pending` state and the decline unregistered.
    - **Source:** Transient Cloudflare D1 database failure or network interruption between the Worker process and the D1 binding during the UPDATE operation that sets the invitation status to `rejected`.
    - **Consequence:** The invitee sees an error response after clicking "Decline" — the invitation token remains `pending` and the invitee remains eligible to accept or decline again after the error resolves.
    - **Recovery:** The server returns HTTP 500 and logs the D1 error with the query context and invitation token — the client falls back to re-enabling the "Decline" button and displaying a localized error message so the invitee can retry once the D1 service recovers.
- **Invitee attempts to decline using an expired or tampered invitation token**
    - **What happens:** The invitee opens an invitation link containing a token that has been tampered with, has expired due to a TTL policy, or references an invitation that no longer exists in the `invitation` table, causing the server to fail during token validation.
    - **Source:** Adversarial manipulation of the invitation URL query parameter, natural expiry of the invitation TTL, or a previously deleted invitation record that no longer exists in the D1 `invitation` table at the time of the decline request.
    - **Consequence:** Without proper validation the server could throw an unhandled exception or return confusing errors — the invitee would see a broken acceptance screen with no actionable path forward.
    - **Recovery:** The server rejects the request with HTTP 422 after failing to find a valid `pending` invitation record for the token — the client displays a localized message explaining the link is no longer valid and notifies the invitee to request a new invitation from the organization admin.
- **Client navigates to a broken route after decline because the redirect logic fails to read session memberships**
    - **What happens:** After the server returns HTTP 200 for the decline, the client-side redirect logic fails to read the invitee's existing organization memberships from the session, causing navigation to target an undefined or stale route instead of the correct existing org dashboard or the organization creation flow.
    - **Source:** A client-side state management gap where the session membership list has not yet loaded or a race condition where the session update from the server has not propagated to the client state store at the time the redirect logic executes after receiving HTTP 200.
    - **Consequence:** The invitee sees a 404 page or a blank dashboard after declining, unable to access any workspace without manually navigating to a known route or refreshing the browser to reload the updated session state.
    - **Recovery:** The decline success handler refetches the session membership list before computing the redirect target — if the refetch fails the client falls back to navigating to `/app/create-organization` unconditionally, which always resolves to a valid route regardless of the invitee's membership count.
- **Admin members page does not reflect the declined status because the D1 read replica is stale**
    - **What happens:** After the invitee's decline is recorded in the primary D1 database, the org admin refreshes the members page and the read query returns data from a stale replica that still lists the invitation as `pending` rather than `rejected`, showing an incorrect state in the Pending tab.
    - **Source:** Cloudflare D1 eventual consistency between the primary write node and read replicas causes a replication lag where the updated `rejected` status has not propagated to the replica serving the admin's read query at the time of the page refresh.
    - **Consequence:** The admin sees an incorrect `pending` entry for an invitation that has already been declined, potentially causing the admin to believe the invitee has not yet responded when they have already rejected the invitation.
    - **Recovery:** The members page query retries with the primary read endpoint if the returned invitation status does not match the expected post-decline state — the admin's page alerts the admin to refresh if the displayed status appears inconsistent, and the correct `rejected` status becomes visible once replication catches up within the D1 consistency window.

## Declared Omissions

- This specification does not address the invitation acceptance flow — that behavior is defined in `user-accepts-an-invitation.md` covering the primary action button and the membership creation that follows a successful acceptance
- This specification does not address the flow by which an org admin sends an initial invitation — that behavior is defined in a separate org-admin-invites-a-member spec covering the invitation creation, email dispatch, and token generation steps
- This specification does not address re-inviting a declined invitee — the admin must navigate to the invite flow defined in the org-admin-invites-a-member spec to generate a fresh token after a prior invitation has been declined
- This specification does not address the sign-in flow triggered when the invitee is unauthenticated — that behavior is fully defined in `user-signs-in-with-email-otp.md` which handles OTP delivery, code verification, and session creation
- This specification does not address invitation token TTL or expiry policies — expiry enforcement and the resulting HTTP 422 response are governed by the Better Auth organization plugin configuration defined in `auth-server-config.md`
- This specification does not address rate limiting on the `rejectInvitation()` endpoint — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly

## Related Specifications

- [user-accepts-an-invitation](user-accepts-an-invitation.md) — The acceptance counterpart to this spec covering the primary action on the same acceptance screen that creates the membership record and grants resource access
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) — The authentication flow triggered when an unauthenticated invitee clicks the invitation link before a session exists, preserving the invitation token throughout sign-in
- [user-creates-first-organization](user-creates-first-organization.md) — The organization creation flow the client redirects to when an invitee declines and holds zero existing organization memberships after the decline completes
- [user-creates-an-organization](user-creates-an-organization.md) — Alternative organization creation flow used when the invitee already has a session but no current organization membership after the decline is recorded
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that provides the `rejectInvitation()` endpoint, token validation logic, and the invitation status state machine
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `invitation` and `member` tables read and written during the decline flow and the admin's History tab query after rejection
