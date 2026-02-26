# User Subscribes to a Plan

> **Status: Planned** — The DodoPayments Better Auth plugin (`@dodopayments/better-auth`) is included in the codebase but commented out, awaiting payment credentials. The flow described below represents the intended design that will activate once credentials are configured.

## Free Tier by Default

The application is fully usable without any payment. Every new user starts on the free tier, which provides access to core features with no payment method required. Subscribing to a paid plan unlocks additional capabilities or higher limits, but the app does not gate basic functionality behind a paywall.

## Planned Subscription Flow

When the DodoPayments integration is active, the user navigates to the billing page within the dashboard. The page displays the available plans with their features and pricing. The user selects a plan and enters the checkout flow powered by DodoPayments. Upon successful payment, a subscription record is created and associated with the user's account. The user's plan information is reflected in their session and user record, making it available to both frontend (for UI adjustments) and backend (for feature gating).

## Webhook-Driven Status Updates

DodoPayments sends webhook callbacks to the API when subscription status changes — activation after initial payment, cancellation by the user, payment failures resulting in a past-due state, or renewal. The Better Auth DodoPayments plugin processes these webhooks and updates the subscription status in the database accordingly. The application does not poll for payment status; all transitions are event-driven.

## Feature Gating

Plan-based feature gating is enforced at the API level. Route handlers or middleware check the user's current plan before allowing access to premium features. If a user on the free tier attempts to access a paid feature, the API returns an appropriate error and the frontend presents an upgrade prompt. This keeps all authorization logic server-side, where it cannot be bypassed by a modified client.
