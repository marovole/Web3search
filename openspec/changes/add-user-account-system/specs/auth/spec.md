## ADDED Requirements

### Requirement: User Registration
Users SHALL be able to register new accounts using email and password.

#### Scenario: Successful registration
- **WHEN** user provides valid email and password meeting requirements
- **THEN** a new user account is created
- **AND** 201 status code is returned with user basic information (excluding password)
- **AND** email must be valid format and unique in database
- **AND** password must be minimum 8 characters with letters and numbers

#### Scenario: Email already exists
- **WHEN** user attempts to register with an existing email
- **THEN** 400 status code is returned
- **AND** error message "Email already registered" is returned

#### Scenario: Weak password
- **WHEN** user provides password that doesn't meet requirements (e.g., less than 8 characters)
- **THEN** 400 status code is returned
- **AND** detailed password requirements are explained

#### Scenario: Invalid email format
- **WHEN** user provides invalid email format
- **THEN** 400 status code is returned
- **AND** error message "Invalid email format" is returned

### Requirement: User Login
Users SHALL be able to login using email and password to obtain JWT tokens.

#### Scenario: Successful login
- **WHEN** user provides correct email and password
- **THEN** 200 status code is returned
- **AND** Access Token and Refresh Token are returned
- **AND** Access Token is JWT format containing user_id and exp, valid for 24 hours
- **AND** Refresh Token is random string stored in HttpOnly Cookie, valid for 30 days

#### Scenario: Incorrect password
- **WHEN** user provides incorrect password
- **THEN** 401 status code is returned
- **AND** error message "Invalid credentials" is returned

#### Scenario: User not found
- **WHEN** user provides non-existent email
- **THEN** 401 status code is returned
- **AND** error message "Invalid credentials" is returned (to avoid revealing user existence)

#### Scenario: Account disabled
- **WHEN** user account is marked as disabled
- **THEN** 403 status code is returned
- **AND** error message "Account disabled" is returned

### Requirement: Token Refresh
Users SHALL be able to refresh Access Token using Refresh Token without re-login.

#### Scenario: Successful token refresh
- **WHEN** user provides valid Refresh Token (read from Cookie)
- **THEN** 200 status code is returned
- **AND** new Access Token is returned
- **AND** Refresh Token is automatically renewed, extending 30-day validity

#### Scenario: Invalid refresh token
- **WHEN** user provides invalid or expired Refresh Token
- **THEN** 401 status code is returned
- **AND** error message "Invalid refresh token" is returned

#### Scenario: Revoked refresh token
- **WHEN** user logs out and Refresh Token is revoked
- **THEN** 401 status code is returned
- **AND** error message "Refresh token revoked" is returned

### Requirement: Password Reset
Users SHALL be able to reset forgotten passwords via email.

#### Scenario: Request password reset
- **WHEN** user provides registered email
- **THEN** 200 status code is returned
- **AND** password reset email is sent (even if email doesn't exist, to avoid leaking information)
- **AND** reset Token is generated and stored in database, valid for 1 hour

#### Scenario: Reset password
- **WHEN** user provides valid reset Token and new password
- **THEN** user password is updated
- **AND** 200 status code is returned
- **AND** Token is immediately invalidated after use

#### Scenario: Expired reset token
- **WHEN** user provides expired reset Token (>1 hour)
- **THEN** 400 status code is returned
- **AND** error message "Reset token expired" is returned

### Requirement: Logout
Users SHALL be able to logout, revoking Refresh Token.

#### Scenario: Successful logout
- **WHEN** user is logged in
- **THEN** Refresh Token is revoked
- **AND** Cookie is cleared
- **AND** 200 status code is returned

#### Scenario: Logout without authentication
- **WHEN** user is not logged in or Token is invalid
- **THEN** 401 status code is returned
- **AND** error message "Not authenticated" is returned

### Requirement: Frontend Authentication UI
The system SHALL provide user interface components for authentication flows.

#### Scenario: Login form
- **WHEN** user navigates to login page
- **THEN** login form is displayed with email and password fields
- **AND** form validation provides immediate feedback
- **AND** loading state prevents duplicate submissions
- **AND** successful login redirects to home page or original destination

#### Scenario: Registration form
- **WHEN** user navigates to registration page
- **THEN** registration form is displayed with email, password, confirm password, and optional username fields
- **AND** password strength validation is enforced
- **AND** successful registration automatically logs in user and redirects

#### Scenario: Forgot password form
- **WHEN** user navigates to forgot password page
- **THEN** form is displayed to request password reset email
- **AND** success message is shown after submission
- **AND** link to return to login is provided

#### Scenario: Reset password form
- **WHEN** user navigates to reset password page with valid token
- **THEN** form is displayed to enter new password
- **AND** token validation occurs before form is shown
- **AND** successful reset redirects to login page
