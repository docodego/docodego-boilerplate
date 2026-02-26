# User Creates a Team

## Starting Point

The user navigates to the teams page at `/app/$orgSlug/teams`, which lists all existing teams in the organization. A "Create team" button is available on the page.

## Creating the Team

The user clicks "Create team" and a dialog appears with a single input field for the team name. The user enters the desired name and submits the form. The client calls `authClient.organization.createTeam({ name, organizationId })` to create the team on the server.

## Limits and Completion

The system enforces a maximum of 25 teams per organization, defined by `LIMITS.MAX_TEAMS_PER_ORG`. If the organization already has 25 teams, the creation request fails and the user sees an error message indicating the team limit has been reached. When the team is created successfully, the dialog closes and the team list refreshes to show the newly created team.
