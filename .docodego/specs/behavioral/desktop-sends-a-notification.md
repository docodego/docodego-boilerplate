---
id: SPEC-2026-071
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# Desktop Sends a Notification

## Intent

This spec defines how the Tauri 2 desktop application sends
OS-native notifications to inform the user of events that occur
while the application is not in the foreground. The first time a
notification is needed, tauri-plugin-notification requests
permission from the operating system. If the user grants
permission, notifications are enabled for the current and all
future sessions. If the user denies permission, the application
silently skips OS-native notifications without prompting again.
Three specific events trigger notifications: an organization
invitation has been received, the current session is about to
expire, and a new application update is available for download.
Each notification includes a localized title and body rendered by
the OS-native notification system — macOS Notification Center,
Windows Action Center, or the Linux desktop environment's
notification daemon. When the user clicks a notification, the
Tauri application is brought to the foreground and navigates to
the page relevant to the event. When the application is already
in the foreground and focused, OS-native notifications are
suppressed and the event is communicated through an in-app toast
rendered by Sonner instead.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| tauri-plugin-notification (Tauri plugin that provides the Notification API for requesting permission and dispatching OS-native notifications) | read/write | When the application first needs to send a notification the plugin checks the current permission state and requests permission if not yet determined, and on each notification event the plugin dispatches the notification payload to the OS | The plugin fails to load or the Tauri configuration omits the notification capability and the application falls back to displaying all events exclusively through the in-app Sonner toast — the count of OS-native notifications sent equals 0 and all events render as in-app toasts instead |
| OS permission prompt (system-level dialog presented by the operating system asking the user to allow or deny notification access for the application) | read | When tauri-plugin-notification calls the permission request API for the first time and the OS has no stored permission decision for this application — the OS displays a native dialog with Allow and Deny options | The OS does not support a permission prompt (older Linux environments without notification capabilities) and the plugin returns a denied state — the application falls back to using only in-app Sonner toasts for all notification events and logs a warning with the platform name |
| OS notification system — macOS Notification Center, Windows Action Center, Linux notification daemon (platform-specific service that renders and manages native notification banners) | write | When tauri-plugin-notification dispatches a notification payload containing the application icon, a localized title, and a localized body message for one of the three trigger events | The OS notification service is unavailable or the desktop environment has no notification daemon running and the dispatch call returns an error — the application falls back to displaying the event as an in-app Sonner toast and logs the dispatch failure with the error code |
| In-app toast via Sonner (React toast library rendered inside the Tauri webview for displaying non-blocking notification banners within the application UI) | write | When the application is in the foreground and focused and an event occurs that would otherwise trigger an OS-native notification — the event is routed to a Sonner toast instead of the OS notification system | Sonner fails to render the toast component due to a React rendering error and the event notification is lost for that instance — the application logs the rendering failure and the user relies on the next page navigation or data refresh to discover the event |
| @repo/i18n (localization infrastructure providing translated strings for notification titles and body messages in the user's configured locale) | read | When constructing the notification payload before dispatching to the OS or rendering as an in-app toast — the title and body strings are resolved from the i18n namespace using the user's configured locale | The i18n namespace fails to load the notification translation keys and the notification falls back to displaying the raw translation key strings instead of localized text — the application logs the missing namespace and retries loading translations on the next notification event |

## Behavioral Flow

1. **[Tauri]** an event occurs that requires notifying the user —
    the event is one of three types: an organization invitation
    has been received, the current session is about to expire
    within 5 minutes, or a new application update is available
    for download

2. **[Tauri]** the notification handler checks whether the
    application window is currently in the foreground and focused
    by querying the Tauri window focus state — if the window is
    focused the flow skips to step 11 for in-app toast delivery

3. **[Tauri]** the notification handler calls
    tauri-plugin-notification to check the current permission
    state — the plugin returns one of three states: granted,
    denied, or not-yet-determined

4. **[Tauri]** if the permission state is not-yet-determined
    because this is the first notification attempt, the plugin
    calls the OS permission request API to present the native
    permission dialog to the user

5. **[OS]** the operating system displays its standard notification
    permission prompt asking the user whether to allow
    notifications from the application — the prompt contains
    Allow and Deny options rendered in the OS locale language

6. **[User]** the user responds to the permission prompt by
    clicking Allow or Deny — the OS stores the decision
    persistently so the prompt is not shown again for this
    application

7. **[Tauri]** if the user granted permission or the permission
    state was already granted from a previous session, the plugin
    proceeds to construct the notification payload — the payload
    includes the application icon, a localized title resolved from
    @repo/i18n, and a localized body message with event-specific
    details such as the organization name for an invitation or the
    version number for an update

8. **[Tauri]** if the user denied permission or the permission
    state was already denied, the plugin skips OS-native
    notification dispatch entirely without prompting again — the
    application silently falls back to in-app toast delivery by
    proceeding to step 11

9. **[OS]** the OS notification system renders the notification
    using the platform-native notification service — on macOS it
    appears in Notification Center, on Windows it appears in
    Action Center, and on Linux it appears through the desktop
    environment's notification daemon — displaying the application
    icon, localized title, and localized body text

10. **[User]** the user clicks on the rendered OS notification
    banner — the Tauri application is brought to the foreground
    and the application navigates to the page relevant to the
    notification event: the invitation acceptance page for an
    invitation notification, the sign-in page for a session expiry
    warning, or the update prompt page for an update notification
    — if the application was closed when the notification was
    clicked, it launches and navigates to the relevant page after
    startup completes

11. **[Tauri]** when the application is in the foreground and
    focused, or when OS notification permission is denied, the
    notification handler routes the event to the in-app Sonner
    toast system — the toast renders a non-blocking banner inside
    the webview with the same localized title and body text that
    would have appeared in the OS notification

12. **[User]** the user sees the in-app Sonner toast and clicks on
    it to navigate to the relevant page, or the toast auto-
    dismisses after 5000 ms if the user takes no action — the
    toast click navigates to the same destination as an OS
    notification click for the same event type

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | checking_focus | A notification-triggering event occurs (invitation received, session expiring within 5 minutes, or update available) | The event payload contains a valid event type and the required data fields (organization name, session expiry timestamp, or version number) are present and non-empty |
| checking_focus | routing_to_toast | The Tauri window focus state query returns true indicating the application is in the foreground and focused | The window handle is valid and the focus state API returns a definitive true value |
| checking_focus | checking_permission | The Tauri window focus state query returns false indicating the application is not in the foreground | The window handle is valid and the focus state API returns a definitive false value |
| checking_permission | requesting_permission | The tauri-plugin-notification permission state returns not-yet-determined because no permission decision has been recorded for this application | The OS supports a notification permission prompt and the plugin has not previously requested permission during this application session |
| checking_permission | constructing_payload | The tauri-plugin-notification permission state returns granted because the user previously allowed notifications for this application | The stored permission decision is granted and the plugin confirms the permission is still active |
| checking_permission | routing_to_toast | The tauri-plugin-notification permission state returns denied because the user previously denied notifications for this application | The stored permission decision is denied and the plugin confirms the decision is final |
| requesting_permission | constructing_payload | The user clicks Allow on the OS permission prompt and the OS stores the granted decision persistently for this application | The OS permission API returns a success response with the granted state |
| requesting_permission | routing_to_toast | The user clicks Deny on the OS permission prompt and the OS stores the denied decision persistently for this application | The OS permission API returns a success response with the denied state |
| constructing_payload | dispatching_notification | The notification payload is assembled with the application icon, localized title from @repo/i18n, and localized body with event-specific details | The title and body strings are non-empty after i18n resolution and the application icon resource is accessible |
| dispatching_notification | notification_displayed | The OS notification service accepts the payload and renders the notification banner on screen using the platform-native notification system | The OS notification service is running and returns a success response for the dispatch call |
| dispatching_notification | routing_to_toast | The OS notification service rejects the payload or returns a dispatch error due to service unavailability or configuration issues | The dispatch call returns an error code and the application logs the failure details |
| notification_displayed | navigating | The user clicks the OS notification banner and the Tauri application receives the click event with the associated event type and navigation target | The click event contains the original event type identifier and the mapped navigation route is valid |
| notification_displayed | idle | The OS notification banner is dismissed by the user without clicking or auto-dismissed by the OS after the platform-defined timeout | The notification display lifecycle completes without a click event being received by the application |
| routing_to_toast | toast_displayed | The Sonner toast component renders the non-blocking banner inside the webview with the localized title and body text | The React rendering pipeline is functional and the Sonner toast container is mounted in the DOM |
| toast_displayed | navigating | The user clicks the in-app Sonner toast banner before the 5000 ms auto-dismiss timeout elapses | The toast click handler contains the event type identifier and the mapped navigation route is valid |
| toast_displayed | idle | The Sonner toast auto-dismisses after 5000 ms without the user clicking on it | The 5000 ms timeout elapses and the toast removal animation completes |
| navigating | idle | The application completes navigation to the relevant page (invitation acceptance page, sign-in page, or update prompt page) and the page renders | The navigation route resolves to a valid page component and the page DOM becomes interactive |

## Business Rules

- **Rule permission-requested-once:** IF the application has never
    requested notification permission from the OS THEN
    tauri-plugin-notification requests permission exactly 1 time
    when the first notification-triggering event occurs — the count
    of OS permission prompts displayed across the entire application
    lifetime equals 1
- **Rule denied-permission-silently-skips:** IF the user denied
    notification permission via the OS prompt or the OS returns a
    denied state THEN the application skips OS-native notification
    dispatch without prompting again and routes all events to
    in-app Sonner toasts — the count of OS permission prompts
    displayed after a denied decision equals 0
- **Rule three-trigger-events:** IF a notification-triggering event
    occurs THEN the event type is one of exactly 3 defined types:
    organization invitation received, session expiring within 5
    minutes, or application update available — the count of
    distinct event types that trigger notifications equals 3
- **Rule os-renders-notification:** IF the application dispatches a
    notification payload to the OS THEN the notification is rendered
    by the OS-native notification system (Notification Center on
    macOS, Action Center on Windows, notification daemon on Linux)
    and not by the application — the count of application-rendered
    notification banners outside the webview equals 0
- **Rule click-brings-to-foreground-and-navigates:** IF the user
    clicks an OS notification or an in-app toast THEN the
    application brings the window to the foreground and navigates
    to the relevant page within 500 ms of the click event — the
    count of milliseconds from click to navigation completion
    equals 500 or fewer
- **Rule in-focus-uses-toast-not-os-notification:** IF the
    application window is in the foreground and focused when a
    notification-triggering event occurs THEN the event is routed
    to the in-app Sonner toast and the OS-native notification is
    suppressed — the count of OS-native notifications sent while
    the window is focused equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User with granted notification permission (the OS has stored an Allow decision for this application's notification access) | Receive OS-native notifications for all three trigger events (invitation, session expiry, update), click notifications to navigate to the relevant page, receive in-app Sonner toasts when the application is focused, dismiss notifications and toasts without navigating | Cannot modify which event types trigger notifications, cannot change the notification title or body content, cannot send notifications to other users or devices from the desktop application | OS-native notifications display the application icon, localized title, and localized body — the user sees notifications in the OS notification area (Notification Center, Action Center, or notification daemon) and in-app toasts in the webview when the application is focused |
| User with denied notification permission (the OS has stored a Deny decision for this application's notification access) | Receive in-app Sonner toasts for all three trigger events when the application is in the foreground, click toasts to navigate to the relevant page, re-enable notifications through the OS system settings outside the application | Cannot receive OS-native notifications because the OS blocks all notification dispatch calls from the application, cannot trigger a new permission prompt from within the application after the initial denial | Only in-app Sonner toasts are visible for notification events — no OS-native notification banners appear in the notification area, and the user discovers events only when the application is in the foreground and focused |
| OS (operating system that manages notification permissions, renders notification banners, and handles click events) | Display the permission prompt on first notification request, store the permission decision persistently, render notification banners using the platform-native notification system, deliver click events back to the Tauri application, auto-dismiss notifications after the platform-defined timeout | Cannot modify the notification payload content (title, body, icon) sent by the application, cannot override the application's decision to suppress notifications when the window is focused, cannot revoke a granted permission without user action in system settings | The OS sees the notification payload (icon, title, body) but has no visibility into the event type, navigation target, or application state that triggered the notification |

## Constraints

- The time between a notification-triggering event occurring and
    the OS notification banner appearing on screen equals 1000 ms
    or fewer when the permission state is already granted and the
    application is not focused.
- The in-app Sonner toast auto-dismisses after exactly 5000 ms
    when the user does not interact with it — the count of toasts
    remaining visible after 5000 ms equals 0.
- Each notification payload contains exactly 2 localized text
    fields resolved from @repo/i18n: 1 title string and 1 body
    string — the count of hardcoded English strings in notification
    payloads equals 0.
- The application icon included in OS notification payloads has a
    resolution of at least 256 by 256 pixels to render clearly on
    high-DPI displays across all three supported platforms.
- The navigation triggered by a notification click completes within
    500 ms of the click event — the count of milliseconds from
    click event to target page DOM interactive equals 500 or fewer.
- The permission request flow completes exactly 1 time across the
    entire application lifetime per OS user account — the count of
    permission prompts displayed after the first request equals 0.

## Acceptance Criteria

- [ ] When the first notification event occurs and permission is not-yet-determined, the OS permission prompt is displayed exactly 1 time — the count of permission prompts equals 1
- [ ] After the user grants permission, OS-native notifications are dispatched for subsequent events within 1000 ms of each event — the count of OS notifications sent after granting equals the count of trigger events that occur while the app is not focused and the dispatch latency equals 1000 ms or fewer
- [ ] After the user denies permission, no OS-native notifications are sent and no additional permission prompts appear — the count of OS notifications sent after denial equals 0 and the count of permission prompts after denial equals 0
- [ ] An organization invitation event triggers an OS notification with a localized title containing the organization name — the count of invitation notifications missing the organization name in the body text equals 0
- [ ] A session expiry event triggers an OS notification warning that the session expires within 5 minutes — the body text contains the remaining minutes and the count of expiry notifications with missing time data equals 0
- [ ] An update available event triggers an OS notification containing the new version number in the body text — the count of update notifications missing the version number equals 0
- [ ] On macOS the notification appears in Notification Center, on Windows in Action Center, and on Linux through the notification daemon — the count of notifications rendered by a non-native system equals 0
- [ ] Clicking an OS notification brings the Tauri window to the foreground within 500 ms — the window `is_focused` property returns true within 500 ms of the click event
- [ ] Clicking an invitation notification navigates to the invitation acceptance page within 500 ms — the count of invitation acceptance UI elements rendered equals 1 and navigation completes in 500 ms or fewer
- [ ] Clicking a session expiry notification navigates to the sign-in page within 500 ms — the count of sign-in form elements rendered equals 1 and the count of authenticated route renders equals 0
- [ ] Clicking an update notification navigates to the update prompt page within 500 ms — the count of update dialog elements rendered equals 1 and navigation completes in 500 ms or fewer
- [ ] When the application is focused, OS notifications are suppressed and a Sonner toast is displayed instead — the count of OS notifications sent while `is_focused` returns true equals 0 and the count of Sonner toasts rendered equals 1
- [ ] The Sonner toast auto-dismisses after 5000 ms — the count of toasts visible after 5000 ms equals 0
- [ ] All notification titles and body messages are resolved from @repo/i18n translation keys — the count of hardcoded English strings in notification payloads equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user clicks an OS notification while the Tauri application process is not running because it was closed after the notification was dispatched | The OS launches the Tauri application process, the runtime completes startup, and the application navigates to the relevant page (invitation acceptance, sign-in, or update prompt) after the webview becomes interactive | The application launches and the rendered route path matches the notification's target page within 5000 ms of the click event |
| Two notification events occur simultaneously (an invitation received and an update available at the same time) while the application is not focused | The application dispatches 2 separate OS notifications, each with its own localized title and body — both notifications appear in the OS notification area and clicking each navigates to its respective target page | The count of OS notifications dispatched equals 2 and each notification contains a distinct title and body matching its event type |
| The user grants notification permission but later revokes it through the OS system settings while the application is running | The next notification dispatch call returns an error because the OS blocks the delivery and the application falls back to displaying the event as an in-app Sonner toast and logs the permission revocation | The count of OS notifications sent after revocation equals 0 and the count of Sonner toasts rendered equals 1 for the next event |
| The OS notification daemon is not running on a Linux desktop environment that does not include a notification service | The tauri-plugin-notification dispatch call returns an error and the application falls back to displaying all events as in-app Sonner toasts and logs a warning with the Linux distribution name and error code | The count of OS notifications sent equals 0 and the count of Sonner toasts rendered equals the count of events that occur while the app is not focused |
| The session expiry notification is dispatched but the session actually expires before the user clicks the notification | The user clicks the notification and the application navigates to the sign-in page where the session is already invalid — the sign-in page renders normally and the user re-authenticates using the standard sign-in flow | The rendered route path equals the sign-in page path and the count of error dialogs displayed equals 0 |
| The @repo/i18n namespace fails to load when constructing the notification payload and translation keys cannot be resolved to localized strings | The notification is dispatched with raw translation key strings as the title and body instead of localized text and the application logs the i18n loading failure with the namespace name and locale code | The notification title equals the raw translation key string and the count of i18n error log entries equals 1 |

## Failure Modes

- **OS notification dispatch fails due to service unavailability**
    - **What happens:** The tauri-plugin-notification calls the OS
        notification dispatch API but the service is unavailable
        because the notification daemon is not running, the Action
        Center service is stopped, or the Notification Center
        process has crashed on the user's machine.
    - **Source:** The Linux desktop environment does not include a
        notification daemon, the Windows Action Center service was
        disabled by a group policy, or the macOS Notification Center
        process terminated unexpectedly during the user's session.
    - **Consequence:** The OS-native notification is not delivered
        and the user does not see the notification banner in the
        system notification area, meaning the event goes unnoticed
        unless the user opens the application window manually.
    - **Recovery:** The application catches the dispatch error and
        falls back to displaying the event as an in-app Sonner
        toast, logs the dispatch failure with the platform name and
        error code, and retries OS dispatch on the next notification
        event to check if the service has recovered.

- **Permission request API returns an unexpected error state**
    - **What happens:** The tauri-plugin-notification calls the OS
        permission request API but receives an error response
        instead of a granted or denied state because the API call
        times out, the OS permission service is unresponsive, or the
        application sandbox configuration blocks the request.
    - **Source:** A macOS sandbox entitlement is missing for the
        notification capability, a Windows registry policy blocks
        notification permission requests, or a Linux D-Bus error
        prevents the permission service from responding within the
        timeout period of 5000 ms.
    - **Consequence:** The permission state remains not-yet-
        determined and the application cannot dispatch OS-native
        notifications for the current event, leaving the user
        without an OS notification for the triggering event.
    - **Recovery:** The application catches the permission API error
        and falls back to displaying the event as an in-app Sonner
        toast, logs the error with the platform name and error
        details, and retries the permission request on the next
        notification event to determine if the OS permission service
        has become available.

- **Notification click event is lost or not delivered to Tauri**
    - **What happens:** The user clicks an OS notification banner
        but the Tauri application does not receive the click event
        because the event listener was not registered, the IPC
        channel between the OS notification service and the Tauri
        runtime is broken, or the application process restarted
        between dispatch and click.
    - **Source:** The tauri-plugin-notification event listener was
        not registered during application startup due to a plugin
        initialization error, the IPC channel was interrupted by a
        system sleep or hibernate cycle, or the application process
        was force-killed and restarted without the notification
        context being preserved.
    - **Consequence:** The application does not navigate to the
        relevant page and the user is brought to the foreground at
        whatever page was last active, requiring manual navigation
        to discover the event that triggered the notification.
    - **Recovery:** The application logs the missing click event
        when the window receives focus without a corresponding
        notification navigation target, and the user falls back to
        discovering the event through the normal in-app notification
        indicators (badge counts, inbox items) that persist
        independently of the OS notification click delivery.

- **Sonner toast fails to render in the webview**
    - **What happens:** The in-app Sonner toast component fails to
        render because the React rendering pipeline encounters an
        error, the Sonner container is not mounted in the DOM, or a
        JavaScript exception interrupts the toast display lifecycle
        during component mounting.
    - **Source:** A React state update conflict causes the Sonner
        provider to unmount, a JavaScript error in a nearby component
        propagates through the error boundary and disrupts the toast
        rendering, or the webview memory is constrained and the
        garbage collector delays component mounting beyond the
        rendering deadline.
    - **Consequence:** The in-app toast notification is not displayed
        and the user misses the event notification entirely when the
        application is in the foreground, because the OS notification
        was already suppressed due to the focused window state.
    - **Recovery:** The application catches the React rendering error
        through the error boundary, logs the toast failure with the
        component stack trace and event type, and the user falls back
        to discovering the event through persistent in-app indicators
        such as notification badge counts and inbox items that do not
        depend on the Sonner toast rendering pipeline.

## Declared Omissions

- This specification does not define the content or layout of the
    invitation acceptance page, session sign-in page, or update
    prompt page that the user navigates to after clicking a
    notification — those pages are defined in their respective
    behavioral specifications.
- This specification does not cover the auto-update download and
    installation mechanism triggered after the user reaches the
    update prompt page — the update lifecycle is defined in a
    separate specification addressing the Tauri updater plugin.
- This specification does not address notification grouping or
    stacking behavior when multiple notifications accumulate in the
    OS notification area — grouping behavior is controlled by the
    operating system and varies by platform without application
    configuration.
- This specification does not define the in-app notification
    persistence layer (badge counts, inbox items) that serves as
    the fallback discovery mechanism when OS notifications or
    toasts are missed — that persistence layer is defined in a
    separate notification inbox specification.
- This specification does not cover notification sound or vibration
    settings because those are controlled entirely by the operating
    system notification preferences and the application does not
    override or configure audio playback for notification events.

## Related Specifications

- [user-launches-desktop-app](user-launches-desktop-app.md) —
    Defines the Tauri 2 desktop application startup sequence that
    initializes the native window and webview, which is the runtime
    environment where the notification handler registers its event
    listeners and the Sonner toast provider mounts
- [user-uses-system-tray](user-uses-system-tray.md) — Defines the
    system tray icon and context menu that coexists with the OS
    notification area where notification banners appear, and both
    features rely on the Tauri runtime's integration with the
    operating system's notification and tray services
- [session-lifecycle](session-lifecycle.md) — Defines the session
    expiration timing and token validation that determines when the
    session-expiry notification event is triggered, specifically when
    the session reaches the 5-minute remaining threshold before
    expiration
- [user-accepts-an-invitation](user-accepts-an-invitation.md) —
    Defines the invitation acceptance page and workflow that the user
    navigates to when clicking an organization invitation notification,
    including the acceptance confirmation and organization membership
    creation
- [user-changes-language](user-changes-language.md) — Defines the
    locale switching mechanism that determines which @repo/i18n
    translation keys are resolved when constructing notification
    payload titles and body messages for all three trigger event types
