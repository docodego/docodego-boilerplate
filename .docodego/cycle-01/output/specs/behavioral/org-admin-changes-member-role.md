---
id: SPEC-2026-036
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [Org Admin, Org Owner]
---

[← Back to Roadmap](../ROADMAP.md)

# Org Admin Changes a Member's Role

## Intent

This spec defines the flow by which an organization admin or owner changes
an existing member's role from the Members tab on the `/app/$orgSlug/members`
page. Each member row displays the member's current role alongside a control
for selecting a different role. The available org-level roles are Member and
Admin, displayed with localized labels and configurable through the
organization's role settings. These are distinct from the app-level
`user.role`. The organization owner row shows the "Owner" label with no
role-change control because the owner role is immutable and cannot be
reassigned through this flow. After the admin selects a new role, the client
calls `authClient.organization.updateRole()` with the member's ID and the
new role value. The role change takes effect immediately on the server side
with no delay or propagation period. The next request the affected member
makes is evaluated against their new permissions. On the admin's side, the
UI refreshes on the next data fetch to reflect the updated role in the
members list.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| oRPC mutation endpoint (`updateRole`) | write | Admin selects a new role for a member and the client calls the endpoint with the member's ID and the new role value to update the member's role on the server | The server returns HTTP 500 and the client displays a localized error message inline near the role control, leaving the member's role unchanged so the admin retries the role change once the endpoint recovers |
| `member` table (D1) | read/write | Server reads the `member` table to verify the target member exists and their current role differs from the requested role, then writes the updated role value to the member's row in the database | The database read or write fails with HTTP 500 and the server returns an error to the client without modifying any record — the client alerts the admin with a localized error so the member's role remains at its previous value until the database recovers |
| Better Auth organization plugin | read/write | Validates the calling user holds the `admin` or `owner` role before processing the role update, and writes the new role value to the target member's row in the `member` table after authorization passes | The server rejects the request with HTTP 403 if the role check fails, logs the unauthorized attempt with the user ID and timestamp, and returns an error to the client without modifying the target member's role in the database |
| `@repo/i18n` | read | All role labels, control text, success messages, and error messages displayed in the members list and the role-change control are rendered via i18n translation keys at component mount time | Translation function falls back to the default English locale strings so the members list and role controls remain fully functional and readable when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[User]** (organization admin or owner) navigates to
    `/app/$orgSlug/members` and sees the Members tab displaying all current
    organization members, with each member row showing the member's name,
    email, and current role alongside a role-change control

2. **[Client]** renders each member row with the current role value from
    `member.role` and a role-change control offering the available options
    (Member and Admin), except for the organization owner row which displays
    the "Owner" label with no role-change control because the owner role is
    immutable and cannot be reassigned

3. **[User]** locates the target member whose role they want to change and
    selects a new role from the available options in that member's row — the
    available roles are Member and Admin, displayed with localized labels

4. **[Client]** calls `authClient.organization.updateRole()` with the target
    member's ID and the new role value, disabling the role-change control for
    that member row and displaying a loading indicator while the request is
    in flight

5. **[Server]** verifies the calling user holds the `admin` or `owner` role
    in the target organization, then reads the target member's current role
    from the `member` table to confirm the member exists and the requested
    role differs from the current value

6. **[Branch — same role selected]** If the requested role equals the
    member's current role in the `member` table, the server returns a
    response indicating no change was needed — the client re-enables the
    role-change control without displaying an error or success indicator

7. **[Server]** updates the target member's `role` field in the `member`
    table to the new value, which takes effect immediately — the next
    request the affected member makes is evaluated against their new
    permissions with no delay or propagation period

8. **[Server]** returns HTTP 200 confirming the role change was applied
    successfully and the member's access level is updated in real time

9. **[Client]** re-enables the role-change control for the target member
    row, updates the displayed role value to reflect the new assignment,
    and the UI refreshes on the next data fetch to reflect the updated
    role in the members list

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| members_list_idle | role_selecting | Admin opens the role-change control on a non-owner member row | Calling user's role in the `member` table equals `admin` or `owner` and the target member's role is not `owner` |
| role_selecting | members_list_idle | Admin closes the role-change control without selecting a different role | No new role value was selected or the selected value equals the current role |
| role_selecting | role_updating | Admin selects a new role value that differs from the current role | Selected role value is non-empty and does not equal the target member's current `member.role` value |
| role_updating | role_update_success | Server returns HTTP 200 confirming the role change | Target member's `role` field in the `member` table is updated to the new value |
| role_updating | role_update_error | Server returns a non-200 error code or the request times out | Database write fails or authorization check fails and the target member's role remains unchanged |
| role_update_success | members_list_idle | Client re-enables the role-change control and displays the updated role | The role-change control shows the new role value and the loading indicator is absent |
| role_update_error | members_list_idle | Admin dismisses the error and the role-change control returns to the previous value | Error message is visible and the control reverts to the member's original role value |

## Business Rules

- **Rule role-gate:** IF the authenticated user's role in the organization
    is not `admin` or `owner` THEN the `updateRole` endpoint rejects the
    request with HTTP 403 AND the server logs the unauthorized attempt with
    the user ID and timestamp before returning the error response
- **Rule owner-immutability:** IF the target member's current role in the
    `member` table equals `owner` THEN the server rejects the role change
    with HTTP 400 AND no modification is made to the owner's `member` row
    because the owner role is immutable and cannot be changed through this
    endpoint
- **Rule valid-roles-only:** IF the requested role value is not `member` or
    `admin` THEN the server rejects the request with HTTP 400 AND the count
    of role updates with an invalid role value written to the `member` table
    equals 0
- **Rule no-self-role-change:** IF the target member's ID equals the calling
    user's ID THEN the server rejects the request with HTTP 400 AND the
    calling user's role remains unchanged because admins and owners cannot
    modify their own role through this endpoint
- **Rule immediate-effect:** IF the server returns HTTP 200 for the role
    update THEN the target member's permissions change immediately AND the
    next API request from the affected member is evaluated against the new
    role with zero delay or propagation period
- **Rule ui-refresh:** IF the role update succeeds THEN the admin's members
    list refreshes on the next data fetch to display the updated role value
    AND the role-change control shows the new role for the affected member

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View the members list with role-change controls on all non-owner member rows, select a new role for any member or admin, and confirm the role change to update the target member's permissions immediately | Changing their own role through this endpoint because the owner row has no role-change control, and the server rejects self-role-change requests with HTTP 400 | Role-change controls are visible on all non-owner member rows; the owner's own row displays the "Owner" label with no role-change control rendered |
| Admin | View the members list with role-change controls on all non-owner and non-self member rows, select a new role for any regular member, and confirm the role change to update the target member's permissions | Changing their own role through this endpoint because the server rejects self-role-change requests with HTTP 400, and changing the owner's role because the owner row has no control | Role-change controls are visible on non-owner non-self member rows; the admin's own row and the owner row show labels without role-change controls |
| Member | View the members list showing all organization members with their current roles displayed as read-only labels without any interactive role-change controls | Changing any member's role because role-change controls are absent from the DOM for member-role users and the server rejects `updateRole` calls with HTTP 403 | All member rows display role labels as static text; the count of role-change control elements in the DOM equals 0 for member-role users |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the members page component renders any content or data | Accessing `/app/$orgSlug/members` or calling the `updateRole` endpoint without a valid authenticated session token | The members page is not rendered; the redirect to `/signin` occurs before any members list UI elements are mounted or visible |

## Constraints

- The `updateRole` mutation endpoint enforces the `admin` or `owner` role
    server-side by reading the calling user's role from the `member` table
    — the count of successful role changes initiated by `member`-role users
    equals 0
- The role-change control lists all roles returned by `listRoles()` for the
    organization (Member and Admin plus any custom roles) — the option count
    equals the organization's active role count and the count of role updates
    written with an invalid role value equals 0
- The owner's member row does not render a role-change control — the count
    of role-change control elements on the owner row equals 0 because the
    owner role is immutable through this flow
- The server rejects self-role-change requests where the target member ID
    equals the calling user's ID with HTTP 400 — the count of successful
    self-role-change operations equals 0
- The role change takes effect immediately on the server side with no delay
    — the elapsed time between the server writing the role update and the
    affected member's next request being evaluated against the new role
    equals 0 milliseconds of propagation delay
- All role labels, control text, and error messages in the members list are
    rendered via i18n translation keys — the count of hardcoded English
    string literals in the members list component equals 0

## Acceptance Criteria

- [ ] Each non-owner member row in the members list displays a role-change control — the role-change control element count per non-owner row equals 1
- [ ] The owner's member row displays the "Owner" label with no role-change control — the role-change control element count on the owner row equals 0
- [ ] The role-change control lists all roles from `listRoles()` for the organization — the option count equals the organization's active role count and equals at least 2
- [ ] Selecting a new role for a member calls `authClient.organization.updateRole()` with the member's ID and new role — the method invocation count equals 1 and the payload member ID is non-empty
- [ ] A successful role change returns HTTP 200 and the member's role in the `member` table equals the new value — the response status equals 200 and the role field is non-empty
- [ ] After a successful role change the role-change control displays the updated role value — the displayed role text equals the new role value and the loading indicator is absent
- [ ] The role change takes effect immediately — the affected member's next API request is evaluated against the new role with propagation delay equals 0
- [ ] A `member`-role user has no role-change controls in the DOM — the count of role-change control elements visible to a member-role user equals 0
- [ ] A direct `updateRole` call from a `member`-role user returns HTTP 403 — the response status equals 403 and the target member's role in the database remains unchanged
- [ ] A self-role-change request where the target member ID equals the calling user's ID returns HTTP 400 — the response status equals 400 and the calling user's role is unchanged
- [ ] An `updateRole` call targeting the organization owner returns HTTP 400 — the response status equals 400 and the owner's role in the `member` table remains `owner`
- [ ] The role-change control is disabled and shows a loading indicator while the `updateRole` request is in flight — the disabled attribute is present on the control during the request
- [ ] All role labels and error messages are rendered via i18n translation keys — the count of hardcoded English string literals in the members list component equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Admin selects a new role for a member but the member is removed from the organization by another admin before the server processes the update | The server detects that the target member ID no longer exists in the `member` table and returns HTTP 400 — the client displays a localized error message and the members list refreshes to exclude the removed member from the displayed rows | HTTP response status equals 400 and the members list row count decreases by 1 after the list refreshes to reflect the removal |
| Admin selects the same role value that the member already holds in the `member` table | The server detects that the requested role equals the current role and returns a response indicating no change was needed — the client re-enables the role-change control without triggering a write operation to the database | The `member` table row version or updated-at timestamp remains unchanged and the role-change control returns to its idle state without an error message |
| Two admins attempt to change the same member's role simultaneously from different browser sessions | The server processes both requests sequentially at the database level — the second write overwrites the first, and each admin's UI reflects the final role value after the next data fetch completes | Both requests return HTTP 200 and the member's final role in the `member` table equals the value from the last processed request |
| Admin changes a member from Admin to Member, removing their admin privileges while that member has the members page open | The demoted member's current page session still shows admin-level controls until the next data fetch — after the page refreshes, the role-change controls disappear because the member's role in the `member` table now equals `member` | After the data refetch the role-change control element count in the demoted member's DOM equals 0 and their session role equals `member` |
| Admin opens the role-change control but navigates away from the members page before selecting a new role value | No `updateRole` request is sent because the admin did not select a new role — the member's role in the `member` table remains at its current value and the navigation proceeds normally | The network request count to the `updateRole` endpoint equals 0 and the member's role in the database is unchanged after the navigation |
| Admin changes a member's role while the server is under high load causing the response to arrive after a 5-second delay | The role-change control remains disabled with a loading indicator during the entire wait period — the admin cannot interact with the control until the response arrives and the UI updates | The disabled attribute is present on the role-change control for the duration of the request and the loading indicator is visible until HTTP 200 is received |

## Failure Modes

- **Database write fails when updating the target member's role in the member table**
    - **What happens:** The admin selects a new role and the client sends the
        `updateRole` request, but the D1 database write fails due to a transient
        storage error before the role value is committed to the `member` table,
        leaving the target member's role at its original value.
    - **Source:** Transient Cloudflare D1 database failure or network interruption
        between the Worker and the D1 binding during the single-row update operation
        that writes the new role value to the target member's record.
    - **Consequence:** The role change does not take effect and the target member
        continues operating with their original permissions, while the admin sees an
        error in the UI where the role-change control was used and the database row
        remains unmodified.
    - **Recovery:** The server returns HTTP 500 and the client displays a localized
        error message near the role-change control — the admin retries the role
        change once the D1 database recovers and the control is re-enabled for
        another selection attempt.
- **Non-admin user bypasses the client guard and calls the updateRole endpoint directly**
    - **What happens:** A user with the `member` role crafts a direct HTTP request
        to the `updateRole` mutation endpoint using a valid session cookie, bypassing
        the client-side UI that hides role-change controls from non-admin members,
        and attempts to change another member's role without authorization.
    - **Source:** Adversarial or accidental action where a member sends a
        hand-crafted HTTP request to the mutation endpoint with a valid session
        token, circumventing the client-side visibility guard that conditionally
        renders role-change controls only for admin and owner members.
    - **Consequence:** Without server-side enforcement any member could escalate
        another member's privileges or demote admins without authorization, breaking
        the organization's role hierarchy and potentially granting unauthorized
        access to admin-level features.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after
        verifying the calling user's role in the `member` table — the server logs
        the unauthorized attempt with the user ID, organization ID, and timestamp,
        and no role change is written to the target member's database row.
- **Admin attempts to change the owner's role by sending a crafted request with the owner's member ID**
    - **What happens:** An admin constructs a direct HTTP request to the `updateRole`
        endpoint with the organization owner's member ID as the target, attempting to
        demote the owner to a non-owner role even though the client UI does not render
        a role-change control on the owner's member row.
    - **Source:** Adversarial action where an admin extracts the owner's member ID
        from the page data and includes it in a hand-crafted `updateRole` request,
        bypassing the client-side guard that omits the role-change control from the
        owner's row in the members list.
    - **Consequence:** Without server-side enforcement an admin could strip the owner
        of their ownership privileges, leaving the organization without an owner and
        breaking all owner-gated operations including billing, deletion, and future
        ownership transfers.
    - **Recovery:** The server rejects the request with HTTP 400 after checking that
        the target member's current role equals `owner` — the server logs the attempt
        with the calling user's ID and the target member's ID, and the owner's role
        in the `member` table remains unchanged at `owner`.
- **updateRole mutation request times out before the server responds to the client**
    - **What happens:** The admin selects a new role and the `updateRole` request is
        dispatched but the Cloudflare Worker takes longer than the client timeout
        threshold to respond, causing the client to receive a timeout error without
        knowing whether the role change was written to the database.
    - **Source:** Cloudflare Worker cold start latency combined with a D1 write
        exceeding the client-configured request timeout window, leaving the outcome
        of the role update unknown to the client because the server either completed
        or failed the write operation before the timeout elapsed.
    - **Consequence:** The admin sees a timeout error on the role-change control
        without knowing whether the role was actually changed — the member either
        retains the old permissions or has new permissions depending on whether the
        server completed the write before the timeout elapsed on the client side.
    - **Recovery:** The client falls back to re-enabling the role-change control
        and displaying a localized timeout error — the admin refreshes the members
        list to check the member's current role value and retries the role change
        if the displayed role does not match the intended value.

## Declared Omissions

- This specification does not address transferring organization ownership to another
    member — that behavior is defined in `user-transfers-organization-ownership.md` as a
    separate concern covering the atomic ownership handoff from the danger zone settings
- This specification does not address inviting new members to the organization — that
    behavior is defined in `org-admin-invites-a-member.md` as a separate concern covering
    the invitation dialog, email dispatch, and pending invitation management
- This specification does not address removing an existing member from the organization
    — that behavior is defined in `org-admin-removes-a-member.md` as a separate concern
    covering the removal confirmation dialog and member record deletion from the table
- This specification does not address rate limiting on the `updateRole` mutation endpoint
    — that behavior is enforced by the global rate limiter defined in `api-framework.md`
    covering all mutation endpoints uniformly across the API layer
- This specification does not address the creation or configuration of custom
    organization roles — that behavior is defined in `org-admin-manages-custom-roles.md`
    covering role creation, permission configuration, and deletion flows

## Related Specifications

- [org-admin-invites-a-member](org-admin-invites-a-member.md) — Invitation flow where the admin assigns an initial role (Member or Admin) to the invitee, which this spec's role-change flow can subsequently modify after the invitee joins
- [user-transfers-organization-ownership](user-transfers-organization-ownership.md) — Ownership transfer flow restricted to the owner role, which is the only mechanism for changing the owner assignment since this spec's role-change flow cannot modify the owner role
- [user-leaves-an-organization](user-leaves-an-organization.md) — Voluntary departure flow where a member removes themselves from the organization, which is distinct from having their role changed by an admin through this spec's flow
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that validates member roles and exposes the `updateRole` endpoint used by this spec's role-change flow
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `member` table containing the `role` field that this spec reads and writes during the role-change operation for organization members
- [shared-contracts](../foundation/shared-contracts.md) — oRPC contract definitions for the `updateRole` mutation including the Zod schema that validates the target member ID and new role value before the mutation reaches the database
