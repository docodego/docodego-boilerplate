[← Back to Index](README.md)

# User Transfers Organization Ownership

## The Danger Zone

On the organization settings page at `/app/$orgSlug/settings`, the danger zone section is visible only to the organization owner. Among the destructive actions listed here — alongside [deleting the organization](user-deletes-an-organization.md) — is the option to transfer ownership. Admins and regular members do not see this section at all.

## Selecting a New Owner

The owner clicks the "Transfer ownership" button. A dialog opens displaying a list of all members who currently hold the Admin role within the organization. Only admins are eligible to become the new owner — regular members do not appear in this list. If the organization has no other admin members, the list is empty and the transfer cannot proceed. The owner selects one admin from the list as the intended new owner.

## Confirmation Step

After selecting the new owner, a confirmation dialog appears with a clear, localized warning explaining what the transfer means. The current owner will lose owner-level privileges and be downgraded to an admin member. The selected admin will gain full ownership, including the ability to delete the organization, manage billing, and perform future ownership transfers. The dialog requires the owner to explicitly confirm the action — there is no way to trigger the transfer accidentally.

## After the Transfer

When the owner confirms, the app calls the ownership transfer endpoint with the selected member's ID. The server updates the organization record atomically: the previous owner's role changes from Owner to Admin, and the new owner's role changes from Admin to Owner. Both changes take effect immediately. The previous owner's UI refreshes to reflect their new admin role — the danger zone section disappears from their settings view, and owner-only controls are no longer available to them. The new owner gains access to all owner-level actions on their next page load or data fetch, including the danger zone in organization settings.

## Constraints

Only the current owner can initiate a transfer. There is no mechanism for admins to request or claim ownership. The organization always has exactly one owner at any given time — the transfer is a direct handoff, never a gap or a shared state.
