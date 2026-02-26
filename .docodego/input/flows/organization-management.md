# Organization Management

## Creating an Organization

A user who has no organizations yet lands on the onboarding screen at `/app/onboarding`. Users who already belong to at least one org can also create a new one from the dashboard header via the OrgSwitcher component, which includes a "Create organization" option.

Either way, the user sees a form with two fields: organization name and slug. As the user types the name, the slug field auto-populates with a URL-friendly version of the name (lowercased, spaces replaced with hyphens, special characters stripped). The user can manually edit the slug if they want something different. The slug must be unique across the platform -- if the generated slug is already taken, the system flags it and the user picks an alternative.

When the user submits, the frontend calls `authClient.organization.create({ name, slug })`. Better Auth creates the organization record and automatically makes the creating user the owner with full permissions. The session updates to set `activeOrganizationId` to the newly created org. The user is then navigated to `/app/{slug}/`, which is the org's dashboard.

If this is the user's first organization (coming from onboarding), this is a seamless transition from "new user with no org" to "org owner on the dashboard." If the user created it from an existing dashboard, the OrgSwitcher reflects the new org and the URL updates accordingly.

## Switching Organizations

A user who belongs to multiple organizations sees all of them listed in the OrgSwitcher component in the dashboard header. The switcher displays the currently active org prominently and lists the others in a dropdown.

When the user clicks a different organization, the app navigates to `/app/{newSlug}/`. The URL is the source of truth for which org is active -- it is bookmarkable and shareable. On navigation, the session's `activeOrganizationId` updates to match the org resolved from the URL slug. All dashboard data (members, teams, settings) re-fetches for the new org context.

There is no separate "switch org" API call beyond navigation. The route change drives the context change. If a user bookmarks `/app/acme-corp/` and opens it later, the dashboard loads for that org directly (assuming they still have access).

## Organization Settings

The organization settings page lives at `/app/$orgSlug/settings`. When a user navigates there, the page loads the current org's details and presents them in a form.

The form has two editable fields: organization name and slug. Both are pre-filled with the current values. The user can update either field and save via an oRPC mutation. Slug changes are validated for uniqueness, same as during creation. If the slug changes, the app navigates to the new URL path after save (since the URL includes the slug).

Below the form is a danger zone section. This contains the "Delete organization" action. When the user clicks the delete button, a confirmation dialog appears warning that this action is permanent and will remove all org data, members, and teams. The dialog makes it very clear there is no undo.

If the user confirms, the frontend fetches the organization ID and calls `authClient.organization.delete({ organizationId })`. After successful deletion, the app redirects to `/app`. From there, the standard routing logic kicks in: if the user still has other organizations, they are redirected to `/app/{activeOrgSlug}/` for one of their remaining orgs. If they have no organizations left, they land on `/app/onboarding` to create a new one.

Only the org owner can delete an organization. Admins and members do not see the delete option.

## URL Routing Behavior

The routing system under `/app` follows a clear set of rules that determine where a user ends up.

When a user navigates to `/app` with no further path, the router checks their session. If they have an active organization, it redirects to `/app/{activeOrgSlug}/`. If they have no organizations at all, it redirects to `/app/onboarding`.

Certain route segments under `/app` are reserved as static routes: `settings` and `onboarding`. These resolve before the dynamic `$orgSlug` parameter. So `/app/settings` always loads user-level settings -- it is never interpreted as an org with the slug "settings." Likewise, `/app/onboarding` always loads the onboarding flow.

For everything else, the `$orgSlug` segment is treated as a dynamic parameter. The router resolves the org from the slug, validates that the current user has membership in that org, and loads the org-scoped dashboard.

If a user tries to access an org they do not belong to (e.g., by manually editing the URL or following a stale bookmark), the app redirects them to their own active org's dashboard. There is no "access denied" page -- the user simply lands where they have access.
