[← Back to Roadmap](../ROADMAP.md)

# Database Schema

## Intent

This spec defines the database schema, ORM configuration, migration strategy, and seed script for the DoCodeGo boilerplate. The database is Cloudflare D1 (SQLite at the edge) accessed through Drizzle ORM with the SQLite dialect. The schema includes core Better Auth tables (user, session, account, verification), plugin-contributed tables (organization, member, invitation, team, passkey, ssoProvider, subscription), and any application-specific extensions. This spec ensures that every table, column, and relationship is explicitly defined in Drizzle schema files, that migrations are generated deterministically from schema diffs, and that the seed script populates development databases with realistic test data for all user roles and organization structures.

## Acceptance Criteria

- [ ] A Drizzle schema directory is present at `apps/api/src/db/schema/` containing at least 1 schema file that exports table definitions
- [ ] The schema defines at least 11 tables: `user`, `session`, `account`, `verification`, `organization`, `member`, `invitation`, `team`, `passkey`, `ssoProvider`, and `subscription`
- [ ] The `user` table includes at least 10 columns: `id`, `name`, `email`, `emailVerified`, `image`, `role`, `banned`, `banReason`, `banExpires`, and `preferredLocale` are all present
- [ ] The `session` table includes at least 8 columns: `id`, `token`, `userId`, `expiresAt`, `ipAddress`, `userAgent`, `activeOrganizationId`, and `activeTeamId` are all present
- [ ] The `member` table includes a `role` column that defaults to `"member"` and a `teamId` column that is present and nullable
- [ ] The `invitation` table includes `status` and `expiresAt` columns — both are present and non-empty in the schema definition
- [ ] Every table that references another table defines explicit foreign key constraints — at least 8 foreign key relationships are present across all tables
- [ ] A `drizzle.config.ts` file is present at `apps/api/` and sets `dialect` to `"sqlite"`, `driver` to `"d1-http"`, and `schema` to the schema directory path
- [ ] Running `pnpm --filter api db:generate` produces a SQL migration file in the migrations directory and exits with code = 0
- [ ] Running `pnpm --filter api db:migrate` applies pending migrations to the local D1 database and exits with code = 0
- [ ] A seed script is present at `apps/api/scripts/seed.ts` and running `pnpm --filter api db:seed` exits with code = 0
- [ ] The seed script creates at least 1 admin user (`user.role = "admin"`), at least 2 regular users, and at least 1 organization with at least 2 members
- [ ] The seed script uses `@faker-js/faker` for generating realistic names, emails, and other test data — the faker import is present in the seed file
- [ ] The `wrangler.toml` file defines a D1 binding named `DB` and an R2 binding named `STORAGE` — both are present in the bindings section
- [ ] All Drizzle table definitions use the `sqliteTable` function from `drizzle-orm/sqlite-core` — 0 tables use raw SQL string definitions

## Constraints

- All database access goes through Drizzle ORM — no raw SQL queries exist in application code outside of migration files. The count of raw SQL template literals (`sql` tagged templates used for queries) in route handlers and services equals 0, except for Drizzle's built-in `sql` operator used in where clauses and expressions.
- The schema is the single source of truth for database structure — Better Auth's `generate` CLI is not used to create tables. All tables, including those required by Better Auth plugins, are defined explicitly in Drizzle schema files so that column types, defaults, and constraints are visible and version-controlled.
- Migration files are committed to the repository and are present in version control — they are not listed in `.gitignore`. Each migration file is immutable after being committed; schema changes produce new migration files, never modify existing ones.
- The seed script is idempotent — running it multiple times on the same database produces no duplicate records and exits with code = 0 each time. It clears existing seed data before inserting fresh records.

## Failure Modes

- **Schema drift from Better Auth**: A Better Auth plugin update adds a new required column that is not reflected in the Drizzle schema, causing runtime query failures when the plugin attempts to read or write the missing column. The CI typecheck step catches the mismatch because the Drizzle-generated types do not include the new column, and route handlers that pass plugin data to Drizzle return type errors that block the build. The developer then updates the schema file and generates a new migration.
- **Migration ordering conflict**: Two developers create migrations concurrently that modify the same table, causing a conflict when both are applied. Drizzle Kit detects the conflict during `db:migrate` and returns error with a diagnostic message identifying the overlapping table and column changes, preventing partial application. The developers coordinate to merge their schema changes into a single sequential migration.
- **Seed script failure on empty database**: The seed script runs before migrations have been applied, causing table-not-found errors. The seed script checks for the presence of the `user` table before inserting data, and if the table is absent, it returns error with a message instructing the developer to run `db:migrate` first before seeding.
- **D1 binding missing in production**: The Cloudflare Worker starts without the `DB` binding configured in the deployment environment, causing every database query to fail with an undefined binding error. The Hono startup middleware validates that both `DB` and `STORAGE` bindings are present on the first request, and if either is absent, it returns error 500 with a diagnostic message that logs the missing binding name to the Worker logs for the operator to resolve.

## Declared Omissions

- Application-specific business tables beyond auth and multi-tenancy (added per project)
- R2 object storage access patterns (covered by `user-uploads-a-file.md`)
- Better Auth plugin wiring and session configuration (covered by `auth-server-config.md`)
- Database backup and disaster recovery procedures (infrastructure concern, not application spec)
