[← Back to Index](README.md)

# App Admin Changes a User's Role

## The app admin selects the user and changes their role

The app admin navigates to the user management section of the app admin dashboard and selects the user whose role needs to change. On the user's profile detail view, the app admin locates the role dropdown, which displays the user's current role. The app admin clicks the dropdown and selects the new role, such as changing from "user" to "admin" or from "admin" to "user".

## The system updates the role

When the app admin confirms the role change, the client calls `authClient.admin.setRole({ userId, role })` with the target user's ID and the newly selected role. The server verifies the caller has the app admin role (`user.role = "admin"`), then updates the target user's `role` field in the database to the new value. The change takes effect immediately at the data level.

## The user experiences the new role

If the target user is currently signed in, their next API request will reflect the updated role. The server reads the user's role from the database on each request, so no session invalidation or re-authentication is required. The user will see their permissions change in real time: if promoted to admin, admin-only sections of the dashboard become accessible on the next navigation; if demoted from admin, those sections become inaccessible.
