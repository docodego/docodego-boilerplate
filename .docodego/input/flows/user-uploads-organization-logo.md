[← Back to Index](README.md)

# User Uploads Organization Logo

## Navigating to Organization Settings

An organization owner or admin navigates to `/app/$orgSlug/settings` via the sidebar's Org Settings link (see [User Updates Organization Settings](user-updates-organization-settings.md)). The settings page displays the organization's current details along with a logo section. If a logo has already been uploaded, it is shown as a thumbnail; otherwise a generic placeholder icon appears. A localized "Change logo" button or clickable overlay invites the admin to upload a new image.

## Selecting an Image

The admin clicks the logo placeholder or change button, which opens the platform's native file picker configured to accept image types only (JPEG, PNG, WebP, SVG). On web and desktop (Tauri webview) this uses the standard browser file input; on mobile, `expo-image-picker` handles the selection (see [User Uploads a File](user-uploads-a-file.md) for platform-specific file selection details). The file picker displays localized text provided by the operating system.

## Validation and Upload

The client validates the selected file against size and type constraints before sending it to the server. If the file is too large or not an accepted image format, a localized error toast appears and the upload is aborted.

If validation passes, the app sends the image to the organization logo upload endpoint in `apps/api`. The API performs server-side validation, confirms the requesting user holds the owner or admin role for the organization, and then streams the file to Cloudflare R2 object storage via the `STORAGE` binding (see [User Uploads a File](user-uploads-a-file.md) for R2 infrastructure details). The API returns the stored object's URL. A second mutation updates the organization record with the new logo URL.

## Reflecting the New Logo

On success, a localized toast confirmation appears via Sonner. The cached organization data is invalidated in TanStack Query, causing every component that displays the organization's logo — the org switcher dropdown, the header, and any member-facing views — to re-fetch and render the new logo immediately.

On failure, an error toast describes the problem. The previous logo or placeholder remains unchanged so the admin can retry.

## Permissions

Only the organization owner and users with an admin role can upload or change the organization logo. Other members see the logo displayed throughout the app but have no access to the upload control. The API enforces this server-side — requests from non-admin members are rejected with an appropriate error regardless of what the client sends.
