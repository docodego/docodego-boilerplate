[← Back to Roadmap](../ROADMAP.md)

# Shared UI

## Intent

This spec defines the `@repo/ui` package that provides the shared component library for the DoCodeGo boilerplate. The package is built on Shadcn UI with the `base-vega` style variant (using `@base-ui/react` primitives instead of Radix) and includes utility functions, a direction provider for RTL support, and theming infrastructure. Components from this package are consumed by `apps/web`, `apps/browser-extension`, and Storybook. This spec ensures that every component follows consistent styling conventions, supports both LTR and RTL layouts via CSS logical properties, and integrates correctly with Tailwind CSS v4 and the project's dark mode implementation.

## Acceptance Criteria

- [ ] The `packages/ui` directory is present and contains a `package.json` with `"name"` set to `"@repo/ui"`
- [ ] The `package.json` sets `"type"` to `"module"` and `"private"` to true
- [ ] The package depends on `@base-ui/react` — this dependency is present in `package.json` with a version >= 1.0.0
- [ ] The package depends on `class-variance-authority`, `clsx`, and `tailwind-merge` — all 3 are present in `package.json`
- [ ] A `cn()` utility function is present that combines `clsx` and `tailwind-merge` for conditional class composition
- [ ] A `DirectionProvider` component is present that sets the `dir` attribute to `"ltr"` or `"rtl"` based on the active locale
- [ ] At least 17 Shadcn components are present in the package: Button, Card, Dialog, Drawer, Dropdown Menu, Input, Label, Popover, Select, Separator, Table, Tabs, Textarea, Tooltip, Badge, Toaster, and Sonner
- [ ] Every component file uses the `base-vega` style variant — the count of Radix primitive imports (`@radix-ui/*`) equals 0 across all component files
- [ ] All Tailwind CSS classes in components use logical properties: `ps-`/`pe-` instead of `pl-`/`pr-`, `text-start`/`text-end` instead of `text-left`/`text-right`, `rounded-s-`/`rounded-e-` instead of `rounded-l-`/`rounded-r-` — the count of non-logical directional classes equals 0
- [ ] No arbitrary Tailwind values are used when a canonical utility class exists — the count of `[arbitrary]` bracket values that have a utility equivalent equals 0
- [ ] The `tsconfig.json` defines a `@/*` path alias that is present and maps to `"./src/*"` for Shadcn-generated imports
- [ ] The count of `biome-ignore` comments in the package equals 1 — only the `Label` component has an accessibility suppression
- [ ] The Sonner toast component is present and configured for the project's theming system
- [ ] The `@fontsource-variable/geist` font package is present as a dependency for self-hosted font loading
- [ ] The package contains a `"typecheck"` script and a `"test"` script in `package.json` — both are present and non-empty
- [ ] Running `pnpm --filter ui typecheck` exits with code = 0 and produces 0 errors

## Constraints

- All components originate from Shadcn's `base-vega` variant and use `@base-ui/react` primitives — no Radix UI packages (`@radix-ui/*`) are installed or imported. The count of `@radix-ui` entries in `package.json` dependencies equals 0, and the count of `@radix-ui` import statements across all source files equals 0.
- After every `shadcn add` command, 3 post-install steps are required: run `pnpm dlx @tailwindcss/upgrade` for canonical class conversion, audit sub-components for missing RTL variants (e.g., `data-[side=inline-start/end]`), and run `pnpm lint:fix` to format and sort imports. The count of non-canonical Tailwind classes introduced by raw Shadcn output must equal 0 after these steps.
- The package never imports from `apps/*` workspaces — it is consumed by apps, not the reverse. The count of import statements referencing `apps/` in the UI source files equals 0.
- CSS direction uses logical properties exclusively — physical directional properties (`left`, `right`, `pl-`, `pr-`, `ml-`, `mr-`, `rounded-l-`, `rounded-r-`, `text-left`, `text-right`) are not used. The only exception is `translate-x` which has no logical equivalent and uses an `rtl:` variant override instead.

## Failure Modes

- **Radix import after shadcn add**: A developer runs `shadcn add` for a new component and the generated code imports from `@radix-ui/react-*` instead of `@base-ui/react`, breaking the `base-vega` variant convention. The CI lint step returns error because the `@radix-ui` package is not installed and the import fails module resolution, prompting the developer to regenerate the component with the correct variant or manually replace the import.
- **Missing RTL variant on sub-component**: A developer adds a Shadcn component where the parent has `data-[side=inline-start/end]` RTL variants but a child sub-component uses hardcoded `data-[side=left/right]`, causing incorrect positioning in Arabic RTL layouts. The visual regression test in Storybook renders the component in both LTR and RTL modes, and returns error if the RTL screenshot differs from the expected baseline by more than 1 percent pixel difference.
- **Non-logical directional class**: A developer writes `pl-4` instead of `ps-4` in a component, causing incorrect padding in RTL layouts. The CI lint step runs a custom Biome rule or grep check that scans for non-logical directional classes and returns error listing each violation with the file path, line number, and the suggested logical property replacement.
- **Arbitrary value instead of canonical class**: A developer uses `p-[16px]` instead of `p-4` in a component, bypassing Tailwind's design token system and creating inconsistency. The `pnpm dlx @tailwindcss/upgrade` post-install step converts arbitrary values to their canonical equivalents automatically, and if any remain after the upgrade, the CI lint step returns error identifying the remaining arbitrary values.

## Declared Omissions

- Tailwind CSS v4 engine configuration and PostCSS setup (infrastructure concern shared at root level)
- Storybook addon configuration and story file conventions (covered by per-workspace DX specs)
- Animation library setup with Motion/Framer Motion (consumed by apps, not defined in the UI package)
- Icon library setup with Lucide React (consumed by apps directly, not wrapped by the UI package)
