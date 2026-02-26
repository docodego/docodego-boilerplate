# Dashboard Navigation Flow

---

## Landing Page

The user arrives at the root URL (`/`). Astro renders a fully static HTML page with zero JavaScript — the entire page is pre-built at deploy time via SSG, so search engine crawlers see complete markup with no client-side hydration required.

The page opens with a hero section: the product name, a one-line description of what DoCodeGo offers, and a prominent call-to-action button that leads to `/signin`. Below the hero sit six feature cards arranged in a grid — Web, API, Mobile, Desktop, Extension, and i18n — each with an icon and a short description of the platform capability.

The header contains a theme toggle. Because this is a static page, the theme toggle is one of the few interactive elements — it reads the user's stored preference from localStorage (or falls back to the system preference) and applies the correct theme class before the first paint. There is no flash of wrong theme.

No authentication is required to view the landing page. The sign-in button in the header and the hero CTA both link to `/signin`.

---

## Entering the App

When the user clicks sign in and completes authentication (or navigates directly to `/app`), TanStack Router takes over. The route tree begins at `/app`, and the first thing that fires is the `beforeLoad` hook in `index.tsx`.

This hook calls the auth session check. If the user has no valid session, the router redirects them to `/signin` immediately — they never see a flash of dashboard UI. The redirect preserves the intended destination so the user can be sent back after signing in.

If the session is valid, the hook fetches the user's organization list via `authClient.organization.list()`. Two outcomes are possible:

The user belongs to at least one organization. The router picks the active organization (the first one, or whichever was most recently used) and redirects to `/app/{activeOrgSlug}/`. The slug is the URL-safe identifier for that organization.

The user has no organizations. This is typical for a brand-new account. The router redirects to `/app/onboarding`, where a simple form lets the user create their first organization. Once they submit the form and the org is created, they land at `/app/{newOrgSlug}/`.

---

## Dashboard Layout

Once inside `/app/{orgSlug}/`, the user sees the main dashboard shell. It is divided into three regions.

On the left is the sidebar. It contains two groups of navigation links. The first group is the organization section: Overview, Members, Teams, and Org Settings. These correspond to the child routes under `$orgSlug/`. The second group is a user section with a single link to Settings, which navigates to `/app/settings/profile` (outside the org scope).

Along the top is the header bar. From left to right it contains: the sidebar collapse toggle (on desktop), the org switcher dropdown, a spacer, the theme toggle button, and the user avatar dropdown.

The center is the main content area. TanStack Router renders the active child route here via its Outlet. When the user clicks "Overview" in the sidebar, the overview page loads in this area. When they click "Members," the members page replaces it. The sidebar and header remain stable throughout navigation.

The sidebar's expanded or collapsed state is managed by a Zustand store (`sidebar-store`). This store persists its state to localStorage, so when the user returns the next day, the sidebar is in the same state they left it.

---

## Org Switcher

The org switcher sits in the header. It displays the name of the current organization, pulled from the URL slug and matched against the user's org list.

Clicking the switcher opens a dropdown that lists all organizations the user belongs to. Each entry shows the org name. The current org is visually marked.

When the user clicks a different organization, the router navigates to `/app/{newSlug}/`, replacing the org slug segment of the URL. The page content updates to reflect the new org context — the overview loads fresh data for the selected org, the members list changes, and so on. No full page reload occurs; TanStack Router handles the transition client-side.

The URL is always the source of truth for which organization is active. Users can bookmark `/app/acme-corp/` or `/app/my-startup/` and land directly in the right org context. Sharing a URL with a teammate takes them to the same org view (assuming they have access).

---

## User Menu

The user avatar in the top-right corner of the header opens a dropdown menu when clicked.

The menu contains a link to Settings. Clicking it navigates to `/app/settings/profile`, which is the user-level settings area — not scoped to any organization. The sidebar updates to reflect the settings context (or the user is taken out of the org layout into the settings layout).

The menu also contains a Sign Out action. When clicked, it calls `authClient.signOut()`, which clears the session cookie and the auth hint cookie. Once sign-out completes, the user is redirected to `/signin`. They cannot navigate back to any `/app/*` route without signing in again.

---

## Sidebar Behavior

On desktop viewports, the sidebar is always visible. A toggle button (in the header or at the top of the sidebar) lets the user collapse it to a narrow icon-only rail, or expand it back to full width showing labels. The collapse state is held in the Zustand sidebar-store and persisted to localStorage, so it survives page refreshes and return visits.

When the viewport shrinks to a mobile breakpoint, the sidebar disappears from the layout entirely. In its place, a hamburger or menu button appears in the header. Tapping this button opens the sidebar as a drawer overlay that slides in from the left. The drawer covers part of the screen with a backdrop. Tapping the backdrop or selecting a navigation item closes the drawer.

The sidebar content is identical in both modes — same two groups (org pages and user section), same links, same active state highlighting. Only the presentation changes: persistent panel on desktop, transient drawer on mobile.

---

## Route Protection

Every route under `/app` is protected. The protection happens at two layout boundaries.

The `$orgSlug/route.tsx` layout runs a `beforeLoad` hook that checks for a valid auth session. If the session is missing, it redirects to `/signin`. If the session is present, the hook extracts the `orgSlug` param from the URL and loads the organization context — confirming the user actually belongs to that org. This context is then available to all child routes (overview, members, teams, org settings) without each one needing to refetch it.

The `settings/route.tsx` layout runs its own `beforeLoad` hook with the same session check. Settings routes are user-scoped (no org context needed), so the hook only validates that the user is authenticated.

TanStack Router resolves static route segments before dynamic ones. This means `/app/settings` is matched as the literal `settings` route, not as a dynamic `$orgSlug` where the slug happens to be "settings." `/app/onboarding` works the same way. Only when no static segment matches does the router treat the segment as a dynamic org slug.

---

## Astro and React Boundary

The application has a clear boundary between Astro's static world and React's dynamic world.

Astro owns the HTML shell. It renders the `<head>` tags, the base HTML structure, fonts, and the critical CSS. For the landing page at `/`, Astro renders the entire page as static HTML — no React involved.

For the dashboard, Astro renders a minimal page at `/app/index.html` that contains a single React island: `<App client:only="react" />`. The `client:only` directive means this component renders exclusively on the client — Astro does not attempt to server-render it. When this HTML loads in the browser, React mounts, TanStack Router initializes, and all subsequent navigation within `/app/*` happens client-side.

A `_redirects` file (or equivalent hosting rule) ensures that any URL under `/app/*` serves the same `/app/index.html` file. This is essential for client-side routing — without it, hitting `/app/acme-corp/members` directly would return a 404 from the static host. With the redirect rule, the static host always serves the SPA shell, and TanStack Router reads the URL and renders the correct route.

The auth hint cookie (`docodego_authed`) bridges the two worlds. It is a JS-readable cookie (not httpOnly) set during sign-in and cleared during sign-out. Astro pages can read this cookie to know whether the user is likely authenticated. This prevents a flash of unauthenticated content (FOUC) on static pages — for example, the landing page can show "Go to Dashboard" instead of "Sign In" if the cookie is present. The cookie is a hint, not a security boundary; actual auth verification always happens server-side when API calls are made.
