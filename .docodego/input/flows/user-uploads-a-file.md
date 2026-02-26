# User Uploads a File

## Storage Configuration

Cloudflare R2 object storage is configured as the `STORAGE` binding in `wrangler.toml`. R2 provides an S3-compatible API with zero egress costs, making it suitable for user-generated content like avatars, organization logos, and document attachments. The binding is available to all route handlers in the API through the Cloudflare Workers environment.

## Upload Flow

The boilerplate provides the R2 binding and infrastructure — the developer implements the specific upload endpoint in `apps/api` to match their application's needs. The general flow works as follows: the user selects a file using the platform's native file picker, the frontend sends the file to the upload endpoint, the API streams the file data to R2, and returns the stored object's URL or key to the client. Size limits and content-type validation are enforced at the API layer before the file reaches R2 — the developer defines these constraints based on the use case (for example, a 2MB limit and image-only types for avatars, or a larger limit for document attachments).

## Download Flow

To serve stored files, the API either generates a presigned URL that grants temporary direct access to the R2 object, or proxies the file content through the API itself. The frontend uses the returned URL to display images or trigger downloads. Presigned URLs are preferred for large files since they avoid routing the entire file through the Worker.

## Platform-Specific File Selection

On the web, the standard browser file input handles file selection. On desktop (Tauri), the native file picker is available through Tauri's APIs, and uploads follow the same API endpoint as the web since the desktop app is a webview wrapper. On mobile, `expo-image-picker` handles photo/camera selection and `expo-document-picker` handles general file selection — both feed into the same upload API endpoint used by web and desktop.
