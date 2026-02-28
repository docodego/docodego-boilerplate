---
id: SPEC-2026-084
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [Visitor]
---

[← Back to Roadmap](../ROADMAP.md)

# User Visits Landing Page

## Intent

This spec defines how a visitor arrives at the DoCodeGo landing page served at the root URL `/` and interacts with the static content rendered by Astro as a fully pre-built SSG page. The page ships zero JavaScript to the client except for one React island in the header that checks session state to toggle between a localized "Sign in" link and an authenticated user avatar. The landing page presents a hero section with a copyable install command and a call-to-action button, a technology stack grid organized by category, and a footer with navigation links and copyright information. On the desktop Tauri app, external links in the footer open in the user's default system browser via `tauri-plugin-opener` rather than navigating the webview. The page requires no authentication, no session, and no redirect logic — the only authentication-aware element is the header island that reads session state to determine whether to display the sign-in link or the user avatar.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Astro SSG build pipeline (static site generator that pre-renders the landing page HTML at deploy time and serves it as a fully static document with zero client-side JavaScript except for explicitly marked React islands) | read | When the visitor's browser requests the root URL `/` and the CDN or origin server responds with the pre-built HTML document that was generated during the last deployment build | The static HTML file is unavailable because the CDN or origin server is down — the browser displays its default connection error page and the visitor retries the request later when the server becomes accessible again |
| React island for session-aware header toggle (client-side React component mounted with `client:load` that checks the user's session state to render either a localized "Sign in" link pointing to `/signin` or the authenticated user's avatar linking to `/app`) | read | When the landing page HTML loads in the browser and the React island hydrates to check session state via the auth client and render the correct header element based on authentication status | The session check fails because the auth API endpoint is unreachable or returns an error — the header falls back to displaying the "Sign in" link as the default unauthenticated state so the visitor can still navigate to the sign-in page |
| Theme toggle with localStorage persistence (header component that reads the user's stored theme preference from localStorage on initial render and applies the correct CSS theme class before the first paint to prevent a flash of the wrong theme) | read/write | When the landing page renders and the theme toggle reads the stored preference from localStorage during the initial paint, and when the visitor clicks the toggle to switch themes and the new preference is written to localStorage | The localStorage API is unavailable because the browser is in a restricted mode or storage is full — the theme toggle falls back to the system default color scheme preference detected via the `prefers-color-scheme` media query and the visitor continues browsing without persistent theme selection |
| Clipboard API for install command copy button (browser `navigator.clipboard.writeText` API that copies the install command text to the system clipboard when the visitor clicks the copy button next to the styled code block in the hero section) | write | When the visitor clicks the copy button adjacent to the install command code block in the hero section, triggering the clipboard write operation to copy the command text to the system clipboard | The clipboard API call is rejected because the browser does not support it or the page lacks the required permissions — the copy button displays a localized error indicator instead of the checkmark confirmation and the visitor manually selects and copies the command text |
| Tauri plugin opener for external links in desktop app (uses `tauri-plugin-opener` to intercept external link clicks in the Tauri webview and open them in the user's default system browser instead of navigating the webview to the external URL) | read | When the visitor clicks an external link in the footer such as the GitHub repository link, the docs site link, or the changelog link while running the desktop Tauri app, triggering the plugin to open the URL externally | The `tauri-plugin-opener` plugin fails to invoke the system browser due to a missing plugin registration or platform-specific error — the link falls back to navigating the webview to the external URL and the visitor uses the browser back button to return to the landing page |
| @repo/i18n localization layer (internationalization framework that provides translated strings for all user-facing text on the landing page including the header sign-in link, hero tagline, technology card descriptions, and footer content via translation keys) | read | When the landing page renders and each localized text element resolves its translation key against the active locale to display the correct language variant for the visitor's configured language preference | The i18n translation lookup fails because translation keys are missing for the active locale — the rendering layer falls back to the English default translation for each missing key and the visitor sees English text for any untranslated strings while the rest of the page renders in the selected locale |

## Behavioral Flow

1. **[Visitor]** navigates to `/` in their browser by entering the URL directly, clicking a link from an external source, or launching the desktop Tauri app which loads the root URL in its webview

2. **[Astro]** serves the landing page as a fully static SSG document that was pre-built at deploy time — the HTML is complete and rendered with zero JavaScript shipped to the client except for explicitly declared React islands

3. **[Browser]** renders the header displaying the product name on the left and a theme toggle on the right — the theme toggle reads the user's preference from localStorage and applies the correct theme class before the first paint, preventing any flash of the wrong theme

4. **[React Island]** the session-aware header component hydrates with `client:load` and checks the user's session state — if the user is not authenticated, a localized "Sign in" link appears pointing to `/signin`; if the user is authenticated, their avatar is displayed linking to `/app` with a fallback to initials if no profile image exists

5. **[Browser]** renders the hero section below the header displaying the product name, a short localized tagline, a styled code block containing the copyable install command `pnpm create docodego-boilerplate@latest`, a copy button beside it, and a prominent call-to-action button linking to `/signin`

6. **[Visitor]** clicks the copy button next to the install command — the browser writes the command text to the clipboard via `navigator.clipboard.writeText` and the button changes to a checkmark indicator for 2000 ms to confirm the copy succeeded before reverting to its original state

7. **[Browser]** renders the technology stack grid below the hero section displaying cards organized by category (Core Platform, Monorepo, Frontend Web, Backend API, Auth, UI Components, Shared Packages, Mobile, Desktop, Browser Extension, Testing, Code Quality, Infrastructure) with each card showing the technology name, its version, and a one-line description of its role

8. **[Browser]** lays out the technology stack cards in a responsive grid that adapts from a single column on mobile viewports to two columns on medium viewports and three columns on wide viewports

9. **[Browser]** renders the footer at the bottom of the page with the product name and a short localized description in the first column, a localized "Product" heading with links to the GitHub repository, docs site, and changelog in the second column, and a copyright line reading "2026 DoCodeGo" alongside a link to the MIT license at the bottom

10. **[Tauri]** when running inside the desktop app, external links in the footer (GitHub repository, docs site, changelog) are intercepted by `tauri-plugin-opener` and opened in the user's default system browser instead of navigating the webview

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| initial_navigation | page_rendered | The visitor's browser receives the static HTML response from the CDN or origin server for the root URL `/` and the browser completes the initial document render | The HTTP response status is 200 and the HTML document parses without errors that block rendering of the main content sections |
| page_rendered | header_hydrated_unauthenticated | The React island in the header hydrates with `client:load` and the session state check completes indicating no valid session exists for the current visitor | The auth client returns no active session or the session check request completes with an empty session response indicating the visitor is not signed in |
| page_rendered | header_hydrated_authenticated | The React island in the header hydrates with `client:load` and the session state check completes indicating the visitor has an active authenticated session | The auth client returns a valid session containing user profile data including an avatar image URL or user initials for the fallback display |
| page_rendered | command_copied | The visitor clicks the copy button next to the install command code block in the hero section and the clipboard write operation completes without errors | The `navigator.clipboard.writeText` call resolves indicating the command text was written to the system clipboard |
| command_copied | page_rendered | The checkmark confirmation indicator displays for 2000 ms after a successful copy operation and then the button reverts to its original copy icon state | The 2000 ms timeout elapses and the button state resets to the default copy icon ready for another copy action |

## Business Rules

- **Rule landing-page-zero-javascript-baseline:** IF the landing page is served at the root URL `/` THEN the static HTML document ships zero JavaScript to the client except for explicitly declared React islands — the count of JavaScript bundles loaded outside of React islands equals 0
- **Rule session-island-fallback-to-sign-in:** IF the React island in the header fails to load or the session check returns an error THEN the header displays the localized "Sign in" link as the default state — the count of header states that show neither sign-in nor avatar equals 0
- **Rule copy-button-confirmation-duration:** IF the visitor clicks the copy button and the clipboard write succeeds THEN the button displays a checkmark indicator for exactly 2000 ms before reverting to the copy icon — the duration of the confirmation state equals 2000 ms
- **Rule responsive-grid-column-breakpoints:** IF the viewport width is below the medium breakpoint THEN the technology stack grid displays 1 column; IF the viewport width is at or above the medium breakpoint and below the wide breakpoint THEN 2 columns are displayed; IF the viewport width is at or above the wide breakpoint THEN 3 columns are displayed — the count of grid columns matches the breakpoint range
- **Rule external-links-open-in-system-browser-on-desktop:** IF the visitor clicks an external link in the footer while running the desktop Tauri app THEN the link opens in the user's default system browser via `tauri-plugin-opener` — the count of external link navigations within the Tauri webview equals 0
- **Rule theme-toggle-no-flash:** IF the landing page renders THEN the theme toggle reads the stored preference from localStorage and applies the correct theme class before the first paint — the count of visible theme flashes during initial page load equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Visitor (any user who navigates to the root URL `/` regardless of authentication status, including first-time visitors, returning users, search engine crawlers, and desktop Tauri app users who view the landing page content) | View all landing page content including the header, hero section, technology stack grid, and footer; click the copy button to copy the install command to the clipboard; click the call-to-action button to navigate to `/signin`; click external links in the footer to open them in the browser or system browser on desktop; toggle the theme preference using the header toggle; view the authenticated avatar in the header if a valid session exists | Cannot modify any landing page content, cannot access admin functionality from the landing page, cannot bypass the sign-in flow by navigating directly to `/app` routes without a valid session, cannot disable or override the React island hydration for the session-aware header component | The visitor sees all static content on the landing page without restriction; the header displays either the "Sign in" link or the authenticated avatar based on session state; the technology stack grid, hero section, and footer content are identical for all visitors regardless of authentication status |

## Constraints

- The static HTML document for the landing page loads and renders the first contentful paint within 1500 ms on a 4G connection — the count of milliseconds from navigation start to first contentful paint equals 1500 or fewer.
- The total JavaScript bundle size for the React island in the header (session-aware toggle) is 50 KB or less after gzip compression — the count of compressed kilobytes for the island bundle equals 50 or fewer.
- The technology stack grid renders all 13 category cards with their technology names, versions, and descriptions within a single viewport scroll depth of 3 screen heights — the count of screen heights required to display all cards equals 3 or fewer.
- The clipboard write operation for the install command copy button completes within 500 ms of the click event — the count of milliseconds from click to clipboard write confirmation equals 500 or fewer.
- All user-facing text on the landing page uses @repo/i18n translation keys with zero hardcoded English strings — the count of hardcoded user-facing strings in the landing page source equals 0.
- The landing page HTML response size is 100 KB or less before compression — the count of uncompressed kilobytes for the HTML document equals 100 or fewer.

## Acceptance Criteria

- [ ] The landing page is served as a fully static SSG document at the root URL `/` with zero JavaScript shipped except for declared React islands — the count of non-island JavaScript bundles equals 0
- [ ] The header displays a localized "Sign in" link pointing to `/signin` when no valid session exists — the sign-in link element is present in the header
- [ ] The header displays the authenticated user's avatar linking to `/app` when a valid session exists — the avatar element is present in the header and the sign-in link is absent
- [ ] The header avatar falls back to user initials when no profile image exists — the initials element is present when the profile image URL is absent
- [ ] The theme toggle reads localStorage and applies the correct theme class before the first paint — the count of visible theme flashes during page load equals 0
- [ ] The hero section displays the product name, localized tagline, install command code block, copy button, and call-to-action button — all 5 elements are present in the hero section
- [ ] Clicking the copy button writes the install command text to the clipboard and displays a checkmark for 2000 ms — the clipboard content equals the install command text after clicking
- [ ] The technology stack grid displays cards for all 13 categories with technology name, version, and description — the count of rendered category cards equals 13
- [ ] The grid layout renders 1 column below 768 px viewport width, 2 columns between 768 px and 1024 px, and 3 columns above 1024 px — the column count equals 1, 2, or 3 matching the breakpoint range
- [ ] The footer displays product name, description, Product heading with 3 navigation links, and copyright line with MIT license link — all footer elements are present
- [ ] External links in the footer open in the default system browser when running in the Tauri desktop app — the count of webview navigations to external URLs equals 0
- [ ] All user-facing text on the landing page is rendered via @repo/i18n translation keys — the count of hardcoded English strings equals 0
- [ ] The first contentful paint completes within 1500 ms on a 4G connection — the count of milliseconds from navigation start to first contentful paint equals 1500 or fewer

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The visitor has JavaScript disabled in their browser and the React island for the session-aware header cannot hydrate or check session state | The static HTML renders completely including the header, hero section, technology stack grid, and footer — the header displays the "Sign in" link as its server-rendered default since the React island cannot override it without JavaScript | The "Sign in" link is visible in the header and all static content sections render without any missing elements or layout shifts |
| The visitor's browser does not support the `navigator.clipboard.writeText` API and clicks the copy button for the install command in the hero section | The copy button catches the clipboard API error and displays a localized error indicator instead of the checkmark, and the install command text remains visible in the styled code block for manual selection and copying by the visitor | The error indicator appears on the copy button and the install command code block text content is selectable for manual copying |
| The visitor loads the landing page with a locale that has incomplete translations in the @repo/i18n framework missing some translation keys for the technology stack descriptions | The i18n framework falls back to the English default translation for each missing key while rendering available translations for all other text — the page displays a mix of the selected locale and English fallback without any blank or broken text elements | The count of empty or missing text elements on the page equals 0 and untranslated strings display in English as the fallback locale |
| The visitor navigates to the landing page on the desktop Tauri app and clicks the GitHub repository link in the footer while offline with no network connection available | The `tauri-plugin-opener` invokes the system browser which opens to the GitHub URL — the system browser displays its own offline error page while the Tauri webview remains on the landing page without navigation | The Tauri webview URL remains at `/` after clicking the external link and the system browser process is launched with the target URL |
| The visitor loads the landing page and the CDN serves a stale cached version that is missing newly added technology stack cards from a recent deployment | The cached HTML renders all technology cards that were present at the time the cache was built — the visitor sees a consistent page without errors but may not see cards added in the latest deployment until the CDN cache expires or is purged | The page renders without errors and the count of technology cards matches the count present in the cached HTML document |
| The visitor accesses the root URL `/` while authenticated and the session check returns a valid session with a profile image URL that returns HTTP 404 from the image server | The header React island receives the valid session, attempts to render the avatar image, detects the image load failure, and falls back to displaying the user's initials as the avatar placeholder | The initials-based avatar element is visible in the header and the broken image element is not displayed |

## Failure Modes

- **Static HTML document fails to load because the CDN or origin server is unreachable when the visitor requests the root URL**
    - **What happens:** The visitor's browser sends a request for the root URL `/` but the CDN or origin server does not respond due to a DNS resolution failure, server downtime, or network connectivity issue between the visitor and the hosting infrastructure.
    - **Source:** The CDN provider experiences an outage, the origin server's deployment is misconfigured, or the visitor's network connection drops during the request — any of these causes prevent the HTTP response from reaching the browser.
    - **Consequence:** The browser displays its default connection error page (ERR_CONNECTION_REFUSED or similar) and the visitor sees no landing page content, no header, no hero section, and no technology stack grid until the server becomes accessible.
    - **Recovery:** The browser displays its built-in retry option and the visitor retries the request manually — the CDN or origin server returns error logs that the operations team uses to diagnose the outage and the visitor falls back to accessing the GitHub repository directly for project information.

- **React island for the session-aware header fails to hydrate due to a JavaScript bundle load error or runtime exception during initialization**
    - **What happens:** The React island JavaScript bundle fails to download because of a CDN cache miss, network interruption, or the bundle contains a runtime error that throws an uncaught exception during the hydration phase preventing the session check from executing.
    - **Source:** A deployment produces a broken island bundle due to a build error, the CDN returns a corrupted or truncated JavaScript file, or a browser extension interferes with the script execution on the page.
    - **Consequence:** The header remains in its server-rendered default state showing the "Sign in" link regardless of the visitor's actual authentication status — authenticated visitors do not see their avatar but can still navigate to `/app` manually or via the sign-in link.
    - **Recovery:** The header degrades to the static "Sign in" link as the safe default state and the visitor navigates to `/signin` or `/app` manually — the build pipeline logs the bundle error for the development team to investigate and fix in the next deployment.

- **Clipboard write operation fails when the visitor clicks the copy button for the install command in the hero section**
    - **What happens:** The visitor clicks the copy button and the `navigator.clipboard.writeText` call is rejected because the browser does not grant clipboard write permission, the page is not served over HTTPS in a non-localhost context, or the browser's clipboard API implementation throws an unexpected error during the write operation.
    - **Source:** Browser security policy denies clipboard access because the page context does not meet the Permissions API requirements, or the clipboard API is not available in the visitor's browser version, or a browser extension blocks clipboard write access on the page.
    - **Consequence:** The install command text is not copied to the clipboard and the visitor does not receive the checkmark confirmation — the command remains visible in the styled code block but the one-click copy convenience is unavailable for this visitor.
    - **Recovery:** The copy button catches the clipboard API error and displays a localized error indicator for 2000 ms, then returns to its default state — the visitor falls back to manually selecting the command text in the code block and using the browser's native copy functionality to copy the command.

- **Theme toggle localStorage read fails during initial page render causing a flash of the wrong theme before the correct preference is applied**
    - **What happens:** The theme toggle attempts to read the stored theme preference from localStorage during the initial render but the localStorage API call throws an exception because the browser is in private browsing mode with storage disabled, storage quota is exceeded, or the storage is corrupted.
    - **Source:** The browser restricts localStorage access in private browsing mode, the visitor's browser storage is full and rejects read operations, or a browser update changed the localStorage behavior for the page's origin causing the read to fail unexpectedly.
    - **Consequence:** The theme toggle cannot determine the visitor's stored preference and the page renders with the system default color scheme instead of the visitor's previously selected theme, potentially causing a brief visual inconsistency if the system default differs from the stored preference.
    - **Recovery:** The theme toggle catches the localStorage error and falls back to reading the `prefers-color-scheme` media query to apply the system default theme — the visitor sees the system-default theme and the toggle logs the storage error to the browser console for debugging purposes.

## Declared Omissions

- This specification does not define the sign-in flow that begins when the visitor clicks the "Sign in" link or the call-to-action button — that behavior is covered by the user-signs-in-with-email-otp and related authentication specifications
- This specification does not cover the `/app` SPA shell loading or organization resolution logic that executes when an authenticated visitor clicks the avatar to navigate to `/app` — that behavior is defined in the user-enters-the-app specification
- This specification does not address SEO metadata, Open Graph tags, or structured data markup for the landing page — those concerns are handled by the Astro build configuration and are outside the scope of behavioral interaction
- This specification does not define the content, ordering, or version numbers displayed in the technology stack grid cards — those values are maintained in the landing page data source and updated independently of the behavioral flow
- This specification does not cover the desktop Tauri app launch sequence or webview initialization that precedes loading the landing page — that behavior is defined in the user-launches-desktop-app specification

## Related Specifications

- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md)
    — defines the email OTP sign-in flow that begins when the visitor
    clicks the "Sign in" link or the call-to-action button on the
    landing page header or hero section
- [user-enters-the-app](user-enters-the-app.md) — defines the SPA
    shell loading and organization resolution logic that executes
    when an authenticated visitor clicks the avatar in the header to
    navigate to the `/app` route
- [user-changes-theme](user-changes-theme.md) — defines the theme
    switching mechanism and localStorage persistence that the landing
    page header's theme toggle reads during initial render to apply
    the correct theme class before the first paint
- [user-changes-language](user-changes-language.md) — defines the
    language switching mechanism that determines which @repo/i18n
    locale the landing page uses to render all localized text
    including the header, hero tagline, and footer content
- [user-launches-desktop-app](user-launches-desktop-app.md) — defines
    the Tauri desktop app launch sequence and webview initialization
    that precedes loading the landing page in the desktop app context
    where external links open in the system browser
