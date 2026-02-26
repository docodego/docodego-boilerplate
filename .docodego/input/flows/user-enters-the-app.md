# User Enters the App

## Astro Serves the SPA Shell

When the user navigates to `/app` or any URL under `/app/*`, Astro's `_redirects` rule routes the request to `/app/index.html`. This single HTML file is the shell for the entire React SPA. Inside it, the `<App client:only="react" />` directive tells Astro to mount the React application entirely on the client side, with no server-side rendering. TanStack Router takes over from here, handling all routing within the `/app/*` namespace.

## Authentication Check

The root route's `beforeLoad` hook in `index.tsx` fires before any child route renders. It checks for a valid session. If no session exists, the user is redirected to `/signin`. The intended destination URL is preserved so that after successful sign-in, the user returns to where they originally wanted to go.

If a valid session exists, the hook proceeds to determine where the user should land.

## Organization Resolution

With a valid session confirmed, the hook fetches the user's organization list via `authClient.organization.list()`. Two outcomes follow:

If the user belongs to at least one organization, the hook redirects to `/app/{activeOrgSlug}/`, where `activeOrgSlug` is the slug of the user's currently active organization from their session. The user lands directly on their org dashboard.

If the user has no organizations — a new user who just signed up, for example — the hook redirects to `/app/onboarding`, where they will create their first organization.

This resolution happens every time someone navigates to the bare `/app` URL. Returning users with organizations skip onboarding entirely and go straight to their active org's dashboard. Users who accepted an invitation and already belong to an org through that path also skip onboarding.
