---
id: SPEC-2026-085
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [Visitor, Authenticated User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Enters the App

## Intent

This spec defines how a user navigates to `/app` or any URL under `/app/*` and the system resolves their authentication state and organization membership to determine the correct landing destination. Astro serves a single HTML shell at `/app/index.html` via a `_redirects` rule, and the React SPA mounts entirely on the client side using `client:only="react"` with zero server-side rendering. TanStack Router takes over all routing within the `/app/*` namespace. The root route's `beforeLoad` hook fires before any child route renders and checks for a valid session. If no session exists, the user is redirected to `/signin` with the original destination URL preserved for post-sign-in redirection. If a valid session exists, the hook fetches the user's organization list via `authClient.organization.list()`. Users with at least one organization are redirected to `/app/{activeOrgSlug}/` to land on their active organization's dashboard. Users with zero organizations are redirected to `/app/onboarding` to create their first organization. This resolution runs on every navigation to the bare `/app` URL, ensuring returning users bypass onboarding and new users are guided to organization creation.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Astro `_redirects` rule (routing configuration that maps all requests to `/app` and `/app/*` URLs to the single `/app/index.html` SPA shell document, enabling client-side routing for the entire application namespace) | read | When the user's browser requests any URL matching `/app` or `/app/*` and the server applies the redirect rule to serve the SPA shell HTML document instead of returning a 404 for non-existent file paths | The redirect rule is misconfigured or missing from the deployment — the server returns HTTP 404 for `/app` sub-routes and the user sees a "page not found" error instead of the SPA shell loading |
| TanStack Router (client-side routing library that manages all route matching, navigation, and guard execution within the `/app/*` namespace after the React SPA mounts in the browser with `client:only="react"`) | read/write | When the React SPA mounts and TanStack Router initializes, it matches the current URL against registered routes and executes the root route's `beforeLoad` hook before rendering any child route component | The router fails to initialize because the JavaScript bundle containing the route definitions fails to load — the SPA shell renders an empty container and the user sees a blank page with no navigation or content until the bundle loads successfully on retry |
| Better Auth session client (authentication client library that exposes `authClient.getSession()` to check whether the current user has a valid authenticated session with an active access token stored in the browser) | read | When the root route's `beforeLoad` hook fires and calls the session check to determine whether the user is authenticated before allowing any child route to render in the SPA | The session check fails because the auth API endpoint is unreachable or returns a network error — the `beforeLoad` hook treats the failed check as an unauthenticated state and redirects the user to `/signin` with the original destination URL preserved for post-sign-in return |
| Better Auth organization client (client library method `authClient.organization.list()` that fetches the list of organizations the authenticated user belongs to, including the active organization slug from the user's session context) | read | When the `beforeLoad` hook confirms a valid session exists and calls the organization list endpoint to determine whether the user has at least one organization and which organization slug to use for the dashboard redirect | The organization list request fails because the API returns an error or times out — the hook retries the request once and if the retry fails, the user is redirected to an error state within the SPA that displays a localized message asking the user to try again |
| `/signin` route (client-side route that renders the localized sign-in UI where unauthenticated users can authenticate via email OTP, passkey, SSO, or guest access before being redirected back to their original destination) | write | When the `beforeLoad` hook determines that no valid session exists and redirects the unauthenticated user to `/signin` with the original destination URL encoded as a query parameter for post-sign-in redirection | The `/signin` route component fails to load because its JavaScript chunk is missing or corrupted — the user sees a blank page at the sign-in URL and must reload the page to trigger a fresh download of the sign-in route bundle |
| `/app/onboarding` route (client-side route that renders the organization creation wizard for authenticated users who have zero organizations, guiding them through creating their first organization before accessing the dashboard) | write | When the `beforeLoad` hook confirms a valid session but the organization list returns zero organizations, the router redirects the user to `/app/onboarding` to begin the organization creation flow | The onboarding route component fails to load because its JavaScript chunk encounters a download error — the user sees a blank page at the onboarding URL and must reload to attempt loading the onboarding wizard again |

## Behavioral Flow

1. **[Visitor]** navigates to `/app` or any URL under `/app/*` by entering the URL directly in the browser, clicking a link from the landing page, or being redirected after completing sign-in

2. **[Astro]** applies the `_redirects` rule to route the request to `/app/index.html`, serving the single HTML shell document that contains the `<App client:only="react" />` directive for mounting the React SPA entirely on the client side with no server-side rendering

3. **[TanStack Router]** initializes when the React SPA mounts, matches the current URL against registered route definitions within the `/app/*` namespace, and prepares to execute the root route's `beforeLoad` hook before rendering any child route component

4. **[TanStack Router]** the root route's `beforeLoad` hook in `index.tsx` fires and calls the Better Auth session client to check whether a valid session exists for the current user before allowing any child route to proceed

5. **[Better Auth]** if no valid session exists, the `beforeLoad` hook redirects the user to `/signin` with the original destination URL preserved as a query parameter so that after successful sign-in the user returns to where they originally intended to navigate

6. **[Better Auth]** if a valid session exists, the `beforeLoad` hook calls `authClient.organization.list()` to fetch the list of organizations the authenticated user belongs to, including the active organization's slug from the session context

7. **[TanStack Router]** if the organization list contains at least one organization, the hook redirects the user to `/app/{activeOrgSlug}/` where `activeOrgSlug` is the slug of the user's currently active organization from their session, landing the user directly on their active organization's dashboard

8. **[TanStack Router]** if the organization list returns zero organizations (a new user who just signed up or a user whose organizations were all deleted), the hook redirects the user to `/app/onboarding` where they will create their first organization

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| initial_navigation | spa_shell_loaded | The user's browser requests a URL matching `/app` or `/app/*` and Astro serves the SPA shell HTML document via the `_redirects` rule and the React application mounts with `client:only="react"` | The HTTP response status is 200 and the SPA shell HTML document loads and the React mount point element is present in the DOM for TanStack Router to initialize |
| spa_shell_loaded | session_check_in_progress | TanStack Router initializes and the root route's `beforeLoad` hook fires, calling the Better Auth session client to verify whether a valid authenticated session exists for the current user | The `beforeLoad` hook is registered on the root route and TanStack Router executes it before rendering any child route component within the `/app/*` namespace |
| session_check_in_progress | redirected_to_signin | The session check returns no valid session indicating the user is not authenticated and the `beforeLoad` hook redirects to `/signin` with the original destination URL preserved in a query parameter | The session client returns a null or empty session response or the session check request fails due to a network error, both treated as unauthenticated state |
| session_check_in_progress | org_resolution_in_progress | The session check returns a valid authenticated session and the `beforeLoad` hook proceeds to call `authClient.organization.list()` to fetch the user's organization membership data | The session response contains a valid access token and user identity confirming the user is authenticated and authorized to proceed to organization resolution |
| org_resolution_in_progress | redirected_to_dashboard | The organization list returns at least one organization and the hook extracts the active organization slug from the session context to construct the redirect URL `/app/{activeOrgSlug}/` | The organization list response contains one or more organization records and the active organization slug is a non-empty string present in the session context |
| org_resolution_in_progress | redirected_to_onboarding | The organization list returns zero organizations indicating the user has no organization membership and the hook redirects to `/app/onboarding` to begin the first organization creation flow | The organization list response is an empty array confirming the user belongs to zero organizations and requires the onboarding wizard to create their first organization |

## Business Rules

- **Rule unauthenticated-user-redirected-to-signin:** IF the `beforeLoad` hook checks the session and no valid session exists THEN the user is redirected to `/signin` with the original destination URL preserved as a query parameter — the count of unauthenticated users who reach a child route without being redirected equals 0
- **Rule destination-url-preserved-across-sign-in:** IF the user is redirected to `/signin` from `/app` or `/app/*` THEN the original destination URL is encoded in the redirect query parameter and restored after successful sign-in — the redirect URL after sign-in matches the originally requested URL
- **Rule user-with-orgs-goes-to-dashboard:** IF the authenticated user's organization list contains at least one organization THEN the user is redirected to `/app/{activeOrgSlug}/` using the active organization slug from the session — the count of authenticated users with organizations who land on onboarding equals 0
- **Rule user-without-orgs-goes-to-onboarding:** IF the authenticated user's organization list contains zero organizations THEN the user is redirected to `/app/onboarding` to create their first organization — the count of users with zero organizations who reach the dashboard equals 0
- **Rule resolution-runs-on-every-bare-app-navigation:** IF the user navigates to the bare `/app` URL THEN the `beforeLoad` hook executes the full session check and organization resolution sequence regardless of previous navigation history — the count of bare `/app` navigations that skip the resolution hook equals 0
- **Rule spa-shell-no-ssr:** IF the browser requests `/app` or `/app/*` THEN the SPA shell mounts the React application with `client:only="react"` using zero server-side rendering — the count of server-rendered React components in the SPA shell equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Visitor (an unauthenticated user who navigates to `/app` or `/app/*` without a valid session, including first-time visitors, users with expired sessions, and users who signed out on a previous visit) | Navigate to `/app` or `/app/*` and trigger the `beforeLoad` hook session check; be redirected to `/signin` with the original destination URL preserved for post-sign-in return; view the sign-in UI and authenticate through available methods | Cannot view any child route content within `/app/*` without first obtaining a valid session through sign-in, cannot bypass the `beforeLoad` hook redirect by manipulating client-side router state, cannot access organization data or dashboard routes | The visitor sees only the `/signin` page after the redirect — no dashboard content, organization data, or onboarding UI is visible until authentication completes successfully |
| Authenticated User (a user with a valid session confirmed by the `beforeLoad` hook session check who proceeds to organization resolution to determine their landing destination within the `/app/*` namespace) | Have their organization list fetched automatically by the `beforeLoad` hook; be redirected to `/app/{activeOrgSlug}/` if they belong to at least one organization; be redirected to `/app/onboarding` if they have zero organizations; navigate freely within their authorized routes after landing | Cannot skip the organization resolution step when navigating to the bare `/app` URL, cannot access another user's organization dashboard without membership, cannot override the active organization slug in the redirect to access organizations they do not belong to | The authenticated user sees only the dashboard for their active organization or the onboarding wizard — organization data for other users is not visible and the active organization slug in the URL reflects only their own session context |

## Constraints

- The SPA shell HTML document at `/app/index.html` loads and the React application mounts within 2000 ms of the browser receiving the HTTP response — the count of milliseconds from response received to React mount equals 2000 or fewer.
- The `beforeLoad` hook session check completes within 1000 ms of TanStack Router invoking the hook — the count of milliseconds from hook invocation to session check result equals 1000 or fewer.
- The organization list fetch via `authClient.organization.list()` completes within 1000 ms of the session check confirming a valid session — the count of milliseconds from session confirmation to organization list result equals 1000 or fewer.
- The total time from initial navigation to the user's final destination (signin, dashboard, or onboarding) completes within 4000 ms on a 4G connection — the count of milliseconds from navigation start to final route render equals 4000 or fewer.
- The redirect to `/signin` preserves the original destination URL in a query parameter with a maximum length of 2048 characters — the count of characters in the preserved URL parameter equals 2048 or fewer.

## Acceptance Criteria

- [ ] Navigating to `/app` serves the SPA shell HTML at `/app/index.html` via the `_redirects` rule — the HTTP response status equals 200 and the document contains the React mount point
- [ ] The React SPA mounts with `client:only="react"` and TanStack Router initializes for client-side routing — the count of server-rendered React components in the shell equals 0
- [ ] The `beforeLoad` hook fires before any child route renders and checks session state — the session check call is present in the network log before any child route data fetches
- [ ] An unauthenticated user navigating to `/app` is redirected to `/signin` — the browser URL changes to `/signin` and the sign-in UI is present
- [ ] The original destination URL is preserved in the redirect query parameter when redirecting to `/signin` — the redirect URL query parameter is non-empty and equals the originally requested path
- [ ] After successful sign-in the user is redirected back to the originally requested URL — the count of mismatches between the post-sign-in browser URL and the preserved destination equals 0
- [ ] An authenticated user with at least one organization is redirected to `/app/{activeOrgSlug}/` — the active organization slug in the browser URL is non-empty and equals the session's active org slug
- [ ] An authenticated user with zero organizations is redirected to `/app/onboarding` — the browser URL equals `/app/onboarding` and the onboarding UI is present
- [ ] The full resolution from navigation to final destination completes within 4000 ms on a 4G connection — the count of milliseconds from navigation start to final render equals 4000 or fewer
- [ ] Navigating to `/app/some/deep/route` without a session redirects to `/signin` and preserves the deep route as the return URL — the return URL query parameter is non-empty and the redirect location after sign-in returns 200

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user navigates to `/app` with a session that expires between the `beforeLoad` hook starting the session check and the organization list fetch completing, creating a race condition between authentication and data fetching | The organization list call returns HTTP 401 because the session expired during the fetch — the `beforeLoad` hook treats this as an unauthenticated state and redirects the user to `/signin` with the original destination URL preserved for post-sign-in return | The browser URL changes to `/signin` and the preserved destination URL parameter equals `/app` after the session expiry is detected during the organization fetch |
| The user navigates to `/app` on a very slow network connection where the SPA shell JavaScript bundle takes more than 5000 ms to download and the React application has not yet mounted when the user attempts to interact with the page | The SPA shell HTML displays a loading indicator (empty shell with no interactive elements) until the JavaScript bundle finishes downloading and TanStack Router initializes — the user cannot interact with any routes until the mount completes | The loading indicator is visible in the DOM until the React mount event fires and TanStack Router begins the `beforeLoad` hook execution after the delayed bundle load |
| The user navigates to `/app` and the organization list fetch returns a list of organizations but the active organization slug from the session does not match any organization in the returned list due to the active org being deleted by another admin | The `beforeLoad` hook detects that the active organization slug is not present in the organization list and falls back to redirecting to the first organization in the list by its slug instead of using the stale active organization reference | The browser URL contains the slug of the first organization from the returned list and the dashboard renders for that organization instead of showing an error |
| The user navigates directly to `/app/onboarding` while already belonging to one or more organizations, bypassing the normal `/app` resolution that checks organization membership before routing | The onboarding route's own guard checks the user's organization list and detects that the user already has organizations — the guard redirects the user to `/app/{activeOrgSlug}/` instead of showing the onboarding wizard | The browser URL changes from `/app/onboarding` to `/app/{activeOrgSlug}/` and the dashboard renders instead of the organization creation wizard |
| The user navigates to `/app` and the Better Auth session client returns a valid session but the `authClient.organization.list()` call fails with a network timeout on both the initial attempt and the single retry | The `beforeLoad` hook catches the organization list failure after the retry exhausts and redirects the user to an error state within the SPA displaying a localized message indicating a temporary error and asking the user to try again | The SPA displays a localized error message and a retry button — the user can click retry to re-trigger the organization resolution without reloading the entire page |
| The user clicks a link to `/app` from the landing page while already on `/app/{orgSlug}/dashboard` with an active session and organization context already established in the client-side state | TanStack Router matches the `/app` route and re-executes the `beforeLoad` hook which checks the session and fetches the organization list again, then redirects back to `/app/{activeOrgSlug}/` based on the current session's active organization | The browser URL returns to `/app/{activeOrgSlug}/` after the resolution completes and the dashboard re-renders with the same organization context as before |

## Failure Modes

- **SPA shell JavaScript bundle fails to download preventing the React application from mounting and TanStack Router from initializing**
    - **What happens:** The browser receives the SPA shell HTML document but the JavaScript bundle containing the React application and TanStack Router fails to download due to a CDN error, network interruption, or corrupted bundle file, leaving the page in an empty state with no interactive routing.
    - **Source:** The CDN returns HTTP 500 or the bundle hash does not match the reference in the HTML document due to a deployment race condition, or the user's network connection drops during the bundle download after the HTML document loaded.
    - **Consequence:** The user sees a blank or loading-only page at the `/app` URL with no interactive elements, no session check, and no redirect to `/signin` or the dashboard — the application is completely non-functional until the bundle loads.
    - **Recovery:** The SPA shell HTML includes a static fallback message with a reload link that the user can click to retry the page load — the browser retries the bundle download and the application logs the load failure to the error tracking service for the development team to investigate.

- **Better Auth session check fails with a network error or API timeout during the `beforeLoad` hook execution preventing authentication state from being determined**
    - **What happens:** The `beforeLoad` hook calls the Better Auth session client to check for a valid session but the auth API endpoint is unreachable due to a Cloudflare Workers outage, DNS resolution failure, or network timeout that prevents the session response from being received.
    - **Source:** The Cloudflare Workers runtime hosting the auth API experiences a regional outage, the user's network connection is intermittent, or a firewall or proxy between the user and the API blocks the session check request.
    - **Consequence:** The `beforeLoad` hook cannot determine whether the user is authenticated and treats the failed check as an unauthenticated state, redirecting the user to `/signin` even if they have a valid session — the user must re-authenticate unnecessarily.
    - **Recovery:** The hook logs the session check failure with the error details and redirects to `/signin` as the safe default — the sign-in page detects the existing valid session on its own session check and returns the user to their intended destination without requiring manual re-authentication.

- **Organization list fetch returns an unexpected response format or empty response body after the session is confirmed as valid**
    - **What happens:** The `beforeLoad` hook confirms a valid session and calls `authClient.organization.list()` but the API returns a malformed JSON response, an unexpected HTTP status code, or an empty response body that cannot be parsed into the expected organization list structure.
    - **Source:** A deployment to the API introduces a breaking change to the organization list endpoint response format, the API's database query times out and returns a partial response, or a middleware strips the response body before it reaches the client.
    - **Consequence:** The `beforeLoad` hook cannot determine whether the user has organizations and cannot construct the correct redirect URL — the user is stuck in the resolution step with no navigation to the dashboard or onboarding.
    - **Recovery:** The hook retries the organization list fetch once and if the retry also fails, the user is redirected to an error state within the SPA that displays a localized error message and a retry button — the user clicks retry to re-trigger the resolution without a full page reload.

## Declared Omissions

- This specification does not define the sign-in flow UI, authentication methods, or session creation logic that executes when the user is redirected to `/signin` — those behaviors are covered by the sign-in specifications for email OTP, passkey, SSO, and guest access
- This specification does not cover the organization creation wizard rendered at `/app/onboarding` for users with zero organizations — that behavior is defined in the user-creates-first-organization specification
- This specification does not address the dashboard layout, navigation structure, or content rendering that occurs after the user lands on `/app/{activeOrgSlug}/` — dashboard behavior is defined in the user-navigates-the-dashboard specification
- This specification does not define the active organization switching mechanism that changes which organization slug appears in the URL — that behavior is covered by the user-switches-organization specification
- This specification does not cover TanStack Router's route-level code splitting, lazy loading configuration, or bundle optimization — those are build-time concerns outside the scope of the runtime behavioral flow

## Related Specifications

- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md)
    — defines the email OTP sign-in flow that the user follows when
    redirected to `/signin` after the `beforeLoad` hook determines no
    valid session exists during the app entry resolution
- [user-creates-first-organization](user-creates-first-organization.md)
    — defines the onboarding wizard at `/app/onboarding` where users
    with zero organizations create their first organization before
    gaining access to the dashboard
- [user-navigates-the-dashboard](user-navigates-the-dashboard.md)
    — defines the dashboard navigation structure and content rendering
    that the user sees after the app entry resolution redirects them
    to `/app/{activeOrgSlug}/` based on their active organization
- [user-switches-organization](user-switches-organization.md)
    — defines the organization switching mechanism that changes the
    active organization slug in the URL and updates the session
    context used by the app entry resolution on subsequent navigations
- [session-lifecycle](session-lifecycle.md) — defines the session
    creation, refresh, and expiration behavior that determines whether
    the `beforeLoad` hook's session check returns a valid session
    during the app entry resolution flow
