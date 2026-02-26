[← Back to Index](README.md)

# System Handles Errors

## Global Error Handler

A global error handler middleware in the Hono middleware chain catches all unhandled errors that propagate from route handlers. Every error response follows a structured JSON format: `{ code: "INTERNAL_ERROR", message: "..." }`. In development, the response includes the full stack trace to help with debugging. In production, error details are redacted and the message is replaced with a generic statement — internal implementation details never leak to end users.

## HTTP Status Code Mapping

Errors map to standard HTTP status codes based on their type. Authentication failures return 401 (the user is not signed in or the session has expired). Authorization failures return 403 (the user is signed in but lacks permission, or the account is banned). Validation errors return 400 with field-level detail — when a Zod schema rejects input, the response includes which fields failed and why, giving the frontend enough information to highlight specific form fields. Resources that do not exist return 404. Unexpected server errors return 500 with the redacted response described above.

## Frontend Error Handling

On the frontend, TanStack Query is configured with `retry: 1` — a failed request is retried once automatically before being treated as a real failure. This handles transient network issues without burdening the user. When a query definitively fails, the component renders an error state that communicates the problem and offers a way to retry.

For mutations (saving a profile, sending an invitation, deleting a resource), failures trigger a toast notification through Sonner. The toast displays a user-readable error message — for example, "Failed to save changes" or "Invitation could not be sent." This ensures the user is always informed when an action they initiated did not succeed, even if they have navigated away from the form that triggered it.

## Preventing Double Submission

Buttons that trigger async operations show a loading state (spinner or disabled appearance) while the request is in flight. This prevents users from clicking repeatedly and submitting the same action multiple times. The loading state clears when the request completes, whether it succeeds or fails.
