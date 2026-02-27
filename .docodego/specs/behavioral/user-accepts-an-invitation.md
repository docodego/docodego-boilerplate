---
id: SPEC-2026-033
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [Invitee, User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Accepts an Invitation

## Intent

This spec defines the full invitation acceptance flow for an invitee who has
received an email containing an invitation link to join an organization. The link
carries an invitation token that the application uses to identify and validate the
invitation. The flow branches based on whether the invitee already has an account:
authenticated users and existing-account holders confirm acceptance through a
localized acceptance screen by calling `authClient.organization.acceptInvitation()`,
which validates the token, confirms the invitation has not expired (invitations are
valid for exactly 7 days), and adds the user to the organization with the role
assigned by the inviting admin. Invitees without accounts are routed through the
email-OTP sign-in flow first, after which acceptance completes automatically and
the user arrives at the organization dashboard as a new member. Invitations can also
be rejected by calling `authClient.organization.rejectInvitation()`, which moves
the invitation to the History tab with a "rejected" status badge displayed in red.
Admins can cancel pending invitations before the invitee acts, and all unacted
invitations expire automatically after 7 days and become permanently invalid.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth organization plugin (`acceptInvitation`) | write | Invitee clicks the confirm button on the acceptance screen — the client calls `authClient.organization.acceptInvitation()` with the invitation token to validate and apply the membership | The server returns HTTP 500 and the client falls back to displaying a localized error message on the acceptance screen, leaving the invitation in the `pending` state so the invitee can retry once the auth service recovers |
| Better Auth organization plugin (`rejectInvitation`) | write | Invitee clicks the reject button on the acceptance screen — the client calls `authClient.organization.rejectInvitation()` with the invitation token to mark the invitation as rejected | The server returns HTTP 500 and the client falls back to displaying a localized error message, leaving the invitation in the `pending` state so the invitee can retry the rejection once the auth service recovers |
| `invitation` table (D1) | read/write | Server reads the invitation record to validate the token, check expiry against the 7-day window, and verify the status is `pending` before writing the new status (`accepted` or `rejected`) | The database read fails with HTTP 500 and the server rejects the acceptance request — the client notifies the user with a localized error and the invitation status remains unchanged in the database |
| `member` table (D1) | write | Server inserts a new `member` row for the invitee linking them to the organization with the role specified in the invitation record upon successful acceptance | The member row insertion fails, the server returns HTTP 500, and the client falls back to showing a localized error — no membership is created and the invitation status is not updated to `accepted` |
| Email delivery system | write | Invitation email is sent to the invitee's email address when an admin creates the invitation — the email carries the invitation link with the embedded token | Email delivery failure prevents the invitee from receiving the link — the admin retries sending the invitation from the Pending tab and the system logs the delivery failure for audit purposes |
| Email OTP sign-in flow (`user-signs-in-with-email-otp.md`) | delegate | The invitation link is clicked by an invitee who does not have an account — the application redirects them through the sign-in/sign-up flow before resuming acceptance | The sign-in flow is unavailable and the invitee cannot create an account — the client returns an error page and the invitation remains in the `pending` state until the invitee retries after the sign-in flow recovers |
| Astro client-side router | write | After a successful acceptance or automatic post-sign-up acceptance, the client navigates the user to the organization dashboard at `/app/$orgSlug/` | Navigation falls back to a full page reload via `window.location.assign` if the client router is unavailable, producing the correct destination URL without a client-side transition animation |
| OS notification system (desktop) | write | The desktop app detects the invitation event and sends an OS-native notification to the user's operating system so the user can accept from the desktop app | The OS notification API is unavailable and the desktop app logs the failure — the invitee can still accept through the web app via the email link without interruption |
| `@repo/i18n` | read | All acceptance screen text, button labels, status badge text, and error messages in the invitation UI are rendered via i18n translation keys for all supported locales | Translation function falls back to the default English locale strings so the acceptance screen remains fully functional and all interactive elements remain visible for non-English users |

## Behavioral Flow

1. **[Invitee]** receives an email containing a link to join the organization — the
    link points to the application and carries the invitation token as a URL parameter
    that the application reads to identify the specific invitation record

2. **[Branch — invitee is already signed in or has an existing account]** The
    application resolves the invitation token, confirms the invitation status equals
    `pending` and the invitation age is less than 7 days, and renders a localized
    acceptance screen presenting the organization name, the assigned role, and two
    action buttons: confirm and reject

3. **[User]** reviews the acceptance screen and clicks the confirm button to accept
    the invitation and join the organization with the role specified by the admin

4. **[Client]** disables the confirm button, displays a loading indicator, and calls
    `authClient.organization.acceptInvitation()` with the invitation token to initiate
    the server-side acceptance

5. **[Server]** receives the acceptance request, reads the `invitation` row to validate
    the token, confirms the status equals `pending`, confirms the invitation age is
    less than 7 days from the creation timestamp, and verifies the invitee's email
    matches the invitation's target email address

6. **[Server]** inserts a new `member` row linking the invitee to the organization
    with the role specified in the invitation record, updates the invitation status
    to `accepted`, and returns HTTP 200

7. **[Client]** receives the HTTP 200 response and navigates the user to the
    organization dashboard at `/app/$orgSlug/` where the user can immediately begin
    working within the organization as a member with the assigned role

8. **[Branch — invitee does not have an account]** The invitation link directs the
    invitee through the sign-in flow defined in `user-signs-in-with-email-otp.md` so
    they can create an account and sign in before acceptance proceeds

9. **[Client]** stores the invitation token so it is available after the sign-in flow
    completes, then redirects the invitee to the email-OTP sign-in/sign-up flow with
    the invitation token as a context parameter

10. **[Invitee]** completes the email-OTP sign-in flow, creating an account if one
    does not exist, and is authenticated with a valid session at the end of the flow

11. **[Client]** resumes the invitation acceptance automatically by calling
    `authClient.organization.acceptInvitation()` with the stored token — no additional
    confirmation screen is presented because the invitee's intent was established when
    they clicked the invitation link

12. **[Server]** validates the token, creates the `member` row, updates the invitation
    status to `accepted`, and returns HTTP 200

13. **[Client]** navigates the new user to the organization dashboard at `/app/$orgSlug/`
    where they arrive as a new member with the assigned role and 0 prior organization
    resources visible from before joining

14. **[Branch — invitee chooses to reject]** The invitee clicks the reject button on
    the acceptance screen, which calls `authClient.organization.rejectInvitation()` with
    the invitation token

15. **[Server]** validates the token, confirms the invitation status equals `pending`,
    updates the invitation status to `rejected`, and returns HTTP 200 — no `member` row
    is created and the invitee is not added to the organization

16. **[Client]** confirms the rejection with a localized message — the invitation moves
    to the History tab on the members page with a "rejected" status displayed as a red
    badge, and the invitation cannot be accepted later from this state

17. **[Branch — admin cancels the invitation]** From the Pending tab on the members
    page, an admin clicks the cancel action for a pending invitation before the invitee
    has acted on it — the server updates the invitation status to `canceled` and the
    invitation moves to the History tab with a "canceled" status badge

18. **[Branch — invitation expires without action]** If neither the invitee nor the
    admin takes action within 7 days of the invitation creation timestamp, the
    invitation status transitions to `expired` and the token becomes permanently invalid
    — subsequent acceptance attempts using the token return a rejection from the server
    and the admin must create a fresh invitation

19. **[Branch — desktop acceptance via OS notification]** The desktop app detects the
    invitation event and sends an OS-native notification to the user's operating system
    — clicking the notification brings the desktop app to the foreground and navigates
    to the invitation acceptance page, allowing the user to confirm or reject directly
    from the desktop app without opening the email or browser

20. **[Branch — desktop acceptance via email link]** The invitee clicks the invitation
    link in their email client on a device running the desktop app — the link opens in
    the browser because invitation emails contain standard HTTP URLs, and the user
    completes acceptance through the web app while the desktop app receives the
    membership update on its next data fetch

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| invitation_sent | acceptance_screen | Invitee clicks the email link and the application resolves the token | Invitation status equals `pending` and invitation age is less than 7 days |
| acceptance_screen | accepting | Invitee clicks the confirm button | Confirm button is enabled and invitation status equals `pending` |
| acceptance_screen | rejecting | Invitee clicks the reject button | Reject button is enabled and invitation status equals `pending` |
| invitation_sent | sign_in_flow | Invitee clicks the email link but has no account | Invitation status equals `pending` and no authenticated session exists for the invitee's email |
| sign_in_flow | auto_accepting | Invitee completes email-OTP sign-in or sign-up successfully | Session is authenticated and the stored invitation token is non-empty |
| accepting | accepted | Server returns HTTP 200 with membership created | `member` row inserted and invitation status equals `accepted` |
| auto_accepting | accepted | Server returns HTTP 200 after automatic post-sign-up acceptance | `member` row inserted and invitation status equals `accepted` |
| accepted | org_dashboard | Client navigates to the organization dashboard | User's `member` row exists for the organization and the org slug is non-empty |
| accepting | acceptance_error | Server returns non-200 response | HTTP status does not equal 200 or request times out |
| rejecting | rejected | Server returns HTTP 200 after rejection | Invitation status updated to `rejected` and no `member` row inserted |
| acceptance_error | acceptance_screen | Client re-enables the confirm button after displaying the error | Error message is visible and invitation status still equals `pending` |
| pending | canceled | Admin cancels the invitation from the Pending tab | Admin role is verified and invitation status equals `pending` |
| pending | expired | 7 days elapse since invitation creation without action | Current timestamp minus invitation creation timestamp is greater than or equal to 7 days |

## Business Rules

- **Rule token-validation:** IF the invitee submits an acceptance request THEN the
    server reads the `invitation` row matching the token AND confirms the status equals
    `pending` before proceeding — requests with tokens that resolve to any other status
    (`accepted`, `rejected`, `canceled`, `expired`) return HTTP 400 and the membership
    is not created
- **Rule expiry-7-days:** IF the invitation creation timestamp plus 7 days is less
    than or equal to the current timestamp THEN the server rejects the acceptance
    request with HTTP 400, updates the status to `expired`, and the admin must create
    a fresh invitation because the expired one cannot be reactivated
- **Rule email-match:** IF the invitee submits an acceptance request THEN the server
    confirms the authenticated session's email address equals the `email` field on the
    invitation record AND rejects the request with HTTP 403 if the values do not match,
    preventing a different user from accepting an invitation intended for another address
- **Rule no-reaccept-after-rejection:** IF the invitation status equals `rejected`,
    `canceled`, or `expired` THEN the server rejects any acceptance or rejection
    request with HTTP 400 and the admin must send a new invitation because the
    terminal-state invitation record cannot be reactivated under any condition
- **Rule automatic-acceptance-post-signup:** IF the invitee completes the sign-in
    flow triggered by an invitation link THEN the client calls
    `authClient.organization.acceptInvitation()` automatically with the stored token
    after the session is established, without requiring the invitee to navigate back
    to the acceptance screen and click confirm a second time
- **Rule rejected-status-badge:** IF the invitation status equals `rejected` THEN the
    invitation moves to the History tab on the members page and a red badge displaying
    the text "rejected" is rendered — the count of acceptance buttons visible for a
    rejected invitation equals 0 because rejected invitations cannot be acted upon
- **Rule admin-cancel-pending-only:** IF the admin initiates a cancellation THEN the
    server confirms the invitation status equals `pending` before applying the change
    AND rejects the cancellation with HTTP 400 if the invitation is in any other state,
    ensuring admins cannot cancel invitations that have already been acted on

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Invitee (authenticated, existing account) | View the acceptance screen with organization name and assigned role, click confirm to call `authClient.organization.acceptInvitation()`, click reject to call `authClient.organization.rejectInvitation()` | Accepting an invitation addressed to a different email address — the server rejects the request with HTTP 403 when the session email does not match the invitation email | Acceptance screen is visible after clicking the email link; the confirm and reject buttons are both present and enabled for an invitation with status `pending` |
| Invitee (no existing account) | Click the invitation link to trigger the sign-in flow, complete email-OTP sign-up, and receive automatic invitation acceptance after the session is established | Bypassing the sign-in flow to call `authClient.organization.acceptInvitation()` without a valid session — the endpoint returns HTTP 401 for unauthenticated requests | Sign-in and sign-up screens are visible; the invitation acceptance screen is not shown because acceptance completes automatically after sign-in without a separate confirmation step |
| Organization Admin | View the Pending tab on the members page listing all outstanding invitations, cancel any pending invitation before the invitee acts, and view the History tab showing accepted, rejected, canceled, and expired invitations with their status badges | Accepting an invitation on behalf of the invitee — acceptance can only be performed by the invitee using their own authenticated session matching the invitation email | Pending tab and History tab on the members page are visible and interactive; cancel buttons are present for each pending invitation row |
| Organization Owner | All actions available to Organization Admin plus organization-level settings management and the ability to transfer or delete the organization — owner can cancel pending invitations and view the full invitation history | Accepting invitations addressed to other users — same restriction applies as for admins | Pending and History tabs are visible; all administrative controls including cancel buttons are present for each pending invitation |
| Unauthenticated visitor | Click the invitation link in their email, which redirects them to the sign-in flow because no session exists — the invitation token is preserved during the redirect so acceptance can complete after sign-in | Accessing the acceptance screen content before signing in — the acceptance page redirects to `/signin` and renders no organization or role information until a session is established | Acceptance screen content is not rendered; only the sign-in redirect is visible before authentication |

## Constraints

- The invitation token is valid for exactly 7 days from the creation timestamp —
    the count of successful acceptances for invitations older than 7 days equals 0
    because the server rejects them with HTTP 400
- The server validates that the authenticated user's email equals the invitation's
    target email before accepting — the count of successful cross-email acceptances
    equals 0 because the server enforces the match with HTTP 403
- Each invitation can be accepted exactly once — the count of `member` rows created
    per invitation equals 1 because the server rejects subsequent acceptance attempts
    against a non-`pending` invitation with HTTP 400
- Rejected invitations cannot be accepted — the count of accepted invitations whose
    previous status was `rejected` equals 0 because the server enforces terminal state
    transitions
- Canceled invitations cannot be accepted — the count of successful acceptances
    for invitations with status `canceled` equals 0 because the server reads the status
    before inserting the member row and returns HTTP 400 for non-pending invitations
- The "rejected" status badge on the History tab is rendered using the red color
    variant — the count of rejected-status badges rendered with a non-red color equals 0
- All UI text including status badges, button labels, and error messages is rendered
    via i18n translation keys — the count of hardcoded English string literals in the
    invitation acceptance UI components equals 0

## Acceptance Criteria

- [ ] Clicking the invitation link for a `pending` invitation with an authenticated session renders the acceptance screen — the acceptance screen element is present in the DOM and its count equals 1 within 500ms of navigation
- [ ] The acceptance screen displays the organization name and the role assigned by the admin — the organization name element and role label element are both present and non-empty
- [ ] Clicking the confirm button calls `authClient.organization.acceptInvitation()` with the invitation token — the method invocation count equals 1 after the confirm button click
- [ ] The confirm button displays a loading indicator and its `disabled` attribute is present while the acceptance request is in flight — the disabled attribute is present within 100ms of the confirm click
- [ ] A successful acceptance returns HTTP 200 and a new `member` row is inserted for the invitee in the target organization — the response status equals 200 and the member row count for the invitee in the organization equals 1
- [ ] After a successful acceptance the client navigates to the organization dashboard — the window location pathname equals `/app/$orgSlug/` within 1000ms of receiving the HTTP 200 response
- [ ] An acceptance request for an invitation older than 7 days returns HTTP 400 — the response status equals 400 and the member row count for the invitee in the organization equals 0
- [ ] An acceptance request where the session email does not match the invitation email returns HTTP 403 — the response status equals 403 and the member row count for the invitee in the organization equals 0
- [ ] Clicking the reject button calls `authClient.organization.rejectInvitation()` with the invitation token — the method invocation count equals 1 after the reject button click
- [ ] A successful rejection returns HTTP 200 and the invitation status in the database equals `rejected` — the response status equals 200 and no member row is inserted for the invitee
- [ ] The rejected invitation appears on the History tab with a red "rejected" status badge — the badge element is present in the History tab DOM and the badge color class matches the red variant
- [ ] The confirm and reject buttons are absent for a rejected invitation — the count of accept and reject button elements in the DOM for a rejected invitation equals 0
- [ ] An invitee without an account who clicks the invitation link is redirected to the email-OTP sign-in flow — the window location pathname changes to the sign-in route within 500ms of clicking the link
- [ ] After completing sign-in, acceptance calls `authClient.organization.acceptInvitation()` automatically without a separate confirm click — the method invocation count equals 1 within 2000ms of the session being established
- [ ] After automatic post-sign-up acceptance, the client navigates to the organization dashboard — the window location pathname equals `/app/$orgSlug/` within 1000ms of the session being established
- [ ] An acceptance request using an expired invitation token returns HTTP 400 — the response status equals 400 and the member row count for the invitee equals 0
- [ ] An acceptance request using a canceled invitation token returns HTTP 400 — the response status equals 400 and the member row count for the invitee equals 0
- [ ] The admin cancel action on the Pending tab updates the invitation status to `canceled` — the invitation status in the database equals `canceled` and the invitation count in the Pending tab decreases by 1
- [ ] All acceptance screen text is rendered via i18n translation keys — the count of hardcoded English string literals in the acceptance UI components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Invitee clicks the confirm button twice in rapid succession before the first acceptance request completes | The confirm button is disabled on the first click, preventing a duplicate acceptance request — the server receives exactly 1 `acceptInvitation` call and the member row count for the invitee equals 1 after both clicks resolve | The disabled attribute is present on the confirm button within 100ms of the first click and the network log count of outbound `acceptInvitation` requests equals 1 |
| Invitee clicks the invitation link after an admin has already canceled the invitation from the Pending tab | The server reads the invitation status as `canceled` and returns HTTP 400 — the acceptance screen displays a localized error stating the invitation is no longer valid and the member row count for the invitee equals 0 | The HTTP response status equals 400 and the error element is present in the DOM with no member row existing in the database for the invitee in that organization |
| Two users with different email addresses both attempt to accept the same invitation token simultaneously | The server validates the session email against the invitation email for each request — the request from the user whose email matches the invitation is processed and the other request returns HTTP 403 with no member row created for the non-matching user | The HTTP response status equals 403 for the non-matching user and the member row count in the organization equals 1 total after both requests complete |
| Invitee completes sign-in but loses network connectivity before the automatic acceptance call completes | The acceptance request times out on the client — the client retries the automatic acceptance with the stored token once connectivity is restored and the session is still valid | The error element is present after the timeout, the invitation status remains `pending` in the database, and the client retries the acceptance once connectivity returns |
| Invitee clicks the invitation link on the desktop app on the same device as the OS notification | The invitation link opens in the browser because email links contain standard HTTP URLs — the desktop app and browser both display the correct organization dashboard after acceptance, and the desktop app reflects membership on its next data fetch | The window location in the browser equals `/app/$orgSlug/` after acceptance and the desktop app member count for the organization equals 1 on the next data fetch |
| Admin sends a new invitation to the same email address after the previous invitation expired | The new invitation generates a fresh token with a new 7-day expiry window — the old expired token remains invalid and the new token is the only valid path to acceptance for that email address | The old token returns HTTP 400 and the new token returns HTTP 200 on acceptance, with exactly 1 member row created for the invitee in the organization |
| Invitee accepts the invitation when they are already a member of the same organization | The server detects the duplicate membership attempt and returns HTTP 400 because a `member` row for the invitee in the organization already exists — the invitation status is not updated to `accepted` because the precondition is not met | The HTTP response status equals 400 and the member row count for the invitee in the organization remains 1 with no duplicate row inserted |

## Failure Modes

- **Invitation token validation fails due to a transient D1 database error during the status check**
    - **What happens:** The client calls `authClient.organization.acceptInvitation()` and the server's SELECT query against the `invitation` table fails due to a transient Cloudflare D1 error or Worker timeout, preventing the server from reading the invitation status or expiry timestamp and leaving the membership uncreated.
    - **Source:** Transient Cloudflare D1 database failure or network interruption between the Worker process and the D1 binding during the SELECT operation that reads the invitation record to validate the token and status.
    - **Consequence:** The server cannot confirm the invitation is `pending` and unexpired, so the acceptance cannot proceed — the invitee sees an error response and remains outside the organization with no `member` row created and the invitation status unchanged.
    - **Recovery:** The server returns HTTP 500 and logs the D1 error with the query context — the client falls back to re-enabling the confirm button and displaying a localized error message on the acceptance screen so the invitee can retry once the D1 service recovers from the transient failure.
- **Member row insertion fails after invitation status validation passes, leaving invitation in an inconsistent state**
    - **What happens:** The server validates the invitation token successfully (status is `pending`, age is less than 7 days, emails match) and proceeds to insert the `member` row, but the INSERT operation against the `member` table fails due to a database constraint violation or transient D1 error, leaving the invitation status as `pending` while no membership is created.
    - **Source:** Transient D1 write failure or a database constraint violation such as a unique constraint on the member-organization pair that prevents the row insertion from completing after the validation step has already passed.
    - **Consequence:** The invitee receives an error response and is not added to the organization — they can retry acceptance and the invitation remains in the `pending` state because the status update to `accepted` is only written after the `member` row insertion succeeds.
    - **Recovery:** The server rolls back the invitation status update when the `member` row insertion fails, returns HTTP 500, and logs the error with the user ID and invitation ID — the client notifies the invitee with a localized error and re-enables the confirm button so they can retry the acceptance once the database recovers.
- **Stored invitation token is lost during the sign-in redirect, preventing automatic post-sign-up acceptance**
    - **What happens:** An invitee without an account clicks the invitation link and the client stores the invitation token before redirecting to the sign-in flow, but the token is lost during the redirect due to a client-side session storage failure or navigation that clears the stored state — after sign-in completes, the automatic acceptance cannot proceed because the token is no longer available.
    - **Source:** Client-side storage failure where the invitation token stored before the sign-in redirect is not available after the redirect completes, caused by a browser private-browsing restriction, storage quota exceeded, or a navigation event that resets the client state store.
    - **Consequence:** The invitee completes sign-in and arrives at the application without being added to the organization — they see their own dashboard or onboarding page instead of the invited organization's dashboard, and they must click the original invitation link again to restart the acceptance flow.
    - **Recovery:** The client falls back to redirecting the invitee to the acceptance screen with the invitation URL parameters intact after sign-in, so the token can be read from the URL instead of client storage — if the token cannot be recovered from either source, the acceptance screen alerts the invitee to click the original email link again to retry.
- **Expired invitation link is clicked after the 7-day window has elapsed**
    - **What happens:** The invitee clicks the invitation link more than 7 days after the admin sent it — the server reads the invitation creation timestamp, computes that the current timestamp minus the creation timestamp is greater than or equal to 7 days, and rejects the acceptance request because the invitation is no longer valid.
    - **Source:** User inaction where the invitee does not click the invitation link within the 7-day validity window, causing the invitation token to become permanently invalid regardless of the invitation's current status in the database.
    - **Consequence:** The invitee sees an error on the acceptance screen stating the invitation has expired — no `member` row is created and the invitee cannot join the organization using this token because expired invitations cannot be reactivated.
    - **Recovery:** The server returns HTTP 400 with an expiry error code and logs the expired acceptance attempt with the invitation ID and invitee email — the acceptance screen notifies the invitee that the link has expired and instructs them to contact the organization admin, who must send a fresh invitation through the admin members panel.

## Declared Omissions

- This specification does not address how an admin creates and sends an invitation — that behavior is defined in `org-admin-invites-a-member.md` covering the invitation creation form, role selection, and email dispatch steps for the admin-initiated invitation flow
- This specification does not address rate limiting on the `acceptInvitation` and `rejectInvitation` endpoints — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly across the API
- This specification does not address what content or permissions the new member gains access to upon joining — that behavior is governed by the organization role definitions in `org-roles-and-permissions.md` covering the specific resource access granted to each role level
- This specification does not address how the admin promotes a member to a different role after they have joined via invitation — that behavior is defined in `org-admin-manages-member-roles.md` covering role assignment and demotion flows for existing members
- This specification does not address the full email-OTP account creation sub-flow that the invitee without an account passes through — that behavior is defined in `user-signs-in-with-email-otp.md` and is referenced here as a delegated flow only at the entry and re-entry points
- This specification does not address re-joining an organization after voluntarily leaving — the departed user must receive a new invitation processed through this flow, and the admin's responsibility to send that invitation is covered in `org-admin-invites-a-member.md`

## Related Specifications

- [org-admin-invites-a-member](org-admin-invites-a-member.md) — Admin-initiated counterpart to this spec covering the invitation creation form, role assignment, email dispatch, and Pending tab management that produces the invitation this spec processes
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) — Email OTP sign-in and account creation flow that invitees without existing accounts pass through before automatic invitation acceptance completes and they join the organization
- [user-leaves-an-organization](user-leaves-an-organization.md) — Voluntary departure flow for members who joined via invitation and later choose to remove themselves from the organization, requiring a new invitation to rejoin
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that provides the `acceptInvitation` and `rejectInvitation` endpoints, token validation logic, and the 7-day expiry enforcement
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `invitation` and `member` tables read and written during token validation, status transitions, and membership creation steps in this flow
- [api-framework](../foundation/api-framework.md) — Hono middleware stack and global error handler that wraps the invitation endpoints and returns consistent JSON error shapes for HTTP 400, 403, and 500 responses consumed by the acceptance screen
