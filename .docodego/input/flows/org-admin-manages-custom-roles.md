[← Back to Index](README.md)

# Org Admin Manages Custom Roles

## Navigating to Access Control

The org admin navigates to the "Roles" or "Access Control" section within the organization settings at `/app/$orgSlug/settings`. The page displays a list of all roles for the organization. The default roles — Owner, Admin, and Member — are shown with localized labels and a visual indicator that they are system roles. These default roles cannot be deleted or renamed. Below them, any previously created custom roles are listed with their assigned permission sets.

## Creating a Custom Role

The admin clicks a localized "Create role" button. A form appears prompting for a role name (e.g., "Viewer" or "Billing Manager") and a checklist of available permissions. The admin enters the name, selects the desired permissions, and submits. The client calls the Organization plugin's `createRole()` method with the role name and selected permissions. The server validates that the role name is unique within the organization and persists the new role. On success, the new custom role appears in the roles list immediately.

## Editing and Renaming a Custom Role

The admin clicks on an existing custom role to expand or open its detail view. From here they can rename the role, add or remove individual permissions from the checklist, and save the changes. The client calls `updateRole()` with the updated fields. The change takes effect immediately — any member currently assigned to that role gains or loses access according to the updated permissions on their next request. The `hasPermission()` check evaluates against the latest role definition, so there is no propagation delay.

## Deleting a Custom Role

The admin clicks a localized "Delete" action on a custom role. A localized confirmation dialog appears warning that all members currently assigned to this role will fall back to the default "Member" role. On confirm, the client calls `deleteRole()`. The server reassigns affected members to the "Member" role and removes the custom role record. The roles list refreshes to reflect the deletion. Default roles (Owner, Admin, Member) do not show a delete action.

## Using Custom Roles

Custom roles appear alongside the default roles in the role dropdown when an admin [changes a member's role](org-admin-changes-member-role.md). The `listRoles()` method returns both default and custom roles with localized display names, making them available throughout the organization management UI. Permission checks across the application use `hasPermission()` against the member's assigned role, whether default or custom. See also [organization settings](user-updates-organization-settings.md) for the broader settings context.
