[← Back to Roadmap](ROADMAP.md)

# Dependencies

Third-party packages used across the spec corpus.

| Package | Version | Ecosystem | Justification |
|---------|---------|-----------|---------------|
| typescript | ^5.9 | npm | Language compiler for all workspaces |
| react | ^19 | npm | UI library for web, mobile, and extension targets |
| react-dom | ^19 | npm | React DOM renderer for web and extension |
| astro | ^5 | npm | SSG framework for landing page and SPA dashboard shell |
| hono | ^4 | npm | API framework running on Cloudflare Workers |
| zod | ^3 | npm | Schema validation for API contracts and form inputs |
| drizzle-orm | ^0.39 | npm | Type-safe SQL ORM for D1 database queries |
| drizzle-kit | ^0.30 | npm | Migration CLI and schema introspection for drizzle-orm |
| better-auth | ^1 | npm | Authentication framework with email, OAuth, and org support |
| @better-auth/expo | ^1 | npm | Better Auth client adapter for Expo and React Native |
| @orpc/contract | ^1 | npm | Type-safe API contract definitions shared between client and server |
| @tanstack/react-router | ^1 | npm | Type-safe file-based client-side routing for React SPA |
| @tanstack/react-query | ^5 | npm | Server state management with caching and retry logic |
| @base-ui/react | ^1 | npm | Unstyled UI primitives for Shadcn base-vega component style |
| class-variance-authority | ^0.7 | npm | Component variant management for Shadcn UI |
| tailwind-merge | ^2 | npm | Tailwind CSS class deduplication in cn() utility |
| clsx | ^2 | npm | Conditional CSS class composition |
| sonner | ^2 | npm | Toast notification component for user feedback |
| lucide-react | ^0.460 | npm | Icon library providing SVG icons as React components |
| @fontsource-variable/geist | ^5 | npm | Self-hosted variable Geist font package |
| tailwindcss | ^4 | npm | Utility-first CSS framework for all web targets |
| expo | ^54 | npm | React Native framework with managed build tooling |
| expo-router | ^6 | npm | File-based navigation for Expo mobile app |
| expo-localization | ^16 | npm | Native device locale detection for i18n |
| expo-secure-store | ^14 | npm | Encrypted credential storage on mobile devices |
| react-native | ^0.76 | npm | Core mobile app framework for iOS and Android |
| react-native-mmkv | ^3 | npm | High-performance key-value storage replacing AsyncStorage |
| react-native-reanimated | ^4 | npm | Native animation library for React Native gestures and transitions |
| @tauri-apps/cli | ^2 | npm | Tauri desktop app build and dev CLI |
| @tauri-apps/api | ^2 | npm | JavaScript IPC bindings for Tauri desktop commands |
| wxt | ^0.19 | npm | Browser extension framework with HMR and manifest v3 support |
| i18next | ^24 | npm | Core i18n framework for translation management |
| react-i18next | ^15 | npm | React bindings and hooks for i18next integration |
| i18next-resources-to-backend | ^1 | npm | Lazy-loading translation bundles on web |
| @cloudflare/workers-types | ^4 | npm | TypeScript type definitions for Cloudflare Worker globals |
| @faker-js/faker | ^9 | npm | Fake data generation for database seed scripts |
| vitest | ^3 | npm | Unit and integration test framework for all workspaces |
| @playwright/test | ^1 | npm | E2E test framework for web application testing |
| @biomejs/biome | ^1 | npm | Linter and formatter replacing ESLint and Prettier |
| knip | ^5 | npm | Dead code and unused dependency detection |
| lefthook | ^1 | npm | Git hooks manager for pre-commit and commit-msg hooks |
| turbo | ^2 | npm | Monorepo build orchestration and task caching |
| storybook | ^8 | npm | Component development and documentation environment |
| @scalar/hono-api-reference | ^0.5 | npm | OpenAPI documentation UI for Hono API endpoints |
| wrangler | ^3 | npm | Cloudflare Workers CLI for local dev and deployment |
