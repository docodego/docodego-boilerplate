[← Back to Index](README.md)

# Extension Receives an Update

## How the Update Arrives

The browser extension is distributed through the Chrome Web Store and Firefox Add-ons. When a new version is published, Chrome and Firefox handle auto-updates in the background according to their own update schedules — typically checking every few hours. The user does not need to take any action. The browser downloads the new extension package and installs it silently.

## Background Service Worker Restarts

After the update is applied, the browser terminates the extension's existing background service worker and starts a fresh instance running the new code. This restart clears any in-memory state the old service worker held, including active timers and cached data. However, data persisted in `chrome.storage.local` — most importantly, the stored authentication token from the [token relay flow](extension-authenticates-via-token-relay.md) — survives the restart intact.

## Seamless Continuation

When the new background service worker initializes, it reads the stored auth token from `chrome.storage.local`. If the token is still valid — meaning the session has not expired server-side and the token format has not changed between versions — the service worker resumes normal operation. It re-establishes the session refresh timer and begins handling API requests as before. The user opens the extension popup and sees their authenticated state exactly as they left it. From their perspective, nothing has changed.

## Breaking Token Migration

In rare cases, a new extension version may introduce a change to the token storage format or authentication contract that makes previously stored tokens incompatible. When the new service worker detects that the stored token cannot be used — either because it fails validation locally or the first API call returns an authentication error — it clears the invalid token from `chrome.storage.local`. The popup reverts to the unauthenticated state and shows the sign-in prompt. The user must re-authenticate through the [token relay flow](extension-authenticates-via-token-relay.md) to continue using the extension.

## What's New Badge

After an update, the extension can optionally display a small badge indicator on the popup icon to signal that something has changed. When the user opens the popup, a brief "What's new" section or link appears at the top, summarizing the changes in the latest version. Once the user has seen the notice, the badge is dismissed and the popup returns to its normal layout. This is entirely optional and only shown when the release includes user-facing changes worth highlighting.
