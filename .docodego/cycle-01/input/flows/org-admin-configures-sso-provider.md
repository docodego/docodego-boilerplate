[← Back to Index](README.md)

# Org Admin Configures SSO Provider

## The org admin navigates to SSO settings

The org admin opens the organization settings page and selects the "Single Sign-On" or "SSO" section. This area is only accessible to users with the org admin role for the current organization. If no SSO provider is configured yet, the page displays an empty state with a "Configure SSO" button. If a provider already exists, the current configuration is shown with options to update or remove it. The org admin clicks "Configure SSO" to begin the setup process.

## The org admin chooses a protocol

The configuration form, with localized labels, first asks the org admin to select a protocol: OIDC (OpenID Connect) or SAML. This choice determines which fields appear next. OIDC is the more modern and commonly used protocol, suitable for most identity providers like Okta, Azure AD, or Google Workspace. SAML is offered for organizations whose identity providers only support SAML 2.0. The org admin selects the protocol that matches their identity provider's capabilities and proceeds.

## The org admin enters OIDC configuration

If the org admin selected OIDC, the form presents three fields: the issuer URL, the client ID, and the client secret. The issuer URL is the base URL of the identity provider — for example, `https://login.example.com`. Once the org admin enters the issuer URL, the system attempts to fetch the provider's `.well-known/openid-configuration` endpoint to auto-discover the authorization, token, and userinfo endpoints. If discovery succeeds, the form confirms that the endpoints were resolved automatically. The org admin enters the client ID and client secret, which they obtained by registering DoCodeGo as an application in their identity provider's admin console.

## The org admin enters SAML configuration

If the org admin selected SAML, the form presents two fields: the IdP's SSO entry point URL and the IdP's signing certificate. The entry point URL is the identity provider's single sign-on endpoint where SAML authentication requests are sent. The certificate is the public X.509 certificate that the identity provider uses to sign SAML responses — DoCodeGo uses this to verify the authenticity of assertions received during the [SSO sign-in flow](user-signs-in-with-sso.md). The org admin pastes or uploads the certificate and fills in the entry point URL.

## The org admin registers the provider

Once the protocol-specific fields are filled in, the org admin clicks "Save" to register the provider. The client calls `registerSSOProvider()` with the configuration details and the current `organizationId`. The server creates a new entry in the `ssoProvider` table, storing the issuer, the `organizationId` that owns this provider, and either the `oidcConfig` or `samlConfig` depending on the selected protocol. At this point the provider is saved but not yet active — domain verification is required before organization members can use it to sign in.

## The org admin verifies domain ownership

After the provider is saved, the form transitions to a domain verification step. The org admin enters the email domain they want to associate with this SSO provider — for example, `example.com`. The client calls `requestDomainVerification()`, which generates a unique DNS TXT record value. The form displays instructions: the org admin must add a TXT record to their domain's DNS configuration with the provided value. Once the DNS record is in place, the org admin clicks "Verify domain" and the client calls `verifyDomain()`. The server performs a DNS lookup to confirm the TXT record exists and matches. If verification succeeds, the domain is linked to the SSO provider and the provider becomes active.

## Organization members can now use SSO

With the provider configured and the domain verified, the SSO setup is complete. Organization members whose email addresses match the verified domain will now see the SSO option when they navigate to the [sign-in page](user-signs-in-with-sso.md). The org admin can return to the SSO settings at any time to update the provider configuration, rotate credentials, or remove the provider entirely.
