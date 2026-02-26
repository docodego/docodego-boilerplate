[← Back to Index](README.md)

# User Installs Browser Extension

## Installation

The user installs the DoCodeGo extension from the Chrome Web Store or Firefox Add-ons. Once installed, the extension icon appears in the browser's toolbar. The WXT framework handles Manifest V3 generation automatically, so the same codebase produces a valid extension for both Chrome and Firefox without browser-specific configuration.

## Background Initialization

On installation, the background service worker starts. This service worker is the extension's persistent backend — it manages authentication tokens, routes API calls, and handles communication between the popup and the web app. The extension requests three permissions at install time: `storage` for persisting the auth token in `chrome.storage.local`, `activeTab` for accessing information about the currently open tab when the user clicks the extension icon, and `host_permissions` scoped to the DoCodeGo API URL for making authenticated requests.

## First Interaction

When the user clicks the extension icon in the toolbar, the popup opens. The popup is a React app built with components from `@repo/ui` — the same Shadcn component library used in the web dashboard. On first launch, the popup detects that no auth token is stored and displays a sign-in prompt. The user cannot interact with any authenticated features until they complete the [token relay authentication flow](extension-authenticates-via-token-relay.md). The popup is compact and focused — it provides a clear call to action to sign in and a brief explanation of what the extension does.