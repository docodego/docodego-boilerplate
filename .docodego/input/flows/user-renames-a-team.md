[← Back to Index](README.md)

# User Renames a Team

## Initiating the Rename

On the teams page at `/app/$orgSlug/teams`, each team row has a pencil icon that opens a rename dialog. The dialog appears with the team's current name pre-filled in the input field, so the user can see exactly what they are changing from.

## Saving the New Name

The user edits the name to their desired value and clicks save. The client calls `authClient.organization.updateTeam({ teamId, data: { name } })` to persist the change. Once the server confirms the update, the dialog closes and the team list refreshes to display the updated team name.
