---
id: SPEC-2026-009
version: 1.0.0
created: 2026-02-26
owner: Mayank (Intent Architect)
status: draft
roles: [Framework Adopter]
---

[← Back to Roadmap](../ROADMAP.md)

# Shared UI

## Intent

This spec defines the `@repo/ui` package that provides the shared
component library for the DoCodeGo boilerplate. The package is
built on Shadcn UI with the `base-vega` style variant (using
`@base-ui/react` primitives instead of Radix) and includes utility
functions, a direction provider for RTL support, and theming
infrastructure. Components from this package are consumed by
`apps/web`, `apps/browser-extension`, and Storybook. This spec
ensures that every component follows consistent styling
conventions, supports both LTR and RTL layouts via CSS logical
properties, and integrates correctly with Tailwind CSS v4 and the
project's dark mode implementation.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `@base-ui/react` | read | Every component render that uses a Base UI primitive | Build fails at compile time because component imports cannot resolve the Base UI module and CI alerts to block deployment |
| `class-variance-authority` | read | Component variant resolution at render time | Build fails at compile time because variant definitions cannot resolve the CVA module and CI alerts to block deployment |
| `tailwind-merge` | read | Every `cn()` utility call that merges Tailwind classes | Build fails at compile time because the `cn()` function cannot resolve the tailwind-merge module and CI alerts to block deployment |
| `@fontsource-variable/geist` | read | Initial page load when the self-hosted Geist font is rendered | Font loading falls back to the browser's default sans-serif font stack so text remains readable but uses a different typeface |
| Tailwind CSS v4 | read | Build time and dev server HMR when processing component styles | Build fails because CSS utility classes cannot be compiled and the dev server alerts with a compilation error |

## Behavioral Flow

1. **[Developer]** runs `pnpm dlx shadcn@latest add <component>`
    targeting the `packages/ui` workspace to scaffold a new
    component from the `base-vega` variant
2. **[Developer]** runs `pnpm dlx @tailwindcss/upgrade` to convert
    non-canonical Tailwind classes to their canonical equivalents
    in the newly added component files
3. **[Developer]** audits the generated component and all
    sub-components for missing RTL variants, replacing physical
    directional properties (`left`/`right`) with logical
    equivalents (`inline-start`/`inline-end`) and adding
    `data-[side=inline-start/end]` where the parent component
    already has them
4. **[Developer]** runs `pnpm lint:fix` to format the component
    source code and sort import statements according to Biome
    rules
5. **[Consumer app]** imports the component from `@repo/ui` and
    renders it inside a `DirectionProvider` that sets the `dir`
    attribute to `"ltr"` or `"rtl"` based on the active locale
6. **[DirectionProvider]** propagates the direction value to all
    child components so CSS logical properties resolve to the
    correct physical direction at render time

## State Machine

No stateful entities. The UI package contains stateless
presentational components with no lifecycle management within
this spec's scope.

## Business Rules

No conditional business rules. Component rendering is
unconditional and driven entirely by props passed from consumer
applications.

## Permission Model

Single role; no permission model is needed. All consumers of
`@repo/ui` have identical access to every exported component
and utility function without any role-based restrictions.

## Acceptance Criteria

- [ ] The `packages/ui` directory is present and contains a `package.json` with `"name"` set to `"@repo/ui"`
- [ ] The `package.json` `"type"` field equals `"module"` and `"private"` equals true — both values are present in the file
- [ ] The `@base-ui/react` dependency is present in `package.json` with a version >= 1.0.0 for Base UI primitives
- [ ] The dependencies `class-variance-authority`, `clsx`, and `tailwind-merge` are all 3 present in `package.json`
- [ ] A `cn()` utility function is present that combines `clsx` and `tailwind-merge` for conditional class composition
- [ ] A `DirectionProvider` component is present that sets the `dir` attribute to `"ltr"` or `"rtl"` based on the active locale
- [ ] At least 17 Shadcn components are present in the package: Button, Card, Dialog, Drawer, Dropdown Menu, Input, Label, Popover, Select, Separator, Table, Tabs, Textarea, Tooltip, Badge, Toaster, and Sonner
- [ ] The count of Radix primitive imports (`@radix-ui/*`) equals 0 across all component files — every component uses `base-vega` style
- [ ] The count of non-logical directional classes equals 0 — all Tailwind CSS classes use `ps-`/`pe-` not `pl-`/`pr-`, `text-start`/`text-end` not `text-left`/`text-right`, `rounded-s-`/`rounded-e-` not `rounded-l-`/`rounded-r-`
- [ ] The count of arbitrary Tailwind bracket values that have a canonical utility equivalent equals 0 across all component files
- [ ] The `tsconfig.json` `@/*` path alias is present and maps to `"./src/*"` for Shadcn-generated imports
- [ ] The count of `biome-ignore` comments in the package equals 1 — only the `Label` component has an accessibility suppression
- [ ] The Sonner toast component is present and configured for the project's theming system with the correct theme provider
- [ ] The `@fontsource-variable/geist` font package is present as a dependency for self-hosted font loading
- [ ] The `"typecheck"` and `"test"` scripts are both present and non-empty in the `package.json` file
- [ ] Running `pnpm --filter ui typecheck` exits with code = 0 and produces 0 errors

## Constraints

- All components originate from Shadcn's `base-vega` variant and
    use `@base-ui/react` primitives — no Radix UI packages
    (`@radix-ui/*`) are installed or imported. The count of
    `@radix-ui` entries in `package.json` dependencies equals 0,
    and the count of `@radix-ui` import statements across all
    source files equals 0.
- After every `shadcn add` command, 3 post-install steps are
    required: run `pnpm dlx @tailwindcss/upgrade` for canonical
    class conversion, audit sub-components for missing RTL
    variants (e.g., `data-[side=inline-start/end]`), and run
    `pnpm lint:fix` to format and sort imports. The count of
    non-canonical Tailwind classes introduced by raw Shadcn output
    equals 0 after these steps.
- The package never imports from `apps/*` workspaces — it is
    consumed by apps, not the reverse. The count of import
    statements referencing `apps/` in the UI source files
    equals 0.
- CSS direction uses logical properties exclusively — physical
    directional properties (`left`, `right`, `pl-`, `pr-`, `ml-`,
    `mr-`, `rounded-l-`, `rounded-r-`, `text-left`,
    `text-right`) are not used. The only exception is
    `translate-x` which has no logical equivalent and uses an
    `rtl:` variant override instead.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| A consumer app renders a component without wrapping it in a `DirectionProvider` ancestor | The component falls back to the browser's default direction (`"ltr"`) and renders with left-to-right layout without throwing an error | The component renders without a console error and all CSS logical properties resolve to their LTR physical equivalents |
| A developer runs `shadcn add` for a component that does not exist in the `base-vega` variant registry | The Shadcn CLI returns an error message indicating the component is not available for the selected style variant | The CLI exits with a non-zero code and no files are created or modified in the `packages/ui` directory |
| A component receives an empty string or `undefined` for a required text prop such as a Button label | The component renders an empty element without crashing and the DOM node is present with zero visible text content | The rendered HTML contains the component element with an empty text node and no JavaScript runtime error appears |
| The `cn()` utility receives conflicting Tailwind classes such as `ps-2` and `ps-4` in the same call | `tailwind-merge` resolves the conflict by keeping the last class `ps-4` and removing the duplicate `ps-2` | The output string contains `ps-4` and does not contain `ps-2` |
| A component is rendered in an RTL context where `dir="rtl"` is set on a parent element | All CSS logical properties (`ps-`, `pe-`, `text-start`, `text-end`, `rounded-s-`, `rounded-e-`) resolve to their RTL physical equivalents | Visual regression snapshot in Storybook RTL mode matches the expected baseline within 1 percent pixel difference |

## Failure Modes

- **Radix import after shadcn add**
    - **What happens:** A developer runs `shadcn add` for a new
        component and the generated code imports from
        `@radix-ui/react-*` instead of `@base-ui/react`, breaking
        the `base-vega` variant convention across the package.
    - **Source:** Incorrect Shadcn CLI configuration or missing
        `base-vega` style selection during component scaffolding.
    - **Consequence:** The build fails because `@radix-ui` is not
        installed as a dependency, and if force-installed it
        introduces a competing primitive library that conflicts
        with existing `@base-ui/react` components.
    - **Recovery:** CI typecheck alerts and blocks deployment
        because the `@radix-ui` module cannot be resolved, and the
        developer falls back to regenerating the component with
        the correct `base-vega` variant or manually replacing the
        import path from `@radix-ui/react-*` to the equivalent
        `@base-ui/react` primitive.
- **Missing RTL variant on sub-component**
    - **What happens:** A developer adds a Shadcn component where
        the parent has `data-[side=inline-start/end]` RTL variants
        but a child sub-component uses hardcoded
        `data-[side=left/right]`, causing incorrect positioning in
        Arabic RTL layouts.
    - **Source:** Incomplete post-install audit of generated
        component code that missed RTL variant propagation to
        nested sub-components.
    - **Consequence:** RTL users see incorrectly positioned
        dropdowns, popovers, or tooltips that overlap content or
        appear on the wrong side of their trigger elements.
    - **Recovery:** The visual regression test in Storybook
        renders the component in both LTR and RTL modes, and CI
        alerts and blocks deployment if the RTL screenshot differs
        from the expected baseline by more than 1 percent pixel
        difference, prompting the developer to add the missing
        logical property variants.
- **Non-logical directional class in component**
    - **What happens:** A developer writes `pl-4` instead of
        `ps-4` in a component file, causing incorrect padding in
        RTL layouts where the physical left side is the logical
        end side rather than the start side.
    - **Source:** Manual class authoring without awareness of
        the logical property convention or copy-pasting from
        external Tailwind examples that use physical properties.
    - **Consequence:** RTL users see padding or margin on the
        wrong side of the element, breaking the visual alignment
        and making the interface unusable for right-to-left
        language speakers.
    - **Recovery:** CI lint step alerts and blocks deployment by
        scanning for non-logical directional classes and returning
        an error that lists each violation with the file path,
        line number, and the suggested logical property
        replacement so the developer can fix all instances before
        merging.
- **Arbitrary value instead of canonical class**
    - **What happens:** A developer uses `p-[16px]` instead of
        `p-4` in a component, bypassing Tailwind's design token
        system and creating inconsistency with the rest of the
        component library's spacing scale.
    - **Source:** Developer unfamiliarity with Tailwind's utility
        class naming or copy-pasting CSS values directly from a
        design tool that outputs pixel measurements.
    - **Consequence:** The component renders with correct spacing
        but breaks design token consistency, making future theme
        changes fail to propagate to the arbitrary value.
    - **Recovery:** The `pnpm dlx @tailwindcss/upgrade`
        post-install step degrades arbitrary values to their
        canonical equivalents automatically, and if any remain
        after the upgrade the CI lint step alerts and blocks
        deployment by identifying the remaining arbitrary values
        in the build output.

## Declared Omissions

- Tailwind CSS v4 engine configuration and PostCSS setup are not
    covered here because they are infrastructure concerns shared
    at the monorepo root level and defined in build tooling specs
- Storybook addon configuration and story file conventions are
    not covered here because they are per-workspace DX concerns
    defined in the developer experience specification
- Animation library setup with Motion or Framer Motion is not
    covered here because animations are consumed by individual
    apps and not defined as part of the shared UI package exports
- Icon library setup with Lucide React is not covered here
    because icons are consumed by apps directly and not wrapped or
    re-exported by the `@repo/ui` package component library

## Related Specifications

- [shared-i18n](shared-i18n.md) — Internationalization
    infrastructure providing locale detection that the
    `DirectionProvider` component uses to determine the active
    text direction
- [shared-contracts](shared-contracts.md) — oRPC contract
    definitions and Zod schemas that define the API types
    consumed by form components for client-side input validation
- [auth-sign-in](../behavioral/auth-sign-in.md) — Authentication
    sign-in flow specification that consumes Button, Input, Label,
    and Card components from the shared UI package for its form
    layouts
- [build-deploy](../foundation/build-deploy.md) — Build and
    deployment pipeline specification that defines how the
    `@repo/ui` package is type-checked, tested, and bundled as
    part of the monorepo CI workflow
