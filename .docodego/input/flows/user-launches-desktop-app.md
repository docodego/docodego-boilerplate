[← Back to Index](README.md)

# User Launches Desktop App

## The user opens the application

On Windows, the user double-clicks the `.exe` file or launches the app from the Start menu. On macOS, the user opens the `.app` bundle, typically from the Applications folder after installing from the `.dmg`. On Linux, the user runs the `.AppImage` or launches from the application menu if installed via the `.deb` package. Regardless of platform, the Tauri runtime starts and opens a native window.

## The window loads the web application

The native window contains a webview that loads the full web application. The Window-State plugin restores the window to its last-used size and position, so the app appears exactly where the user left it in their previous session. If this is the first launch, the window opens at a sensible default size and centered on the screen. There is no browser chrome visible: no address bar, no tabs, no forward/back navigation buttons. The window has an OS-native title bar with the standard minimize, maximize, and close buttons, making the application feel like any other native desktop program.

## The system tray icon appears

As part of the launch process, a tray icon is registered in the system notification area on Windows, or the menu bar area on macOS. This icon provides quick access to show, hide, or quit the application without needing to find the window. The application is now fully running and ready for the user to sign in or continue their session. Because auth works via cookies natively in the Tauri webview, the user's existing session persists across restarts just as it would in a browser.
