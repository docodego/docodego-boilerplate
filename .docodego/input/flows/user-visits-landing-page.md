# User Visits Landing Page

## Arriving at the Root URL

The user navigates to `/` in their browser. Astro serves this as a fully static SSG page — the HTML is pre-built at deploy time with zero JavaScript shipped to the client. Search engine crawlers receive a complete, rendered document with no hydration delay.

## Page Structure

The page opens with a header that includes the product name and a theme toggle. The theme toggle reads the user's preference from localStorage on the server-rendered page and applies the correct theme class before the first paint, preventing any flash of the wrong theme.

Below the header, a hero section displays the product name, a short description of the boilerplate, and a prominent call-to-action button linking to `/signin`. This is the primary conversion path for new visitors.

Following the hero, a grid of six feature cards presents the platform's capabilities: Web, API, Mobile, Desktop, Extension, and i18n. Each card gives a brief summary of what the boilerplate provides for that target. The cards are laid out in a responsive grid that adapts from a single column on mobile to two or three columns on wider screens.

The page ends with a footer containing standard links and copyright information.

## No Authentication Required

This page is entirely public. There is no auth check, no session requirement, and no redirect logic. A visitor who is already signed in sees the same page as a first-time visitor — the landing page makes no distinction. The only path forward into the authenticated application is through the `/signin` CTA.
