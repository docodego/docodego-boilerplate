[← Back to Index](README.md)

# Developer Views API Reference

## Navigating to the Reference

A developer or API consumer navigates to the API reference endpoint (e.g., `/api/reference`) in their browser. No authentication is required to view the documentation — the endpoint is publicly accessible so that both internal developers and external API consumers can browse the available endpoints without needing credentials.

## Interactive Documentation

The Scalar Hono API Reference middleware serves an interactive documentation page at this route. The page is auto-generated from the OpenAPI specification produced by oRPC, which derives its schema definitions directly from the Zod validators used across the API's route handlers. This means the documentation always reflects the actual validation rules enforced by the API — there is no separate spec file to maintain or keep in sync.

## Browsing Endpoints and Schemas

The developer can browse all endpoints organized by resource. Each endpoint displays its HTTP method, path, description, request parameters, request body schema, and response schemas with their Zod-derived types. Required fields, optional fields, enums, and nested object shapes are all visible in the schema viewer. The developer can expand and collapse sections to focus on the endpoints relevant to their integration.

## Testing API Calls

The Scalar interface includes a built-in API client that allows the developer to test API calls directly from the browser. The developer can fill in request parameters, set headers, provide a request body, and execute the call against the running server. The response — including status code, headers, and body — is displayed inline. This eliminates the need to switch to a separate tool like Postman or curl for quick exploratory testing.

## Automatic Updates

Because the OpenAPI spec is generated at runtime from the oRPC router definitions and their Zod schemas, the reference page updates automatically whenever the API schema changes. Adding a new endpoint, modifying a request body validator, or changing a response shape in the code is immediately reflected in the documentation the next time the page is loaded. There is no build step or manual regeneration required.
