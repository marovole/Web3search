## ADDED Requirements

### Requirement: Data Migration Detection
The system SHALL detect localStorage data and prompt users to migrate after login.

#### Scenario: Detect local data
- **WHEN** user logs in successfully and frontend detects localStorage
- **THEN** migration prompt dialog is displayed asking user if they want to migrate data
- **AND** detects web3search_report_history, web3search_watchlist, web3search_preferences

#### Scenario: No local data
- **WHEN** user logs in successfully but localStorage is empty
- **THEN** no migration prompt is shown
- **AND** user is taken directly to main interface

#### Scenario: Partial data exists
- **WHEN** user only has partial data (e.g., only preferences)
- **THEN** only prompt migration for existing data types

### Requirement: Conversation History Migration
The system SHALL migrate conversation history from localStorage to database, associated with user account.

#### Scenario: Migrate conversation history
- **WHEN** user confirms migration and localStorage contains conversation history
- **THEN** POST /api/v1/users/me/migrate-data is called with conversations data
- **AND** new Conversation records are created with user_id association
- **AND** 201 status code is returned with migration results
- **AND** localStorage JSON is parsed and required fields are validated
- **AND** duplicates are skipped or updated if session_id already exists

#### Scenario: Migrate messages
- **WHEN** conversation history contains messages array
- **THEN** Message records are automatically created when migrating conversations
- **AND** all messages are correctly associated with corresponding Conversation
- **AND** message chronological order is preserved

#### Scenario: Handle migration failures
- **WHEN** some conversation data has invalid format during migration
- **THEN** invalid data is skipped and migration continues for other data
- **AND** partial success result and error list are returned

### Requirement: Report History Migration
The system SHALL migrate report history from localStorage to database.

#### Scenario: Migrate report history
- **WHEN** user confirms migration and localStorage contains report history
- **THEN** POST /api/v1/users/me/migrate-data is called with reports data
- **AND** new Report records are created with user_id association
- **AND** 201 status code is returned
- **AND** report format and required fields are validated

#### Scenario: Associate reports with conversations
- **WHEN** report contains conversation_id or session_id
- **THEN** corresponding Conversation is looked up during migration
- **AND** if conversation is found, association is established; otherwise independent report is created

#### Scenario: Report deduplication
- **WHEN** database already contains report with same share_id
- **THEN** duplicate report is skipped and no new record is created

### Requirement: Preferences Migration
The system SHALL migrate user preferences from localStorage to database.

#### Scenario: Migrate preferences
- **WHEN** user confirms migration and localStorage contains preferences
- **THEN** POST /api/v1/users/me/migrate-data is called with preferences data
- **AND** user preferences are updated
- **AND** 200 status code is returned
- **AND** if database already has preferences, localStorage values are merged (localStorage takes priority)

#### Scenario: Preferences validation
- **WHEN** localStorage contains invalid preference values
- **THEN** invalid values are filtered during migration
- **AND** only valid preferences are migrated

#### Scenario: Default value filling
- **WHEN** localStorage is missing some preference fields
- **THEN** system default values are used to fill missing fields

### Requirement: Watchlist Migration
The system SHALL migrate watchlist from localStorage to database (if implemented).

#### Scenario: Migrate watchlist
- **WHEN** user confirms migration and localStorage contains watchlist
- **THEN** POST /api/v1/users/me/migrate-data is called with watchlist data
- **AND** user watchlist records are created
- **AND** 201 status code is returned
- **AND** if backend doesn't implement watchlist feature, this type is skipped

#### Scenario: Watchlist deduplication
- **WHEN** database already contains same watchlist items
- **THEN** duplicate items are skipped and no new records are created

### Requirement: Migration Progress and Feedback
The system SHALL provide migration progress feedback and result statistics.

#### Scenario: Display migration progress
- **WHEN** user starts migrating large amounts of data
- **THEN** progress bar and current migration data type are displayed
- **AND** progress is updated when each data type migration completes

#### Scenario: Migration result statistics
- **WHEN** migration completes
- **THEN** backend returns migration results
- **AND** frontend displays success and failure count statistics
- **AND** statistics include number of conversations, reports, and preferences successfully migrated

#### Scenario: Post-migration cleanup
- **WHEN** migration completes successfully
- **THEN** user can optionally clean migrated data from localStorage
- **AND** migrated data is retained in localStorage for 7 days to allow recovery
