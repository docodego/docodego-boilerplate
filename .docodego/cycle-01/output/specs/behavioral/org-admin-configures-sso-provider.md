---
id: SPEC-2026-038
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [Org Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# Org Admin Configures SSO Provider

## Intent

This spec defines the flow by which an organization admin configures a single sign-on (SSO) provider for their organization from the organization settings page. The admin navigates to the SSO section, selects either OIDC (OpenID Connect) or SAML as the protocol, fills in the protocol-specific fields, and saves the configuration. For OIDC, the admin provides an issuer URL, client ID, and client secret; the system auto-discovers endpoints via the `.well-known/openid-configuration` endpoint. For SAML, the admin provides the IdP entry point URL and signing certificate. After saving, the admin completes a domain verification step by adding a DNS TXT record to prove ownership of their email domain. Once domain verification succeeds, the SSO provider becomes active and organization members whose email addresses match the verified domain can use SSO to sign in. The admin can return to the SSO settings at any time to update the configuration, rotate credentials, or remove the provider entirely.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| oRPC mutation endpoint (`registerSSOProvider`) | write | Admin clicks "Save" after filling in protocol-specific fields — the client calls the endpoint with the configuration details and `organizationId` to create the provider record | The server returns HTTP 500 and the client displays a localized error message inside the configuration form, leaving no provider record created and allowing the admin to retry once the endpoint recovers |
| `ssoProvider` table (D1) | read/write | Server writes a new provider record with issuer, `organizationId`, and either `oidcConfig` or `samlConfig` depending on the selected protocol during the registration step | The database write fails with HTTP 500 and the server returns error to the client without persisting any provider record — the client alerts the admin with a localized error so the configuration is not partially committed |
| IdP `.well-known/openid-configuration` endpoint | read | Admin enters an OIDC issuer URL and the system fetches the discovery document to auto-resolve authorization, token, and userinfo endpoints before the form is submitted | The discovery fetch times out after 10 seconds and the form displays a localized warning that endpoint auto-discovery failed, allowing the admin to verify the issuer URL and retry the fetch |
| DNS resolver service | read | Admin clicks "Verify domain" after adding the TXT record — the server performs a DNS lookup to check for the presence and value of the verification record on the specified domain | The DNS lookup times out or returns an error and the server returns HTTP 502 — the client falls back to displaying a localized message instructing the admin to wait for DNS propagation and retry verification later |
| `@repo/i18n` | read | All form labels, field placeholders, button text, error messages, and verification instructions are rendered via i18n translation keys at component mount time | Translation function falls back to the default English locale strings so the SSO configuration form remains fully functional even when the i18n resource bundle is unavailable for non-English locales |
| oRPC mutation endpoint (`requestDomainVerification`) | write | Admin enters the email domain and clicks to request verification — the client calls the endpoint which generates a unique DNS TXT record value and returns it with placement instructions | The server returns HTTP 500 and the client displays a localized error message indicating the verification request failed — the admin retries once the endpoint recovers without losing previously saved provider configuration |
| oRPC mutation endpoint (`verifyDomain`) | write | Admin clicks "Verify domain" after placing the TXT record — the client calls the endpoint which performs the DNS lookup and links the domain to the provider if verification succeeds | The server returns HTTP 500 or HTTP 502 and the client falls back to a localized error message instructing the admin to retry domain verification — the provider record remains saved but inactive until verification completes |

## Behavioral Flow

1. **[Org Admin]** opens the organization settings page and selects the "Single Sign-On" or "SSO" section, which is only accessible to users with the org admin role for the current organization

2. **[Client]** renders the SSO settings page: if no SSO provider is configured yet, the page displays an empty state with a "Configure SSO" button; if a provider already exists, the current configuration is shown with options to update or remove it

3. **[Org Admin]** clicks "Configure SSO" to begin the setup process, which opens the configuration form with localized labels

4. **[Client]** renders the protocol selection step in the configuration form, presenting two options: OIDC (OpenID Connect) and SAML — this choice determines which fields appear next in the form

5. **[Org Admin]** selects the protocol that matches their identity provider's capabilities — OIDC for providers like Okta, Azure AD, or Google Workspace, and SAML for identity providers that only support SAML 2.0

6. **[Branch — OIDC selected]** The form presents three fields: the issuer URL (the base URL of the identity provider, for example `https://login.example.com`), the client ID, and the client secret obtained by registering DoCodeGo as an application in the identity provider's admin console

7. **[Client]** after the admin enters the issuer URL, the system fetches the provider's `.well-known/openid-configuration` endpoint to auto-discover the authorization, token, and userinfo endpoints — if discovery succeeds, the form confirms that the endpoints were resolved automatically

8. **[Branch — SAML selected]** The form presents two fields: the IdP's SSO entry point URL (the identity provider's single sign-on endpoint where SAML authentication requests are sent) and the IdP's signing certificate (the public X.509 certificate that the identity provider uses to sign SAML responses for verifying authenticity of assertions)

9. **[Org Admin]** fills in the protocol-specific fields and clicks "Save" to register the provider with the organization

10. **[Client]** calls `registerSSOProvider()` with the configuration details and the current `organizationId`, disabling the submit button and displaying a loading indicator while the request is in flight

11. **[Server]** creates a new entry in the `ssoProvider` table, storing the issuer, the `organizationId` that owns this provider, and either the `oidcConfig` or `samlConfig` depending on the selected protocol — at this point the provider is saved but not yet active

12. **[Client]** transitions to the domain verification step after receiving a success response, displaying a domain input field where the admin enters the email domain to associate with this SSO provider

13. **[Org Admin]** enters the email domain they want to associate with this SSO provider (for example, `example.com`) and submits the domain for verification

14. **[Client]** calls `requestDomainVerification()` with the domain value, which generates a unique DNS TXT record value on the server and returns it to the client

15. **[Client]** displays instructions directing the org admin to add a TXT record to their domain's DNS configuration with the provided verification value

16. **[Org Admin]** adds the TXT record to their domain's DNS configuration through their DNS provider's management console, then returns to the SSO settings page and clicks "Verify domain"

17. **[Client]** calls `verifyDomain()` to trigger the server-side DNS lookup that confirms the TXT record exists and matches the generated verification value

18. **[Server]** performs a DNS lookup to confirm the TXT record exists and its value matches the expected verification string — if verification succeeds, the domain is linked to the SSO provider and the provider becomes active

19. **[Client]** displays a success confirmation indicating the SSO provider is now active — organization members whose email addresses match the verified domain will see the SSO option on the sign-in page

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| sso_settings_empty | config_form_open | Admin clicks the "Configure SSO" button on the empty state page | Calling user's role in the `member` table equals `admin` or `owner` for the current organization |
| sso_settings_configured | config_form_open | Admin clicks the "Update" button on the existing provider configuration display | Calling user's role in the `member` table equals `admin` or `owner` for the current organization |
| config_form_open | protocol_selected_oidc | Admin selects "OIDC" from the protocol selection options in the form | Protocol selection value equals the string `oidc` |
| config_form_open | protocol_selected_saml | Admin selects "SAML" from the protocol selection options in the form | Protocol selection value equals the string `saml` |
| protocol_selected_oidc | oidc_fields_filled | Admin enters issuer URL, client ID, and client secret into the OIDC form fields | All three OIDC fields are non-empty and the issuer URL is a valid URL format |
| protocol_selected_saml | saml_fields_filled | Admin enters entry point URL and pastes or uploads the signing certificate | Both SAML fields are non-empty and the entry point URL is a valid URL format |
| oidc_fields_filled | provider_saving | Admin clicks the "Save" button after completing all OIDC configuration fields | All three OIDC fields are non-empty and validated |
| saml_fields_filled | provider_saving | Admin clicks the "Save" button after completing all SAML configuration fields | Both SAML fields are non-empty and validated |
| provider_saving | domain_verification_pending | Server returns HTTP 200 confirming provider record was created in the `ssoProvider` table | Provider record is persisted with either `oidcConfig` or `samlConfig` |
| provider_saving | provider_save_error | Server returns HTTP 500 or a non-200 error code during provider registration | Database write or validation fails on the server |
| provider_save_error | oidc_fields_filled | Admin dismisses the error and the form returns to the filled state for OIDC | Error message is visible and the form fields retain their values |
| provider_save_error | saml_fields_filled | Admin dismisses the error and the form returns to the filled state for SAML | Error message is visible and the form fields retain their values |
| domain_verification_pending | dns_instructions_shown | Admin enters email domain and client calls `requestDomainVerification()` successfully | Domain field is non-empty and server returns the DNS TXT record value |
| dns_instructions_shown | domain_verifying | Admin clicks "Verify domain" after adding the TXT record to their DNS configuration | Verify button is clicked and the client calls `verifyDomain()` |
| domain_verifying | sso_active | Server DNS lookup confirms TXT record exists and matches the expected value | DNS TXT record is present and its value matches the generated verification string |
| domain_verifying | domain_verification_failed | Server DNS lookup fails to find the TXT record or the value does not match | DNS TXT record is absent or its value does not match the expected verification string |
| domain_verification_failed | dns_instructions_shown | Admin reviews the DNS instructions again and retries after updating their DNS records | Error message is visible and the domain verification instructions are still displayed |
| sso_active | sso_settings_configured | Admin navigates back to the SSO settings overview page | Provider record exists in the `ssoProvider` table with a verified domain linked |

## Business Rules

- **Rule protocol-routing:** IF the admin selects OIDC THEN the form presents exactly 3 fields (issuer URL, client ID, client secret) AND the server stores the configuration in `oidcConfig`; IF the admin selects SAML THEN the form presents exactly 2 fields (entry point URL, signing certificate) AND the server stores the configuration in `samlConfig`
- **Rule oidc-discovery:** IF the admin enters an OIDC issuer URL THEN the client fetches the `.well-known/openid-configuration` endpoint within 10 seconds AND if the fetch succeeds the form displays a confirmation that endpoints were auto-discovered; IF the fetch fails or times out THEN the form displays a localized warning that auto-discovery failed
- **Rule domain-uniqueness:** IF the admin requests domain verification for a domain that is already verified and linked to another SSO provider in the `ssoProvider` table THEN the server rejects the request with HTTP 409 AND returns error to the client indicating the domain is already claimed by another organization
- **Rule provider-inactive-until-verified:** IF a provider record is created in the `ssoProvider` table but the associated domain is not yet verified THEN the provider remains inactive AND organization members cannot use it to sign in until domain verification succeeds
- **Rule role-gate:** IF the authenticated user's role in the organization is not `admin` or `owner` THEN all SSO configuration endpoints reject the request with HTTP 403 AND the server logs the unauthorized attempt with the user ID and timestamp before returning the error response
- **Rule dns-txt-verification:** IF the admin clicks "Verify domain" THEN the server performs a DNS lookup for the TXT record on the specified domain AND if the record value matches the generated verification string the domain is linked to the provider and the provider becomes active; IF the record is absent or does not match THEN the server returns an error and the provider remains inactive
- **Rule single-provider-per-org:** IF the organization already has a configured SSO provider THEN the admin can update or remove the existing provider but cannot create a second concurrent provider — the count of active SSO providers per organization at any point in time equals exactly 0 or 1

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View the SSO settings page, click "Configure SSO" to begin setup, select a protocol, fill in configuration fields, save the provider, enter a domain for verification, verify the domain, update an existing provider, and remove an existing provider | Creating a second concurrent SSO provider for the same organization — the form enforces a single-provider constraint per organization | The SSO section is visible in the organization settings navigation; all configuration controls and domain verification controls are visible and enabled |
| Admin | View the SSO settings page, click "Configure SSO" to begin setup, select a protocol, fill in configuration fields, save the provider, enter a domain for verification, verify the domain, update an existing provider, and remove an existing provider | Creating a second concurrent SSO provider for the same organization — the form enforces a single-provider constraint per organization | The SSO section is visible in the organization settings navigation; all configuration controls and domain verification controls are visible and enabled |
| Member | None — members cannot access the SSO configuration controls because the SSO section is not rendered in the organization settings navigation for non-admin roles | Viewing the SSO settings page, configuring a provider, verifying a domain, updating a provider, or removing a provider — all SSO configuration endpoints return HTTP 403 for members | The SSO section is absent from the organization settings navigation; the count of SSO configuration elements in the DOM equals 0 for users with the `member` role |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the organization settings page component renders any content | Accessing the SSO settings page or calling any SSO configuration endpoint without a valid session — the redirect occurs before any SSO UI is mounted | The organization settings page is not rendered; the redirect to `/signin` occurs before any SSO configuration UI is mounted or visible to the visitor |

## Constraints

- The SSO configuration form supports exactly 2 protocols: OIDC and SAML — the count of protocol options rendered in the form equals 2 and the server rejects any provider registration with a protocol value outside this set
- The OIDC configuration requires exactly 3 fields: issuer URL, client ID, and client secret — the count of empty OIDC fields at submission time equals 0 because the client validates all fields are non-empty before enabling the submit button
- The SAML configuration requires exactly 2 fields: entry point URL and signing certificate — the count of empty SAML fields at submission time equals 0 because the client validates both fields are non-empty before enabling the submit button
- The OIDC discovery fetch to `.well-known/openid-configuration` completes within 10 seconds or times out — the timeout threshold for the discovery HTTP request equals 10000 milliseconds
- The DNS TXT record verification value is a unique string generated per domain verification request — the count of duplicate verification values across all pending verifications in the system equals 0
- Each organization can have at most 1 SSO provider configured at any point in time — the count of `ssoProvider` records per `organizationId` equals 0 or 1
- All form labels, field placeholders, button text, error messages, and verification instructions are rendered via i18n translation keys — the count of hardcoded English string literals in the SSO configuration components equals 0
- The SSO settings section is only accessible to users with `admin` or `owner` role — the count of SSO configuration requests accepted from users with `member` role equals 0

## Acceptance Criteria

- [ ] The SSO section is present in the organization settings navigation for an `admin`-role user — the SSO navigation element count equals 1
- [ ] The SSO section is present in the organization settings navigation for an `owner`-role user — the SSO navigation element count equals 1
- [ ] The SSO section is absent from the organization settings navigation for a `member`-role user — the SSO navigation element count equals 0
- [ ] When no SSO provider is configured, the page displays an empty state with a "Configure SSO" button — the button element is present and the provider configuration display is absent
- [ ] Clicking "Configure SSO" opens the configuration form with a protocol selection step — the protocol option count in the form equals 2
- [ ] Selecting OIDC renders exactly 3 input fields: issuer URL, client ID, and client secret — the OIDC input field count equals 3
- [ ] Selecting SAML renders exactly 2 input fields: entry point URL and signing certificate — the SAML input field count equals 2
- [ ] Entering a valid OIDC issuer URL triggers a fetch to `.well-known/openid-configuration` within 10 seconds — the discovery fetch invocation count equals 1
- [ ] If OIDC discovery succeeds, the form displays a confirmation that endpoints were auto-discovered — the discovery success indicator is present
- [ ] If OIDC discovery fails or times out after 10000 milliseconds, the form displays a localized warning — the discovery warning element is present
- [ ] The "Save" button is disabled when any required field is empty — the disabled attribute is present on the submit button when field validation returns false
- [ ] Clicking "Save" calls `registerSSOProvider()` with the configuration and `organizationId` — the method invocation count equals 1 and the payload `organizationId` is non-empty
- [ ] A successful provider registration returns HTTP 200 and a new record exists in the `ssoProvider` table — the response status equals 200 and the provider row count for the organizationId equals 1
- [ ] After successful registration, the form transitions to the domain verification step — the domain input field is present and the protocol fields are absent
- [ ] Entering a domain and requesting verification calls `requestDomainVerification()` — the method invocation count equals 1 and the domain parameter is non-empty
- [ ] The verification response returns a unique DNS TXT record value — the TXT value field in the response is present and non-empty
- [ ] Clicking "Verify domain" calls `verifyDomain()` to trigger DNS lookup — the method invocation count equals 1
- [ ] If DNS verification succeeds, the provider status transitions to active — the provider `active` field in the database equals true
- [ ] If DNS verification fails, the form displays a localized error and the provider remains inactive — the error element is present and the provider `active` field equals false
- [ ] Requesting verification for a domain already linked to another provider returns HTTP 409 — the response status equals 409
- [ ] A direct SSO configuration endpoint call from a `member`-role user returns HTTP 403 — the response status equals 403 and no provider record is created
- [ ] All form text, labels, and messages are rendered via i18n translation keys — the count of hardcoded English string literals in the SSO configuration components equals 0
- [ ] When a provider is already configured, the settings page displays the current configuration with update and remove options — the update button and remove button are both present

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Admin enters an OIDC issuer URL that returns a valid JSON response but is missing the `authorization_endpoint` field required for endpoint discovery | The form displays a localized warning indicating that the discovery document is incomplete and the admin must verify the issuer URL or contact their identity provider | The discovery warning element is present in the form and the discovery success indicator is absent after the fetch completes |
| Admin pastes a SAML signing certificate that is not a valid X.509 PEM-encoded certificate string | The client validates the certificate format before submission and displays a localized validation error indicating the certificate format is invalid — the submit button remains disabled | The validation error element is present and the disabled attribute on the submit button is present while the invalid certificate value is in the field |
| Admin clicks "Verify domain" before the DNS TXT record has propagated to public DNS resolvers after adding it to their DNS configuration | The server DNS lookup fails to find the TXT record and returns an error — the form displays a localized message instructing the admin to wait for DNS propagation (up to 48 hours) and retry | The error element is present in the domain verification section and the provider `active` field in the database equals false after the failed lookup |
| Admin attempts to verify a domain that is already verified and linked to an SSO provider belonging to a different organization in the system | The server detects the domain conflict and returns HTTP 409 — the form displays a localized error indicating the domain is already claimed by another organization and cannot be reused | The response status equals 409 and the error element is present in the domain verification section with a domain conflict message |
| Admin removes an existing SSO provider and then immediately creates a new one with different protocol and configuration values for the same organization | The removal deletes the existing `ssoProvider` record and the new creation inserts a fresh record — the count of `ssoProvider` records for the organizationId equals 1 after both operations complete | The provider row count for the organizationId equals 1 and the new record's protocol configuration matches the newly submitted values |
| Admin opens the SSO configuration form but navigates away from the page before clicking "Save" without submitting the form data | The form closes with no network request sent — the provider record count for the organizationId remains unchanged and no partial configuration is persisted to the database | The network request count to `registerSSOProvider` equals 0 after the navigation event and the `ssoProvider` table row count remains the same |

## Failure Modes

- **OIDC discovery endpoint unreachable when the admin enters the issuer URL during configuration**
    - **What happens:** The client attempts to fetch the `.well-known/openid-configuration` endpoint from the identity provider but the request fails due to a network timeout, DNS resolution error, or the endpoint returning a non-200 HTTP status code, preventing auto-discovery of authorization, token, and userinfo endpoints.
    - **Source:** Network connectivity failure between the client browser and the external identity provider's discovery endpoint, or the identity provider's discovery endpoint is temporarily down or returns an error response during the configuration attempt.
    - **Consequence:** The admin cannot confirm that the OIDC issuer URL is valid and the form cannot auto-discover the provider's endpoints, leaving the admin uncertain whether the issuer URL they entered will work correctly when organization members attempt to sign in via SSO.
    - **Recovery:** The client applies a timeout of 10 seconds on the discovery fetch and falls back to displaying a localized warning message indicating that auto-discovery failed — the admin can still save the configuration manually and retry the discovery later, or verify the issuer URL with their identity provider's documentation.

- **Database write failure when the server attempts to create the SSO provider record in the ssoProvider table**
    - **What happens:** The server receives the `registerSSOProvider()` request and attempts to write the new provider record to the `ssoProvider` table in D1 but the database returns a connection error, timeout, or constraint violation that prevents the record from being persisted.
    - **Source:** Cloudflare D1 service degradation, exceeded rate limits, transient infrastructure failure in the database binding, or an unexpected constraint violation during the insert operation that blocks the write.
    - **Consequence:** The SSO provider configuration is not saved despite the admin completing all form fields, and the admin must re-enter the configuration and retry the submission — no partial or corrupted record exists in the database because the write failed entirely.
    - **Recovery:** The server returns HTTP 500 and the client falls back to displaying a localized error message inside the configuration form — the form retains the entered field values so the admin can retry submission without re-entering the data, and the server logs the database error with the organizationId for operational investigation.

- **DNS verification lookup fails or times out when the admin clicks Verify domain to confirm TXT record placement**
    - **What happens:** The server performs a DNS lookup to find the TXT record on the specified domain but the DNS resolver returns an error, times out, or returns no records because the TXT record has not yet propagated to the public DNS infrastructure after the admin added it.
    - **Source:** DNS propagation delay (which can take up to 48 hours), DNS resolver infrastructure failure, or a transient network error between the Cloudflare Worker and the DNS resolver service during the verification lookup.
    - **Consequence:** The domain verification fails and the SSO provider remains inactive — organization members cannot use SSO to sign in until the domain is successfully verified, even though the provider configuration itself is already saved and correct.
    - **Recovery:** The server returns HTTP 502 and the client falls back to displaying a localized error message instructing the admin to wait for DNS propagation and retry verification later — the provider record remains saved in the inactive state and the admin can retry the verification step without re-entering the provider configuration.

- **Non-admin user bypasses the client guard and calls SSO configuration endpoints directly via crafted HTTP requests**
    - **What happens:** A user with the `member` role crafts a direct HTTP request to the `registerSSOProvider`, `requestDomainVerification`, or `verifyDomain` endpoint using a valid session cookie, circumventing the client-side UI that hides the SSO section from non-admin users, and attempts to create or modify an SSO provider configuration.
    - **Source:** Adversarial or accidental action where a member sends a hand-crafted HTTP request to the mutation endpoint with a valid session token, bypassing the client-side visibility guard that conditionally renders the SSO configuration controls only for admin and owner role members.
    - **Consequence:** Without server-side enforcement any member could configure an SSO provider for the organization without admin or owner approval, potentially linking the organization to a malicious identity provider and redirecting member sign-in attempts to an attacker-controlled endpoint.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after verifying the calling user's role in the `member` table — the server logs the unauthorized attempt with the user ID, organization ID, and timestamp, and no provider record is written or modified in the `ssoProvider` table.

## Declared Omissions

- This specification does not address the SSO sign-in flow that organization members use after the provider is configured and active — that behavior is defined in `user-signs-in-with-sso.md` as a separate concern covering IdP redirect, callback validation, user provisioning, and session creation
- This specification does not address OIDC key rotation, SAML metadata refresh, or certificate renewal workflows — those are operational maintenance concerns that occur after initial configuration and are handled by the identity provider administrator
- This specification does not address rate limiting on the SSO configuration endpoints — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly across the API layer
- This specification does not address the detailed DNS TXT record format or DNS provider-specific instructions for adding records — those details vary by DNS provider and are displayed as generic instructions in the verification step
- This specification does not address bulk SSO provider configuration or migration tooling for organizations switching between identity providers — the current flow supports configuring one provider at a time with manual credential entry

## Related Specifications

- [user-signs-in-with-sso](user-signs-in-with-sso.md) — The counterpart flow defining how organization members authenticate via the configured SSO provider, including IdP redirect, callback validation, user provisioning, and session creation
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the SSO plugin that manages the `ssoProvider` table, provider registration, and domain verification endpoints
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `ssoProvider`, `member`, and `organization` tables read and written during provider configuration and domain verification steps
- [shared-contracts](../foundation/shared-contracts.md) — oRPC contract definitions for `registerSSOProvider`, `requestDomainVerification`, and `verifyDomain` mutations including Zod schemas for payload validation
- [user-updates-organization-settings](user-updates-organization-settings.md) — The parent organization settings page that contains the SSO section as one of its navigation items accessible to admin and owner role members
- [org-admin-invites-a-member](org-admin-invites-a-member.md) — Related admin flow for inviting members to the organization, which operates on the same permission model requiring admin or owner role for access
