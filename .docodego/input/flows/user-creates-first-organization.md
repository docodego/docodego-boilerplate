# User Creates First Organization

## Landing on Onboarding

A new user who has just signed up and has no organizations is redirected from `/app` to `/app/onboarding`. This is the only time a user sees this page — returning users who already belong to at least one organization are routed directly to their active org's dashboard. Users who joined through an invitation and already have org membership also skip this step entirely.

## The Onboarding Form

The onboarding page presents a clean form with two fields: an organization name input and a URL slug input. As the user types in the name field, the slug field auto-generates a value via a `toSlug()` function that converts the name to lowercase, replaces spaces with hyphens, and strips special characters. A slug preview below the field shows the final URL the org will live at: `docodego.com/app/{slug}/`.

The slug field is editable. If the user manually changes the slug, the auto-generation stops — further edits to the name no longer overwrite the slug. This lets users customize their URL while still getting a reasonable default.

## Slug Validation

The slug must pass several validation rules: minimum 3 characters, only lowercase letters, numbers, and hyphens allowed, and no leading or trailing hyphens. These rules are checked client-side as the user types.

Beyond format validation, the slug must be unique. A debounced availability check fires after the user stops typing, calling `authClient.organization.checkSlug({ slug })` to verify that no other organization has claimed the slug. The UI shows a visual indicator for the check result — available or taken.

## Creating the Organization

When the user submits the form, the app calls `authClient.organization.create({ name, slug })`. The user becomes the owner of the new organization, and the session's `activeOrganizationId` is set to this org. Upon successful creation, the app redirects to `/app/{slug}/`, landing the user on their new org's dashboard for the first time.
