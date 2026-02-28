[← Back to Index](README.md)

# User Switches Active Team

## Opening the Team Switcher

Within an organization, the user may belong to multiple teams. The dashboard sidebar or a dedicated team switcher component displays the localized name of the user's currently active team. When the user clicks it, a dropdown opens listing all teams the user is a member of within the current organization. The active team is visually marked — highlighted or checked — so the user can see which team context they are working in at a glance.

## Selecting a Different Team

The user clicks on a different team in the dropdown list. The client calls `authClient.organization.setActiveTeam({ teamId })` with the ID of the selected team. The server updates the session's `activeTeamId` to reflect the newly selected team. Unlike [organization switching](user-switches-organization.md), which is driven by a URL change, team switching is a session-level operation — the URL does not change, but the session now carries the new team context.

## Scoped Data and Permissions

Once the active team updates, API responses and permission checks scope to the new team context. Any team-specific data — such as team members, team settings, or team-scoped resources — reflects the newly selected team. The user's effective permissions may change depending on their role within the selected team. For example, a user who is an admin of one team but a regular member of another will see different options after switching.

## Dashboard Re-renders

The dashboard re-renders to reflect the new team context. Components that display team-scoped data refetch their content based on the updated `activeTeamId` in the session. TanStack Query caches keyed by team ID ensure that previously visited teams may load instantly from cache while background refetches run. The sidebar, header, and content area all update to match the selected team.
