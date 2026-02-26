[← Back to Index](README.md)

# Org Admin Manages Team Members

## Opening the Team Members Dialog

On the teams page at `/app/$orgSlug/teams`, each team row has a users icon. Clicking it opens the TeamMembersDialog, which displays all current members of that specific team.

## Adding Members to the Team

To add a member, the org admin selects from a list of organization members who are not yet part of this team. After selecting a member, the client calls `authClient.organization.addTeamMember()` to associate that person with the team. The dialog updates immediately to show the newly added member in the team members list.

## Removing Members from the Team

Each team member row in the dialog has a remove option. When the org admin removes someone, the client calls `authClient.organization.removeTeamMember()`. This removes the person from the team only — they remain a full member of the organization with all their org-level permissions intact. Team membership is entirely independent of organization membership; removing someone from a team does not affect their access to the organization or any other team they belong to. The dialog updates after each add or remove operation to reflect the current state of the team.
