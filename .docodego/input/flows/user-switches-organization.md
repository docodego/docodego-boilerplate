# User Switches Organization

## Opening the Org Switcher

The OrgSwitcher component sits in the dashboard header and displays the name of the user's current organization. When the user clicks it, a dropdown opens listing all organizations the user belongs to. The current organization is visually marked — highlighted or checked — so the user can immediately see which org they are working in.

## Selecting a Different Organization

The user clicks on a different organization in the dropdown list. The app navigates to `/app/{newSlug}/`, where `newSlug` is the slug of the selected org. The URL is the source of truth for org context — it is bookmarkable and shareable. Anyone with access to that org can paste the URL into their browser and land directly in that org's dashboard.

The session's `activeOrganizationId` updates to reflect the newly selected organization. There is no separate API call to switch context — the route change itself drives the context change. The `$orgSlug` layout route's `beforeLoad` hook picks up the new slug from the URL and loads the corresponding org data.

## Dashboard Re-renders

Once the route change completes, all dashboard data re-fetches for the new org context. TanStack Query caches are keyed by org, so if the user has visited this org recently, cached data may appear instantly while background refetches run. The sidebar, header, and content area all reflect the new organization — page titles, member lists, settings, and any org-specific data update to match the selected org.
