# Better Auth Plugin Research: Comprehensive Configuration, Schema & Compatibility Guide

> Research date: 2026-02-23
> Sources: better-auth.com/llms.txt, GitHub issues, DeepWiki, npm packages

---

## Table of Contents

1. [Core Schema (Base Tables)](#1-core-schema-base-tables)
2. [Server Configuration with Hono](#2-server-configuration-with-hono)
3. [Client Configuration for React/Web](#3-client-configuration-for-reactweb)
4. [React Native / Expo Configuration](#4-react-native--expo-configuration)
5. [Drizzle ORM Integration](#5-drizzle-orm-integration)
6. [Session Management](#6-session-management)
7. [Plugin 1: Passkey (WebAuthn/FIDO2)](#7-plugin-1-passkey-webauthfido2)
8. [Plugin 2: Anonymous (Guest Sessions)](#8-plugin-2-anonymous-guest-sessions)
9. [Plugin 3: Email OTP](#9-plugin-3-email-otp)
10. [Plugin 4: SSO (SAML/OIDC)](#10-plugin-4-sso-samloidc)
11. [Plugin 5: Organisation (with Teams)](#11-plugin-5-organisation-with-teams)
12. [Plugin 6: Admin](#12-plugin-6-admin)
13. [Plugin 7: DodoPayments](#13-plugin-7-dodopayments)
14. [Cross-Plugin Conflict Analysis](#14-cross-plugin-conflict-analysis)
15. [Combined Schema Summary](#15-combined-schema-summary)
16. [Combined Server Configuration Pattern](#16-combined-server-configuration-pattern)
17. [Combined Client Configuration Pattern](#17-combined-client-configuration-pattern)

---

## 1. Core Schema (Base Tables)

Better Auth requires four foundational tables:

### User Table

| Field           | Type    | Required | Notes                              |
|-----------------|---------|----------|------------------------------------|
| id              | string  | Yes      | Primary key (UUID by default)      |
| name            | string  | Yes      | Display name                       |
| email           | string  | Yes      | Unique, used for login             |
| emailVerified   | boolean | Yes      | Verification status                |
| image           | string  | No       | Profile image URL                  |
| createdAt       | Date    | Yes      | Account creation timestamp         |
| updatedAt       | Date    | Yes      | Last modification timestamp        |

### Session Table

| Field     | Type   | Required | Notes                              |
|-----------|--------|----------|------------------------------------|
| id        | string | Yes      | Primary key                        |
| userId    | string | Yes      | FK -> user.id                      |
| token     | string | Yes      | Unique session token (cookie val)  |
| expiresAt | Date   | Yes      | Session expiration                 |
| ipAddress | string | No       | Client IP                          |
| userAgent | string | No       | Browser/device info                |
| createdAt | Date   | Yes      | Creation timestamp                 |
| updatedAt | Date   | Yes      | Update timestamp                   |

### Account Table

| Field                  | Type   | Required | Notes                              |
|------------------------|--------|----------|------------------------------------|
| id                     | string | Yes      | Primary key                        |
| userId                 | string | Yes      | FK -> user.id                      |
| accountId              | string | Yes      | Provider-specific account ID       |
| providerId             | string | Yes      | Auth provider name                 |
| accessToken            | string | No       | OAuth access token                 |
| refreshToken           | string | No       | OAuth refresh token                |
| accessTokenExpiresAt   | Date   | No       | Token expiration                   |
| refreshTokenExpiresAt  | Date   | No       | Refresh expiration                 |
| scope                  | string | No       | Provider permissions               |
| idToken                | string | No       | OpenID token                       |
| password               | string | No       | Hashed password (credential auth)  |
| createdAt              | Date   | Yes      | Creation timestamp                 |
| updatedAt              | Date   | Yes      | Update timestamp                   |

### Verification Table

| Field      | Type   | Required | Notes                              |
|------------|--------|----------|------------------------------------|
| id         | string | Yes      | Primary key                        |
| identifier | string | Yes      | Email or phone being verified      |
| value      | string | Yes      | Verification code/token            |
| expiresAt  | Date   | Yes      | Request expiration                 |
| createdAt  | Date   | Yes      | Creation timestamp                 |
| updatedAt  | Date   | Yes      | Update timestamp                   |

### Relationships

- `session.userId` -> `user.id`
- `account.userId` -> `user.id`

---

## 2. Server Configuration with Hono

### Basic Route Mounting

```ts
import { Hono } from "hono";
import { cors } from "hono/cors";
import { auth } from "./auth"; // betterAuth instance

const app = new Hono();

// CORS MUST be registered BEFORE routes
app.use("/api/auth/*", cors({
    origin: "http://localhost:3001", // your frontend origin
    allowHeaders: ["Content-Type", "Authorization"],
    allowMethods: ["POST", "GET", "OPTIONS"],
    credentials: true,
}));

// Mount Better Auth handler
app.on(["POST", "GET"], "/api/auth/*", (c) => {
    return auth.handler(c.req.raw);
});
```

### Session Middleware for Protected Routes

```ts
app.use("*", async (c, next) => {
    const session = await auth.api.getSession({ headers: c.req.raw.headers });
    c.set("user", session?.user || null);
    c.set("session", session?.session || null);
    await next();
});
```

### Cookie Configuration for Cross-Domain

- **Cross-subdomain**: Enable `crossSubDomainCookies` to maintain `SameSite=Lax`
- **Cross-domain**: Set `SameSite=None` and `Secure=true` via `defaultCookieAttributes`

### Cloudflare Workers Deployment Notes

- Runtime environment variables are not available at build time
- Use programmatic migrations via `getMigrations()` exposed as a POST endpoint
- Use `import { env } from 'cloudflare:workers'` for Prisma/Drizzle support
- Add compatibility flag in `wrangler.toml` to populate `process.env`

---

## 3. Client Configuration for React/Web

```ts
import { createAuthClient } from "better-auth/client";
import { passkeyClient } from "@better-auth/passkey/client";
import { anonymousClient } from "better-auth/client/plugins";
import { emailOTPClient } from "better-auth/client/plugins";
import { ssoClient } from "@better-auth/sso/client";
import { organizationClient } from "better-auth/client/plugins";
import { adminClient } from "better-auth/client/plugins";

export const authClient = createAuthClient({
    baseURL: "http://localhost:8787", // Hono server URL
    plugins: [
        passkeyClient(),
        anonymousClient(),
        emailOTPClient(),
        ssoClient(),
        organizationClient(),
        adminClient(),
        // DodoPayments client (from @dodopayments/better-auth)
    ],
});
```

### Using Hono Client (RPC-style)

```ts
import { hc } from "hono/client";

const client = hc<AppType>("http://localhost:8787/", {
    init: { credentials: "include" },
});
```

---

## 4. React Native / Expo Configuration

### Installation

```
npm install better-auth @better-auth/expo expo-secure-store expo-network expo-linking expo-web-browser expo-constants
```

### Client Setup

```ts
import { createAuthClient } from "better-auth/react";
import { expoClient } from "@better-auth/expo/client";
import * as SecureStore from "expo-secure-store";

export const authClient = createAuthClient({
    baseURL: "http://localhost:8081", // your backend URL
    plugins: [
        expoClient({
            scheme: "myapp",
            storagePrefix: "myapp",
            storage: SecureStore,
        }),
        // other plugins...
    ],
});
```

### Deep Linking

Add scheme to `app.json`:
```json
{ "expo": { "scheme": "myapp" } }
```

Register trusted origins on server:
```ts
export const auth = betterAuth({
    trustedOrigins: [
        "myapp://",
        "myapp://*",
        ...(process.env.NODE_ENV === "development" ? ["exp://**"] : []),
    ],
});
```

### Session Management in Expo

```tsx
const { data: session } = authClient.useSession();
```

Sessions cache locally in SecureStore; disable via `disableCache: true`.

### Authenticated Requests

```tsx
const cookies = authClient.getCookie();
const response = await fetch("/api/endpoint", {
    headers: { Cookie: cookies },
    credentials: "omit",
});
```

### Metro / Babel Configuration

```js
// metro.config.js
const config = getDefaultConfig(__dirname);
config.resolver.unstable_enablePackageExports = true;
```

Alternative Babel aliases:
```js
// babel.config.js
plugins: [[
    "module-resolver",
    {
        alias: {
            "better-auth/react": "./node_modules/better-auth/dist/client/react/index.mjs",
            "@better-auth/expo/client": "./node_modules/@better-auth/expo/dist/client.mjs",
        },
    },
]];
```

### Passkey + Expo Note

Configure `cookiePrefix` to match `webAuthnChallengeCookie` prefix:
```ts
// Server
passkey({ advanced: { webAuthnChallengeCookie: "my-app-passkey" } })

// Client
expoClient({ cookiePrefix: ["better-auth", "my-app"] })
```

---

## 5. Drizzle ORM Integration

### Adapter Setup

```ts
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "./db"; // your Drizzle instance

export const auth = betterAuth({
    database: drizzleAdapter(db, {
        provider: "sqlite", // or "pg" or "mysql"
        // schema: authSchema, // pass generated schema with relations
    }),
    // ...plugins
});
```

### Supported Providers

- `"sqlite"` (Cloudflare D1 uses this)
- `"pg"` (PostgreSQL)
- `"mysql"`

### Schema Generation

```bash
# Generate Drizzle schema file (auth-schema.ts)
npx @better-auth/cli generate

# Then generate Drizzle migrations
npx drizzle-kit generate

# Apply migrations
npx drizzle-kit migrate
```

The CLI auto-generates `relations()` definitions needed for the joins feature.

### Performance: Joins (Experimental)

```ts
database: drizzleAdapter(db, {
    provider: "pg",
    schema: authSchema, // must include relations
}),
advanced: {
    database: {
        // 2x-3x performance improvement
    },
},
```

Enable joins in Drizzle adapter by passing schema with relations. The `getFullOrganization` endpoint benefits significantly from this.

### Table/Field Customization

```ts
// Rename tables
user: {
    modelName: "users",
    fields: {
        id: { columnName: "user_id" },
    },
}

// Plural table names shortcut
database: drizzleAdapter(db, {
    provider: "pg",
    usePlural: true, // user -> users, session -> sessions, etc.
})
```

### Migration Gotchas

1. CLI `migrate` command only works with Kysely adapters. Drizzle users MUST use `generate` then `drizzle-kit`.
2. PostgreSQL auto-detects non-default schemas via `search_path`.
3. Config must export `betterAuth()` as `auth` or default export. CLI searches: `auth.ts`, `lib/auth.ts`, `utils/auth.ts`.
4. Foreign key types must match referenced table ID types (CLI handles this automatically).
5. `defaultValue` in `additionalFields` is JS-only; DB columns remain nullable.
6. Drizzle requires `relations()` definitions for join support.

---

## 6. Session Management

### Cookie-Based Architecture

Sessions are stored in the database and a signed cookie is set on the client. The server validates the cookie on each request.

### Configuration

```ts
session: {
    expiresIn: 60 * 60 * 24 * 7,    // 7 days (default)
    updateAge: 60 * 60 * 24,         // refresh daily (default)
    disableSessionRefresh: false,     // set true to disable auto-refresh
    freshAge: 60 * 60 * 24,          // 1 day freshness window (default)
}
```

### Session Operations

| Operation                | Description                           |
|--------------------------|---------------------------------------|
| `getSession()`           | Retrieve current active session       |
| `useSession()`           | Reactive session hook (React)         |
| `listSessions()`         | All user's active sessions            |
| `revokeSession(token)`   | End specific session                  |
| `revokeOtherSessions()`  | End all sessions except current       |
| `revokeSessions()`       | Invalidate all sessions               |

### Cookie Cache (Performance)

Avoids database hit on every session check:

```ts
session: {
    cookieCache: {
        enabled: true,
        maxAge: 5 * 60, // 5 minutes
        strategy: "compact", // "compact" | "jwt" | "jwe"
    },
}
```

Strategies:
- **compact** (default): Base64url + HMAC-SHA256. Smallest, fastest.
- **jwt**: Standard JWT (HS256). Compatible with external systems.
- **jwe**: Full encryption (A256CBC-HS512 + HKDF). Maximum security.

**Caveat**: Revoked sessions persist on other devices until cache expires.

### Secondary Storage (Redis)

```ts
secondaryStorage: {
    get: async (key) => await redis.get(key),
    set: async (key, value, ttl) => await redis.set(key, value, "EX", ttl),
    delete: async (key) => await redis.del(key),
},
session: {
    storeSessionInDatabase: true, // also keep in DB for audit
}
```

### Stateless Mode

Omit database config for fully stateless sessions:
```ts
session: {
    cookieCache: {
        enabled: true,
        maxAge: 7 * 24 * 60 * 60,
        strategy: "jwe",
        refreshCache: true,
    },
}
```

Invalidate all stateless sessions by incrementing `version`:
```ts
session: { cookieCache: { version: "2" } }
```

---

## 7. Plugin 1: Passkey (WebAuthn/FIDO2)

### Installation

```bash
npm install @better-auth/passkey
```

**Note**: As of Better Auth 1.4, the passkey plugin moved to its own separate package (`@better-auth/passkey`) rather than being bundled in `better-auth/plugins`.

### Database Tables

**New table: `passkey`**

| Field        | Type    | Required | Notes                                       |
|--------------|---------|----------|---------------------------------------------|
| id           | string  | Yes      | Primary key                                 |
| name         | string  | No       | Human-readable passkey name                 |
| publicKey    | string  | Yes      | Public key of the passkey                   |
| userId       | string  | Yes      | FK -> user.id                               |
| credentialID | string  | Yes      | Unique credential identifier                |
| counter      | number  | Yes      | Authenticator counter                       |
| deviceType   | string  | Yes      | Device type used during registration        |
| backedUp     | boolean | Yes      | Whether passkey is backed up                |
| transports   | string  | No       | Transports used during registration         |
| createdAt    | Date    | No       | Creation timestamp                          |
| aaguid       | string  | No       | Authenticator Attestation GUID              |

### Server Configuration

```ts
import { betterAuth } from "better-auth";
import { passkey } from "@better-auth/passkey";

export const auth = betterAuth({
    plugins: [
        passkey({
            rpID: "example.com",        // Domain (not bare TLD)
            rpName: "My Application",    // Human-readable name
            origin: "http://localhost:3000", // No trailing slash
            // Optional:
            authenticatorSelection: {
                authenticatorAttachment: "platform", // or "cross-platform"
                residentKey: "preferred",            // "required" | "preferred" | "discouraged"
                userVerification: "preferred",       // "required" | "preferred" | "discouraged"
            },
            advanced: {
                webAuthnChallengeCookie: "better-auth-passkey", // cookie name
            },
        }),
    ],
});
```

### Client Configuration

```ts
import { createAuthClient } from "better-auth/client";
import { passkeyClient } from "@better-auth/passkey/client";

export const authClient = createAuthClient({
    plugins: [passkeyClient()],
});
```

### API Endpoints

| Method                                  | Description                            | Auth Required |
|-----------------------------------------|----------------------------------------|---------------|
| `authClient.passkey.addPasskey()`       | Register a new passkey                 | Yes           |
| `authClient.signIn.passkey()`           | Sign in with passkey                   | No            |
| `authClient.passkey.listUserPasskeys()` | List user's passkeys                   | Yes           |
| `authClient.passkey.deletePasskey()`    | Delete a passkey                       | Yes           |
| `authClient.passkey.updatePasskey()`    | Update passkey name                    | Yes           |

### Conditional UI (Autofill)

```html
<input autocomplete="username webauthn" />
```

Before calling sign-in, check:
```ts
const available = await PublicKeyCredential.isConditionalMediationAvailable();
if (available) {
    authClient.signIn.passkey({ autoFill: true });
}
```

### Middleware/Ordering

- No specific ordering constraints with other plugins
- Register and sign-in methods always return data objects (`throw: true` has no effect)
- Powered by SimpleWebAuthn library

### Known Issues

- Registration currently requires an authenticated session (cannot register passkey during signup flow without workaround)
- Client API does not allow passing WebAuthn extensions or reading extension results (GitHub issue #7151)

---

## 8. Plugin 2: Anonymous (Guest Sessions)

### Installation

Built-in: `import { anonymous } from "better-auth/plugins"`

### Database Schema Additions

**User table addition:**

| Field       | Type    | Required | Notes                        |
|-------------|---------|----------|------------------------------|
| isAnonymous | boolean | No       | Flags anonymous users        |

### Server Configuration

```ts
import { betterAuth } from "better-auth";
import { anonymous } from "better-auth/plugins";

export const auth = betterAuth({
    plugins: [
        anonymous({
            emailDomainName: "guest.example.com",  // default: temp-{id}.com
            // OR custom email generation (overrides emailDomainName):
            generateRandomEmail: async (id) => `guest-${id}@example.com`,
            generateName: async () => `Guest User ${Date.now()}`,
            onLinkAccount: async ({ anonymousUser, newUser }) => {
                // Called when anonymous account links to real account
                // Migrate user data here
            },
            disableDeleteAnonymousUser: false, // default: false
        }),
    ],
});
```

### Client Configuration

```ts
import { createAuthClient } from "better-auth/client";
import { anonymousClient } from "better-auth/client/plugins";

export const authClient = createAuthClient({
    plugins: [anonymousClient()],
});
```

### API Endpoints

| Method                                     | Description                                |
|--------------------------------------------|--------------------------------------------|
| `authClient.signIn.anonymous()`            | Create anonymous user session              |
| `authClient.deleteAnonymousUser({})`       | Delete anonymous user record               |

### Account Linking Behavior

1. Anonymous user signs in with email/password or social auth
2. `onLinkAccount` callback fires with `{ anonymousUser, newUser }`
3. Anonymous user record is auto-deleted (unless `disableDeleteAnonymousUser: true`)
4. All session data transfers to new account

### Known Issues

- GitHub issue #3658: Anonymous plugin's 'after' hook may incorrectly reject successful user creation requests (auto anonymous user sign-in failure)

---

## 9. Plugin 3: Email OTP

### Installation

Built-in: `import { emailOTP } from "better-auth/plugins"`

### Database Schema Additions

No dedicated new table. OTPs are stored in the existing `verification` table (the `value` field stores the OTP code).

### Server Configuration

```ts
import { betterAuth } from "better-auth";
import { emailOTP } from "better-auth/plugins";

export const auth = betterAuth({
    plugins: [
        emailOTP({
            // REQUIRED: implement email sending
            async sendVerificationOTP({ email, otp, type }) {
                // type: "sign-in" | "email-verification" | "forget-password"
                // Send OTP via your email service
                // RECOMMENDED: do NOT await email sending (timing attacks)
                // On serverless: use waitUntil() to ensure delivery
            },
            otpLength: 6,             // default: 6
            expiresIn: 300,           // default: 300 seconds (5 min)
            allowedAttempts: 3,       // default: 3 (then OTP invalidated)
            disableSignUp: false,     // default: false (auto-register new users)
            sendVerificationOnSignUp: false, // default: false
            overrideDefaultEmailVerification: false, // replace link-based verify
            // OTP storage options:
            storeOTP: "plain",        // "plain" | "encrypted" | "hashed"
            generateOTP: async () => { /* custom OTP generation */ },
        }),
    ],
});
```

### Client Configuration

```ts
import { createAuthClient } from "better-auth/client";
import { emailOTPClient } from "better-auth/client/plugins";

export const authClient = createAuthClient({
    plugins: [emailOTPClient()],
});
```

### API Endpoints

| Method                                              | Description                        |
|-----------------------------------------------------|------------------------------------|
| `authClient.emailOtp.sendVerificationOtp()`         | Send OTP to email                  |
| `authClient.emailOtp.checkVerificationOtp()`        | Validate OTP (optional check)      |
| `authClient.signIn.emailOtp({ email, otp })`       | Sign in with OTP                   |
| `authClient.emailOtp.verifyEmail({ email, otp })`  | Verify email address               |
| `authClient.emailOtp.requestPasswordReset()`        | Request password reset OTP         |
| `authClient.emailOtp.resetPassword()`               | Reset password with OTP            |

### Flows

**Sign-in flow:**
1. `sendVerificationOtp({ email, type: "sign-in" })`
2. User enters OTP
3. `signIn.emailOtp({ email, otp })` -- auto-registers if user does not exist

**Email verification flow:**
1. `sendVerificationOtp({ email, type: "email-verification" })`
2. `verifyEmail({ email, otp })`

**Password reset flow:**
1. `requestPasswordReset({ email })`
2. Optionally `checkVerificationOtp()` to validate
3. `resetPassword({ email, otp, password })`

### Deprecation Notice

`/forget-password/email-otp` endpoint is deprecated. Use `/email-otp/request-password-reset` instead.

---

## 10. Plugin 4: SSO (SAML/OIDC)

### Installation

```bash
npm install @better-auth/sso
```

### Database Tables

**New table: `ssoProvider`**

| Field          | Type   | Required | Notes                                    |
|----------------|--------|----------|------------------------------------------|
| id             | string | Yes      | Primary key                              |
| providerId     | string | Yes      | Unique provider identifier               |
| issuer         | string | Yes      | Issuer URL                               |
| domain         | string | Yes      | Provider domain                          |
| userId         | string | Yes      | FK -> user.id (who registered provider)  |
| oidcConfig     | string | No       | OIDC settings (JSON)                     |
| samlConfig     | string | No       | SAML settings (JSON)                     |
| organizationId | string | No       | FK -> organization.id (links to org)     |
| domainVerified | boolean| No       | Only when domain verification enabled    |

### Server Configuration

```ts
import { betterAuth } from "better-auth";
import { sso } from "@better-auth/sso";

export const auth = betterAuth({
    plugins: [
        sso({
            // Optional:
            provisionUser: async ({ user, userInfo, token, provider }) => {
                // Runs after successful SSO auth
            },
            organizationProvisioning: {
                disabled: false,
                defaultRole: "member", // or "admin"
                getRole: async ({ user, userInfo, provider }) => "member",
            },
            defaultOverrideUserInfo: false,
            disableImplicitSignUp: false,
            providersLimit: 10,        // max providers per user
            domainVerification: {
                enabled: false,
                tokenPrefix: "better-auth-verify",
            },
            // SAML security settings:
            saml: {
                enableInResponseToValidation: false,
                allowIdpInitiated: true,
                requestTTL: 300,       // 5 minutes
                clockSkew: 300,        // 5 minutes
                requireTimestamps: false,
                algorithms: {
                    onDeprecated: "warn", // "warn" | "reject" | "allow"
                },
                maxResponseSize: 262144,  // 256KB
                maxMetadataSize: 102400,  // 100KB
            },
        }),
    ],
});
```

### Client Configuration

```ts
import { createAuthClient } from "better-auth/client";
import { ssoClient } from "@better-auth/sso/client";

export const authClient = createAuthClient({
    plugins: [ssoClient()],
});
```

### OIDC Configuration (per provider)

```ts
oidcConfig: {
    clientId: "...",
    clientSecret: "...",
    // Auto-discovered from {issuer}/.well-known/openid-configuration:
    authorizationEndpoint: "...",
    tokenEndpoint: "...",
    jwksEndpoint: "...",
    userInfoEndpoint: "...",
    scopes: ["openid", "email", "profile"],
    pkce: true,
    mapping: {
        id: "sub",
        email: "email",
        emailVerified: "email_verified",
        name: "name",
        image: "picture",
        extraFields: { /* custom mappings */ },
    },
}
```

### SAML Configuration (per provider)

```ts
samlConfig: {
    entryPoint: "https://idp.example.com/sso",
    cert: "MIIDpD...",
    callbackUrl: "https://app.example.com/api/auth/sso/saml2/callback/{providerId}",
    audience: "my-app",
    wantAssertionsSigned: true,
    signatureAlgorithm: "sha256",
    mapping: {
        id: "nameID",
        email: "email",
        name: "displayName",
    },
}
```

### SAML Endpoints

- **SP Metadata**: `/api/auth/sso/saml2/sp/metadata?providerId={id}`
- **Callback (GET & POST)**: `/api/auth/sso/saml2/callback/{providerId}`
- **Redirect URL pattern**: `{baseURL}/api/auth/sso/callback/{providerId}`

### API Endpoints

| Method                                    | Description                        | Auth Required |
|-------------------------------------------|------------------------------------|---------------|
| `registerSSOProvider()`                   | Register OIDC or SAML provider     | Yes           |
| `authClient.signIn.sso()`                | Sign in via SSO                    | No            |
| `verifyDomain()`                          | Validate DNS TXT record            | Yes           |
| `requestDomainVerification()`             | Issue new verification token       | Yes           |

### OIDC Discovery Errors

| Error Code                  | Cause                                     |
|-----------------------------|-------------------------------------------|
| issuer_mismatch             | IdP reports different issuer              |
| discovery_incomplete        | Missing required endpoints                |
| discovery_not_found         | 404 on discovery document                 |
| discovery_timeout           | No response (10s default)                 |
| discovery_invalid_url       | Malformed discovery URL                   |
| discovery_untrusted_origin  | URL not in trustedOrigins                 |
| discovery_invalid_json      | Invalid response format                   |
| unsupported_token_auth_method | IdP uses unsupported auth              |

### Known Issues (from GitHub)

1. **Users signing in via non-SSO methods are NOT auto-added to the organization** (issue #4972)
2. **Multi-domain SAML**: Single IdP serving multiple email domains fails because `findOne` uses `providerId` only (issue #7324)
3. **`disableImplicitSignUp` ignored for SAML** -- SAML callback does not check this flag (issue #5958)
4. **Static provider registration requires logged-in session** -- blocks clean deployments/automation (issue #4346)
5. **Cloudflare Workers regression in v1.4.6** -- Node API usage breaks edge runtime (issue #6635)
6. **SAML support is "in active development"** -- may not be suitable for production use
7. **SCIM provisioning not yet supported** (issue #3276)

---

## 11. Plugin 5: Organisation (with Teams)

### Installation

Built-in: `import { organization } from "better-auth/plugins"`

### Database Tables

**New table: `organization`**

| Field     | Type   | Required | Notes                    |
|-----------|--------|----------|--------------------------|
| id        | string | Yes      | Primary key              |
| name      | string | Yes      | Org display name         |
| slug      | string | Yes      | URL-friendly identifier  |
| logo      | string | No       | Logo URL                 |
| metadata  | string | No       | JSON metadata            |
| createdAt | Date   | Yes      | Creation timestamp       |

**New table: `member`**

| Field          | Type   | Required | Notes                    |
|----------------|--------|----------|--------------------------|
| id             | string | Yes      | Primary key              |
| userId         | string | Yes      | FK -> user.id            |
| organizationId | string | Yes      | FK -> organization.id    |
| role           | string | Yes      | Role assignment          |
| createdAt      | Date   | Yes      | Creation timestamp       |

**New table: `invitation`**

| Field          | Type   | Required | Notes                    |
|----------------|--------|----------|--------------------------|
| id             | string | Yes      | Primary key              |
| email          | string | Yes      | Invitee email            |
| inviterId      | string | Yes      | FK -> user.id            |
| organizationId | string | Yes      | FK -> organization.id    |
| role           | string | Yes      | Assigned role            |
| status         | string | Yes      | pending/accepted/rejected|
| teamId         | string | No       | FK -> team.id (if teams) |
| createdAt      | Date   | Yes      | Creation timestamp       |
| expiresAt      | Date   | Yes      | Invitation expiry        |

**Session table additions:**

| Field                  | Type   | Required | Notes                    |
|------------------------|--------|----------|--------------------------|
| activeOrganizationId   | string | No       | Currently active org     |
| activeTeamId           | string | No       | Currently active team    |

**New table (dynamic access control): `organizationRole`** (when `dynamicAccessControl.enabled: true`)

| Field          | Type   | Required | Notes                    |
|----------------|--------|----------|--------------------------|
| id             | string | Yes      | Primary key              |
| organizationId | string | Yes      | FK -> organization.id    |
| role           | string | Yes      | Role name                |
| permission     | string | Yes      | Permission set (JSON)    |
| createdAt      | Date   | Yes      | Creation timestamp       |
| updatedAt      | Date   | Yes      | Update timestamp         |

**New table (teams enabled): `team`**

| Field          | Type   | Required | Notes                    |
|----------------|--------|----------|--------------------------|
| id             | string | Yes      | Primary key              |
| name           | string | Yes      | Team name                |
| organizationId | string | Yes      | FK -> organization.id    |
| createdAt      | Date   | Yes      | Creation timestamp       |
| updatedAt      | Date   | No       | Update timestamp         |

**New table (teams enabled): `teamMember`**

| Field     | Type   | Required | Notes                    |
|-----------|--------|----------|--------------------------|
| id        | string | Yes      | Primary key              |
| teamId    | string | Yes      | FK -> team.id            |
| userId    | string | Yes      | FK -> user.id            |
| createdAt | Date   | Yes      | Creation timestamp       |

### Server Configuration

```ts
import { betterAuth } from "better-auth";
import { organization } from "better-auth/plugins";

export const auth = betterAuth({
    plugins: [
        organization({
            // Required: implement invitation email
            sendInvitationEmail: async (data) => {
                const inviteLink = `https://example.com/accept-invitation/${data.id}`;
                // Send email
            },
            allowUserToCreateOrganization: true,          // or async fn
            organizationLimit: undefined,                  // max orgs per user
            creatorRole: "owner",                          // "owner" | "admin"
            membershipLimit: 100,                          // max members per org
            invitationExpiresIn: 172800,                   // 48 hours (seconds)
            cancelPendingInvitationsOnReInvite: false,
            invitationLimit: 100,                          // max pending per user
            requireEmailVerificationOnInvitation: false,
            disableOrganizationDeletion: false,
            // Dynamic access control:
            dynamicAccessControl: {
                enabled: false,
                maximumRolesPerOrganization: undefined,    // unlimited
            },
            // Teams:
            teams: {
                enabled: true,                             // MUST SET TRUE
                maximumTeams: undefined,                   // unlimited
                maximumMembersPerTeam: undefined,          // unlimited
                allowRemovingAllTeams: true,
            },
        }),
    ],
});
```

### Client Configuration

```ts
import { createAuthClient } from "better-auth/client";
import { organizationClient } from "better-auth/client/plugins";

export const authClient = createAuthClient({
    plugins: [organizationClient()],
});
```

### Default Roles & Permissions

| Role   | Capabilities                                                     |
|--------|------------------------------------------------------------------|
| owner  | Full control; delete org, change ownership                       |
| admin  | Full control except org deletion and owner changes               |
| member | Read-only; cannot create, update, or delete resources            |

Default permission resources & actions:
- `organization`: update, delete
- `member`: create, update, delete
- `invitation`: create, cancel

### Custom Permissions

```ts
import { createAccessControl } from "better-auth/plugins/access";

const statement = {
    project: ["create", "share", "update", "delete"],
} as const;

const ac = createAccessControl(statement);
const customRole = ac.newRole({
    project: ["create", "update"],
    organization: ["update"],
});
```

### API Endpoints (Selected Key Endpoints)

**Organization CRUD**: create, list, update, delete, checkSlug, getFullOrganization, setActive
**Member Management**: listMembers, addMember, removeMember, updateMemberRole, getActiveMember
**Invitations**: inviteMember, acceptInvitation, rejectInvitation, cancelInvitation, listInvitations
**Teams**: createTeam, listTeams, updateTeam, removeTeam, setActiveTeam, listTeamMembers, addTeamMember, removeTeamMember
**Access Control**: hasPermission, createRole, deleteRole, listRoles, updateRole

### Hooks

Full lifecycle hooks for: organizations, members, invitations, and teams (`before*` / `after*` for create, update, delete, add, remove operations). Throwing errors in `before` hooks prevents the operation.

### Known Issues

- GitHub issue #3693: `listTeamMembers` does not work for organization Owner/Admins in some configurations

---

## 12. Plugin 6: Admin

### Installation

Built-in: `import { admin } from "better-auth/plugins"`

### Database Schema Additions

**User table additions:**

| Field      | Type    | Required | Notes                           |
|------------|---------|----------|---------------------------------|
| role       | string  | No       | Default: "user"                 |
| banned     | boolean | No       | Ban status indicator            |
| banReason  | string  | No       | Reason for the ban              |
| banExpires | Date    | No       | Temporary ban expiration        |

**Session table additions:**

| Field           | Type   | Required | Notes                          |
|-----------------|--------|----------|--------------------------------|
| impersonatedBy  | string | No       | Admin ID performing impersonation |

### Server Configuration

```ts
import { betterAuth } from "better-auth";
import { admin } from "better-auth/plugins";

export const auth = betterAuth({
    plugins: [
        admin({
            defaultRole: "user",
            adminRoles: ["admin"],                        // roles with admin access
            adminUserIds: [],                             // user IDs that are always admin
            impersonationSessionDuration: 3600,           // 1 hour (seconds)
            defaultBanReason: "No reason",
            defaultBanExpiresIn: undefined,               // permanent by default
            bannedUserMessage: "You have been banned...",
            allowImpersonatingAdmins: false,              // safety guard
        }),
    ],
});
```

### Client Configuration

```ts
import { createAuthClient } from "better-auth/client";
import { adminClient } from "better-auth/client/plugins";

export const authClient = createAuthClient({
    plugins: [adminClient()],
});
```

### API Endpoints

**User Management:**

| Method                   | Description                                    |
|--------------------------|------------------------------------------------|
| `admin.createUser()`    | Create new user with optional role             |
| `admin.listUsers()`     | List users (search, filter, sort, pagination)  |
| `admin.getUser()`       | Fetch single user by ID                        |
| `admin.updateUser()`    | Modify user details                            |
| `admin.removeUser()`    | Permanently delete user                        |
| `admin.setUserPassword()`| Change user's password                        |
| `admin.setRole()`       | Assign role(s)                                 |

**User Restrictions:**

| Method                   | Description                                    |
|--------------------------|------------------------------------------------|
| `admin.banUser()`       | Block signin (optional expiry + reason)        |
| `admin.unbanUser()`     | Restore access                                 |

**Session Control:**

| Method                        | Description                               |
|-------------------------------|-------------------------------------------|
| `admin.listUserSessions()`    | Get all sessions for a user               |
| `admin.revokeUserSession()`   | Terminate single session                  |
| `admin.revokeUserSessions()`  | Terminate all user sessions               |

**Impersonation:**

| Method                        | Description                               |
|-------------------------------|-------------------------------------------|
| `admin.impersonateUser()`     | Create session as another user            |
| `admin.stopImpersonating()`   | Return to admin account                   |

### Permission System

Default resources and actions:
- `user`: create, list, set-role, ban, impersonate, delete, set-password
- `session`: list, revoke, delete

Supports custom access control via `createAccessControl()` (same system as organization plugin).

### Features

- Multiple roles per user (stored comma-separated)
- Temporary and permanent bans with reason tracking
- Impersonation capped at 1 hour (configurable)
- Search operators: contains, starts_with, ends_with
- Filter operators: eq, ne, lt, lte, gt, gte
- Pagination with metadata (total, limit, offset)

---

## 13. Plugin 7: DodoPayments

### Installation

```bash
npm install @dodopayments/better-auth dodopayments
```

### Database Schema

The DodoPayments plugin does NOT define explicit database tables within Better Auth. It is integration-agnostic -- customer and payment data live in the Dodo Payments platform. The plugin maps Better Auth users to Dodo Payments customers via API.

### Environment Variables

```env
DODO_PAYMENTS_API_KEY=your_api_key
DODO_PAYMENTS_WEBHOOK_SECRET=your_webhook_secret
BETTER_AUTH_URL=http://localhost:3000
```

### Server Configuration

```ts
import { betterAuth } from "better-auth";
import { dodopayments } from "@dodopayments/better-auth";
import { DodoPayments } from "dodopayments";
import { checkout, portal, usage, webhooks } from "@dodopayments/better-auth";

const dodoClient = new DodoPayments({
    bearerToken: process.env.DODO_PAYMENTS_API_KEY,
    environment: "test_mode", // or "live_mode"
});

export const auth = betterAuth({
    plugins: [
        dodopayments({
            client: dodoClient,
            createCustomerOnSignUp: true, // auto-create Dodo customer
            use: [
                checkout({
                    products: {
                        pro: "prd_xxx", // slug -> product ID mapping
                    },
                    successUrl: "/dashboard",
                }),
                portal(),
                usage(),
                webhooks({
                    webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_SECRET!,
                    onPayload: async (payload) => {
                        // Handle webhook events
                    },
                }),
            ],
        }),
    ],
});
```

### Client Configuration

```ts
// Client plugin from @dodopayments/better-auth
import { dodopayments } from "@dodopayments/better-auth/client";

export const authClient = createAuthClient({
    plugins: [dodopayments()],
});
```

### API Endpoints / Client Methods

**Checkout:**
- `authClient.dodopayments.checkoutSession()` -- primary checkout method
- `authClient.dodopayments.checkout()` -- DEPRECATED legacy method

**Customer Portal:**
- `customer.portal()` -- redirect to self-service billing portal
- `customer.subscriptions.list()` -- query active subscriptions (paginated)
- `customer.payments.list()` -- retrieve payment history with status filtering

**Usage Tracking:**
- `usage.ingest()` -- record consumption events with metadata
- `usage.meters.list()` -- retrieve historical usage data

### Webhook Endpoint

Default: `/api/auth/dodopayments/webhooks`

Configure in Dodo Payments Dashboard by setting the webhook URL to your server's webhook endpoint and copying the generated secret into `DODO_PAYMENTS_WEBHOOK_SECRET`.

### Constraints

- Usage timestamps older than 1 hour or more than 5 minutes in the future are rejected
- Metered usage limited to verified email customers only
- Product IDs must be configured in the Dodo Payments dashboard first
- Omitting `meter_id` returns all customer subscription-linked meters

---

## 14. Cross-Plugin Conflict Analysis

### Confirmed Conflicts

1. **Endpoint Path Conflicts**: Better Auth 1.4+ detects when multiple plugins register the same endpoint path with the same HTTP method. The error message reads: `"Endpoint path conflicts detected! Multiple plugins are trying to use the same endpoint paths with conflicting HTTP methods"`. This was specifically documented between `mcp` + `oidc` plugins (issue #6270), but the detection system applies globally.

2. **SSO + Organization Provisioning Gap**: Users who sign in via non-SSO methods (email/password, social, etc.) are NOT automatically added to the organization linked to the SSO provider's domain (issue #4972). This means the automatic org-provisioning only works through the SSO sign-in flow itself.

### Potential Conflict Areas in Our Plugin Set

| Plugin Pair                  | Risk Level | Notes                                                                |
|------------------------------|------------|----------------------------------------------------------------------|
| SSO + Organization           | MEDIUM     | SSO org provisioning only works for SSO sign-ins, not other methods. Must ensure `organizationProvisioning` is configured correctly. SAML multi-domain support is broken for single-IdP multi-domain setups. |
| Admin + Organization         | LOW        | Both add fields to user/session tables. Admin's `role` field on user table is separate from Organization's `member.role`. No endpoint conflicts documented. Admin can manage org users via user management. |
| Anonymous + Email OTP        | LOW        | Anonymous creates temp users; Email OTP can be used as the "promotion" method. The `onLinkAccount` callback handles the transition. |
| Anonymous + Admin            | LOW        | Anonymous users will have `isAnonymous: true` and will appear in admin user lists. Admin can filter/manage these. |
| Passkey + Anonymous          | LOW        | Passkey requires authenticated session for registration, so a passkey cannot be directly added to an anonymous session without first linking to a real account. |
| SSO + Admin                  | LOW        | SSO admin users provisioned via SSO need their admin role set via `provisionUser` callback or `organizationProvisioning.getRole`. The admin plugin's `adminUserIds` can be used as a fallback. |
| DodoPayments + Anonymous     | MEDIUM     | Anonymous users should NOT trigger `createCustomerOnSignUp` because they don't have real emails. Guard against this in the sign-up flow or use conditional customer creation. |
| DodoPayments + Organization  | LOW        | No documented conflicts. Billing is per-user, not per-org, unless you build custom org-level billing logic. |
| Email OTP + SSO              | LOW        | No endpoint conflicts. Both are alternative sign-in methods. |
| Passkey + Email OTP          | LOW        | No conflicts. Both are passwordless methods that can coexist. |

### Session Table Field Accumulation

Multiple plugins add fields to the session table:

| Plugin       | Session Fields Added                           |
|--------------|------------------------------------------------|
| Organization | `activeOrganizationId`, `activeTeamId`         |
| Admin        | `impersonatedBy`                               |

These do not conflict as they use different field names.

### User Table Field Accumulation

| Plugin    | User Fields Added                                  |
|-----------|----------------------------------------------------|
| Admin     | `role`, `banned`, `banReason`, `banExpires`        |
| Anonymous | `isAnonymous`                                      |

These do not conflict as they use different field names.

---

## 15. Combined Schema Summary

### All Tables (Core + All 7 Plugins)

| Table              | Source         | Notes                                      |
|--------------------|----------------|--------------------------------------------|
| user               | Core           | Extended by Admin + Anonymous               |
| session            | Core           | Extended by Organization + Admin            |
| account            | Core           | No plugin extensions                        |
| verification       | Core           | Used by Email OTP for OTP storage           |
| passkey            | Passkey plugin | New table                                   |
| ssoProvider        | SSO plugin     | New table                                   |
| organization       | Org plugin     | New table                                   |
| member             | Org plugin     | New table (org membership)                  |
| invitation         | Org plugin     | New table                                   |
| team               | Org plugin     | New table (when teams enabled)              |
| teamMember         | Org plugin     | New table (when teams enabled)              |
| organizationRole   | Org plugin     | New table (when dynamic access control on)  |

**Total new tables**: 7 (or 9 with teams + dynamic roles)
**Total tables**: 11 (or 13 with teams + dynamic roles)

### All User Table Fields (Combined)

| Field         | Source    | Type    |
|---------------|-----------|---------|
| id            | Core      | string  |
| name          | Core      | string  |
| email         | Core      | string  |
| emailVerified | Core      | boolean |
| image         | Core      | string  |
| createdAt     | Core      | Date    |
| updatedAt     | Core      | Date    |
| role          | Admin     | string  |
| banned        | Admin     | boolean |
| banReason     | Admin     | string  |
| banExpires    | Admin     | Date    |
| isAnonymous   | Anonymous | boolean |

### All Session Table Fields (Combined)

| Field                  | Source       | Type   |
|------------------------|--------------|--------|
| id                     | Core         | string |
| userId                 | Core         | string |
| token                  | Core         | string |
| expiresAt              | Core         | Date   |
| ipAddress              | Core         | string |
| userAgent              | Core         | string |
| createdAt              | Core         | Date   |
| updatedAt              | Core         | Date   |
| activeOrganizationId   | Organization | string |
| activeTeamId           | Organization | string |
| impersonatedBy         | Admin        | string |

---

## 16. Combined Server Configuration Pattern

```ts
import { betterAuth } from "better-auth";
import { passkey } from "@better-auth/passkey";
import { sso } from "@better-auth/sso";
import { anonymous, emailOTP, organization, admin } from "better-auth/plugins";
import { dodopayments, checkout, portal, usage, webhooks } from "@dodopayments/better-auth";
import { DodoPayments } from "dodopayments";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { db } from "./db";

const dodoClient = new DodoPayments({
    bearerToken: process.env.DODO_PAYMENTS_API_KEY!,
    environment: process.env.NODE_ENV === "production" ? "live_mode" : "test_mode",
});

export const auth = betterAuth({
    database: drizzleAdapter(db, {
        provider: "sqlite", // or "pg" for PostgreSQL
    }),

    session: {
        expiresIn: 60 * 60 * 24 * 7,    // 7 days
        updateAge: 60 * 60 * 24,         // refresh daily
        cookieCache: {
            enabled: true,
            maxAge: 5 * 60,              // 5 min cache
        },
    },

    trustedOrigins: [
        "http://localhost:3001",
        "myapp://",
        "myapp://*",
    ],

    plugins: [
        // 1. Passkey
        passkey({
            rpID: "example.com",
            rpName: "My App",
            origin: "http://localhost:3000",
        }),

        // 2. Anonymous
        anonymous({
            onLinkAccount: async ({ anonymousUser, newUser }) => {
                // Migrate anonymous user data
            },
        }),

        // 3. Email OTP
        emailOTP({
            async sendVerificationOTP({ email, otp, type }) {
                // Send via email service
            },
        }),

        // 4. SSO
        sso({
            organizationProvisioning: {
                disabled: false,
                defaultRole: "member",
            },
        }),

        // 5. Organisation with Teams
        organization({
            sendInvitationEmail: async (data) => {
                // Send invitation email
            },
            teams: {
                enabled: true,
            },
        }),

        // 6. Admin
        admin({
            defaultRole: "user",
            adminRoles: ["admin"],
        }),

        // 7. DodoPayments
        dodopayments({
            client: dodoClient,
            createCustomerOnSignUp: true,
            use: [
                checkout({
                    products: { pro: "prd_xxx" },
                    successUrl: "/dashboard",
                }),
                portal(),
                usage(),
                webhooks({
                    webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_SECRET!,
                    onPayload: async (payload) => {
                        // Handle payment events
                    },
                }),
            ],
        }),
    ],
});
```

---

## 17. Combined Client Configuration Pattern

### Web (React)

```ts
import { createAuthClient } from "better-auth/client";
import { passkeyClient } from "@better-auth/passkey/client";
import { ssoClient } from "@better-auth/sso/client";
import {
    anonymousClient,
    emailOTPClient,
    organizationClient,
    adminClient,
} from "better-auth/client/plugins";
// import { dodopayments } from "@dodopayments/better-auth/client";

export const authClient = createAuthClient({
    baseURL: "http://localhost:8787",
    plugins: [
        passkeyClient(),
        anonymousClient(),
        emailOTPClient(),
        ssoClient(),
        organizationClient(),
        adminClient(),
        // dodopayments(),
    ],
});
```

### Mobile (React Native / Expo)

```ts
import { createAuthClient } from "better-auth/react";
import { expoClient } from "@better-auth/expo/client";
import { passkeyClient } from "@better-auth/passkey/client";
import { ssoClient } from "@better-auth/sso/client";
import {
    anonymousClient,
    emailOTPClient,
    organizationClient,
    adminClient,
} from "better-auth/client/plugins";
import * as SecureStore from "expo-secure-store";

export const authClient = createAuthClient({
    baseURL: "https://api.example.com",
    plugins: [
        expoClient({
            scheme: "myapp",
            storagePrefix: "myapp",
            storage: SecureStore,
        }),
        passkeyClient(),
        anonymousClient(),
        emailOTPClient(),
        ssoClient(),
        organizationClient(),
        adminClient(),
    ],
});
```

---

## Appendix: Key Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| SAML support is "in active development" and may not be production-ready | HIGH | Use OIDC where possible; test SAML thoroughly; pin Better Auth version |
| SSO org provisioning only works via SSO sign-in, not other auth methods | MEDIUM | Build custom hook to check domain and add to org on any sign-in method |
| DodoPayments `createCustomerOnSignUp` will fire for anonymous users | MEDIUM | Set `createCustomerOnSignUp: false` and create customers explicitly after account linking |
| Passkey registration requires authenticated session | MEDIUM | Users must sign up via another method first, then add passkey |
| `disableImplicitSignUp` does not work for SAML providers | MEDIUM | Validate users manually in `provisionUser` callback |
| SSO static provider registration requires active session | MEDIUM | Use seed script or admin API to pre-register providers |
| Cloudflare Workers + SSO may break on specific versions | MEDIUM | Test edge runtime compatibility; use Node.js runtime if on CF |
| Multi-domain SAML with single IdP is broken | HIGH | Use separate SSO provider entries per domain, or OIDC instead |
| Organization `listTeamMembers` may fail for owners/admins | LOW | Test thoroughly; may require specific version fix |
| Cookie cache means revoked sessions persist until cache expires | LOW | Use short `maxAge` for cookie cache (5 min recommended) |
