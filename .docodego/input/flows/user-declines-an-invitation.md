[← Back to Index](README.md)

# User Declines an Invitation

## Receiving the Invitation

The invitee receives an email containing a link to join the organization. The link points to the application and carries the invitation token. Clicking the link opens the app and resolves the invitation details from the server, including the organization name, logo, and the role being offered.

## Viewing the Acceptance Screen

The application presents a localized acceptance screen showing the organization's name, the role the invitee has been offered, and two action buttons: a primary "Accept" button and a secondary "Decline" button. If the invitee is not yet signed in, they are directed through the [sign-in flow](user-signs-in-with-email-otp.md) first and returned to this screen once authenticated.

## Declining the Invitation

The invitee clicks the localized "Decline" button. The client calls `authClient.organization.rejectInvitation()`, which marks the invitation as rejected on the server. A localized confirmation message is displayed to the invitee confirming that the invitation has been declined. The invitee is then navigated away from the acceptance screen — either to their existing dashboard if they belong to other organizations, or to the organization creation flow if they have none.

## Impact on the Admin's View

On the organization members page, the invitation moves from the Pending tab to the History tab. The History tab displays the invitation with a "declined" badge in a red accent color, along with the invitee's email and the date of rejection. The [org admin](org-admin-invites-a-member.md) can see at a glance that this person chose not to join.

## Finality of the Decline

A declined invitation cannot be accepted later — the token is permanently invalidated once the invitee rejects it. If the org admin still wants to add the person, they must send a fresh invitation from the [invite flow](org-admin-invites-a-member.md). The previous declined record remains visible in the History tab for audit purposes.
