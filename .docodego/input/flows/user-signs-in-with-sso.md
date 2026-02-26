# User Signs In with SSO

## Initiating SSO

An enterprise user navigates to `/signin` and sees an SSO option alongside the standard sign-in methods. They either enter their work email address or select their identity provider (IdP) from a list of configured providers. The client calls `authClient.signIn.sso()` with the provider information. The server looks up the matching provider in the `ssoProvider` table, which stores the `issuer`, `organizationId`, and either an `oidcConfig` or `samlConfig` depending on the protocol the provider uses.

## Redirecting to the Identity Provider

For OIDC-based providers, the server fetches the provider's `.well-known/openid-configuration` endpoint to construct the authorization URL, then redirects the user's browser to the external IdP. For SAML-based providers, the server constructs a SAML authentication request and redirects the user to the IdP's single sign-on URL. In both cases, the user leaves the DoCodeGo application and authenticates directly with their corporate identity provider using their enterprise credentials. The IdP may require additional multi-factor authentication depending on the organization's security policies.

## Handling the Callback

After successful authentication at the external IdP, the user is redirected back to DoCodeGo. For OIDC, the callback URL is `/api/auth/sso/callback/{providerId}` — the server exchanges the authorization code for tokens, validates the ID token's signature and claims, and extracts the user's email and profile information. For SAML, the callback URL is `/api/auth/saml2/callback/{providerId}` — the server validates the XML signature on the SAML response, checks assertion timestamps to prevent replay, and extracts the user's identity attributes.

## Account Resolution and Session Creation

The server finds an existing user by the email from the IdP response, or creates a new user record if one does not exist. If the SSO provider is linked to an organization via its `organizationId`, the user is automatically provisioned as a member of that organization. A session is created in the `session` table with the standard fields — signed token cookie, `userId`, `ipAddress`, `userAgent`, and `expiresAt` set to 7 days. The `docodego_authed` hint cookie is set, and the client redirects the user to `/app`.

## Provider Configuration

SSO provider configuration is managed by organization administrators through the organization settings interface. Admins can add, update, or remove SSO providers for their organization, specifying the IdP's issuer URL and choosing between OIDC and SAML protocols. This configuration determines which providers appear on the sign-in page for users associated with that organization.
