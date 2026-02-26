[← Back to Index](README.md)

# User Accepts an Invitation

## Receiving the Invitation

The invitee receives an email containing a link to join the organization. The link points to the application and carries the invitation token. What happens next depends on whether the invitee already has an account.

## Accepting with an Existing Account

If the invitee is already signed in or has an existing account, clicking the link resolves the invitation and presents a localized acceptance screen. The user confirms by triggering `authClient.organization.acceptInvitation()`, which validates the token, checks that the invitation has not expired (invitations are valid for 7 days), and adds the user to the organization with the role specified by the admin. The user is then navigated to the organization dashboard where they can immediately begin working within the org.

## Accepting without an Account

If the invitee does not have an account, clicking the invitation link directs them through the [sign-in flow](user-signs-in-with-email-otp.md) first. Once the account is created and the user is signed in, the invitation acceptance completes automatically. The user arrives at the organization dashboard as a new member with the assigned role.

## Rejecting an Invitation

The invitee can also choose to reject the invitation by triggering `authClient.organization.rejectInvitation()`. The invitation moves to the History tab on the members page with a "rejected" status displayed as a red badge. A rejected invitation cannot be accepted later — the admin would need to send a new one.

## Admin Cancellation and Expiry

From the Pending tab, an admin can cancel any pending invitation before the invitee acts on it. Canceling sets the invitation status to "canceled" and it moves to the History tab with a corresponding status badge. If neither the invitee nor the admin takes action within 7 days, the invitation expires automatically and becomes invalid. Expired invitations can no longer be accepted — the admin must create a fresh invitation if they still want to add that person.
