[← Back to Index](README.md)

# Desktop Opens External Link

## The User Clicks an External Link

While using the desktop app, the user clicks a link that points outside the application — for example, a GitHub repository link, a documentation link, or a changelog link from the footer of the [landing page](user-visits-landing-page.md). Because the desktop app runs inside a Tauri webview with no browser chrome (no address bar, no tabs, no back button), navigating the webview to an external URL would strand the user outside the application with no way to return.

## Tauri Opener Intercepts the Navigation

The `tauri-plugin-opener` intercepts outbound link clicks that target external domains. Instead of navigating the webview away from the application, the plugin opens the URL in the user's default system browser — Chrome, Firefox, Safari, or whichever browser is configured as the OS default. The webview remains on the page the user was viewing, undisturbed.

## The User Continues in Both Contexts

The external page loads in a new browser tab or window. The user can read the documentation, browse the repository, or interact with whatever external resource they clicked. Meanwhile, the desktop app stays exactly where it was — no navigation occurred in the webview, no state was lost, and the user can switch back to the app window at any time to continue working.

## OAuth Redirects Use the Same Mechanism

This same plugin handles OAuth redirects during [SSO sign-in](user-signs-in-with-sso.md). When the user initiates SSO, the opener plugin launches the identity provider's sign-in page in the system browser. After authentication completes, the provider redirects back to the app via a [deep link](user-opens-a-deep-link.md) (`docodego://auth/callback`), returning the user to the desktop app with their session established.
