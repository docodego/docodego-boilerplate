[← Back to Index](README.md)

# User Deletes a Team

## Initiating Deletion

On the teams page at `/app/$orgSlug/teams`, each team row has a trash icon for deletion. Clicking it opens a confirmation dialog that asks: "Are you sure you want to delete '{name}'?" This confirmation step prevents accidental team deletions.

## Safety Guard

If this is the last remaining team in the organization, the delete button is disabled. The organization must always have at least one team, so the system prevents deletion of the final team entirely.

## Confirming Deletion

When the user confirms, the client calls `authClient.organization.removeTeam({ teamId, organizationId })`. The server deletes the team record and all team-member associations tied to it. Organization members who were part of the deleted team remain in the organization — only their association with that specific team is removed. The team list refreshes to reflect the deletion.
