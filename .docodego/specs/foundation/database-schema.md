---
id: SPEC-2026-005
version: 1.0.0
created: 2026-02-26
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Database Schema

## Intent

This spec defines the database schema, ORM configuration,
migration strategy, and seed script for the DoCodeGo
boilerplate. The database is Cloudflare D1 (SQLite at the
edge) accessed through Drizzle ORM with the SQLite dialect.
The schema includes core Better Auth tables (user, session,
account, verification), plugin-contributed tables
(organization, member, invitation, team, passkey,
ssoProvider, subscription), and any application-specific
extensions. This spec ensures that every table, column, and
relationship is explicitly defined in Drizzle schema files,
that migrations are generated deterministically from schema
diffs, and that the seed script populates development
databases with realistic test data for all user roles and
organization structures.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| D1 (Cloudflare SQL) | read/write | Every database query via Drizzle ORM | Route handlers return 500 and the global error handler falls back to a generic JSON error message for the client |
| Drizzle ORM | read/write | Every database operation in route handlers and services | Build fails at compile time because table types cannot be resolved, and CI alerts to block deployment |
| Better Auth | read | App startup (schema contract) | Auth plugin queries fail at runtime because expected columns are absent, and the error handler returns 500 for all auth routes |
| `@faker-js/faker` | read | Seed script execution during development | Seed script falls back to hardcoded placeholder values or exits with a diagnostic error message identifying the missing dependency |
| Drizzle Kit CLI | write | Migration generation and application via `db:generate` and `db:migrate` | Migration commands exit with non-zero code and log a diagnostic error message identifying the connection or schema issue |

## Behavioral Flow

1. **[Developer]** defines or modifies table schemas in
   `apps/api/src/db/schema/` using Drizzle's
   `sqliteTable` function
2. **[Developer]** runs `pnpm --filter api db:generate`
   which invokes Drizzle Kit to diff the current schema
   against the last migration snapshot
3. **[Drizzle Kit]** produces a new SQL migration file in
   the migrations directory containing only the delta
   changes (CREATE TABLE, ALTER TABLE, etc.)
4. **[Developer]** runs `pnpm --filter api db:migrate`
   which applies all pending migration files to the local
   D1 database in sequential order
5. **[Developer]** runs `pnpm --filter api db:seed` which
   executes the seed script that first clears existing
   seed data, then inserts fresh records using
   `@faker-js/faker` for realistic test data
6. **[Seed script]** checks for the presence of the `user`
   table before inserting data and returns an error with a
   diagnostic message if migrations have not been applied
7. **[CI pipeline]** runs `pnpm --filter api db:generate`
   and verifies no new migration files are produced,
   confirming schema and migrations are in sync

## State Machine

No stateful entities. The database schema defines static
table structures and column definitions. Entity lifecycle
states (such as invitation status transitions) are governed
by the specs that own those business flows, not by this
schema definition spec.

## Business Rules

- **Rule idempotent-seed:** IF the seed script is executed
  AND the database already contains seed data THEN the
  script clears all existing seed records before inserting
  fresh data, ensuring the final row count equals the
  expected count with 0 duplicates
- **Rule migration-immutability:** IF a migration file has
  been committed to version control THEN it is never
  modified; schema changes produce new migration files, and
  the count of modified committed migration files equals 0
- **Rule schema-as-source-of-truth:** IF a table is
  required by Better Auth or its plugins THEN the table is
  defined explicitly in Drizzle schema files with all
  columns, types, and defaults visible in version control,
  and the count of tables created by Better Auth's
  `generate` CLI equals 0

## Permission Model

Single role; no permission model is needed for the database
schema definition itself. Access control for database
operations is enforced at the application layer by
route-specific specs and the auth-server-config spec, not
at the schema definition level.

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
- [ ] All Drizzle table definitions use the `sqliteTable` function from `drizzle-orm/sqlite-core` — the count of tables using raw SQL string definitions equals 0

## Constraints

- All database access goes through Drizzle ORM — no raw SQL queries exist in application code outside of migration files. The count of raw SQL template literals (`sql` tagged templates used for queries) in route handlers and services equals 0, except for Drizzle's built-in `sql` operator used in where clauses and expressions.
- The schema is the single source of truth for database structure — Better Auth's `generate` CLI is not used to create tables. All tables, including those required by Better Auth plugins, are defined explicitly in Drizzle schema files so that column types, defaults, and constraints are visible and version-controlled.
- Migration files are committed to the repository and are present in version control — they are not listed in `.gitignore`. Each migration file is immutable after being committed; schema changes produce new migration files, never modify existing ones.
- The seed script is idempotent — running it multiple times on the same database produces 0 duplicate records and exits with code = 0 each time. It clears existing seed data before inserting fresh records.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The seed script runs before migrations have been applied, causing table-not-found errors on insert | The seed script checks for the presence of the `user` table and returns an error with a diagnostic message instructing the developer to run `db:migrate` first | Exit code is non-zero and stderr contains the text `db:migrate` |
| A developer runs `db:generate` when the schema has not changed since the last migration was generated | Drizzle Kit produces 0 new migration files and exits with code = 0, confirming schema and migrations are in sync | The migrations directory file count remains unchanged after the command completes |
| Two developers create migrations concurrently that modify the same table with overlapping column changes | Drizzle Kit detects the conflict during `db:migrate` and returns a non-zero exit code with a diagnostic message identifying the overlapping changes | Exit code is non-zero and the error output names the conflicting table |
| The `user` table is missing the `preferredLocale` column that Better Auth's locale plugin expects at runtime | The Drizzle-generated TypeScript types do not include the missing column, causing route handlers that reference it to fail typecheck with a compile-time error | `pnpm typecheck` exits with non-zero code and the error references `preferredLocale` |
| The seed script is executed twice consecutively on the same database without clearing data between runs | The seed script clears all existing seed records before inserting, resulting in 0 duplicate rows and the same final record count after both executions | Row count query returns the expected count with 0 extra records |
| A foreign key constraint references a table that does not exist because migration ordering is incorrect | SQLite rejects the migration with a foreign key constraint error, and `db:migrate` exits with a non-zero code identifying the missing referenced table | Exit code is non-zero and the error output contains `foreign key` |

## Failure Modes

- **Schema drift from Better Auth plugin update**
    - **What happens:** A Better Auth plugin update adds a new required column that is not reflected in the Drizzle schema, causing runtime query failures when the plugin attempts to read or write the missing column during auth operations.
    - **Source:** Plugin version upgrade introduces schema requirements that are not yet mirrored in the Drizzle table definitions.
    - **Consequence:** Auth endpoints return 500 errors for all users because the plugin cannot find the expected column, and session creation and verification both fail completely.
    - **Recovery:** The CI typecheck step alerts on the mismatch because Drizzle-generated types do not include the new column, causing route handler type errors that block the build and prevent deployment until the developer updates the schema file and generates a new migration.
- **Migration ordering conflict between concurrent developers**
    - **What happens:** Two developers create migrations concurrently that modify the same table with overlapping column definitions, causing a conflict when both migration files are applied in sequence during `db:migrate` execution.
    - **Source:** Concurrent development on branches that both alter the same table schema without coordinating migration sequence numbers.
    - **Consequence:** The `db:migrate` command fails with a non-zero exit code on the second conflicting migration, leaving the database in a partially migrated state that blocks all schema-dependent operations.
    - **Recovery:** Drizzle Kit logs a diagnostic error message identifying the overlapping table and column changes, and the developers coordinate to merge their schema changes into a single sequential migration file that resolves the conflict before retrying the migration.
- **Seed script executed on empty database without migrations**
    - **What happens:** A developer runs `pnpm --filter api db:seed` before running `db:migrate`, causing the seed script to attempt inserts into tables that do not exist in the D1 database.
    - **Source:** Incorrect command execution order during initial development environment setup or after a database reset.
    - **Consequence:** The seed script fails with table-not-found errors and exits with a non-zero code, leaving the database empty with 0 seed records and blocking local development testing.
    - **Recovery:** The seed script checks for the presence of the `user` table before inserting any data, and if the table is absent, it returns an error with a diagnostic message that logs the instruction to run `db:migrate` first, alerting the developer to the correct command sequence.
- **D1 binding missing in production deployment**
    - **What happens:** The Cloudflare Worker starts without the `DB` binding configured in the deployment environment, causing every database query to fail with an undefined binding error on the first request that accesses D1.
    - **Source:** Misconfigured `wrangler.toml` or missing environment binding in the Cloudflare dashboard after a deployment configuration change.
    - **Consequence:** All routes that query the database return 500 errors and all auth flows that check session state also fail, effectively locking out all authenticated users from the application.
    - **Recovery:** The Hono startup middleware validates that both `DB` and `STORAGE` bindings are present on the first request, and if either is absent, it returns 500 with a diagnostic message that logs the missing binding name to Worker logs, and the system degrades gracefully because non-database routes continue serving normally.
- **Seed script produces duplicate records on re-execution**
    - **What happens:** A bug in the seed script causes it to skip the data clearing step, resulting in duplicate user and organization records when the script is executed multiple times on the same database.
    - **Source:** Missing or broken DELETE/TRUNCATE logic at the beginning of the seed script that fails to remove existing seed records before inserting new ones.
    - **Consequence:** The database contains duplicate email addresses and organization names that cause unique constraint violations in subsequent operations, breaking auth flows and organization lookups.
    - **Recovery:** The seed script degrades to a safe state by wrapping all operations in a transaction that rolls back on any constraint violation, and an integration test verifies that running the seed script twice consecutively produces 0 duplicate records by comparing row counts after each execution.

## Declared Omissions

- Application-specific business tables beyond auth and multi-tenancy are not defined in this spec and are added per project in separate feature specs
- R2 object storage access patterns, upload flows, and file metadata schemas are not covered here and are defined in `user-uploads-a-file.md`
- Better Auth plugin wiring, session strategy, and OAuth provider configuration are not covered here and are defined in `auth-server-config.md`
- Database backup, disaster recovery procedures, and point-in-time restore strategies are infrastructure-level concerns not addressed by this application-level spec
- Query performance optimization, index definitions beyond foreign keys, and query plan analysis are not specified here and are deferred to performance-tuning efforts

## Related Specifications

- [auth-server-config](auth-server-config.md) — Better Auth plugin configuration, session strategy, and OAuth provider setup that depend on the tables defined in this schema
- [api-framework](api-framework.md) — Hono framework configuration and middleware stack that creates the D1 database binding consumed by Drizzle ORM in this spec
- [shared-contracts](shared-contracts.md) — oRPC contract definitions and Zod schemas that validate request and response data shaped by the database tables defined here
- [shared-i18n](shared-i18n.md) — Internationalization infrastructure providing locale values stored in the `user.preferredLocale` column defined in this schema
- [ci-cd-pipelines](ci-cd-pipelines.md) — CI/CD deployment workflow and GitHub Actions pipelines that run migration generation checks to verify schema and migration sync
