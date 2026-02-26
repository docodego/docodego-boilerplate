[← Back to Index](README.md)

# User Deletes Their Account

## Accessing Account Deletion

The user navigates to their account settings page at `/app/settings/account`. At the bottom of the page, a danger zone section contains the account deletion option. This section is always visible to the authenticated user — account deletion is a self-service action available to everyone.

## Ownership Check

Before the deletion can proceed, the system checks whether the user is the owner of any organization. If the user owns one or more organizations, the deletion is blocked. The interface displays a message explaining that the user must first either transfer ownership of each organization to another member or [delete those organizations](user-deletes-an-organization.md). The user cannot delete their account while they remain responsible for an organization's existence.

## Confirmation

Once the ownership check passes, the user clicks the delete account button. A confirmation dialog appears with a strong, localized permanent warning: deleting the account cannot be undone. All personal data, profile information, and organization memberships will be permanently removed. The dialog requires the user to type a confirmation phrase — such as the word "delete" or their email address — to prevent accidental deletion. Only after typing the correct phrase can the user click the final confirmation button.

## Processing the Deletion

After the user confirms, the client calls the account deletion endpoint. The server performs the following cleanup: all active sessions belonging to the user are revoked immediately, the user is removed from every organization they belong to, and the user record itself is permanently deleted from the database. Any session cookies are cleared from the response.

## After Deletion

The user is redirected to the landing page or the sign-in page. From this point, the user's credentials no longer exist in the system — any attempt to sign in with the same email will fail as if the account never existed. If the user wants to use the application again, they must [register a new account](user-signs-in-with-email-otp.md) from scratch. The deletion is final and there is no recovery mechanism.
