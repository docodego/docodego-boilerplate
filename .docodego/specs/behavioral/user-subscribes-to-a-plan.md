---
id: SPEC-2026-093
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Subscribes to a Plan

## Intent

This spec defines how an authenticated user subscribes to a paid plan
through the DodoPayments integration to unlock additional capabilities
or higher usage limits beyond the free tier. Every new user starts on
the free tier with access to core features and no payment method
required. When the user navigates to the billing page within the
dashboard, the page displays available plans with their features and
pricing. The user selects a plan and enters the checkout flow powered
by DodoPayments. Upon successful payment, a subscription record is
created and associated with the user's account through the Better Auth
DodoPayments plugin. The user's plan information is reflected in their
session and user record, making it available to both the frontend for
UI adjustments and the backend for feature gating. All subscription
status transitions are event-driven through DodoPayments webhook
callbacks — activation after initial payment, cancellation, payment
failure resulting in past-due state, or renewal. Plan-based feature
gating is enforced at the API level where route handlers check the
user's current plan before allowing access to premium features,
keeping all authorization logic server-side where it cannot be
bypassed by a modified client.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| DodoPayments checkout flow (external payment processing service that collects payment details from the user through a hosted checkout page and processes the initial subscription payment securely without the application handling raw card data) | read/write | When the user selects a plan on the billing page and initiates the checkout flow, the client redirects the user to the DodoPayments hosted checkout page where they enter payment details and confirm the subscription | DodoPayments checkout is unreachable due to a service outage or network failure and the user cannot complete the subscription — the billing page displays an error message and the user retries the checkout after the DodoPayments service is restored |
| DodoPayments webhook endpoint (API route that receives POST callbacks from DodoPayments when subscription status changes occur, including activation after payment, cancellation, payment failure, and renewal events) | write | When DodoPayments processes a subscription event such as initial activation, cancellation by the user, payment failure, or automatic renewal, it sends an HTTP POST webhook to the configured API endpoint with the event payload | The webhook endpoint is unreachable because the API server is down or the route is misconfigured — DodoPayments retries the webhook delivery according to its retry policy and the subscription status update is delayed until the endpoint becomes available |
| Better Auth DodoPayments plugin (server-side authentication plugin that processes incoming DodoPayments webhooks, validates webhook signatures, and updates the subscription record in the database to reflect the current plan status for the authenticated user) | read/write | When a DodoPayments webhook arrives at the API endpoint, the Better Auth plugin validates the webhook signature, extracts the subscription event data, and updates the user's subscription record in the database with the new plan status | The plugin fails to process the webhook due to a signature validation error or database write failure — the plugin returns an HTTP 500 error and DodoPayments retries the webhook according to its retry schedule until the processing succeeds |
| Application database (stores user records, subscription records, and plan information that the Better Auth plugin writes when processing webhooks and that route handlers read when enforcing plan-based feature gating at the API level) | read/write | When the Better Auth plugin processes a webhook event it writes the subscription status change to the database, and when API route handlers check the user's plan for feature gating they read the current subscription record from the database | The database is unreachable due to a connection failure or query timeout — the webhook processing fails and returns an HTTP 500 error causing DodoPayments to retry, and feature gating requests fall back to denying access until the database connection is restored |
| Billing page in the dashboard (frontend interface within the authenticated dashboard that displays available plans with pricing and features, provides the plan selection interface, and initiates the DodoPayments checkout flow when the user selects a plan) | read | When the authenticated user navigates to the billing section of the dashboard, the page fetches available plans from the API and renders them with their features, pricing, and current subscription status | The billing page fails to load plan data because the API endpoint returns an error — the page displays a loading error message and the user retries by refreshing the page after the API returns to normal operation |

## Behavioral Flow

1. **[User]** navigates to the billing page within the authenticated
    dashboard to view available subscription plans — the application
    is fully usable on the free tier and subscribing to a paid plan
    is optional for unlocking additional capabilities or higher limits

2. **[Billing Page]** fetches the list of available plans from the
    API including plan names, feature descriptions, and pricing for
    each tier and renders them in a comparison layout showing what
    each plan includes relative to the free tier

3. **[User]** reviews the available plans and selects the plan that
    matches their needs by clicking the subscribe button on the
    desired plan card

4. **[Billing Page]** initiates the DodoPayments checkout flow by
    calling the subscription creation endpoint on the API, which
    returns a checkout URL or session identifier that redirects the
    user to the DodoPayments hosted checkout page

5. **[User]** enters their payment details on the DodoPayments hosted
    checkout page which collects card information in an isolated
    environment without the application's servers handling raw
    payment data

6. **[User]** confirms the subscription by completing the payment on
    the DodoPayments checkout page — DodoPayments processes the
    payment and creates the subscription record on their platform

7. **[DodoPayments]** sends a webhook callback to the API's webhook
    endpoint with the subscription activation event payload indicating
    that the initial payment has succeeded and the subscription is
    now active

8. **[Better Auth Plugin]** receives the webhook, validates the
    DodoPayments signature to confirm the webhook is authentic, and
    processes the activation event by creating a subscription record
    in the application database associated with the user's account

9. **[Better Auth Plugin]** updates the user's session and user
    record with the new plan information making the subscription
    status available to both the frontend for UI adjustments and the
    backend for feature gating decisions

10. **[User]** is redirected back to the billing page after completing
    checkout and sees their active subscription status reflected on
    the page including the plan name, billing cycle, and next renewal
    date

11. **[API Route Handler]** checks the user's current plan from the
    subscription record in the database when the user attempts to
    access a premium feature — if the user's plan includes access the
    request proceeds, otherwise the API returns HTTP 403

12. **[Billing Page]** displays an upgrade prompt when the user on
    the free tier attempts to access a premium feature and the API
    returns HTTP 403 indicating the feature requires a paid plan

13. **[DodoPayments]** sends additional webhook callbacks when
    subscription status changes occur — cancellation by the user,
    payment failure resulting in a past-due state, or successful
    automatic renewal — and the Better Auth plugin processes each
    event to update the subscription record accordingly

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| free_tier | checkout_in_progress | The user selects a paid plan on the billing page and the application initiates the DodoPayments checkout flow redirecting the user to the hosted payment page | The user is authenticated and has an active session, the selected plan exists in the available plans list, and the DodoPayments checkout URL is successfully generated by the API |
| checkout_in_progress | subscribed_active | DodoPayments sends a webhook with the subscription activation event after the user completes payment and the Better Auth plugin creates the subscription record in the database | The webhook signature validation passes, the payment processing completes with a success status, and the database write for the subscription record succeeds |
| checkout_in_progress | free_tier | The user abandons the checkout flow by closing the DodoPayments checkout page or the payment fails during processing due to an invalid card or insufficient funds | The DodoPayments checkout session expires without a successful payment event or DodoPayments sends a payment failure webhook indicating the transaction was declined |
| subscribed_active | subscribed_past_due | DodoPayments sends a webhook indicating that an automatic renewal payment has failed due to an expired card, insufficient funds, or a payment processor error | The webhook signature validation passes and the event type indicates a payment failure on a renewal attempt for the active subscription |
| subscribed_past_due | subscribed_active | DodoPayments sends a webhook indicating that a retry payment has succeeded after a previous renewal failure and the subscription is restored to active status | The webhook signature validation passes and the event type indicates a successful payment that resolves the past-due state |
| subscribed_active | cancellation_pending | The user initiates cancellation from the billing portal and DodoPayments sends a webhook indicating the subscription will not renew at the end of the current billing period | The webhook signature validation passes and the event type indicates a cancellation request with an end-of-period effective date |
| cancellation_pending | free_tier | The current billing period ends and DodoPayments sends a webhook indicating the subscription has fully expired and is no longer active | The webhook signature validation passes, the event type indicates subscription expiration, and the Better Auth plugin removes the active subscription record from the user's account |
| subscribed_past_due | free_tier | DodoPayments exhausts all payment retry attempts and sends a webhook indicating the subscription has been terminated due to repeated payment failure | The webhook signature validation passes and the event type indicates subscription termination after all retry attempts have failed |

## Business Rules

- **Rule free-tier-no-payment-required:** IF a new user creates an
    account THEN the user starts on the free tier with access to core
    features — the count of payment methods required to access the
    free tier equals 0
- **Rule checkout-creates-subscription-on-success:** IF the user
    completes the DodoPayments checkout with a successful payment THEN
    the Better Auth plugin creates a subscription record in the
    database associated with the user's account — the count of
    subscription records created after successful payment equals 1
- **Rule webhook-driven-status-transitions:** IF a subscription
    status changes on DodoPayments THEN the status update is delivered
    through a webhook callback — the count of polling requests sent
    from the application to DodoPayments to check subscription status
    equals 0
- **Rule feature-gating-enforced-server-side:** IF a user on the
    free tier attempts to access a premium feature THEN the API route
    handler returns HTTP 403 — the count of premium feature requests
    that bypass server-side plan checks equals 0
- **Rule webhook-signature-validated:** IF a webhook arrives at the
    API endpoint THEN the Better Auth plugin validates the
    DodoPayments signature before processing the event — the count
    of unsigned or invalid-signature webhooks processed into database
    updates equals 0
- **Rule plan-info-available-in-session:** IF the Better Auth plugin
    creates or updates a subscription record THEN the user's session
    and user record reflect the current plan status — the count of
    session reads that return stale plan information after a webhook
    update equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User (authenticated user who navigates to the billing page, selects a plan, completes the DodoPayments checkout flow, and receives plan-based feature access determined by their active subscription status) | View available plans on the billing page, select a plan and enter the DodoPayments checkout flow, complete payment to activate a subscription, access features permitted by their current plan, view their active subscription status on the billing page | Cannot modify their subscription record directly in the database without going through the DodoPayments checkout or billing portal flow, cannot access premium features when on the free tier without an active paid subscription, cannot forge or replay webhook events to change their plan status | The user sees available plans with pricing on the billing page, sees their current plan name and billing cycle after subscribing, sees an upgrade prompt when attempting to access a premium feature on the free tier, and does not see internal webhook processing details or other users' subscription records |

## Constraints

- The billing page loads and renders the available plan listing
    within 2000 ms of the user navigating to the billing section —
    the count of milliseconds from navigation to rendered plan list
    equals 2000 or fewer.
- The API processes incoming DodoPayments webhooks and updates the
    subscription record in the database within 5000 ms of receiving
    the webhook request — the count of milliseconds from webhook
    receipt to database update equals 5000 or fewer.
- The feature gating check in API route handlers completes within
    50 ms per request by reading the subscription record from the
    database or session cache — the count of milliseconds from
    feature gate check start to decision equals 50 or fewer.
- The DodoPayments webhook endpoint validates the webhook signature
    before processing any event data — the count of webhook events
    processed without signature validation equals 0.

## Acceptance Criteria

- [ ] The billing page displays available plans with names, features, and pricing when the user navigates to the billing section — the count of plan entries rendered equals at least 1
- [ ] The user can select a plan and enter the DodoPayments checkout flow — the checkout URL returned by the API is non-empty when the user clicks subscribe
- [ ] A subscription record is created in the database after the user completes payment and the webhook is processed — the count of subscription records for the user after activation equals 1
- [ ] The user's session reflects the active plan status after the webhook creates the subscription record — the plan field in the session data is non-empty after activation
- [ ] The API returns HTTP 403 when a free-tier user attempts to access a premium feature — the response status code returned equals 403
- [ ] The billing page displays an upgrade prompt when the API returns HTTP 403 for a premium feature access attempt — the upgrade prompt element is present on the page
- [ ] DodoPayments webhook signature is validated before processing any event — the count of webhooks processed with invalid signatures equals 0
- [ ] The subscription status updates to past-due when DodoPayments sends a payment failure webhook — the subscription status field in the database equals the value past_due after processing
- [ ] The user reverts to the free tier when the subscription expires after cancellation — the count of active subscription records for the user after expiration equals 0
- [ ] All subscription status transitions are driven by DodoPayments webhooks — the count of polling requests sent to DodoPayments to check subscription status equals 0
- [ ] The webhook endpoint processes activation events and updates the database within 5000 ms — the count of milliseconds from webhook receipt to database update equals 5000 or fewer
- [ ] New users start on the free tier with access to core features without a payment method — the count of payment methods required for free tier access equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user completes the DodoPayments checkout but the activation webhook is delayed by more than 30 seconds due to DodoPayments delivery latency | The user is redirected back to the billing page which shows the subscription as pending until the webhook arrives and the Better Auth plugin processes the activation event — the user can refresh the page to see the updated status | The billing page displays a pending status until the webhook is processed, and after processing the plan status updates to active |
| The user closes the DodoPayments checkout page before completing payment and the checkout session expires without a successful payment event | No subscription record is created in the database and the user remains on the free tier — the billing page continues to show the free tier status and the plan selection options | The count of subscription records for the user remains 0 and the billing page renders the free tier status with plan selection available |
| DodoPayments sends a duplicate webhook for the same activation event because the first delivery received an HTTP 500 error due to a transient database failure | The Better Auth plugin processes the second webhook delivery and creates the subscription record — the plugin uses idempotency checks to prevent duplicate subscription records from being created for the same event | The count of subscription records for the user after processing duplicate webhooks equals 1 |
| A user with an active subscription attempts to subscribe to a different plan without canceling the current subscription first | The billing page displays the user's current active plan and provides an option to change plans through the billing portal rather than creating a duplicate subscription — the change plan flow is handled through the DodoPayments portal | The count of active subscription records for the user remains 1 and the billing page displays the current plan with a change option |
| The DodoPayments webhook endpoint receives a webhook with an invalid signature that does not match the configured signing secret | The Better Auth plugin rejects the webhook and returns an HTTP 401 error without processing the event or updating the database — the subscription status remains unchanged | The count of database writes triggered by invalid-signature webhooks equals 0 and the endpoint returns HTTP 401 |
| The user's payment method fails on the first renewal attempt and DodoPayments transitions the subscription to past-due status through a webhook | The Better Auth plugin updates the subscription status to past-due in the database and the billing page reflects the past-due status — premium features remain accessible during the DodoPayments retry grace period | The subscription status in the database equals past_due and the billing page displays a payment update notice to the user |

## Failure Modes

- **DodoPayments checkout service is unavailable when the user attempts to subscribe to a plan**
    - **What happens:** The user selects a plan on the billing page and the application calls the API to initiate the checkout flow, but the DodoPayments service is unreachable and the API cannot generate a checkout URL or redirect the user to the hosted payment page.
    - **Source:** A DodoPayments platform outage, a network connectivity issue between the API server and the DodoPayments service, or an expired or invalid DodoPayments API key that prevents the checkout session from being created.
    - **Consequence:** The user cannot complete the subscription process and remains on the free tier without access to paid features — the billing page cannot initiate the checkout flow until the DodoPayments service becomes available again.
    - **Recovery:** The API returns an error response with the checkout failure reason, the billing page displays a notification explaining that payment processing is temporarily unavailable, and the user retries the subscription after the DodoPayments service is restored.

- **Webhook processing fails due to a database write error when updating the subscription record after a successful payment**
    - **What happens:** DodoPayments sends the activation webhook after the user completes payment, the Better Auth plugin validates the signature, but the database write to create the subscription record fails due to a connection timeout, constraint violation, or storage quota exceeded error.
    - **Source:** A database connection pool exhaustion, a schema constraint violation caused by a data format mismatch between the webhook payload and the database schema, or the database storage quota being exceeded on the hosting platform.
    - **Consequence:** The user's payment has been collected by DodoPayments but the subscription record is not created in the application database — the user does not receive access to premium features despite having paid, and the billing page continues to show the free tier status.
    - **Recovery:** The Better Auth plugin returns an HTTP 500 error for the webhook and DodoPayments retries the webhook delivery according to its retry policy — the database write succeeds on a subsequent retry after the connection or storage issue is resolved, and the user's subscription is activated.

- **Feature gating check fails because the database is unreachable when the API route handler queries the subscription record**
    - **What happens:** The user with an active subscription attempts to access a premium feature, the API route handler queries the database for the user's subscription record, but the database is unreachable due to a connection failure or query timeout.
    - **Source:** A database connection pool exhaustion, a network partition between the API server and the database, or a database server crash that makes the subscription records temporarily inaccessible.
    - **Consequence:** The route handler cannot determine the user's plan status and the premium feature request is denied with an error response — the user with a valid subscription is temporarily unable to access paid features until the database connection is restored.
    - **Recovery:** The API route handler returns an HTTP 503 error indicating a temporary service unavailability, and the user retries the request after the database connection is restored — the application logs the database connection failure for monitoring and alerts the operations team.

- **DodoPayments webhook delivery fails repeatedly and the subscription activation is never recorded in the application database**
    - **What happens:** DodoPayments sends the activation webhook but every delivery attempt fails because the API webhook endpoint is consistently returning errors due to a deployment misconfiguration, a routing error, or a sustained infrastructure outage.
    - **Source:** A misconfigured webhook URL in the DodoPayments dashboard, a deployment that removed or renamed the webhook route, or a sustained infrastructure outage that keeps the API server offline for longer than the DodoPayments retry window.
    - **Consequence:** The user has paid for a subscription through DodoPayments but the application never records the activation — the user remains on the free tier in the application despite having an active subscription on the DodoPayments platform.
    - **Recovery:** The operations team detects the webhook delivery failures through DodoPayments dashboard monitoring, alerts the engineering team to fix the webhook endpoint configuration, and manually reconciles the missing subscription records by replaying the failed webhook events from the DodoPayments event log.

## Declared Omissions

- This specification does not define the DodoPayments account setup, API key configuration, or the initial integration steps required to connect the application with the DodoPayments payment processing platform
- This specification does not cover the plan definition and pricing configuration process — how plans are created, priced, and managed within the DodoPayments dashboard or the application's admin interface is outside this scope
- This specification does not address subscription upgrade or downgrade flows where a user changes from one paid plan to another — plan changes require a separate specification covering proration, billing cycle adjustments, and feature access transitions
- This specification does not define the mobile or desktop-specific checkout experience — platform-specific payment flow variations for Expo and Tauri applications require separate specifications

## Related Specifications

- [user-manages-billing-portal](user-manages-billing-portal.md) —
    defines the billing portal flow where subscribed users manage
    their active subscriptions including viewing payment history,
    updating payment methods, and canceling their plan through the
    DodoPayments portal interface
- [session-lifecycle](session-lifecycle.md) — defines the session
    management behavior that ensures the user's plan information is
    available in the session data after the Better Auth plugin updates
    the subscription record through webhook processing
- [developer-views-api-reference](developer-views-api-reference.md)
    — documents the API endpoints for subscription management
    including the checkout initiation endpoint and webhook receiver
    that are available in the interactive Scalar API reference page
- [user-enters-the-app](user-enters-the-app.md) — defines the user
    registration and app entry flow that creates the initial free-tier
    account from which the user can later upgrade to a paid plan through
    the subscription checkout flow described in this specification
