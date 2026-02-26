[← Back to Index](README.md)

# App Admin Creates a User

## The app admin opens the user creation form

The app admin navigates to the user management section of the app admin dashboard and clicks the "Create user" button. This opens a form with fields for the new user's details: name, email address, password, and role. This flow exists for situations where the normal self-service signup process is not appropriate, such as provisioning accounts for team members, creating test accounts, or onboarding users who need to be set up by an app admin.

## The app admin fills in user details and submits

The app admin enters the required information into the form. The name and email fields accept standard text input, the password field requires a value that meets the application's password requirements, and the role dropdown lets the app admin assign either "user" or "admin" as the initial role. Once all fields are filled, the app admin submits the form. The client calls `authClient.admin.createUser()` with the provided data.

## The server creates the user account

The server receives the request, verifies the caller has the app admin role (`user.role = "admin"`), and creates the new user record in the database with the provided name, email, password, and role. The password is hashed before storage, following the same process as the normal signup flow. The new user immediately appears in the user management list. No welcome email or verification step is triggered by this admin-created flow. The created user can now sign in with the email and password the app admin provided.
