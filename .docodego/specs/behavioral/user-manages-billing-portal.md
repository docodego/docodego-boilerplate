---
id: SPEC-2026-094
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Manages Billing Portal

## Intent

This spec defines how an authenticated user with an active
subscription accesses and interacts with the self-service billing
portal powered by DodoPayments to manage their subscription, view
payment history, update payment methods, review usage-based billing
data, and cancel their subscription. After subscribing to a plan, the
user navigates to the billing section within the dashboard and clicks
the "Manage Billing" button which calls `customer.portal()` to open
the DodoPayments self-service billing portal. The portal displays
active subscriptions with plan name, billing cycle, next renewal date,
and current status. The payment history section is populated by
`customer.payments.list()` showing each payment's date, amount, method,
and status. The user can add, update, or remove payment methods through
the DodoPayments isolated input flow where card details are collected in
a dedicated iframe that never touches the application's servers. For
plans with usage-based components the portal displays current
consumption data via `usage.meters.list()` showing metered resource
usage for the current billing period. The user can cancel their
subscription from the portal with a confirmation step that explains
the subscription remains active until the end of the current billing
period. On the desktop app, the billing portal configured to open in
a new window is launched in the user's default system browser via
`tauri-plugin-opener` rather than attempting a new browser-style
window in the Tauri webview.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| DodoPayments self-service billing portal (hosted portal interface opened by calling `customer.portal()` that provides subscription management, payment history, payment method updates, usage metering display, and cancellation capabilities for the authenticated user) | read/write | When the user clicks the "Manage Billing" button on the billing page, the client calls `customer.portal()` to open the DodoPayments self-service portal either inline within the page or in a new browser window depending on integration configuration | The DodoPayments portal is unreachable due to a service outage and the `customer.portal()` call fails — the billing page displays an error notification and the user retries after the DodoPayments service is restored |
| `customer.payments.list()` API (DodoPayments API method that returns the payment history for the authenticated user including payment date, amount, payment method used, and status for each transaction in the billing history) | read | When the billing portal renders the payment history section, it calls `customer.payments.list()` to fetch the complete list of past transactions associated with the user's DodoPayments customer account | The payments API returns an error due to a DodoPayments service degradation and the payment history section displays a loading error — the user retries by refreshing the portal after the DodoPayments API recovers |
| `usage.meters.list()` API (DodoPayments API method that returns current consumption data for usage-based billing components showing metered resource usage quantities for the current billing period for plans that include usage-based pricing) | read | When the billing portal renders the usage section for plans with usage-based components, it calls `usage.meters.list()` to fetch the current consumption data for each metered resource in the active billing period | The usage metering API returns an error due to a DodoPayments service issue and the usage section displays a loading error — the user retries by refreshing the portal and the metering data loads when the API recovers |
| DodoPayments isolated payment input (dedicated iframe hosted by DodoPayments that collects card details and payment method information without the data passing through the application's servers, providing PCI-compliant payment data collection for adding or updating payment methods) | read/write | When the user adds a new payment method or updates an existing one in the billing portal, the DodoPayments isolated iframe renders the card input fields and handles the payment method creation or update directly with the payment processor | The isolated input iframe fails to load due to a DodoPayments CDN error or content security policy blocking — the user cannot add or update payment methods and retries after the hosting issue is resolved or the CSP is corrected |
| DodoPayments webhook endpoint (API route that receives cancellation and payment method update callbacks from DodoPayments after the user performs actions in the billing portal, updating the subscription record in the application database) | write | When the user cancels their subscription or the billing period ends after cancellation, DodoPayments sends a webhook to the API endpoint with the cancellation event — the Better Auth plugin processes the webhook and updates the subscription status in the database | The webhook endpoint is unreachable due to an API server outage and DodoPayments retries the webhook delivery — the subscription status update is delayed until the API server recovers and processes the retried webhook |
| `tauri-plugin-opener` (Tauri desktop plugin that launches URLs in the user's default system browser, used on the desktop app to open the billing portal in an external browser window when the portal is configured for new-window mode rather than inline embedding) | write | When the desktop app user clicks "Manage Billing" and the portal is configured to open in a new window, the application calls `tauri-plugin-opener` to launch the portal URL in the user's default system browser | The `tauri-plugin-opener` plugin fails to launch the browser due to a missing default browser configuration or plugin initialization error — the application logs the launcher error and displays a fallback message with the portal URL for the user to copy and open manually |

## Behavioral Flow

1. **[User]** navigates to the billing section within the
    authenticated dashboard after having subscribed to a plan and
    sees their current subscription status including plan name and
    billing cycle

2. **[User]** clicks the "Manage Billing" button on the billing page
    to access the self-service billing portal powered by DodoPayments

3. **[Billing Page]** calls `customer.portal()` to open the
    DodoPayments self-service billing portal — the portal opens either
    inline within the page or in a new window depending on the
    integration configuration setting

4. **[Desktop App]** if the portal is configured to open in a new
    window and the user is on the Tauri desktop app,
    `tauri-plugin-opener` launches the portal URL in the user's
    default system browser because the Tauri webview cannot open new
    browser-style windows

5. **[Billing Portal]** displays the user's active subscriptions
    listing each subscription with its plan name, billing cycle, next
    renewal date, and current status — if the user has multiple
    subscriptions or add-ons each is listed separately with its own
    details

6. **[User]** reviews their active subscriptions to see what they are
    paying for and when the next charge will occur for each
    subscription entry

7. **[Billing Portal]** renders the payment history section populated
    by `customer.payments.list()` showing each past transaction with
    its payment date, amount, payment method used, and status
    (succeeded, failed, or refunded)

8. **[User]** reviews past charges in the payment history section to
    verify billing accuracy or locate a specific transaction — the
    history is read-only and the user cannot modify past payment
    records

9. **[User]** navigates to the payment methods section and adds a new
    card or payment method through the DodoPayments isolated input flow
    where card details are collected in a dedicated iframe that never
    touches the application's servers

10. **[User]** sets a new default payment method in the portal and
    future charges are automatically applied to the updated payment
    method without requiring manual selection for each renewal

11. **[Billing Portal]** displays the usage section for plans with
    usage-based components, fetching current consumption data via
    `usage.meters.list()` showing how much of each metered resource
    the user has consumed during the current billing period

12. **[User]** reviews their usage data to anticipate upcoming charges
    and manage consumption proactively for resources such as API
    calls, storage, or compute hours

13. **[User]** clicks "Cancel" to initiate subscription cancellation
    from the billing portal — a confirmation step explains that the
    subscription remains active until the end of the current billing
    period after which it will not renew

14. **[User]** confirms the cancellation and DodoPayments processes
    the cancellation request, sending a webhook to the API endpoint
    to update the subscription status in the database

15. **[Better Auth Plugin]** receives the cancellation webhook,
    validates the DodoPayments signature, and updates the subscription
    record to reflect the cancellation-pending status — the user
    reverts to the free tier once the paid period ends

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| billing_page_loaded | portal_open | The user clicks the "Manage Billing" button and the client calls `customer.portal()` to open the DodoPayments self-service billing portal inline or in a new window | The user is authenticated with an active subscription and the `customer.portal()` call returns a valid portal session |
| portal_open | viewing_subscriptions | The billing portal loads and displays the user's active subscriptions with plan name, billing cycle, next renewal date, and current status for each entry | The DodoPayments portal session is valid and the subscription data loads from the DodoPayments platform within the portal's loading timeout |
| viewing_subscriptions | viewing_payment_history | The user navigates to the payment history section within the billing portal and the portal renders past transactions fetched via `customer.payments.list()` | The `customer.payments.list()` API returns the payment history data and the portal renders at least 1 transaction entry or an empty history message |
| viewing_payment_history | updating_payment_method | The user navigates to the payment methods section and initiates adding a new card or updating an existing payment method through the DodoPayments isolated input iframe | The DodoPayments isolated input iframe loads in the portal and the user's browser allows the iframe content to render without content security policy violations |
| updating_payment_method | viewing_subscriptions | The user completes the payment method addition or update and the portal confirms the new payment method is saved as the default for future charges | The DodoPayments platform validates the new payment method, stores it against the customer account, and returns a success confirmation to the portal |
| viewing_subscriptions | viewing_usage | The user navigates to the usage section within the billing portal and the portal renders current consumption data fetched via `usage.meters.list()` for plans with usage-based components | The user's plan includes usage-based billing components and the `usage.meters.list()` API returns metered consumption data for the current billing period |
| viewing_subscriptions | cancellation_confirming | The user clicks the "Cancel" button for a subscription and the portal displays the confirmation step explaining that the subscription remains active until the end of the current billing period | The user's subscription is in an active or past-due state and the portal renders the cancellation confirmation dialog with the end-of-period explanation |
| cancellation_confirming | cancellation_pending | The user confirms the cancellation and DodoPayments processes the request, sending a webhook to the API with the cancellation event that the Better Auth plugin writes to the database | The user confirms the cancellation action, DodoPayments processes the cancellation, and the webhook delivery to the API endpoint succeeds |
| cancellation_confirming | viewing_subscriptions | The user decides not to cancel and dismisses the confirmation dialog to return to the subscription listing without making any changes | The user clicks the dismiss or back button on the cancellation confirmation dialog without confirming the cancellation action |

## Business Rules

- **Rule portal-requires-active-subscription:** IF the user clicks
    "Manage Billing" THEN the user has at least 1 active or past-due
    subscription — the count of portal access attempts from users
    with zero subscriptions that reach the portal equals 0
- **Rule payment-history-read-only:** IF the user views the payment
    history section THEN all transaction records are displayed as
    read-only — the count of user-initiated modifications to past
    payment records through the portal equals 0
- **Rule card-details-never-touch-application-servers:** IF the user
    adds or updates a payment method through the billing portal THEN
    the card details are collected in an isolated DodoPayments iframe
    — the count of raw card numbers transmitted to the application's
    API servers equals 0
- **Rule cancellation-effective-end-of-period:** IF the user confirms
    a subscription cancellation THEN the subscription remains active
    until the end of the current billing period and does not renew —
    the count of features revoked before the billing period end date
    after cancellation equals 0
- **Rule desktop-portal-opens-in-system-browser:** IF the user is on
    the Tauri desktop app and the portal is configured for new-window
    mode THEN `tauri-plugin-opener` launches the portal URL in the
    default system browser — the count of portal windows opened inside
    the Tauri webview in new-window mode equals 0
- **Rule default-payment-method-applies-to-renewals:** IF the user
    sets a new default payment method in the portal THEN future
    automatic renewal charges use the updated payment method — the
    count of renewal charges applied to a payment method the user has
    replaced as default equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User (authenticated user with an active or past-due subscription who opens the DodoPayments self-service billing portal to manage subscriptions, view payment history, update payment methods, review usage data, and cancel subscriptions) | Open the billing portal via the "Manage Billing" button, view active subscriptions with plan details, view payment history with transaction dates and amounts, add update or remove payment methods through the isolated input flow, set a new default payment method, review usage-based consumption data for metered resources, initiate and confirm subscription cancellation | Cannot modify past payment records in the payment history, cannot access raw card details for stored payment methods (only last 4 digits and card brand are visible), cannot bypass the cancellation confirmation step to immediately terminate a subscription, cannot access other users' billing portal or subscription data | The user sees their own active subscriptions and payment history only, sees masked payment method details (last 4 digits and card brand), sees usage consumption data for their own metered resources only, and does not see internal webhook processing or database update operations |

## Constraints

- The `customer.portal()` call opens the DodoPayments billing portal
    within 3000 ms of the user clicking the "Manage Billing" button —
    the count of milliseconds from click to portal visible equals
    3000 or fewer.
- The payment history section loads transaction records from
    `customer.payments.list()` within 2000 ms of the user navigating
    to the payment history view — the count of milliseconds from
    navigation to rendered history equals 2000 or fewer.
- The usage metering section loads consumption data from
    `usage.meters.list()` within 2000 ms of the user navigating to
    the usage view — the count of milliseconds from navigation to
    rendered usage data equals 2000 or fewer.
- Card details entered in the DodoPayments isolated input iframe are
    collected without passing through the application's servers — the
    count of raw card numbers processed by the application's API
    equals 0.
- The cancellation confirmation step displays before the cancellation
    is processed — the count of cancellations processed without the
    user seeing the confirmation dialog equals 0.

## Acceptance Criteria

- [ ] The "Manage Billing" button opens the DodoPayments billing portal within 3000 ms of the user clicking it — the portal is visible within 3000 ms
- [ ] The billing portal displays active subscriptions with plan name, billing cycle, next renewal date, and current status — the count of subscription fields displayed per entry equals 4
- [ ] The payment history section renders past transactions with date, amount, method, and status for each entry — the count of fields per transaction entry equals 4
- [ ] Payment history records are read-only and the user cannot modify past payment entries — the count of editable fields in the payment history section equals 0
- [ ] The user can add a new payment method through the DodoPayments isolated iframe without card data touching the application servers — the count of raw card numbers transmitted to the API equals 0
- [ ] The user can set a new default payment method and future charges use the updated method — the default payment method field is non-empty after the update
- [ ] The usage section displays current consumption data via `usage.meters.list()` for plans with usage-based components — the usage section is non-empty when the plan includes at least 1 metered resource
- [ ] The cancellation flow presents a confirmation step before processing — the count of cancellations processed without confirmation equals 0
- [ ] After cancellation confirmation the subscription remains active until the end of the billing period — the count of features revoked before the billing period end date equals 0
- [ ] On the Tauri desktop app the portal opens in the default system browser via `tauri-plugin-opener` when configured for new-window mode — the count of portal windows opened inside the Tauri webview equals 0
- [ ] The user reverts to the free tier after the paid billing period ends following cancellation — the count of active subscriptions after period expiration equals 0
- [ ] The cancellation webhook is processed by the Better Auth plugin and the subscription record is updated in the database — the subscription status field in the database is non-empty after webhook processing

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user clicks "Manage Billing" but the `customer.portal()` call fails because the DodoPayments service is experiencing an outage and cannot create a portal session | The billing page catches the portal creation error and displays an error notification explaining that the billing portal is temporarily unavailable — the user can retry after the service recovers | The error notification element is present on the billing page and the portal does not open |
| The user opens the billing portal on the Tauri desktop app but `tauri-plugin-opener` fails to launch the default system browser because no default browser is configured on the operating system | The application catches the launcher error, logs the failure details, and displays a fallback message containing the portal URL that the user can copy and paste into a browser manually | The fallback message with the portal URL is present on the page and the application log contains the `tauri-plugin-opener` failure entry |
| The user adds a new payment method but the DodoPayments isolated iframe fails to load because a content security policy on the hosting page blocks the iframe source domain | The portal displays a payment method input error indicating the isolated form could not load — the user cannot add or update payment methods until the CSP configuration is corrected by the development team | The payment method form displays an error message and the browser console contains a CSP violation entry for the DodoPayments iframe domain |
| The user opens the payment history section but has zero past transactions because they just subscribed and the first charge has not yet appeared in the DodoPayments records | The payment history section renders an empty state message indicating no payment records are available yet — the section does not display an error and the user can return to it later after the first charge is processed | The payment history section displays the empty state message and the count of transaction entries rendered equals 0 |
| The user confirms subscription cancellation but the DodoPayments webhook fails to deliver to the API endpoint because the server is temporarily unreachable during a deployment | DodoPayments retries the cancellation webhook according to its retry policy and the subscription status update is delayed — the user's subscription remains in its current state until the webhook is successfully delivered and processed | The subscription status in the database does not change until the retried webhook is processed, and the DodoPayments dashboard shows webhook delivery retry attempts |
| The user has a plan with usage-based components but the `usage.meters.list()` API returns an empty result because no metered consumption has occurred in the current billing period | The usage section renders a message indicating zero consumption for the current billing period rather than displaying an error — each metered resource shows a usage value of zero | The usage section displays the metered resources with zero consumption values and does not render an error state |

## Failure Modes

- **DodoPayments billing portal fails to open when the user clicks the "Manage Billing" button due to a service outage or session creation error**
    - **What happens:** The user clicks "Manage Billing" on the billing page and the client calls `customer.portal()`, but the call fails because the DodoPayments service is unreachable or the portal session cannot be created due to an expired customer token or API authentication error.
    - **Source:** A DodoPayments platform outage affecting the portal service, a network connectivity issue between the user's browser and the DodoPayments CDN, or an expired DodoPayments customer session token that prevents the portal from initializing.
    - **Consequence:** The user cannot access subscription management, payment history, payment methods, or cancellation functionality and must wait for the DodoPayments service to recover before managing their billing through the portal.
    - **Recovery:** The billing page catches the `customer.portal()` error, logs the failure with the error code and customer identifier, and displays a notification explaining that the billing portal is temporarily unavailable — the user retries after the DodoPayments service is restored.

- **Payment method update fails because the DodoPayments isolated input iframe cannot validate the card details provided by the user**
    - **What happens:** The user enters card details in the DodoPayments isolated input iframe to add or update a payment method, but the card validation fails because the card number is invalid, the expiration date has passed, the CVV does not match, or the card issuer declines the verification charge.
    - **Source:** The user entered incorrect card details, the card has expired or been cancelled by the issuer, the card issuer's fraud detection blocked the verification charge, or the DodoPayments payment processor returned a validation error for the provided card data.
    - **Consequence:** The payment method is not added or updated and the user's existing default payment method remains unchanged — future charges continue to use the previous payment method which itself remains at risk of failure if the user was attempting to replace an expiring card.
    - **Recovery:** The DodoPayments isolated input form displays the specific validation error message (invalid card number, expired card, or issuer decline) and the user retries by entering correct card details or using a different payment method.

- **`usage.meters.list()` API returns an error when loading the usage section for plans with usage-based billing components**
    - **What happens:** The billing portal attempts to load the usage section by calling `usage.meters.list()` but the API returns an error because the DodoPayments metering service is experiencing degraded performance or the user's metering data is temporarily unavailable due to a data aggregation delay.
    - **Source:** A DodoPayments metering service degradation that affects usage data retrieval, a data aggregation pipeline delay that makes the current period's consumption data temporarily unavailable, or a network timeout between the billing portal and the DodoPayments metering API.
    - **Consequence:** The usage section in the billing portal displays a loading error instead of the current consumption data and the user cannot review their metered resource usage to anticipate upcoming charges for the current billing period.
    - **Recovery:** The billing portal displays an error message in the usage section explaining that usage data is temporarily unavailable, and the user retries by refreshing the portal page after the DodoPayments metering service recovers.

- **Cancellation webhook is lost after the user confirms subscription cancellation in the billing portal and DodoPayments exhausts all retry attempts**
    - **What happens:** The user confirms subscription cancellation in the billing portal and DodoPayments processes the cancellation on their platform, but every webhook delivery attempt to the API endpoint fails because the endpoint is persistently unavailable during the entire DodoPayments retry window.
    - **Source:** A sustained API server outage that lasts longer than the DodoPayments webhook retry window, a misconfigured webhook URL that consistently returns HTTP 404, or a firewall rule change that blocks incoming requests from DodoPayments IP addresses to the webhook endpoint.
    - **Consequence:** The user's subscription is cancelled on the DodoPayments platform but the application database still shows an active subscription — the user continues to have access to premium features until the discrepancy is detected and reconciled.
    - **Recovery:** The operations team detects the webhook delivery failures through DodoPayments dashboard monitoring alerts, fixes the webhook endpoint availability issue, and manually reconciles the subscription status by replaying the failed cancellation event from the DodoPayments event log.

## Declared Omissions

- This specification does not define the DodoPayments billing portal's visual design, branding customization, or theme configuration — the portal's appearance is controlled by the DodoPayments platform settings outside this application
- This specification does not cover subscription upgrade or downgrade flows where the user changes their plan through the billing portal — plan change proration and feature transition logic require a separate specification
- This specification does not address refund processing or dispute handling through the billing portal — refund workflows and chargeback resolution are managed through DodoPayments administrative tools outside the user-facing portal
- This specification does not define the mobile app billing portal experience — Expo-specific payment management and in-app purchase requirements for iOS and Android platforms require a separate specification

## Related Specifications

- [user-subscribes-to-a-plan](user-subscribes-to-a-plan.md) — defines
    the subscription checkout flow that creates the initial paid plan
    subscription which the user subsequently manages through the
    billing portal described in this specification
- [session-lifecycle](session-lifecycle.md) — defines the session
    management behavior that ensures the user's subscription status
    is available in the session data when determining whether to show
    the "Manage Billing" button on the billing page
- [developer-views-api-reference](developer-views-api-reference.md)
    — documents the API endpoints for billing portal access and
    webhook processing that are available in the interactive Scalar
    API reference page for developer integration
- [user-changes-language](user-changes-language.md) — defines the
    language switching mechanism that determines the locale used when
    the billing portal renders localized text for subscription details
    and cancellation confirmation messages
