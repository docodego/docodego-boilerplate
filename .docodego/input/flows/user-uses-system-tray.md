# User Uses System Tray

## The tray icon is present

When the desktop application launches, a tray icon appears in the system notification area. On Windows, this is the taskbar notification area (system tray) in the bottom-right corner. On macOS, the icon appears in the menu bar at the top of the screen. The icon remains present for the entire lifetime of the application, providing a persistent access point for controlling the app.

## The user interacts with the tray icon

Left-clicking the tray icon toggles the main window's visibility. If the window is currently visible, a left-click hides it. If the window is hidden, a left-click brings it back and focuses it. This gives the user a quick way to show or dismiss the application window without closing it.

Right-clicking the tray icon opens a context menu with two options: "Show" and "Quit". The "Show" option brings the window to the foreground and focuses it, useful when the user wants to access the app without the toggle behavior. The "Quit" option closes the application entirely, removing the tray icon and terminating the process.

## Closing the window quits the app

When the user clicks the close button (X) on the application window, the app quits entirely. There is no minimize-to-tray behavior on close. The window closes, the tray icon is removed, and the application process terminates. This keeps the behavior simple and predictable: closing means closing.
