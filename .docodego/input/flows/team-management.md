# Team Management

## Viewing Teams

The teams page lives at `/app/$orgSlug/teams`. When a user navigates there, the page displays a list of all teams in the organization. Each team row shows the team's name, the date it was created, and action buttons for renaming, managing members, and deleting.

The data is fetched via `authClient.organization.listTeams({ query: { organizationId } })`. The list is straightforward -- teams are a flat structure within an org, not nested or hierarchical.

## Creating a Team

From the teams page, a user clicks the "Create team" button. A dialog opens with a single field: the team name.

The user types a name and submits. The frontend calls `authClient.organization.createTeam({ name, organizationId })`. The system enforces a limit of 25 teams per organization (defined by `LIMITS.MAX_TEAMS_PER_ORG`). If the org already has 25 teams, the creation fails and the user sees an error indicating the limit has been reached.

After successful creation, the dialog closes and the team list refreshes to include the new team.

## Renaming a Team

Each team row has a pencil icon for renaming. Clicking it opens a rename dialog with the current name pre-filled in the input field.

The user edits the name and saves. The frontend calls `authClient.organization.updateTeam({ teamId, data: { name } })`. The dialog closes and the team list refreshes to show the updated name.

## Managing Team Members

Each team row has a users icon that opens the TeamMembersDialog. This dialog shows all current members of that specific team.

From this dialog, admins can add organization members to the team or remove existing team members. Adding a member calls `authClient.organization.addTeamMember()` with the team ID and the user to add. The dialog likely presents a list or search of org members who are not yet on this team, making it easy to pick who to add.

Removing a team member calls `authClient.organization.removeTeamMember()`. The member is taken off the team but remains a member of the organization -- team membership and org membership are independent. A person can be in the org without being on any team, or on multiple teams simultaneously.

The dialog updates its member list after each add or remove operation.

## Deleting a Team

Each team row has a trash icon for deletion. Clicking it opens a confirmation dialog that asks: "Are you sure you want to delete '{name}'?"

There is a safety guard: if this is the only team in the organization, the delete button is disabled. This prevents a state where the org has no teams at all, which could orphan team-dependent functionality.

When the user confirms deletion (and the team is not the last one), the frontend calls `authClient.organization.removeTeam({ teamId, organizationId })`. The team and all its team-member associations are removed. Organization members who were on that team remain in the org -- they just lose that team association.

After deletion, the team list refreshes to reflect the change.
