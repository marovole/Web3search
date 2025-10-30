# user-management Specification

## Purpose
TBD - created by archiving change add-user-account-system. Update Purpose after archive.
## Requirements
### Requirement: User Profile Management
Users SHALL be able to view and update their personal information.

#### Scenario: Get current user information
- **WHEN** user is logged in
- **THEN** GET /api/v1/users/me returns 200 status code and user information
- **AND** returns id, email, username, created_at etc.
- **AND** password_hash is not returned

#### Scenario: Update user information
- **WHEN** user is logged in and provides new username or other information
- **THEN** PUT /api/v1/users/me updates user information
- **AND** returns 200 status code and updated information
- **AND** email and password cannot be modified through this endpoint

#### Scenario: Unauthorized access
- **WHEN** user is not logged in or Token is invalid
- **THEN** GET /api/v1/users/me returns 401 status code
- **AND** error message "Not authenticated" is returned

### Requirement: User Preferences Management
Users SHALL be able to manage personal preferences with cross-device synchronization.

#### Scenario: Get preferences
- **WHEN** user is logged in
- **THEN** GET /api/v1/users/me/preferences returns 200 status code and complete preferences JSON
- **AND** if user has no preferences, system default preferences are returned

#### Scenario: Update preferences
- **WHEN** user is logged in and provides preference updates (partial or full)
- **THEN** PUT /api/v1/users/me/preferences merges and updates preferences
- **THEN** returns 200 status code and updated preferences
- **AND** partial updates only modify provided fields, other fields remain unchanged

#### Scenario: Preferences validation
- **WHEN** user provides invalid preference values
- **THEN** PUT /api/v1/users/me/preferences returns 400 status code
- **AND** validation error details are returned
- **AND** theme must be "light"/"dark"/"system", language must be supported language code

#### Scenario: Cross-device synchronization
- **WHEN** user updates preferences on device A
- **THEN** when user logs in on device B and fetches preferences
- **THEN** device B receives same preferences as device A

### Requirement: Account Deletion
Users SHALL be able to delete their accounts and all associated data.

#### Scenario: Delete account
- **WHEN** user is logged in
- **THEN** DELETE /api/v1/users/me soft deletes user account (marks as deleted)
- **AND** all associated data is deleted
- **AND** returns 200 status code
- **AND** associated data includes conversations, reports, preferences, sessions
- **AND** soft delete sets user.deleted_at to current time, retains email for 30 days (for recovery)

#### Scenario: Confirm deletion
- **WHEN** user requests account deletion
- **THEN** DELETE /api/v1/users/me requires password confirmation
- **AND** password is verified before deletion is executed

#### Scenario: Export data before deletion
- **WHEN** user requests account deletion
- **THEN** user can first call POST /api/v1/users/me/export-data to export data
- **AND** JSON file containing all user data is returned
- **AND** then deletion is allowed

### Requirement: Data Export
Users SHALL be able to export all their data (GDPR compliance).

#### Scenario: Export user data
- **WHEN** user is logged in
- **THEN** POST /api/v1/users/me/export-data returns 200 status code and JSON file
- **AND** contains all user data including user info, conversation history, report list, preferences, usage statistics

#### Scenario: Export format
- **THEN** format is JSON, UTF-8 encoded
- **AND** structure is hierarchical for easy reading and processing
- **AND** if data is too large, pagination or compression options are provided

#### Scenario: Export history records
- **WHEN** user has large amount of history records
- **THEN** POST /api/v1/users/me/export-data returns complete conversation and report data
- **AND** includes timestamps and metadata

