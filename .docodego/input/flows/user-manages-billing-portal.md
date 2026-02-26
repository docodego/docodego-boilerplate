[← Back to Index](README.md)

# User Manages Billing Portal

> **Status: Planned** — The DodoPayments Better Auth plugin (`@dodopayments/better-auth`) is included in the codebase but commented out, awaiting payment credentials. The flow described below represents the intended design that will activate once credentials are configured.

## Accessing the Billing Portal

After [subscribing to a plan](user-subscribes-to-a-plan.md), the user navigates to the billing section within the dashboard. A "Manage Billing" button is available on the page. When the user clicks it, the client calls `customer.portal()` to open the self-service billing portal powered by DodoPayments. The portal opens either inline or in a new window, depending on the integration configuration.

## Viewing Active Subscriptions

The billing portal displays the user's active subscriptions, including the plan name, billing cycle, next renewal date, and current status. If the user has multiple subscriptions or add-ons, each is listed separately with its own details. The user can see at a glance what they are paying for and when the next charge will occur.

## Payment History

The portal provides a payment history section populated by `customer.payments.list()`. Each entry shows the payment date, amount, payment method used, and status (succeeded, failed, or refunded). The user can review past charges to verify billing accuracy or locate a specific transaction. This history is read-only — the user cannot modify past payment records.

## Updating Payment Methods

The user can add, update, or remove payment methods from the billing portal. Adding a new card or payment method follows the DodoPayments secure input flow, where card details are collected in an isolated iframe and never touch the application's servers directly. The user can set a new default payment method, and future charges will use it automatically.

## Usage-Based Billing

For plans that include usage-based components, the portal displays current consumption data via `usage.meters.list()`. The user can see how much of each metered resource they have consumed during the current billing period — for example, API calls, storage, or compute hours. This helps the user anticipate upcoming charges and manage their usage proactively.

## Canceling a Subscription

The user can cancel their subscription from the billing portal. Clicking "Cancel" presents a confirmation step explaining what happens next — typically, the subscription remains active until the end of the current billing period, after which it will not renew. Cancellation is processed through DodoPayments, which sends a webhook to update the subscription status in the database, as described in the [subscription flow](user-subscribes-to-a-plan.md). The user reverts to the free tier once the paid period ends.
