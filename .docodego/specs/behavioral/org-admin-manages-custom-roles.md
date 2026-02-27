---
id: SPEC-2026-039
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [Org Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# Org Admin Manages Custom Roles

## Intent

This spec defines the flow by which an organization admin creates, edits,
renames, and deletes custom roles from the Roles or Access Control section
within the organization settings page at `/app/$orgSlug/settings`. The page
lists all roles for the organization: the three default system roles (Owner,
Admin, Member) are displayed with localized labels and a visual indicator
marking them as immutable system roles that cannot be deleted or renamed.
Below the system roles, any previously created custom roles are listed with
their assigned permission sets. The admin can create a new custom role by
providing a unique name and selecting permissions from a checklist, edit an
existing custom role to rename it or adjust its permissions, or delete a
custom role which causes all members assigned to that role to fall back to
the default Member role. Custom roles appear alongside default roles in the
role dropdown when changing a member's role, and permission checks throughout
the application evaluate against the latest role definition via the
`hasPermission()` method with zero propagation delay.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Organization plugin `createRole()` method | write | Admin submits the create-role form with a unique role name and at least one selected permission from the checklist | The server returns HTTP 500 and the client displays a localized error message inside the create-role form, leaving no custom role record created and allowing the admin to retry once the endpoint recovers |
| Organization plugin `updateRole()` method | write | Admin saves changes to an existing custom role after renaming it or modifying its permission checklist selections in the detail view | The server returns HTTP 500 and the client displays a localized error message in the role detail view, leaving the existing role definition unchanged until the admin retries when the endpoint recovers |
| Organization plugin `deleteRole()` method | write | Admin confirms deletion of a custom role after acknowledging the confirmation dialog warning about member reassignment to the default Member role | The server returns HTTP 500 and the client displays a localized error message in the confirmation dialog, leaving the custom role and all member assignments unchanged until the admin retries when the endpoint recovers |
| Organization plugin `listRoles()` method | read | Settings page loads to populate the roles list with both default system roles and previously created custom roles including their permission sets and localized display names | The server returns HTTP 500 and the roles list fails to load — the client displays a localized error message on the settings page and the admin retries by refreshing the page when the endpoint recovers |
| `hasPermission()` permission check | read | Any permission-gated action across the application evaluates the member's assigned role against the latest role definition to determine whether the action is permitted or denied | The permission check falls back to denying the requested action and the server returns HTTP 403 to the client, logging the permission evaluation failure with the member ID, role ID, and requested action for audit purposes |
| `role` table (D1) | read/write | Server reads the role table to validate name uniqueness within the organization before writing a new custom role record, and writes updated permission sets during edit operations | The database operation fails with HTTP 500 and the server returns error to the client without writing any record — the client alerts the admin with a localized error so no partial role data is committed to the database |
| `@repo/i18n` | read | All page headings, form labels, button text, role name labels, permission checklist labels, confirmation dialog text, and error messages are rendered via i18n translation keys at component mount time | Translation function falls back to the default English locale strings so the roles management page remains fully functional even when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[User]** (organization admin) navigates to the "Roles" or "Access
    Control" section within the organization settings at
    `/app/$orgSlug/settings` and sees the roles list page displaying all
    roles for the organization

2. **[Client]** renders the roles list with the three default system roles
    (Owner, Admin, Member) at the top, each shown with localized labels and a
    visual indicator marking them as system roles that cannot be deleted or
    renamed; below them, any previously created custom roles are listed with
    their assigned permission sets

3. **[User]** clicks the localized "Create role" button to begin the custom
    role creation flow, which causes the create-role form to appear in the
    foreground

4. **[Client]** renders the create-role form containing a role name input
    field and a checklist of all available permissions that can be assigned
    to the new custom role, with all permissions unchecked by default

5. **[User]** enters a role name (such as "Viewer" or "Billing Manager")
    into the name field, selects the desired permissions from the checklist,
    and clicks the submit button to create the new custom role

6. **[Client]** calls the Organization plugin's `createRole()` method with
    the role name and the array of selected permission identifiers, disabling
    the submit button and displaying a loading indicator while the request is
    in flight

7. **[Server]** validates that the role name is unique within the organization
    by querying the `role` table — if a role with the same name already exists
    the server returns an error and the client displays a localized duplicate
    name error message in the create-role form

8. **[Branch — name is unique]** The server persists the new custom role
    record with the provided name and selected permissions to the `role`
    table and returns HTTP 200 confirming the creation was successful

9. **[Client]** closes the create-role form and refreshes the roles list so
    the new custom role appears immediately below the system roles with its
    name and assigned permission set visible to the admin

10. **[User]** clicks on an existing custom role in the roles list to expand
    or open its detail view for editing, which displays the current role name
    and the permission checklist with currently assigned permissions checked

11. **[User]** modifies the role name, adds or removes individual permissions
    from the checklist, and clicks the save button to persist the changes to
    the custom role definition

12. **[Client]** calls `updateRole()` with the role ID and the updated fields
    including the new name and the modified permission set, disabling the save
    button and displaying a loading indicator while the request is in flight

13. **[Server]** validates the updated role name for uniqueness within the
    organization (excluding the role being edited) and persists the changes
    — the updated permissions take effect immediately so that any member
    assigned to this role gains or loses access on their next request

14. **[Client]** refreshes the role detail view and the roles list to reflect
    the updated name and permission set; the `hasPermission()` check evaluates
    against the latest role definition so there is no propagation delay

15. **[User]** clicks the localized "Delete" action on a custom role, which
    opens a localized confirmation dialog warning that all members currently
    assigned to this role will fall back to the default Member role

16. **[Branch — default role]** Default system roles (Owner, Admin, Member)
    do not display a delete action — the delete button element count for
    system roles equals 0 because they are protected from deletion

17. **[User]** confirms the deletion by clicking the confirm button in the
    localized confirmation dialog to proceed with removing the custom role

18. **[Client]** calls `deleteRole()` with the role ID, disabling the confirm
    button and displaying a loading indicator while the request is in flight

19. **[Server]** reassigns all members currently assigned to the deleted
    custom role to the default Member role, removes the custom role record
    from the `role` table, and returns HTTP 200 confirming the deletion

20. **[Client]** closes the confirmation dialog and refreshes the roles list
    to reflect the deletion — the removed custom role no longer appears and
    the member list shows the reassigned members with the Member role

21. **[User]** navigates to the member role dropdown when changing a member's
    role assignment and sees custom roles listed alongside the default roles
    — the `listRoles()` method returns both default and custom roles with
    localized display names for use throughout the organization management UI

22. **[Server]** evaluates permission checks across the application using
    `hasPermission()` against the member's assigned role, whether default or
    custom, consulting the latest role definition from the `role` table on
    each check with zero propagation delay

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| roles_list_idle | create_form_open | Admin clicks the "Create role" button on the roles list page | Calling user's role in the `member` table equals `admin` or `owner` |
| create_form_open | create_form_filled | Admin enters a non-empty role name and selects at least one permission | Role name field value is non-empty and permission checklist selection count is greater than 0 |
| create_form_filled | create_form_open | Admin clears the role name field or deselects all permissions | Role name field value is empty or permission checklist selection count equals 0 |
| create_form_filled | create_submitting | Admin clicks the submit button to create the custom role | Role name field value is non-empty and permission checklist selection count is greater than 0 |
| create_submitting | create_success | Server returns HTTP 200 with the custom role record created | Role record is written to the `role` table with the provided name and permissions |
| create_submitting | create_error_duplicate | Server returns an error indicating the role name already exists | A role with the same name and organizationId already exists in the `role` table |
| create_submitting | create_error_server | Server returns HTTP 500 or a non-200 error code | Database write fails during custom role record creation |
| create_error_duplicate | create_form_filled | Admin dismisses the error and modifies the role name field | Error message is visible and the name field is re-enabled for editing |
| create_error_server | create_form_filled | Admin dismisses the error and the form returns to the filled state | Error message is visible and the submit button is re-enabled for retry |
| create_success | roles_list_idle | Client closes the form and the roles list refreshes with the new entry | Create-role form element count in the DOM equals 0 and the new role appears in the list |
| roles_list_idle | role_detail_open | Admin clicks on an existing custom role to open its detail view | The clicked role is a custom role and not a system default role |
| role_detail_open | edit_submitting | Admin modifies the name or permissions and clicks the save button | At least one field has changed from its original value in the role detail view |
| edit_submitting | edit_success | Server returns HTTP 200 with the updated role record persisted | Updated role record is written to the `role` table with the modified fields |
| edit_submitting | edit_error_duplicate | Server returns an error indicating the new name conflicts with an existing role | A different role with the same name and organizationId already exists in the `role` table |
| edit_submitting | edit_error_server | Server returns HTTP 500 or a non-200 error code | Database write fails during custom role update operation |
| edit_error_duplicate | role_detail_open | Admin dismisses the error and modifies the role name field | Error message is visible and the name field is re-enabled for editing |
| edit_error_server | role_detail_open | Admin dismisses the error and the detail view returns to the editable state | Error message is visible and the save button is re-enabled for retry |
| edit_success | roles_list_idle | Client refreshes the roles list and the detail view reflects the updated data | Updated role name and permissions are visible in the roles list |
| roles_list_idle | delete_confirm_open | Admin clicks the "Delete" action on a custom role | The target role is a custom role and the delete action element is present for custom roles only |
| delete_confirm_open | delete_submitting | Admin clicks the confirm button in the deletion confirmation dialog | Confirmation dialog is visible and the confirm button is enabled |
| delete_confirm_open | roles_list_idle | Admin clicks cancel or dismisses the confirmation dialog without confirming | Confirmation dialog is dismissed and the custom role record remains unchanged |
| delete_submitting | delete_success | Server returns HTTP 200 after reassigning members and removing the custom role | Custom role record is deleted from the `role` table and affected members are reassigned to Member |
| delete_submitting | delete_error_server | Server returns HTTP 500 or a non-200 error code | Database write fails during custom role deletion or member reassignment |
| delete_error_server | delete_confirm_open | Admin dismisses the error and the confirmation dialog returns to the actionable state | Error message is visible and the confirm button is re-enabled for retry |
| delete_success | roles_list_idle | Client closes the confirmation dialog and the roles list refreshes without the deleted role | Confirmation dialog element count in the DOM equals 0 and the deleted role is absent from the list |

## Business Rules

- **Rule name-uniqueness:** IF the admin submits a create-role or update-role
    request AND a role with the same name already exists in the `role` table
    for the same organizationId THEN the server returns an error to the client
    AND no new role record is written or updated — the admin must choose a
    different name that does not collide with any existing role in the organization
- **Rule system-role-immutability:** IF the target role is a default system
    role (Owner, Admin, or Member) THEN the delete action, rename action, and
    permission edit controls are not rendered in the UI AND any direct API call
    to `updateRole()` or `deleteRole()` for a system role returns HTTP 400 with
    a localized error indicating that system roles cannot be modified or deleted
- **Rule delete-fallback-to-member:** IF a custom role is deleted THEN all
    members currently assigned to that role are reassigned to the default Member
    role before the custom role record is removed from the `role` table — the
    count of members with an orphaned role ID after deletion equals 0
- **Rule permission-immediate-effect:** IF a custom role's permissions are
    updated via `updateRole()` THEN the `hasPermission()` check evaluates
    against the latest role definition on the next request — there is no
    propagation delay and the updated permissions take effect immediately for
    all members assigned to that custom role
- **Rule role-dropdown-inclusion:** IF the admin opens the role dropdown when
    changing a member's role assignment THEN the `listRoles()` method returns
    both default system roles and custom roles with localized display names —
    the count of roles in the dropdown equals the sum of system roles (3) plus
    the count of custom roles for the organization
- **Rule permission-gate:** IF the authenticated user's role in the organization
    is not `admin` and not `owner` THEN the "Create role" button, edit controls,
    and delete actions are not rendered in the UI AND any direct API call to
    `createRole()`, `updateRole()`, or `deleteRole()` returns HTTP 403 with a
    localized error indicating insufficient permissions for role management

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View the roles list with system and custom roles, click "Create role" to create a new custom role with a name and permissions, edit or rename any custom role, delete any custom role with member reassignment to Member role | Deleting, renaming, or modifying permissions of the three default system roles (Owner, Admin, Member) — these actions return HTTP 400 from the server | All role management controls are visible: "Create role" button, edit action on custom roles, delete action on custom roles; system roles show a read-only indicator |
| Admin | View the roles list with system and custom roles, click "Create role" to create a new custom role with a name and permissions, edit or rename any custom role, delete any custom role with member reassignment to Member role | Deleting, renaming, or modifying permissions of the three default system roles (Owner, Admin, Member) — the server rejects these mutations with HTTP 400 | All role management controls are visible: "Create role" button, edit action on custom roles, delete action on custom roles; system roles show a read-only indicator |
| Member | View the roles list in read-only mode showing system and custom roles with their permission sets displayed as non-interactive labels without management controls | Creating, editing, renaming, or deleting any role — the "Create role" button is absent and any direct API call returns HTTP 403 from the server | The "Create role" button is absent from the DOM; edit and delete actions on custom roles are absent; the roles list is visible in read-only mode only |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the organization settings page renders any role management content | Accessing `/app/$orgSlug/settings` or calling any role management endpoint without a valid authenticated session — all requests are redirected or rejected | The settings page is not rendered; the redirect to `/signin` occurs before any roles list or management UI is mounted or visible |

## Constraints

- The custom role name must be unique within the organization — the count of
    role records in the `role` table sharing the same name and organizationId
    combination equals exactly 1, enforced by the server's uniqueness validation
    before any write operation completes
- The three default system roles (Owner, Admin, Member) cannot be deleted,
    renamed, or have their permissions modified — the count of successful
    `updateRole()` or `deleteRole()` operations targeting a system role equals 0
    because the server returns HTTP 400 for all modification attempts
- After a custom role is deleted, the count of members with an orphaned or
    invalid role assignment equals 0 — the server reassigns all affected members
    to the default Member role within the same database transaction as the role
    record deletion
- The `hasPermission()` check evaluates against the latest role definition stored
    in the `role` table on every invocation — the count of permission decisions
    based on stale or cached role definitions equals 0 because the check reads
    the current state on each request
- All page headings, form labels, button text, permission checklist labels,
    confirmation dialog text, and error messages are rendered via i18n translation
    keys — the count of hardcoded English string literals in the role management
    UI components equals 0
- The "Create role" button and all edit and delete actions on custom roles are
    absent from the DOM for users with the `member` role — the count of role
    management control elements rendered for non-admin users equals 0

## Acceptance Criteria

- [ ] Navigating to the roles section at `/app/$orgSlug/settings` renders the three default system roles (Owner, Admin, Member) with localized labels — the system role element count equals 3
- [ ] Each default system role displays a visual indicator marking it as a system role — the system role indicator element count equals 3 and each indicator is present
- [ ] The default system roles do not display delete or rename actions — the delete button count for system roles equals 0 and the rename control count equals 0
- [ ] Previously created custom roles appear below the system roles with their assigned permission sets visible — the custom role list element count equals the number of custom roles stored in the database
- [ ] Clicking the "Create role" button opens the create-role form — the form element is present and visible within 200ms of the click event
- [ ] The create-role form contains a role name input field and a permission checklist — the input field count equals 1 and the permission checkbox count is greater than 0
- [ ] Submitting a role name that already exists within the organization returns an error — the error element is present in the form and the role record count for that name remains 1
- [ ] Submitting a unique role name with at least one permission selected creates the custom role and returns HTTP 200 — the response status equals 200 and the new role record exists in the `role` table
- [ ] After successful creation the roles list refreshes and the new custom role is present — the custom role element for the new name is present and non-empty in the roles list
- [ ] Clicking on an existing custom role opens its detail view with the current name and checked permissions — the detail view element is present and the permission checkbox checked count equals the stored permission count
- [ ] Saving an edited custom role with a modified name and permissions calls `updateRole()` and returns HTTP 200 — the response status equals 200 and the updated record exists in the `role` table
- [ ] Updated permissions take effect immediately — calling `hasPermission()` after the update returns true for newly added permissions and false for removed permissions
- [ ] Clicking the delete action on a custom role opens a localized confirmation dialog — the dialog element is present and the warning text about member reassignment is non-empty
- [ ] Confirming deletion calls `deleteRole()` and returns HTTP 200 — the response status equals 200 and the deleted role record is absent from the `role` table
- [ ] After deletion all members previously assigned to the deleted role are reassigned to the Member role — the count of members with the deleted role ID equals 0 and the count of reassigned members with the Member role increases accordingly
- [ ] The roles list refreshes after deletion and the deleted custom role is absent — the element count for the deleted role name equals 0 in the roles list
- [ ] Custom roles appear in the member role dropdown alongside default roles — the dropdown option count equals 3 plus the count of custom roles returned by `listRoles()`
- [ ] A direct `createRole()` call from a `member`-role user returns HTTP 403 — the response status equals 403 and the role record count in the database equals 0
- [ ] A direct `updateRole()` or `deleteRole()` call targeting a system role returns HTTP 400 — the response status equals 400 and the system role record remains unchanged
- [ ] The "Create role" button is absent from the DOM for a `member`-role user — the button element count equals 0
- [ ] All text in the roles management UI is rendered via i18n translation keys — the count of hardcoded English string literals in the role management components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Admin creates a custom role with a name that matches a default system role name such as "Owner" or "Admin" or "Member" | The server rejects the creation with a uniqueness error because system role names are reserved within the organization — the error element is present in the form and no custom role record is created with a system role name | The error element is present in the create-role form and the custom role record count with the reserved name equals 0 in the database |
| Admin deletes a custom role that has zero members currently assigned to it so no member reassignment is needed | The server deletes the custom role record without performing any member reassignment operations — the deletion completes with HTTP 200 and the roles list refreshes to remove the entry without affecting any member records | The response status equals 200 and the member record count with the deleted role ID equals 0 both before and after the deletion operation |
| Admin edits a custom role and removes all permissions from the checklist leaving the role with an empty permission set | The server either rejects the update with HTTP 400 requiring at least one permission selected, or persists the empty permission set so the role exists but grants no permissions — either way the outcome is deterministic | The response status equals 400 with an error element present, or equals 200 with the permission count for the role equaling 0 in the database |
| Two admins simultaneously create custom roles with the same name in the same organization from different browser sessions | The server's uniqueness constraint on role name and organizationId ensures only one creation succeeds — the second request returns a duplicate name error and the role record count for that name equals 1 | The first request returns HTTP 200 and the second request returns error with the role record count for that name equaling exactly 1 |
| Admin clicks the delete button twice in rapid succession on the same custom role before the first request completes | The client disables the confirm button on the first click preventing duplicate deletion requests — the server receives at most one `deleteRole()` call per confirmation action and the deletion operation executes exactly once | The disabled attribute is present on the confirm button within 100ms of the first click and the `deleteRole()` invocation count equals 1 |
| Admin opens the role detail view for editing but navigates away from the page before saving changes to the custom role | The unsaved changes are discarded and no `updateRole()` request is sent to the server — the custom role retains its original name and permissions as stored in the database before the edit view was opened | The network request count to `updateRole()` equals 0 after the navigation and the role record in the database matches its state before the edit view was opened |

## Failure Modes

- **createRole() fails due to a transient D1 write error during role record insertion**
    - **What happens:** The server validates the role name as unique but the subsequent
        INSERT operation to the `role` table fails due to a transient D1 database error
        or network timeout, so the custom role is not persisted despite passing all
        validation checks on the server side.
    - **Source:** Cloudflare D1 transient write failure or network interruption between
        the Worker and the D1 binding during the INSERT query execution step that follows
        the successful uniqueness validation for the new custom role name.
    - **Consequence:** The admin sees an error in the create-role form and the custom
        role does not appear in the roles list — no partial role data is committed to
        the database because the write operation failed before completion.
    - **Recovery:** The server logs the D1 write error with the role name, organization
        ID, and error context, then returns HTTP 500 — the client alerts the admin with
        a localized error message and the admin retries by clicking submit again once
        the D1 service recovers from the transient failure.

- **deleteRole() fails midway through member reassignment leaving orphaned role assignments**
    - **What happens:** The server begins the deletion flow by reassigning members from
        the custom role to the default Member role but the database transaction fails
        after some reassignments complete and before the role record is deleted, leaving
        the system in an inconsistent state with partially reassigned members.
    - **Source:** A D1 transaction failure that interrupts the multi-step deletion
        process after some member records are updated to the Member role but before the
        custom role record is removed from the `role` table, caused by a transient
        database timeout or connection interruption.
    - **Consequence:** Some members retain the custom role assignment while others have
        been reassigned to Member — the roles list still shows the custom role but the
        member assignments are inconsistent until the transaction is rolled back or
        retried by the admin.
    - **Recovery:** The server wraps the member reassignment and role deletion in a
        single database transaction so a partial failure triggers a full rollback — the
        server returns error to the client and logs the transaction failure, then the
        admin retries the deletion which re-executes the entire operation atomically.

- **Non-admin user bypasses the client guard and calls createRole() or updateRole() directly**
    - **What happens:** A user with the `member` role crafts a direct HTTP request to
        the `createRole()` or `updateRole()` endpoint using a valid session cookie,
        circumventing the client-side UI that hides role management controls from
        non-admin members, and attempts to create or modify a custom role definition.
    - **Source:** Adversarial or accidental action where a member sends a hand-crafted
        HTTP request to the role management mutation endpoint with a valid session token,
        bypassing the client-side visibility guard that conditionally renders role
        management controls only for admin and owner role members.
    - **Consequence:** Without server-side enforcement any member could create arbitrary
        custom roles or modify existing role permissions, potentially escalating their
        own access or granting unauthorized permissions to other members across the
        organization without admin or owner approval.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after verifying
        the calling user's role in the `member` table — the server logs the unauthorized
        attempt with the user ID, organization ID, and timestamp, and no role record is
        created or modified in the `role` table.

- **hasPermission() returns stale results due to a caching layer serving outdated role definitions**
    - **What happens:** The `hasPermission()` check evaluates a member's permissions
        against a cached version of the role definition that does not reflect the latest
        update made by an admin, causing the member to retain access to actions that
        were removed from the role or to be denied access to newly added permissions.
    - **Source:** An intermediate caching layer between the `hasPermission()` function
        and the `role` table that serves a stale role definition record after an admin
        has updated the permissions via `updateRole()`, creating a window where the
        cached data diverges from the persisted state in the database.
    - **Consequence:** Members assigned to the updated role experience incorrect access
        control until the cache expires or is invalidated — they can perform actions
        that were revoked or are denied actions that were granted, undermining the
        integrity of the permission model for the duration of the stale cache window.
    - **Recovery:** The `updateRole()` mutation handler notifies the permission cache to
        invalidate the entry for the updated role immediately after persisting the change
        — subsequent `hasPermission()` calls read the latest definition from the `role`
        table and the stale window is eliminated within the same request cycle.

## Declared Omissions

- This specification does not address the definition or assignment of individual
    permissions to system-level resources — the available permission identifiers
    are defined in the auth server configuration and this spec consumes them as
    opaque values in the permission checklist without defining their granular behavior
- This specification does not address bulk member reassignment to a different custom
    role — the only automated reassignment covered is the fallback to the default Member
    role upon deletion of a custom role, not voluntary migration between custom roles
- This specification does not address rate limiting on the `createRole()`, `updateRole()`,
    or `deleteRole()` mutation endpoints — that behavior is enforced by the global rate
    limiter defined in `api-framework.md` covering all mutation endpoints uniformly
- This specification does not address how custom roles interact with team-level
    permissions or sub-organization scopes — the scope of custom roles is limited to the
    organization level and team-level permission models are defined in separate specs
- This specification does not address the audit log recording of role creation, editing,
    or deletion events — audit logging behavior is defined in a separate cross-cutting
    specification covering all administrative actions across the organization settings

## Related Specifications

- [user-updates-organization-settings](user-updates-organization-settings.md) — The broader organization settings page context within which the roles management section is rendered, covering the settings navigation structure and permission model
- [org-admin-invites-a-member](org-admin-invites-a-member.md) — The invitation flow that assigns a role to new members, where custom roles appear alongside default roles in the role selection dropdown during the invitation process
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that provides the `createRole()`, `updateRole()`, `deleteRole()`, `listRoles()`, and `hasPermission()` methods
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `role` and `member` tables that store custom role records, permission sets, and member-to-role assignments read and written during role management operations
- [shared-contracts](../foundation/shared-contracts.md) — oRPC contract definitions for the role management mutations including the Zod schemas that validate role name, permission arrays, and organization ID before mutations reach the database layer
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization infrastructure providing translation keys for all role management page labels, form fields, confirmation dialogs, and error messages rendered in the roles UI
