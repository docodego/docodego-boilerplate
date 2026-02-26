# User Signs In on Mobile

## Sign-In Screen

The sign-in screen presents an email input field with a "Send code" button and an SSO option below it. There is no passkey option — WebAuthn is not reliably supported on React Native, so the mobile app omits it entirely. The available sign-in methods are email OTP, SSO, and anonymous guest access. The `react-native-keyboard-controller` manages keyboard appearance so that the input fields shift smoothly upward when the keyboard opens, preventing content from being obscured.

## Email OTP Flow

The user types their email address and taps "Send code." The app calls `authClient.emailOtp.sendVerificationOtp({ email, type: "sign-in" })` to request a one-time passcode. The server generates a 6-digit code and sends it to the provided email address. The UI transitions to a code entry step with six individual digit inputs. As the user types each digit, focus advances to the next input. Pasting a full 6-digit code fills all inputs at once. Once complete, the app calls `authClient.signIn.emailOtp({ email, otp })` to verify. The keyboard controller keeps the code inputs visible and accessible throughout this interaction.

## SSO Flow

If the user taps the SSO option, the app opens the system browser to the web sign-in page for the configured identity provider. The user completes authentication in the browser. After successful sign-in, the identity provider redirects back to the app via a deep link that Expo Router intercepts. The session token returned from the OAuth flow is stored securely for subsequent use.

## Token Storage and Navigation

On successful authentication through any method, the session token is persisted via `expo-secure-store`, which stores it in the device's encrypted keychain. This token survives app restarts without requiring the user to sign in again. The app then navigates the user forward — if the user belongs to at least one organization, they land on their active organization's dashboard. If they have no organizations, they are directed to the onboarding flow to create their first one. An anonymous guest session follows the same navigation logic, with the option to upgrade to a full account later.