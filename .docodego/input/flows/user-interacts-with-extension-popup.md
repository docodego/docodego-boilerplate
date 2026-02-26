[← Back to Index](README.md)

# User Interacts with Extension Popup

## Opening the Popup

The user clicks the DoCodeGo extension icon in the browser toolbar and the popup opens. The popup is a React app rendered from the `src/entrypoints/popup/` directory, built with components from `@repo/ui` — the same Shadcn component library and Tailwind styling used in the web dashboard. If the user is not authenticated, the popup shows only the sign-in prompt. If authenticated, the popup displays the main interface with relevant data and actions.

## Data Fetching and API Calls

The popup uses the oRPC client with typed contracts from `@repo/contracts` to make API calls, identical to how the web app fetches data. The key difference is that all requests route through the background service worker rather than going directly to the API. The popup sends a message to the background script, which attaches the stored auth token and forwards the request. This indirection is invisible to the user — the popup loads data and displays it as any other interface would.

## Content Script Interaction

When the extension needs to interact with the current browser tab, it communicates through the content script injected into the page. The popup can request information about the active tab or trigger actions on the page via messaging between the popup and the content script. The `activeTab` permission ensures the extension only accesses the tab the user explicitly clicked on, not all open tabs.

## Theming and Localization

Dark mode in the popup follows the user's browser or system preference, or their explicitly chosen theme setting if one is stored. The popup uses translations from `@repo/i18n`, supporting the same locales as the web app — including Arabic with RTL layout. Locale detection works the same way: the browser's language setting determines the initial locale.

## Closing the Popup

The popup closes when the user clicks anywhere outside it or presses Escape. Any in-progress state within the popup is lost on close — the next time the user opens the popup, it reinitializes. Persistent state like the auth token and user preferences lives in `chrome.storage.local` via the background service worker and survives popup open/close cycles.