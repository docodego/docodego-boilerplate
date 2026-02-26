[← Back to Index](README.md)

# User Visits Landing Page

## Arriving at the Root URL

The user navigates to `/` in their browser. Astro serves this as a fully static SSG page — the HTML is pre-built at deploy time with zero JavaScript shipped to the client. Search engine crawlers receive a complete, rendered document with no hydration delay.

## Header

The header displays the product name on the left and a theme toggle on the right. The theme toggle reads the user's preference from localStorage on the server-rendered page and applies the correct theme class before the first paint, preventing any flash of the wrong theme.

Next to the theme toggle, a small React island checks the user's session state. If the user is not authenticated, a localized "Sign in" link appears, pointing to `/signin`. If the user is already authenticated, their avatar is displayed instead — rendered from the session's user profile image, falling back to initials if no image exists. Clicking the avatar navigates to `/app`, which routes the user into their active organization's dashboard.

## Hero Section

Below the header, a hero section displays the product name and a short localized tagline describing the boilerplate.

Directly beneath the tagline, a copyable install command is presented in a styled code block — for example, `pnpm create docodego-boilerplate@latest`. A copy button sits beside it. When the user clicks the copy button, the command text is written to the clipboard and the button briefly changes to a checkmark to confirm the copy succeeded.

Below the install command, a prominent call-to-action button links to `/signin`. This remains the primary conversion path for new visitors who want to see the live demo.

## Tech Stack Grid

Following the hero, a grid of cards presents the project's technology choices organized by category. Each card shows the technology name, its version, and a one-line description of its role. The categories map to the major sections of the stack:

- **Core Platform** — TypeScript, Node.js ESM
- **Monorepo** — pnpm, Turborepo
- **Frontend Web** — Astro, React 19, TanStack Router, TanStack Query, Zustand, Tailwind CSS, Motion
- **Backend API** — Hono, Cloudflare Workers, D1, R2, Drizzle ORM, oRPC
- **Auth** — Better Auth with Email OTP, Passkey, SSO, Organization, Admin, Anonymous, DodoPayments plugins
- **UI Components** — Shadcn (base-vega), Base UI, CVA, Sonner, Lucide icons, Geist font
- **Shared Packages** — oRPC contracts, Zod, i18next (en + ar, 5 namespaces)
- **Mobile** — Expo 54, React Native, Expo Router v6, MMKV, Maestro
- **Desktop** — Tauri 2, system tray, auto-updates, deep links
- **Browser Extension** — WXT, Manifest V3, token relay auth
- **Testing** — Vitest, Playwright, Storybook 10
- **Code Quality** — Biome, Knip, Commitlint, Lefthook
- **Infrastructure** — Cloudflare Workers/Pages, EAS Build, GitHub Actions

The cards are laid out in a responsive grid that adapts from a single column on mobile to two or three columns on wider screens.

## Footer

The footer sits at the bottom of the page and is divided into columns. The first column displays the product name and a short localized description. The second column groups navigation links under a localized **Product** heading: links to the GitHub repository, the docs site, and the changelog. At the very bottom, a copyright line reads "© 2026 DoCodeGo" alongside a link to the MIT license.

## Authentication-Aware Header

The landing page itself is entirely public — there is no auth gate, no session requirement, and no redirect logic. The only authentication-aware element is the header's sign-in link / avatar toggle, which is mounted as a React island with `client:load`. The rest of the page remains fully static with zero JavaScript.
