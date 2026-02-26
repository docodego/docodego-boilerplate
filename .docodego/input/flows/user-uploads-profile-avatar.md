[← Back to Index](README.md)

# User Uploads Profile Avatar

## Navigating to the Avatar Upload

The user navigates to `/app/settings/profile` via the Settings link in the sidebar's user section (see [User Updates Profile](user-updates-profile.md)). The profile page displays an avatar section showing either the user's current avatar image or a fallback circle with the user's initials. A localized "Change avatar" button or clickable overlay appears on hover, inviting the user to upload a new image.

## Selecting an Image

The user clicks the avatar placeholder or change button, which opens the platform's native file picker. The picker is configured to accept image types only (JPEG, PNG, WebP). On the web this uses a standard file input; on desktop the same browser-based picker applies since Tauri renders a webview; on mobile, `expo-image-picker` handles photo selection (see [User Uploads a File](user-uploads-a-file.md) for platform-specific details). The file picker displays localized text provided by the operating system.

## Validation and Upload

Once the user selects an image, the client validates the file size (within the limit defined by the API, for example 2 MB) and confirms the MIME type is an accepted image format. If validation fails, a localized error toast appears explaining the constraint — "File too large" or "Unsupported format" — and the upload does not proceed.

If validation passes, the app sends the image to the avatar upload endpoint in `apps/api`. The API performs its own server-side validation, then streams the file to Cloudflare R2 object storage using the `STORAGE` binding (see [User Uploads a File](user-uploads-a-file.md) for the R2 infrastructure). The API returns the stored object's public URL. A second mutation updates the user record with the new avatar URL by calling `authClient.updateUser()`.

## Reflecting the New Avatar

On success, a localized toast confirmation appears via Sonner. The cached user data is invalidated in TanStack Query, causing every component that displays the user's avatar — the header dropdown, organization member lists, the org switcher — to re-fetch and render the new image immediately. The initials fallback is replaced by the uploaded image across the entire app.

On failure, an error toast describes what went wrong. The previous avatar (or initials fallback) remains unchanged so the user can retry.

## Initials Fallback

Whenever a user has no avatar URL set — either because they never uploaded one or because the image was removed — the app renders a colored circle containing the user's initials derived from their display name. This fallback is consistent everywhere avatars appear: the header, member lists, and the org switcher.
