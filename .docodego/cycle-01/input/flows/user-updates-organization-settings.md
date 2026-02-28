[← Back to Index](README.md)

# User Updates Organization Settings

## Navigating to Settings

The user navigates to `/app/$orgSlug/settings` via the sidebar's Org Settings link. The settings page loads with a form displaying localized labels, pre-filled with the current organization's details: the organization name and the organization slug.

## Editing and Saving

The user edits either the name, the slug, or both, then clicks a save button. The save action triggers an oRPC mutation that sends the updated values to the API. If the slug was changed, the API validates the new slug for uniqueness — the same rules apply as during creation (minimum 3 characters, lowercase letters, numbers, and hyphens only, no leading or trailing hyphens, must not already be taken by another org).

If the slug changes and the mutation succeeds, the app navigates to the new URL path at `/app/{newSlug}/settings` so the URL stays in sync with the updated slug. If only the name changed, the page stays at the same URL and the updated name is reflected in the header's OrgSwitcher and throughout the dashboard.

## Permissions

Only the organization owner and users with an admin role can access and edit organization settings. Other members who navigate to this page either see a read-only view or are redirected away, depending on the route guard implementation.
