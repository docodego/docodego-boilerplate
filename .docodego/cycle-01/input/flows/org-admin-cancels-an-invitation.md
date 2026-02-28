[← Back to Index](README.md)

# Org Admin Cancels an Invitation

## Starting Point

The org admin or owner is on the organization members page at `/app/$orgSlug/members`. They navigate to the Pending tab, which lists all outstanding invitations that have not yet been accepted, declined, or expired. Each row shows the invitee's email, the assigned role, the expiration date, and a "Cancel" action button.

## Initiating the Cancellation

The org admin clicks the "Cancel" button on the invitation they wish to revoke. A localized confirmation dialog appears, asking the admin to confirm that they want to cancel the invitation. The dialog clearly states that the invitee will no longer be able to use the invitation link to join the organization. The admin clicks the localized "Confirm" button to proceed, or "Cancel" to dismiss the dialog without taking action.

## Processing the Cancellation

On confirmation, the client calls `authClient.organization.cancelInvitation()` with the invitation identifier. The server invalidates the invitation token and sets the invitation status to "canceled." The Pending tab refreshes automatically, and the invitation is no longer listed there. It moves to the History tab with a "canceled" badge displayed in a neutral accent color, alongside the invitee's email and the date of cancellation.

## Invitee Clicks an Invalidated Link

If the invitee clicks the invitation link after the admin has canceled it, the application resolves the token and detects that the invitation is no longer valid. Instead of the acceptance screen, the invitee sees a localized message explaining that the invitation is no longer valid. No action buttons are presented — the invitee is given a link to return to the app's home page or sign-in screen.

## Re-Inviting the Same Person

The cancellation does not prevent the admin from [sending a new invitation](org-admin-invites-a-member.md) to the same email address. Once the original invitation is canceled, the duplicate-check no longer blocks a fresh invitation. The admin can return to the Pending tab, click "Invite member," and issue a new invitation with the same or a different role. The canceled record remains in the History tab for reference.
