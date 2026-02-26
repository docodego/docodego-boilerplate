# User Navigates the Dashboard

## Dashboard Shell Layout

Once the user lands on `/app/{orgSlug}/`, the dashboard shell renders with three regions: a sidebar on the left, a header bar across the top, and the main content area in the center. The content area is a TanStack Router Outlet that renders the active child route. The sidebar and header remain stable as the user moves between pages — only the content area swaps.

## Sidebar Navigation

The sidebar is divided into two groups. The first group contains organization-level pages: Overview, Members, Teams, and Org Settings. The second group is a user-level section containing a link to personal Settings. Clicking any nav item in the sidebar loads the corresponding child route into the content area. The sidebar itself does not re-render or reset.

On desktop, the sidebar is persistent and visible by default. A collapse toggle in the header shrinks it to a narrow icon rail, showing only icons without labels. The expanded or collapsed state is managed by a Zustand sidebar-store and persisted to localStorage, so the sidebar remembers its position across page reloads and sessions.

On mobile viewports, the sidebar transforms into a drawer overlay that slides in from the side. A hamburger button in the header opens it. Tapping outside the drawer or selecting a nav item closes it.

## Header Bar

The header bar sits across the top of the dashboard and contains several controls. On the left, the collapse toggle controls the sidebar's expanded or collapsed state. In the center or right area, the org switcher displays the current organization's name and provides access to switch between organizations. A theme toggle lets the user flip between light, dark, and system themes. An avatar dropdown in the far right provides access to account-related actions.

## Org Context

All pages under the `$orgSlug/` route share the same organization context. The `route.tsx` `beforeLoad` hook for the `$orgSlug` layout route loads the active organization's data based on the slug from the URL. Every child route inherits this context automatically, so navigating between Overview, Members, Teams, and Org Settings all operates within the same org without re-fetching the org identity.
