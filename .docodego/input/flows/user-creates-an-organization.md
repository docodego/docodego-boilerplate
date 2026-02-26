[← Back to Index](README.md)

# User Creates an Organization

## Starting from the Org Switcher

A user who already belongs to at least one organization can create additional organizations from within the dashboard. In the header, the user clicks on the OrgSwitcher component, which opens a dropdown listing their current organizations. At the bottom of this dropdown, a "Create organization" option is available. Clicking it opens the organization creation form.

## The Creation Form

The form mirrors the onboarding experience: an organization name input and a URL slug input. As the user types the name, the slug auto-generates via the `toSlug()` function — lowercase, hyphens for spaces, special characters stripped. The slug field is editable, and manually changing it disables further auto-generation from the name. A slug preview shows the resulting URL: `docodego.com/app/{slug}/`.

Slug validation follows the same rules as onboarding: minimum 3 characters, lowercase letters, numbers, and hyphens only, no leading or trailing hyphens. A debounced availability check calls `authClient.organization.checkSlug({ slug })` to confirm the slug is not already taken.

## Creating and Switching

On submit, the app calls `authClient.organization.create({ name, slug })`. The user becomes the owner of the new organization, and the session automatically switches to it — `activeOrganizationId` updates to the newly created org. The app navigates to `/app/{newSlug}/`, landing the user on the new org's dashboard.

The OrgSwitcher dropdown now includes the new organization in its list alongside all previously existing orgs. The user can switch back to any previous org at any time through the same switcher.
