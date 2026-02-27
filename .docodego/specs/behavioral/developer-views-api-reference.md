---
id: SPEC-2026-092
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [Developer]
---

[← Back to Roadmap](../ROADMAP.md)

# Developer Views API Reference

## Intent

This spec defines how a developer or API consumer navigates to the
publicly accessible API reference endpoint and interacts with the
auto-generated interactive documentation powered by Scalar Hono API
Reference middleware. The documentation page is derived at runtime
from the OpenAPI specification produced by oRPC, which reads schema
definitions directly from the Zod validators used across the API
route handlers. This ensures the documentation always reflects the
actual validation rules enforced by the API without maintaining a
separate specification file. The developer can browse all endpoints
organized by resource, inspect request and response schemas with
Zod-derived types, and test API calls directly from the browser
using the built-in Scalar API client. Because the OpenAPI spec is
generated at runtime from the oRPC router definitions and their Zod
schemas, the reference page updates automatically whenever the API
schema changes without requiring a manual build step or regeneration
command.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Scalar Hono API Reference middleware (serves the interactive documentation page at the configured route by rendering the OpenAPI specification into a browsable and testable developer interface directly within the Hono application) | read | When a developer navigates to the `/api/reference` endpoint in their browser, the middleware intercepts the request and serves the interactive documentation page generated from the OpenAPI specification | The middleware fails to load due to a configuration error or missing dependency and the server returns an HTTP 500 error — the developer falls back to reading the raw OpenAPI JSON specification directly from the oRPC schema endpoint |
| oRPC router definitions (define the API route structure, HTTP methods, paths, and handler bindings that form the structural backbone of the OpenAPI specification served by the Scalar middleware) | read | When the Scalar middleware generates the OpenAPI specification at runtime, it reads the oRPC router definitions to enumerate all registered endpoints with their HTTP methods, paths, and associated handler metadata | The oRPC router fails to initialize due to a missing route handler or circular dependency and the OpenAPI specification is empty — the Scalar page renders with zero endpoints and the developer logs the router initialization error to diagnose the missing routes |
| Zod validators (define the request body schemas, query parameter schemas, response schemas, and field-level constraints that oRPC uses to generate the typed schema definitions embedded in the OpenAPI specification) | read | When oRPC builds the OpenAPI specification it reads the Zod validators attached to each route handler to derive the JSON Schema representations of request parameters, request bodies, and response shapes including required fields, optional fields, enums, and nested objects | A Zod validator is malformed or references an undefined schema and the OpenAPI generation throws a runtime error — the server logs the schema compilation error and the Scalar page returns an HTTP 500 until the developer fixes the invalid Zod validator definition |
| Built-in Scalar API client (embedded HTTP client within the Scalar documentation interface that allows developers to compose and execute API requests directly from the browser without switching to external tools like Postman or curl) | read/write | When the developer fills in request parameters, sets headers, provides a request body, and clicks the execute button within the Scalar interface to test an API call against the running server | The API server is unreachable because the development server is stopped or the network connection is interrupted — the Scalar client displays a connection error in the response panel and the developer retries after restarting the development server or restoring network connectivity |
| Cloudflare Workers runtime (hosts the Hono application including the Scalar middleware and oRPC router, serving the API reference page and handling test API calls made through the Scalar client) | read/write | When the developer's browser sends an HTTP request to the API reference endpoint or when the Scalar client sends a test API request, the Cloudflare Workers runtime processes the incoming request through the Hono application middleware chain | The Workers runtime is unavailable due to a deployment failure or platform outage and all requests to the API including the reference page return HTTP 502 or timeout — the developer retries after confirming the Workers deployment status in the Cloudflare dashboard |

## Behavioral Flow

1. **[Developer]** navigates to the API reference endpoint at
    `/api/reference` in their browser — no authentication is required
    because the endpoint is publicly accessible to both internal
    developers and external API consumers

2. **[Scalar Middleware]** intercepts the request to the reference
    route and generates the interactive documentation page at runtime
    by reading the OpenAPI specification produced by oRPC from its
    router definitions and attached Zod validators

3. **[Developer]** views the documentation page which lists all API
    endpoints organized by resource, displaying each endpoint's HTTP
    method, path, description, request parameters, request body
    schema, and response schemas with Zod-derived types

4. **[Developer]** expands and collapses endpoint sections to focus
    on the specific endpoints relevant to their integration, reviewing
    required fields, optional fields, enums, and nested object shapes
    in the schema viewer for each endpoint

5. **[Developer]** selects an endpoint to test and opens the built-in
    Scalar API client which provides input fields for request
    parameters, headers, and request body content

6. **[Developer]** fills in the request parameters, sets any required
    headers, provides a request body matching the Zod-derived schema,
    and clicks the execute button to send the API call against the
    running server

7. **[Scalar Client]** sends the composed HTTP request to the API
    server and receives the response including the HTTP status code,
    response headers, and response body — the response is displayed
    inline in the documentation interface

8. **[Developer]** reviews the API response directly in the Scalar
    interface without needing to switch to an external tool like
    Postman or curl, verifying that the endpoint behavior matches the
    documented schema

9. **[Developer]** modifies the API code by adding a new endpoint,
    changing a request body validator, or updating a response shape in
    the oRPC route handlers with their Zod schemas

10. **[Developer]** reloads the API reference page and sees the
    documentation automatically reflects the code changes because the
    OpenAPI spec is generated at runtime from the oRPC router
    definitions — no manual build step or regeneration command is
    required

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| no_page_loaded | documentation_rendered | The developer navigates to the `/api/reference` endpoint in their browser and the Scalar middleware generates and serves the interactive documentation page from the runtime OpenAPI specification | The Hono application is running, the Scalar middleware is configured on the reference route, and the oRPC router initializes with at least 1 registered endpoint |
| documentation_rendered | endpoint_expanded | The developer clicks on an endpoint section to expand it and view the full request parameters, request body schema, and response schemas with Zod-derived type information | The endpoint entry exists in the rendered documentation and the schema viewer has loaded the JSON Schema representation for the selected endpoint |
| endpoint_expanded | api_client_open | The developer opens the built-in Scalar API client for the selected endpoint to compose a test request with parameters, headers, and a request body | The Scalar interface has rendered the API client panel with input fields corresponding to the selected endpoint's request schema |
| api_client_open | request_sent | The developer fills in the request fields and clicks the execute button to send the composed HTTP request to the running API server through the Scalar client | The developer has provided values for all required request parameters and the API server is reachable at the configured base URL |
| request_sent | response_displayed | The Scalar client receives the HTTP response from the API server including the status code, headers, and body and renders the response inline in the documentation interface | The API server returns an HTTP response within the client timeout period and the response body is valid JSON or text that the Scalar client can render |
| response_displayed | documentation_rendered | The developer closes the API client panel or navigates to a different endpoint section to continue browsing the documentation after reviewing the test response | The developer initiates a navigation action within the documentation interface to return to the endpoint listing or expand a different endpoint |
| documentation_rendered | documentation_rendered | The developer reloads the page after modifying API code and the Scalar middleware regenerates the documentation from the updated runtime OpenAPI specification reflecting the new or changed endpoints | The Hono application has restarted with the updated code and the oRPC router successfully initializes with the modified route definitions and Zod validators |

## Business Rules

- **Rule reference-endpoint-publicly-accessible:** IF a developer
    navigates to the `/api/reference` endpoint THEN the server serves
    the documentation page without requiring authentication — the
    count of authentication challenges returned for the reference
    endpoint equals 0
- **Rule documentation-generated-at-runtime:** IF the oRPC router
    definitions or Zod validators change in the API code THEN the
    documentation page reflects the changes on the next page load
    without requiring a manual build step — the count of manual build
    commands required to update the documentation equals 0
- **Rule schemas-derived-from-zod-validators:** IF a Zod validator
    is attached to an oRPC route handler THEN the OpenAPI
    specification includes the JSON Schema representation of that
    validator with required fields, optional fields, enums, and nested
    object shapes — the count of endpoints with missing schema
    definitions when a Zod validator is attached equals 0
- **Rule api-client-executes-against-running-server:** IF the
    developer clicks the execute button in the Scalar API client THEN
    the client sends the composed HTTP request to the running API
    server and displays the response inline — the count of requests
    that require switching to an external tool equals 0
- **Rule no-separate-spec-file-maintained:** IF the API schema is
    defined through oRPC router definitions and Zod validators THEN
    no separate OpenAPI specification file exists in the repository
    that requires manual synchronization — the count of standalone
    OpenAPI YAML or JSON files that duplicate the oRPC-generated
    specification equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Developer (any developer or API consumer who navigates to the publicly accessible API reference endpoint to browse endpoint documentation, inspect schemas, and test API calls through the Scalar interface) | Navigate to the `/api/reference` endpoint without authentication, browse all listed endpoints organized by resource, expand endpoint sections to view request and response schemas, use the built-in Scalar API client to compose and execute test requests, view the full HTTP response including status code headers and body | Cannot modify the API documentation content directly through the Scalar interface, cannot add or remove endpoints from the reference page without changing the underlying oRPC route definitions, cannot bypass Zod validation rules when sending test requests through the Scalar client | The developer sees all endpoints registered in the oRPC router regardless of whether those endpoints require authentication to call — the documentation lists all routes but calling authenticated endpoints through the Scalar client returns HTTP 401 unless valid credentials are provided in the request headers |

## Constraints

- The API reference page at `/api/reference` loads and renders the
    complete endpoint listing within 3000 ms of the browser request
    on a standard broadband connection — the count of milliseconds
    from request to fully rendered documentation equals 3000 or fewer.
- The OpenAPI specification generated by oRPC includes a schema
    definition for every route handler that has at least 1 Zod
    validator attached — the count of endpoints with attached Zod
    validators but missing schema definitions equals 0.
- The Scalar API client displays the HTTP response from a test
    request within 5000 ms of the developer clicking the execute
    button when the API server responds within its normal processing
    time — the count of milliseconds from click to response display
    equals 5000 or fewer.
- The reference endpoint returns HTTP 200 with the documentation page
    for unauthenticated requests — the count of HTTP 401 or HTTP 403
    responses returned for the `/api/reference` route equals 0.

## Acceptance Criteria

- [ ] The `/api/reference` endpoint returns HTTP 200 with the interactive documentation page when accessed without authentication — the count of authentication challenges returned equals 0
- [ ] The documentation page lists all endpoints registered in the oRPC router organized by resource — the count of registered endpoints missing from the documentation listing equals 0
- [ ] Each endpoint entry displays the HTTP method, path, description, request parameters, request body schema, and response schemas derived from Zod validators — the count of schema fields present equals the count defined in the Zod validators
- [ ] The Scalar API client sends a test request and displays the HTTP response inline including status code, headers, and body — the response panel is non-empty within 5000 ms of clicking execute
- [ ] The documentation page reflects API code changes after a page reload without requiring a manual build step — the count of manual build commands required to update documentation equals 0
- [ ] Required fields, optional fields, enums, and nested object shapes from Zod validators are visible in the schema viewer for each endpoint — the count of Zod-defined field constraints missing from the schema viewer equals 0
- [ ] The reference page loads and renders the complete endpoint listing within 3000 ms on a standard broadband connection — the count of milliseconds from request to render complete equals 3000 or fewer
- [ ] The developer can expand and collapse endpoint sections to focus on specific endpoints — the count of expandable endpoint sections equals at least 1 per registered endpoint
- [ ] Test requests sent through the Scalar client reach the running API server and return actual responses — the response panel displays an HTTP status code that is non-empty within 5000 ms of sending the request

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The developer navigates to `/api/reference` while the oRPC router has zero registered endpoints because all route handlers failed to initialize due to a missing dependency | The Scalar middleware serves the documentation page with an empty endpoint listing and no schema definitions — the page renders without errors but displays zero endpoints | The documentation page returns HTTP 200 and the rendered endpoint count equals 0 with no JavaScript console errors |
| The developer sends a test request through the Scalar client to an authenticated endpoint without providing valid credentials in the request headers | The Scalar client sends the request and displays the HTTP 401 response from the API server inline in the response panel — the documentation page continues to function and the developer can retry with valid credentials | The response panel displays HTTP status code 401 and the response body contains the authentication error message from the API |
| A Zod validator attached to a route handler references a circular schema definition that causes the OpenAPI generation to enter an infinite loop during runtime specification building | The oRPC OpenAPI generator detects the circular reference and either resolves it using JSON Schema `$ref` pointers or throws a bounded error — the documentation page serves the remaining valid endpoints while logging the circular schema warning | The server logs contain the circular schema detection entry and the documentation page renders with the non-circular endpoints present |
| The developer reloads the reference page immediately after changing API code but before the development server has finished restarting with the updated route definitions | The browser receives either a connection refused error while the server is restarting or the old documentation from the previous server instance if the request arrives before the restart completes — the developer reloads again after the server finishes restarting | The browser displays a connection error or the previous documentation version, and a subsequent reload after server restart shows the updated endpoint listing |
| The developer accesses the reference page from a mobile browser with a narrow viewport that does not support the full Scalar interactive layout | The Scalar interface renders a responsive layout that stacks the endpoint listing and schema viewer vertically — the developer can scroll to browse endpoints and the API client panel adapts to the narrow width | The documentation page renders without horizontal scrolling and all endpoint sections remain accessible through vertical scrolling |
| The API server is deployed to Cloudflare Workers and the Scalar client sends a test request that exceeds the Workers CPU time limit of 50 ms for the free tier | The Workers runtime terminates the request handler and returns an HTTP 503 or 524 error — the Scalar client displays this error response inline and the developer identifies the CPU limit as the cause from the error message | The response panel displays the HTTP 503 or 524 status code and the response body contains the Cloudflare Workers limit exceeded error |

## Failure Modes

- **Scalar middleware fails to serve the documentation page due to a configuration or initialization error in the Hono application**
    - **What happens:** The developer navigates to `/api/reference` and the server returns an HTTP 500 error instead of the interactive documentation page because the Scalar middleware failed to initialize during the Hono application startup due to a missing configuration parameter or incompatible middleware version.
    - **Source:** A missing or incorrect Scalar middleware configuration parameter in the Hono application setup, an incompatible version of the Scalar Hono plugin that does not match the installed Hono version, or a runtime error during the middleware initialization sequence that prevents the documentation handler from registering.
    - **Consequence:** The developer cannot access the interactive API documentation through the browser and must fall back to reading the raw oRPC schema output or inspecting the Zod validators directly in the source code to understand the available endpoints and their schemas.
    - **Recovery:** The server logs the Scalar middleware initialization error with the specific configuration parameter or version mismatch details, and the developer alerts the team to fix the middleware configuration and redeploy the application.

- **oRPC router fails to generate the OpenAPI specification due to a malformed Zod validator on one or more route handlers**
    - **What happens:** The oRPC OpenAPI generator encounters a Zod validator that cannot be converted to a valid JSON Schema representation — such as a validator using a custom Zod transform that has no JSON Schema equivalent — and throws a runtime error that prevents the entire specification from being generated.
    - **Source:** A route handler uses a Zod validator with a `.transform()`, `.refine()`, or `.pipe()` method that produces a type the oRPC OpenAPI generator cannot serialize to JSON Schema, or a Zod schema references an unregistered custom type that the generator does not recognize.
    - **Consequence:** The Scalar documentation page either returns an HTTP 500 error because the entire OpenAPI specification failed to generate, or renders with missing schema details for the affected endpoints depending on whether the generator fails completely or gracefully omits the problematic schema.
    - **Recovery:** The server logs the specific Zod validator compilation error including the route path and validator name, and the developer falls back to inspecting the Zod validators in the source code to understand the endpoint schema until the incompatible validator is fixed or replaced.

- **Scalar API client test request fails because the API server is unreachable or the development server has stopped running**
    - **What happens:** The developer fills in request parameters and clicks the execute button in the Scalar API client, but the HTTP request fails with a connection refused or network timeout error because the API server is not running or has become unreachable due to a network interruption.
    - **Source:** The development server was stopped manually or crashed due to an unhandled error, the Cloudflare Workers deployment is in a failed state, or a network proxy or firewall blocks the request from the Scalar client to the API server.
    - **Consequence:** The Scalar client displays a connection error in the response panel instead of the expected HTTP response, and the developer cannot verify the endpoint behavior through the built-in test client until the server is restarted or the network issue is resolved.
    - **Recovery:** The Scalar client displays the connection error with the network failure details in the response panel, and the developer retries the test request after restarting the development server or restoring network connectivity to the API endpoint.

## Declared Omissions

- This specification does not define the oRPC router configuration, route handler implementation patterns, or Zod validator authoring conventions used to build the API endpoints that produce the OpenAPI specification
- This specification does not cover the Cloudflare Workers deployment pipeline, environment configuration, or production hosting setup that serves the API reference endpoint in non-development environments
- This specification does not address API versioning strategy, endpoint deprecation notices, or how multiple API versions are represented in the documentation when the application supports concurrent API versions
- This specification does not define authentication mechanisms for the API endpoints themselves — the reference page is public but individual endpoint calls through the Scalar client require the same authentication as direct API calls

## Related Specifications

- [user-subscribes-to-a-plan](user-subscribes-to-a-plan.md) — defines
    the subscription flow whose API endpoints for plan listing,
    checkout initiation, and webhook processing are documented in the
    API reference and testable through the Scalar client interface
- [user-manages-billing-portal](user-manages-billing-portal.md) —
    defines the billing portal management flow whose API endpoints for
    portal access, payment history, and subscription cancellation are
    documented in the API reference page
- [session-lifecycle](session-lifecycle.md) — defines the session
    management API endpoints whose authentication and refresh behaviors
    are documented in the API reference and relevant when testing
    authenticated endpoints through the Scalar client
- [visitor-signs-up](visitor-signs-up.md) — defines the user
    registration API endpoints whose request schemas and response
    formats are documented in the API reference and testable through
    the built-in Scalar API client
