# Onboarding Flow

---

## First-Time User Experience

After a user signs in successfully — whether through email OTP, passkey, anonymous guest promotion, or SSO — the system needs to figure out where to send them. The routing logic at `/app` checks whether the user belongs to any organizations by calling `authClient.organization.list()`.

If the user already has organizations, the system redirects them straight to their active workspace. It reads `activeOrganizationId` from the session to determine which org they were last working in, then sends them to `/app/{activeOrgSlug}/`. If there is no active org set (e.g., the session is brand new), it picks the first organization in the list and sets it as active.

If the user has no organizations at all — which is always the case for a brand-new user who just signed up via email OTP or got promoted from an anonymous guest — the system redirects them to `/app/onboarding`.

---

## The Onboarding Page

The onboarding page is clean and focused. There is a brief welcome message, and then a simple form with two fields: organization name and URL slug.

The organization name field is a standard text input. As the user types a name — say "Acme Corporation" — the slug field below it auto-generates in real time. The `toSlug()` utility from `@repo/library` converts the name to a URL-friendly format: lowercased, spaces replaced with hyphens, special characters stripped. So "Acme Corporation" becomes `acme-corporation`.

The slug field is editable. If the user wants a different slug than what was auto-generated — maybe just `acme` instead of `acme-corporation` — they can click into the slug field and type whatever they want. Once the user manually edits the slug, the auto-generation stops so their customization is preserved. The slug field shows a preview of what the final URL will look like: `docodego.com/app/acme/`.

The slug has validation rules. It must be at least 3 characters, can only contain lowercase letters, numbers, and hyphens, and cannot start or end with a hyphen. These validations run client-side as the user types, showing inline feedback. The form also checks slug availability by calling `authClient.organization.checkSlug({ slug })` with a debounce — if the slug is already taken, the user sees a message saying so and needs to pick a different one.

---

## Creating the Organization

Once the user has a valid name and an available slug, they click the "Create organization" button. The client calls `authClient.organization.create({ name, slug })`.

The server creates a new record in the `organization` table with the provided name and slug. The user who created it is automatically added to the `member` table with the role of `owner` — the highest privilege level. As the owner, they have full control over the organization: managing members, configuring settings, setting up teams, and deleting the org if needed.

The server also updates the user's session, setting `activeOrganizationId` to the newly created organization's ID. This means all subsequent API calls that depend on org context will automatically use this organization.

On success, the client redirects to `/app/{orgSlug}/` — the organization's dashboard. The user lands in their new workspace, ready to start using the app. The sidebar shows the organization name, and the main content area displays the org dashboard with getting-started guidance.

---

## Edge Cases

If the organization creation fails — maybe a network error or the slug was taken between the availability check and the actual creation — the form shows an error message and the user can try again. The slug field re-validates, and if the slug collision was the issue, the user picks a new slug and resubmits.

If the user navigates away from the onboarding page without creating an org (e.g., they close the tab), the next time they sign in, the same check runs again. They have no orgs, so they get redirected back to `/app/onboarding`. They are not stuck — they can always complete onboarding whenever they return.

If a user was invited to an existing organization before they ever signed up, the flow is different. When they sign in for the first time (likely through an invitation link), they accept the invitation via `authClient.organization.acceptInvitation({ invitationId })`. This adds them to the organization as a member. Now when the system checks for orgs, it finds one, and the user skips onboarding entirely — they go straight to `/app/{orgSlug}/`.

Anonymous users who get promoted to full accounts also go through onboarding if they have no orgs. The promotion flow clears the anonymous flag and links their real email, but it does not create an organization. So after promotion, the org check finds nothing, and the user lands on the onboarding page to set up their workspace.

---

## Returning Users

For users who have already completed onboarding and have at least one organization, the `/app` route never shows the onboarding page. It always redirects to the active org's dashboard.

If a user belongs to multiple organizations, the system uses the `activeOrganizationId` stored in their session. The user can switch between organizations using the org switcher in the sidebar, which calls `authClient.organization.setActive({ organizationId })` to update the session and then navigates to `/app/{newOrgSlug}/`.
