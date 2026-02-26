# Org Admin Invites a Member

## Starting Point

The org admin or owner is on the organization members page at `/app/$orgSlug/members`. This page shows all current members in an Active tab, pending invitations in a Pending tab, and past invitations in a History tab. An "Invite member" button is visible in the top-right area of the page.

## Sending the Invitation

The org admin clicks "Invite member" and a dialog opens. The dialog contains two fields: an email input for the invitee's address and a role dropdown with two options — Member and Admin. The org admin fills in the email, selects the appropriate role, and clicks the submit button.

On submit, the client calls `authClient.organization.inviteMember({ email, inviteRole, organizationId })`. The server creates an invitation record tied to the organization with a 7-day expiry window. An email is sent to the invitee containing an invitation link. In development mode, this email is logged to the console rather than sent through a real mail provider; in production, the email is delivered through the configured email service.

## After the Invitation Is Sent

The dialog closes and the Pending tab refreshes automatically, showing the new invitation with the invitee's email, the assigned role, and the expiration date. If the org admin attempts to invite an email address that already has a pending invitation for this organization, the system returns an error indicating a duplicate invitation exists. The org admin must either wait for the existing invitation to expire, cancel it from the Pending tab, or use a different email address.
