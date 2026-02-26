[← Back to Index](README.md)

# Org Admin Changes a Member's Role

## Viewing Role Controls

From the Members tab on the `/app/$orgSlug/members` page, each member row displays the member's current role (`member.role`) alongside a control for changing it. The one exception is the organization owner — the owner row shows the "Owner" label with no role-change control, because the owner role is immutable and cannot be reassigned.

## Changing the Role

The org admin selects a new role from the available options for a given member. The available roles are Member and Admin (org-level roles, distinct from the app-level `user.role`), which are configurable through the organization's role settings. After selecting the new role, the client calls `authClient.organization.updateRole()` with the member's ID and the new role value.

## Immediate Effect

The role change takes effect immediately on the server side. The next request the affected member makes will be evaluated against their new permissions. There is no delay or propagation period — the member's access level updates in real time. On the admin's side, the UI refreshes on the next data fetch to reflect the updated role in the members list.
