# Subscription & Billing Specification

## ADDED Requirements

### Requirement: Subscription Plans

The system SHALL offer three subscription tiers with differentiated features and quotas.

#### Scenario: Free tier limits

- **GIVEN** a user on the Free plan
- **WHEN** the user attempts to use features
- **THEN** the user is limited to:
  - 5 tokens in watchlist
  - 3 active price alerts
  - 3 deep research per day
  - Basic risk scoring only
  - 7-day data retention
  - Browser push notifications only

#### Scenario: Pro tier features

- **GIVEN** a user on the Pro plan ($9.9/month)
- **WHEN** the user accesses the platform
- **THEN** the user has access to:
  - 50 tokens in watchlist
  - 30 active price alerts
  - 10 whale tracking tokens
  - 20 deep research per day
  - 10 conversational agent interactions per month
  - Real-time risk monitoring with history
  - Weekly portfolio diagnostics
  - 3 opportunity recommendations per week
  - 90-day data retention
  - Push + Email notifications

#### Scenario: Team tier features

- **GIVEN** a user on the Team plan ($29.9/month)
- **WHEN** the user accesses the platform
- **THEN** the user has access to:
  - Unlimited watchlist
  - Unlimited price alerts
  - Unlimited whale tracking
  - Unlimited deep research
  - 100 conversational agent interactions per month
  - All Pro features plus custom alert sources
  - Daily portfolio diagnostics
  - Unlimited opportunity recommendations
  - 365-day data retention
  - Push + Email + Webhook notifications
  - API access for integrations

### Requirement: Subscription Checkout

The system SHALL integrate with Stripe for payment processing.

#### Scenario: User initiates upgrade

- **GIVEN** a Free user wanting to upgrade to Pro
- **WHEN** the user clicks "Upgrade to Pro"
- **THEN** the system calls Stripe to create a Checkout Session
- **AND** the user is redirected to Stripe's hosted checkout page
- **AND** the checkout includes the correct price and billing interval

#### Scenario: Successful payment

- **GIVEN** a user completes payment on Stripe checkout
- **WHEN** Stripe sends `checkout.session.completed` webhook
- **THEN** the system updates `user_profiles.plan` to "pro"
- **AND** the system updates `user_profiles.subscription_id`
- **AND** the system updates `user_profiles.subscription_status` to "active"
- **AND** the user's quotas are immediately expanded

#### Scenario: Payment fails

- **GIVEN** a user's payment fails during checkout
- **WHEN** the user is redirected back to the app
- **THEN** the system displays an error message
- **AND** the user remains on their current plan
- **AND** no subscription is created

### Requirement: Subscription Management

The system SHALL allow users to manage their subscription through Stripe Customer Portal.

#### Scenario: User accesses billing portal

- **GIVEN** an authenticated user with an active subscription
- **WHEN** the user clicks "Manage Subscription"
- **THEN** the system creates a Stripe Customer Portal session
- **AND** the user is redirected to the portal
- **AND** the user can update payment method, cancel, or change plan

#### Scenario: User cancels subscription

- **GIVEN** a Pro user who cancels via Customer Portal
- **WHEN** Stripe sends `customer.subscription.deleted` webhook
- **THEN** the system updates `subscription_status` to "cancelled"
- **AND** the system sets `subscription_ends_at` to period end date
- **AND** the user retains Pro access until period end
- **AND** after period end, the user is downgraded to Free

#### Scenario: Subscription renewal

- **GIVEN** a Pro user with upcoming renewal
- **WHEN** Stripe successfully charges the renewal
- **THEN** the system receives `invoice.paid` webhook
- **AND** the subscription continues without interruption

### Requirement: Quota Management

The system SHALL enforce usage quotas based on subscription tier.

#### Scenario: Check quota before action

- **GIVEN** a Free user who has used 3 deep research today
- **WHEN** the user attempts a 4th deep research
- **THEN** the system returns HTTP 429 (Too Many Requests)
- **AND** the response includes `quota_exceeded` error code
- **AND** the response includes upgrade prompt

#### Scenario: View current quota usage

- **GIVEN** an authenticated user
- **WHEN** the user calls `GET /api/v1/users/quota`
- **THEN** the system returns current usage and limits:
  - `daily_deep_research_used` / `daily_deep_research_limit`
  - `monthly_agent_conversations_used` / `monthly_agent_conversations_limit`
  - `watchlist_count` / `max_watchlist`
  - `active_alerts_count` / `max_alerts`

#### Scenario: Daily quota reset

- **GIVEN** a user with exhausted daily quota
- **WHEN** the daily reset Cron runs at midnight UTC
- **THEN** the system resets `daily_deep_research_used` to 0
- **AND** the system updates `daily_reset_at` to next midnight

#### Scenario: Monthly quota reset

- **GIVEN** a user with exhausted monthly quota
- **WHEN** the monthly reset Cron runs on the 1st
- **THEN** the system resets `monthly_agent_conversations_used` to 0
- **AND** the system updates `monthly_reset_at` to next month

### Requirement: Webhook Security

The system SHALL verify Stripe webhook signatures to prevent tampering.

#### Scenario: Valid webhook received

- **GIVEN** a webhook request from Stripe with valid signature
- **WHEN** the system receives the webhook at `/api/v1/billing/webhook`
- **THEN** the system verifies the signature using `STRIPE_WEBHOOK_SECRET`
- **AND** the system processes the event
- **AND** the system returns HTTP 200

#### Scenario: Invalid webhook signature

- **GIVEN** a webhook request with invalid or missing signature
- **WHEN** the system receives the request
- **THEN** the system rejects the request with HTTP 400
- **AND** the system logs the security event

#### Scenario: Duplicate webhook event

- **GIVEN** Stripe retries a webhook that was already processed
- **WHEN** the system receives the duplicate event
- **THEN** the system recognizes it via event ID
- **AND** the system returns HTTP 200 (idempotent)
- **AND** the system does not process it again
