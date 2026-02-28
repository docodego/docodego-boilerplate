---
id: SPEC-2026-091
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [System, User]
---

[← Back to Roadmap](../ROADMAP.md)

# System Handles Errors

## Intent

This spec defines how the DoCodeGo application handles errors at the API layer through a global error handler middleware and at the frontend through TanStack Query retry behavior, error state rendering, and toast notifications. The Hono middleware chain includes a global error handler that catches all unhandled errors from route handlers and returns a structured JSON response with a `code` field and a `message` field. In development, the response includes the full stack trace for debugging. In production, error details are redacted and the message is replaced with a generic statement to prevent leaking internal implementation details. Errors map to standard HTTP status codes: 401 for authentication failures, 403 for authorization failures, 400 for validation errors with field-level Zod schema detail, 404 for missing resources, and 500 for unexpected server errors. On the frontend, TanStack Query retries failed requests once with `retry: 1` before treating the failure as definitive. Failed queries render an error state component with a retry option. Failed mutations trigger a localized toast notification through Sonner displaying a user-readable error message. Buttons triggering async operations show a loading state to prevent double submission.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Hono global error handler middleware (the outermost middleware in the Hono middleware chain that catches all unhandled errors propagating from route handlers and transforms them into structured JSON error responses with the matching HTTP status codes) | read/write | When any route handler or downstream middleware throws an unhandled error or exception, the global error handler catches it, determines the matching HTTP status code based on the error type, constructs the structured JSON response, and sends it to the client | The global error handler itself throws an error during response construction — the Cloudflare Workers runtime returns a generic HTTP 500 response with no structured body and the error details are lost until the developer inspects the Workers runtime logs |
| Zod schema validation (runtime schema validation library used in API route handlers to validate request input against defined schemas, producing detailed field-level error information when input does not match the expected structure) | read | When a route handler receives request input (body, query parameters, path parameters), Zod validates the input against the defined schema, and if validation fails, the handler throws a validation error containing the field-level details that the global error handler transforms into an HTTP 400 response | The Zod library fails to load or the schema definition is missing from the route handler — the request input is not validated and passes through to the handler logic unchecked, potentially causing a runtime error that the global error handler catches as an HTTP 500 |
| TanStack Query on the frontend (data fetching and caching library configured with `retry: 1` that automatically retries failed requests once before treating the failure as definitive and transitioning the query to an error state) | read/write | When a query or mutation request to the API fails with a network error or an HTTP error status, TanStack Query evaluates the retry configuration, retries the request once for queries, and if the retry also fails, transitions the query to its error state or triggers the mutation error handler | TanStack Query fails to initialize due to a missing query client provider in the React component tree — all data fetching calls throw a context error and the application cannot make any API requests until the provider is added to the component tree |
| Sonner toast notification library (frontend toast notification system that displays localized, user-readable error messages for failed mutations, ensuring the user is informed when an action they initiated did not succeed) | write | When a mutation fails after TanStack Query reports the error, the mutation error handler invokes Sonner to display a localized toast notification with a user-readable error message describing the failed action (for example "Failed to save changes" or "Invitation could not be sent") | Sonner fails to render the toast due to a missing toast container in the DOM or a CSS rendering issue — the mutation error is caught by TanStack Query but the user receives no visual feedback about the failure until they notice the unchanged state |
| Loading state management on action buttons (frontend pattern where buttons triggering async operations display a spinner or disabled appearance while the request is in flight, preventing users from clicking repeatedly and submitting duplicate requests) | write | When the user clicks a button that triggers an async mutation, the button transitions to its loading state (showing a spinner and becoming non-clickable) before the request is sent, and returns to its normal clickable state when the request completes with either success or failure | The loading state binding fails due to a React state management error — the button remains clickable during the request and the user can click it multiple times, causing duplicate mutation requests to be sent to the API |

## Behavioral Flow

1. **[User]** performs an action in the application that triggers an
    API request — either a data query (fetching a resource) or a
    mutation (creating, updating, or deleting a resource)

2. **[System]** the API route handler receives the request and
    processes it through the Hono middleware chain — if the handler
    throws an unhandled error, the global error handler middleware
    catches the error before the response is sent

3. **[System]** the global error handler examines the error type and
    maps it to the matching HTTP status code: 401 for authentication
    failures (user not signed in or session expired), 403 for
    authorization failures (user lacks permission or account is banned),
    400 for Zod validation errors, 404 for missing resources, and 500
    for unexpected server errors

4. **[System]** the error handler constructs a structured JSON response
    with the format `{ code: "ERROR_CODE", message: "..." }` — in
    development the response includes the full stack trace, and in
    production the message is replaced with a generic statement to
    prevent leaking internal implementation details

5. **[System]** for HTTP 400 validation errors, the Zod schema
    rejection produces field-level detail in the error response
    specifying which fields failed and why, giving the frontend enough
    information to highlight specific form fields that need correction

6. **[System]** on the frontend, TanStack Query receives the error
    response and evaluates its retry configuration — for queries (data
    fetching), TanStack Query retries the failed request once with
    `retry: 1` before treating the failure as definitive

7. **[System]** if the query retry also fails, TanStack Query
    transitions the query to its error state and the component renders
    an error state UI that communicates the problem to the user and
    offers a retry button to attempt the request again

8. **[User]** sees the error state component in the UI when a query
    definitively fails and can click the retry button to re-attempt
    the data fetch

9. **[System]** for mutations (saving a profile, sending an invitation,
    deleting a resource), TanStack Query does not retry automatically
    and instead triggers the mutation error handler immediately upon
    receiving an error response from the API

10. **[System]** the mutation error handler invokes Sonner to display a
    localized toast notification with a user-readable error message —
    for example "Failed to save changes" or "Invitation could not be
    sent" — ensuring the user is informed even if they have navigated
    away from the form

11. **[User]** sees the toast notification appear and understands that
    the action they initiated did not succeed, with the message
    displayed in their active locale via @repo/i18n translation keys

12. **[System]** buttons that trigger async operations show a loading
    state (spinner or disabled appearance) while the request is in
    flight, preventing the user from clicking repeatedly and submitting
    duplicate requests — the loading state clears when the request
    completes whether it succeeds or fails

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| request_pending | error_caught | A route handler or downstream middleware throws an unhandled error during request processing, and the global error handler middleware catches the exception before the response is sent to the client | The error propagates up the Hono middleware chain without being handled by an inner middleware and reaches the global error handler |
| error_caught | response_sent_4xx | The global error handler identifies the error as a client-side issue (authentication failure, authorization failure, validation error, or missing resource) and constructs a structured JSON response with the corresponding 4xx HTTP status code | The error type maps to HTTP 400, 401, 403, or 404 based on the error classification logic in the global error handler |
| error_caught | response_sent_500 | The global error handler identifies the error as an unexpected server-side failure that does not map to a known client error type and constructs a redacted structured JSON response with HTTP 500 status code | The error type does not match any known client error classification and the handler defaults to the 500 status code with a generic error message in production |
| response_sent_4xx | frontend_retry | The frontend receives the 4xx error response and TanStack Query evaluates the retry configuration — for queries, the library retries the request once based on the `retry: 1` configuration before treating the failure as definitive | The failed request is a query (not a mutation) and TanStack Query has not exhausted its retry count of 1 |
| response_sent_4xx | toast_displayed | The frontend receives the 4xx error response for a mutation and the mutation error handler invokes Sonner to display a localized toast notification with a user-readable error message describing the failed action | The failed request is a mutation (not a query) and the Sonner toast container is present in the DOM to render the notification |
| frontend_retry | error_state_rendered | The retry request also fails and TanStack Query transitions the query to its definitive error state, causing the component to render an error state UI with a description of the problem and a retry button | The retry count is exhausted (1 retry attempted and failed) and TanStack Query marks the query as definitively failed |
| error_state_rendered | request_pending | The user clicks the retry button in the error state UI, triggering a new query request to the API that restarts the request lifecycle from the beginning | The user interacts with the retry button and the component dispatches a new query fetch to TanStack Query |

## Business Rules

- **Rule structured-json-error-format:** IF any API route handler
    throws an unhandled error THEN the global error handler returns a
    structured JSON response with format
    `{ code: "ERROR_CODE", message: "..." }` — the count of error
    responses without a `code` field equals 0
- **Rule production-redacts-details:** IF the application runs in
    production mode and the global error handler catches an unexpected
    server error THEN the response message is replaced with a generic
    statement — the count of production error responses containing
    stack traces equals 0
- **Rule development-includes-stack-trace:** IF the application runs
    in development mode and the global error handler catches an error
    THEN the response includes the full stack trace — the stack trace
    field in development error responses is non-empty
- **Rule auth-failure-returns-401:** IF a request fails because the
    user is not signed in or the session has expired THEN the API
    returns HTTP 401 — the HTTP status code for authentication failures
    equals 401
- **Rule authz-failure-returns-403:** IF a request fails because the
    user is signed in but lacks permission or the account is banned
    THEN the API returns HTTP 403 — the HTTP status code for
    authorization failures equals 403
- **Rule validation-failure-returns-400:** IF a Zod schema validation
    rejects request input THEN the API returns HTTP 400 with
    field-level detail specifying which fields failed — the HTTP status
    code for validation failures equals 400
- **Rule missing-resource-returns-404:** IF a request targets a
    resource that does not exist THEN the API returns HTTP 404 — the
    HTTP status code for missing resources equals 404
- **Rule unexpected-error-returns-500:** IF an unexpected server error
    occurs that does not map to a known client error type THEN the API
    returns HTTP 500 — the HTTP status code for unexpected server
    errors equals 500
- **Rule query-retry-once:** IF a frontend query fails THEN TanStack
    Query retries the request once before treating the failure as
    definitive — the count of automatic retries per failed query
    equals 1
- **Rule mutation-no-auto-retry:** IF a frontend mutation fails THEN
    TanStack Query does not retry automatically and triggers the error
    handler immediately — the count of automatic retries per failed
    mutation equals 0
- **Rule toast-on-mutation-failure:** IF a mutation fails THEN a
    localized toast notification is displayed through Sonner — the
    count of mutation failures without a toast notification equals 0
- **Rule loading-state-prevents-double-submit:** IF an async operation
    is in flight THEN the trigger button shows a loading state and is
    non-clickable — the count of duplicate requests sent from repeated
    clicks during a loading state equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| System (the API runtime that catches unhandled errors through the global error handler middleware, classifies error types, constructs structured JSON responses with the matching HTTP status codes, and manages the development versus production response format toggle) | Catch all unhandled errors from route handlers and downstream middleware, classify errors into authentication (401), authorization (403), validation (400), not-found (404), and server (500) categories, construct structured JSON error responses, include full stack traces in development mode, redact error details in production mode, extract field-level validation detail from Zod schema rejections | Cannot retry failed requests on behalf of the client, cannot suppress errors from reaching the global handler without an inner middleware explicitly catching them, cannot display toast notifications or error state UI on the frontend | The system has visibility into the full error stack trace, the error type classification, the environment mode (development or production), and the Zod validation field details, but has no visibility into whether the frontend successfully displayed the error to the user |
| User (the person using the application who triggers API requests through queries and mutations, sees error state components for failed queries, receives toast notifications for failed mutations, and interacts with retry buttons to re-attempt failed operations) | View error state components for definitively failed queries and click the retry button to re-attempt the request, view toast notifications for failed mutations with localized error messages, interact with buttons that show loading states during async operations, retry failed uploads or form submissions by re-initiating the action | Cannot view raw error details, stack traces, or internal error codes in production mode, cannot bypass the TanStack Query retry logic to force immediate error state, cannot dismiss the loading state on a button while a request is still in flight | The user sees localized error messages in toast notifications, sees error state components with retry options for failed queries, sees the loading state on buttons during async operations, but does not see the internal error code mapping, the Zod field-level detail beyond what the form highlights, or the production-redacted original error message |

## Constraints

- The global error handler processes caught errors and returns the
    structured JSON response within 10 ms of catching the error — the
    count of milliseconds from error catch to response sent equals 10
    or fewer.
- The TanStack Query retry for failed queries executes within 1000 ms
    of the initial failure — the count of milliseconds from initial
    failure to retry request sent equals 1000 or fewer.
- The Sonner toast notification for a failed mutation appears within
    500 ms of the mutation error being received by the frontend — the
    count of milliseconds from error received to toast displayed equals
    500 or fewer.
- The error state component renders within 200 ms of TanStack Query
    marking a query as definitively failed — the count of milliseconds
    from query error state to component render equals 200 or fewer.
- The loading state on async action buttons activates within 100 ms
    of the user clicking the button — the count of milliseconds from
    click event to loading state display equals 100 or fewer.
- All user-facing error messages in toast notifications use @repo/i18n
    translation keys with zero hardcoded English strings — the count
    of hardcoded English strings in toast error messages equals 0.

## Acceptance Criteria

- [ ] The global error handler catches unhandled errors from route handlers and returns a structured JSON response with a `code` field — the `code` field in every error response is non-empty
- [ ] The error response includes the format `{ code, message }` for all error types — the count of error responses missing the `message` field equals 0
- [ ] In production mode the error response for HTTP 500 contains a generic message with no stack trace — the count of stack trace characters in production 500 responses equals 0
- [ ] In development mode the error response includes the full stack trace for debugging — the stack trace field in development error responses is non-empty
- [ ] Authentication failures return HTTP 401 when the user is not signed in or the session has expired — the HTTP status code for unauthenticated requests equals 401
- [ ] Authorization failures return HTTP 403 when the user lacks permission or the account is banned — the HTTP status code for unauthorized requests equals 403
- [ ] Zod validation failures return HTTP 400 with field-level detail specifying which fields failed — the HTTP status code equals 400 and the field detail array is non-empty
- [ ] Missing resource requests return HTTP 404 — the HTTP status code for requests targeting nonexistent resources equals 404
- [ ] Unexpected server errors return HTTP 500 with a redacted message in production — the HTTP status code equals 500 and the message contains no internal implementation details
- [ ] TanStack Query retries failed queries once before showing the error state — the count of automatic retries per failed query equals 1
- [ ] The error state component renders with a retry button when a query definitively fails — the retry button element is present in the error state component
- [ ] Failed mutations trigger a localized toast notification through Sonner — the toast element is present within 500 ms of mutation failure
- [ ] Toast messages use @repo/i18n translation keys with zero hardcoded English strings — the count of hardcoded strings in mutation error toasts equals 0
- [ ] Buttons triggering async operations show a loading state while the request is in flight — the button disabled attribute is present during the async operation
- [ ] The loading state clears when the request completes whether it succeeds or fails — the button disabled attribute is absent after request completion

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| A route handler throws an error that is neither a known client error type nor a standard JavaScript Error object (for example a thrown string or number primitive) | The global error handler catches the non-standard thrown value, treats it as an unexpected server error, and returns HTTP 500 with the structured JSON format containing a generic message in production | The HTTP status code equals 500 and the `code` field equals `INTERNAL_ERROR` |
| Multiple Zod validation errors occur on the same request with failures on 3 different fields simultaneously | The API returns HTTP 400 with the structured JSON response containing field-level detail for all 3 failing fields, not just the first one encountered during validation | The count of field-level error entries in the response body equals 3 |
| TanStack Query's retry request succeeds after the initial query failure, recovering from a transient network error without user intervention | TanStack Query transitions the query from the error state back to the success state, the component renders the successful data, and no error state UI or toast notification is displayed to the user | The query status equals `success` after the retry and the count of error state components displayed equals 0 |
| A mutation fails while the user has already navigated away from the form that triggered it and is viewing a different screen in the application | The Sonner toast notification is still displayed because it renders at the application root level outside the form component, ensuring the user is informed of the failure regardless of their current navigation state | The toast element is present and visible on the current screen even though the user has navigated away from the originating form |
| The global error handler catches an error but the JSON response serialization itself throws an error due to a circular reference in the error object | The Cloudflare Workers runtime catches the serialization failure and returns a minimal HTTP 500 response with no body, and the original error details are available in the Workers runtime logs | The HTTP status code equals 500 and the response body is empty or contains the Workers runtime default error output |
| A button is clicked twice in rapid succession before the loading state activates within the 100 ms threshold due to a React render cycle exceeding 100 ms | The second click event fires while the first request is already in flight, potentially sending a duplicate mutation request to the API because the loading state had not yet disabled the button | The count of mutation requests sent equals 2 if the loading state activation exceeded 100 ms, confirming the need for the 100 ms constraint |

## Failure Modes

- **The global error handler middleware itself throws an unhandled error during response construction**
    - **What happens:** The global error handler catches an error from a route handler but encounters its own unhandled exception during error classification or JSON response construction, such as a TypeError when accessing properties on an unexpected error object shape.
    - **Source:** The caught error object has an unexpected shape that the error classification logic does not handle (for example a Symbol thrown instead of an Error instance), or the JSON serialization encounters a non-serializable value in the error payload.
    - **Consequence:** The structured JSON error response is not sent to the client, and the Cloudflare Workers runtime returns its default HTTP 500 response with no structured body, making it harder for the frontend to parse and display a meaningful error message.
    - **Recovery:** The Workers runtime logs the unhandled error from the global handler in the runtime console, the frontend receives the generic HTTP 500, and the developer alerts the team to add handling for the unexpected error shape in the global error handler.

- **Sonner toast container is missing from the DOM when a mutation error occurs preventing the notification from rendering**
    - **What happens:** A mutation fails and the error handler invokes Sonner to display a toast notification, but the Sonner toast container component (`<Toaster />`) is not mounted in the DOM because it was accidentally removed during a refactor or is conditionally rendered and currently unmounted.
    - **Source:** A code refactor removed the `<Toaster />` component from the application layout, or the component is wrapped in a conditional render that evaluates to false, or the CSS positioning of the container places it outside the visible viewport.
    - **Consequence:** The mutation error is caught by TanStack Query and processed by the error handler, but the user receives no visual feedback about the failure because the toast cannot render without its container, leaving the user unaware that their action did not succeed.
    - **Recovery:** The application logs the toast rendering failure when the Sonner API call returns without displaying a notification, and the developer notifies the team to restore the `<Toaster />` component to the application layout root so subsequent toast notifications render correctly.

- **TanStack Query retry triggers a duplicate mutation because the retry logic is accidentally applied to a mutation instead of only queries**
    - **What happens:** A mutation request fails and TanStack Query retries it once due to a misconfiguration where the `retry: 1` setting is applied globally to all requests instead of only queries, causing a side-effecting mutation (such as a resource deletion or payment charge) to execute twice.
    - **Source:** The TanStack Query client configuration applies `retry: 1` at the global level without distinguishing between queries and mutations, or a specific mutation hook overrides its retry setting to a non-zero value.
    - **Consequence:** The mutation executes twice on the server, potentially creating duplicate records, sending duplicate emails, or double-charging the user, depending on the mutation's side effects and whether the server implements idempotency.
    - **Recovery:** The server-side mutation handler rejects the duplicate request using an idempotency key check, returns error HTTP 409 or the original success response for the duplicate, and the developer logs the misconfiguration to correct the TanStack Query retry setting so mutations default to `retry: 0`.

- **Loading state binding on an action button fails to activate within the 100 ms threshold allowing a double-click submission**
    - **What happens:** The user clicks a button that triggers an async mutation, but the React state update that activates the loading state (disabling the button and showing the spinner) takes longer than 100 ms due to a render cycle exceeding the threshold, and the user clicks the button again during the gap.
    - **Source:** A heavy component tree re-render caused by the state update blocks the main thread for more than 100 ms, a concurrent mode transition delays the state commit, or the loading state is managed through a context provider that triggers a wide subtree re-render.
    - **Consequence:** Two identical mutation requests are sent to the API because the button was clickable during the gap between the first click and the loading state activation, potentially causing duplicate side effects on the server.
    - **Recovery:** The mutation handler on the server rejects the duplicate request using request deduplication or an idempotency key, returns the result of the first request for both calls, and the developer logs the render cycle duration to optimize the component tree and ensure the loading state activates within the 100 ms threshold.

## Declared Omissions

- This specification does not define specific error codes or messages for individual API endpoints — each endpoint defines its own error codes based on its business logic and this specification defines the shared error handling infrastructure that all endpoints use
- This specification does not cover rate limiting or throttling error responses (HTTP 429) — rate limiting requires a separate specification defining the rate limit configuration, counting mechanism, and retry-after header behavior
- This specification does not address WebSocket or real-time streaming error handling — the defined error handling applies to HTTP request-response cycles and real-time error propagation requires a separate specification with its own error framing protocol
- This specification does not define the Zod schema structures used by individual route handlers — this specification defines how Zod validation errors are transformed into HTTP 400 responses and the schema definitions are the responsibility of each endpoint's specification
- This specification does not cover client-side form validation that occurs before the request is sent to the API — frontend validation is a UX optimization that does not replace the server-side validation defined in this error handling flow

## Related Specifications

- [user-uploads-a-file](user-uploads-a-file.md) — defines the file
    upload flow where HTTP 400 validation errors for oversized files
    or disallowed content-types and HTTP 502 storage errors use the
    structured JSON error format defined in this error handling
    specification
- [session-lifecycle](session-lifecycle.md) — defines the session
    creation, refresh, and expiry behavior that determines when the
    error handler returns HTTP 401 for authentication failures and
    when expired sessions trigger the re-authentication flow
- [system-detects-locale](system-detects-locale.md) — defines the
    locale detection flow that determines which language the frontend
    uses for localized error messages in toast notifications and error
    state components displayed through this error handling flow
- [user-changes-language](user-changes-language.md) — defines the
    language switching mechanism that updates the active locale used
    by @repo/i18n translation keys in error toast messages and error
    state component text rendered by this error handling system
