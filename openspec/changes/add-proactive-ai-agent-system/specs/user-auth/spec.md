# User Authentication Specification

## ADDED Requirements

### Requirement: User Registration

The system SHALL allow new users to register using email and password through Supabase Auth.

#### Scenario: Successful email registration

- **GIVEN** a visitor with a valid email address
- **WHEN** the visitor submits registration form with email and password
- **THEN** the system creates a new user in Supabase Auth
- **AND** the system creates a corresponding `user_profiles` record
- **AND** the system creates a `user_quotas` record with Free tier limits
- **AND** the system sends a confirmation email
- **AND** the user is redirected to the dashboard

#### Scenario: Registration with existing email

- **GIVEN** a visitor using an email already registered
- **WHEN** the visitor attempts to register
- **THEN** the system returns an error indicating email is taken
- **AND** the system suggests password reset if they already have an account

#### Scenario: Registration with weak password

- **GIVEN** a visitor with a password less than 8 characters
- **WHEN** the visitor attempts to register
- **THEN** the system rejects the registration
- **AND** the system displays password requirements

### Requirement: User Login

The system SHALL authenticate users and issue JWT tokens for API access.

#### Scenario: Successful login

- **GIVEN** a registered user with confirmed email
- **WHEN** the user submits correct email and password
- **THEN** the system issues a JWT token
- **AND** the system stores the session in local storage
- **AND** the user is redirected to the dashboard

#### Scenario: Login with incorrect credentials

- **GIVEN** a user with incorrect password
- **WHEN** the user attempts to login
- **THEN** the system returns authentication error
- **AND** the system does not reveal whether email exists

#### Scenario: Login with unconfirmed email

- **GIVEN** a registered user who has not confirmed email
- **WHEN** the user attempts to login
- **THEN** the system prompts to confirm email first
- **AND** the system offers to resend confirmation email

### Requirement: Session Management

The system SHALL manage user sessions with automatic refresh and secure logout.

#### Scenario: Token refresh

- **GIVEN** a logged-in user with a token expiring soon
- **WHEN** the user makes an API request
- **THEN** the system automatically refreshes the token
- **AND** the new token is stored in local storage

#### Scenario: User logout

- **GIVEN** a logged-in user
- **WHEN** the user clicks logout
- **THEN** the system invalidates the session
- **AND** the system clears local storage
- **AND** the user is redirected to the login page

### Requirement: User Profile Management

The system SHALL allow users to view and update their profile settings.

#### Scenario: View user profile

- **GIVEN** an authenticated user
- **WHEN** the user calls `GET /api/v1/users/profile`
- **THEN** the system returns user profile including plan, preferences, and settings

#### Scenario: Update notification preferences

- **GIVEN** an authenticated user
- **WHEN** the user updates notification settings via `PATCH /api/v1/users/profile`
- **THEN** the system updates the `notification_settings` JSONB field
- **AND** the system returns the updated profile

#### Scenario: Update risk preference

- **GIVEN** an authenticated user
- **WHEN** the user changes risk preference to "aggressive"
- **THEN** the system updates `risk_preference` field
- **AND** agent recommendations adjust accordingly

### Requirement: Protected Routes

The system SHALL protect all user-specific endpoints with authentication.

#### Scenario: Access protected endpoint without token

- **GIVEN** an unauthenticated request to `/api/v1/watchlist`
- **WHEN** the request is made without Authorization header
- **THEN** the system returns HTTP 401 Unauthorized
- **AND** the response includes WWW-Authenticate header

#### Scenario: Access protected endpoint with expired token

- **GIVEN** a request with an expired JWT token
- **WHEN** the request is made to a protected endpoint
- **THEN** the system returns HTTP 401 with "token_expired" error code
- **AND** the client should attempt token refresh

#### Scenario: Access another user's data

- **GIVEN** an authenticated user A
- **WHEN** user A attempts to access user B's watchlist via ID manipulation
- **THEN** the RLS policy blocks the access
- **AND** the system returns HTTP 404 (not 403, for security)
