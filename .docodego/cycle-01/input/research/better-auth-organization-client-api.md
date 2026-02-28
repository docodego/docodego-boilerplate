# Better Auth — Organization Plugin Client API Reference

> Source: https://www.better-auth.com/docs/plugins/organization
> Research date: 2026-02-27
> Purpose: Prevent Claude from hallucinating method signatures when implementing org features.

---

## Setup

### Server
```ts
import { betterAuth } from "better-auth";
import { organization } from "better-auth/plugins";

export const auth = betterAuth({
    plugins: [organization()],
});
```

### Client
```ts
import { createAuthClient } from "better-auth/client";
import { organizationClient } from "better-auth/client/plugins";

export const authClient = createAuthClient({
    plugins: [organizationClient()],
});
```

All client methods are accessed via `authClient.organization.*`.
React hooks are accessed via `authClient.use*()`.
Import source for both: `@/lib/auth-client` (local alias, NOT from `better-auth` directly).

---

## React Hooks (only 2)

```ts
const { data: orgs, isPending, error } = authClient.useListOrganizations();
// data: Organization[]

const { data: activeOrg, isPending, error } = authClient.useActiveOrganization();
// data: Organization | null
```

---

## Organization Methods

```ts
// Create
const { data, error } = await authClient.organization.create({
    name: string,
    slug: string,
    logo?: string,                          // URL
    metadata?: Record<string, any>,
    keepCurrentActiveOrganization?: boolean,
});
// data: Organization

// List (imperative — prefer useListOrganizations() hook in React)
const { data, error } = await authClient.organization.list({});
// data: Organization[]

// Get full org with members
const { data, error } = await authClient.organization.getFullOrganization({
    organizationId?: string,
    organizationSlug?: string,
    membersLimit?: number,                  // default 100
});
// data: Organization & { members: Member[] }

// Set active (updates session)
const { data, error } = await authClient.organization.setActive({
    organizationId?: string | null,         // null to unset
    organizationSlug?: string,
});
// data: Session

// Update
const { data, error } = await authClient.organization.update({
    data: {
        name?: string,
        slug?: string,
        logo?: string,
        metadata?: Record<string, any> | null,
    },
});
// data: Organization

// Delete
const { data, error } = await authClient.organization.delete({
    organizationId: string,
});
// data: null

// Check slug availability
const { data, error } = await authClient.organization.checkSlug({
    slug: string,
});
// data: { available: boolean }
```

---

## Member Methods

```ts
// List members
const { data, error } = await authClient.organization.listMembers({
    organizationId?: string,
    limit?: number,
    offset?: number,
    sortBy?: string,
    sortDirection?: "asc" | "desc",
    filterField?: string,
    filterOperator?: "eq" | "ne" | "gt" | "gte" | "lt" | "lte" | "in" | "nin" | "contains",
    filterValue?: string,
});
// data: Member[]

// Get current user's member record in active org
const { data, error } = await authClient.organization.getActiveMember({});
// data: Member

// Get current user's role in active org
const { data, error } = await authClient.organization.getActiveMemberRole({});
// data: { role: string | string[] }

// Add member directly (no invitation)
const { data, error } = await authClient.organization.addMember({
    userId?: string | null,
    role: string | string[],
    organizationId?: string,
    teamId?: string,
});
// data: Member

// Remove member
const { data, error } = await authClient.organization.removeMember({
    memberIdOrEmail: string,               // member ID or email address
    organizationId?: string,
});
// data: null

// Update member role
const { data, error } = await authClient.organization.updateMemberRole({
    memberId: string,
    role: string | string[],
    organizationId?: string,
});
// data: Member

// Leave organization (current user)
const { data, error } = await authClient.organization.leave({
    organizationId: string,
});
// data: null
```

---

## Invitation Methods

```ts
// Send invitation
const { data, error } = await authClient.organization.inviteMember({
    email: string,
    role: string | string[],
    organizationId?: string,
    resend?: boolean,
    teamId?: string,
});
// data: Invitation

// Accept invitation
const { data, error } = await authClient.organization.acceptInvitation({
    invitationId: string,
});
// data: Member

// Reject invitation
const { data, error } = await authClient.organization.rejectInvitation({
    invitationId: string,
});
// data: null

// Cancel invitation (by org admin)
const { data, error } = await authClient.organization.cancelInvitation({
    invitationId: string,
});
// data: null

// Get single invitation
const { data, error } = await authClient.organization.getInvitation({
    id: string,
});
// data: Invitation

// List org invitations
const { data, error } = await authClient.organization.listInvitations({
    organizationId?: string,
});
// data: Invitation[]

// List invitations for current user (across all orgs)
const { data, error } = await authClient.organization.listUserInvitations({});
// data: Invitation[]
```

---

## Access Control Methods

```ts
// Check permission (async — hits server)
const { data, error } = await authClient.organization.hasPermission({
    permissions: Record<string, string[]>,  // e.g. { project: ["create"] }
});
// data: { hasPermission: boolean }

// Check role permission (sync — no server roundtrip)
const allowed: boolean = authClient.organization.checkRolePermission({
    permissions: Record<string, string[]>,
    role: string,
});
```

---

## Custom Role Methods (Dynamic Access Control)

```ts
// Create custom role
const { data, error } = await authClient.organization.createRole({
    role: string,
    permission?: Record<string, string[]>,
    organizationId?: string,
});
// data: Role

// List roles
const { data, error } = await authClient.organization.listRoles({
    organizationId?: string,
});
// data: Role[]

// Get role
const { data, error } = await authClient.organization.getRole({
    roleName?: string,
    roleId?: string,
    organizationId?: string,
});
// data: Role

// Update role
const { data, error } = await authClient.organization.updateRole({
    roleName?: string,
    roleId?: string,
    organizationId?: string,
    data: { permission?: Record<string, string[]> },
});
// data: Role

// Delete role
const { data, error } = await authClient.organization.deleteRole({
    roleName?: string,
    roleId?: string,
    organizationId?: string,
});
// data: null
```

---

## Team Methods

```ts
// Create team
const { data, error } = await authClient.organization.createTeam({
    name: string,
    organizationId?: string,
});
// data: Team

// List org teams
const { data, error } = await authClient.organization.listTeams({
    organizationId?: string,
});
// data: Team[]

// Update team
const { data, error } = await authClient.organization.updateTeam({
    teamId: string,
    data: { name?: string },
});
// data: Team

// Remove team
const { data, error } = await authClient.organization.removeTeam({
    teamId: string,
    organizationId?: string,
});
// data: null

// Set active team (updates session)
const { data, error } = await authClient.organization.setActiveTeam({
    teamId?: string,                        // undefined/null to unset
});
// data: Session

// List teams for current user (across all orgs)
const { data, error } = await authClient.organization.listUserTeams({});
// data: Team[]

// List team members
const { data, error } = await authClient.organization.listTeamMembers({
    teamId?: string,                        // defaults to active team
});
// data: Member[]

// Add member to team
const { data, error } = await authClient.organization.addTeamMember({
    teamId: string,
    userId: string,
});
// data: TeamMember

// Remove member from team
const { data, error } = await authClient.organization.removeTeamMember({
    teamId: string,
    userId: string,
});
// data: null
```

---

## Common Mistakes to Avoid

- **Do NOT** import hooks from `better-auth/react` or `better-auth/client` — hooks live on `authClient` instance
- **Do NOT** call `authClient.useListOrganizations` — it's `authClient.useListOrganizations()` (invoked)
- **Do NOT** pass `organizationId` to `getActiveMember` / `getActiveMemberRole` / `list` — they take `{}`
- **Do NOT** use `memberId` in `removeMember` — parameter is `memberIdOrEmail`
- **Do NOT** use `id` in `cancelInvitation` — parameter is `invitationId`
- **`setActive`** updates the session and returns `Session`, not `Organization`
- **`checkRolePermission`** is synchronous (returns `boolean`); **`hasPermission`** is async (returns `Promise`)
- **`listUserInvitations`** takes `{}` not `organizationId` — it lists across all orgs for current user
