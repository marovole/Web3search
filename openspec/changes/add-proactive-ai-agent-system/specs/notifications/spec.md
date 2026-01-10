# Notifications Specification

## ADDED Requirements

### Requirement: Browser Push Notifications

The system SHALL send push notifications to users via the Web Push API even when the browser is closed.

#### Scenario: User subscribes to push notifications

- **GIVEN** an authenticated user who has not subscribed to push
- **WHEN** the user clicks "Enable Notifications" and grants browser permission
- **THEN** the browser generates a push subscription object
- **AND** the system stores the subscription in `push_subscriptions` table
- **AND** the system sends a test notification to confirm

#### Scenario: User denies push permission

- **GIVEN** a user who denies browser notification permission
- **WHEN** the permission dialog is dismissed with "Block"
- **THEN** the system gracefully handles the rejection
- **AND** the system displays in-app notifications as fallback
- **AND** the system shows option to enable in browser settings

#### Scenario: Send push notification

- **GIVEN** an agent task triggers a notification for a user
- **WHEN** the system creates the notification
- **THEN** the system queries user's active `push_subscriptions`
- **AND** the system sends push to all active endpoints via web-push library
- **AND** the system records delivery status in `notifications.channels_succeeded`

#### Scenario: Push endpoint becomes invalid

- **GIVEN** a push subscription that has expired or been revoked
- **WHEN** the system attempts to send a push notification
- **THEN** the push service returns 410 Gone
- **AND** the system marks the subscription as `active = false`
- **AND** the system does not retry to that endpoint

#### Scenario: User unsubscribes from push

- **GIVEN** a user with active push subscriptions
- **WHEN** the user calls `DELETE /api/v1/push/subscribe`
- **THEN** the system deactivates all push subscriptions for the user
- **AND** the Service Worker unregisters the subscription

### Requirement: Notification Center

The system SHALL maintain a history of notifications accessible through the UI.

#### Scenario: List notifications

- **GIVEN** an authenticated user with notifications
- **WHEN** the user calls `GET /api/v1/notifications`
- **THEN** the system returns paginated list of notifications
- **AND** notifications are ordered by `created_at` descending
- **AND** each notification includes type, severity, title, body, and read status

#### Scenario: Mark notification as read

- **GIVEN** an authenticated user with unread notifications
- **WHEN** the user calls `PATCH /api/v1/notifications/:id/read`
- **THEN** the system updates `read = true` and `read_at = NOW()`
- **AND** the unread count decreases

#### Scenario: Mark all as read

- **GIVEN** an authenticated user with multiple unread notifications
- **WHEN** the user calls `POST /api/v1/notifications/read-all`
- **THEN** the system updates all unread notifications to read
- **AND** the unread count becomes 0

#### Scenario: Delete notification

- **GIVEN** an authenticated user with a notification
- **WHEN** the user calls `DELETE /api/v1/notifications/:id`
- **THEN** the system deletes the notification record
- **AND** the notification no longer appears in the list

### Requirement: Notification Types

The system SHALL support multiple notification types with appropriate severity levels.

#### Scenario: Price alert notification

- **GIVEN** a price alert condition is met (e.g., SOL < $100)
- **WHEN** the agent triggers the notification
- **THEN** the notification is created with:
  - `type = "alert"`
  - `severity = "warning"`
  - `title = "价格预警: SOL"`
  - `body = "SOL 价格已跌破 $100，当前价格 $99.50 (-5.2%)"`
  - `data = { token: "SOL", price: 99.50, threshold: 100, change_pct: -5.2 }`

#### Scenario: Risk alert notification

- **GIVEN** a risk score increases significantly
- **WHEN** the risk monitor agent triggers the notification
- **THEN** the notification is created with:
  - `type = "alert"`
  - `severity = "critical"`
  - `title = "风险预警: XYZ"`
  - `body = "XYZ 的风险评分从 30 上升到 65，新增红旗: 巨鲸抛售"`

#### Scenario: Report notification

- **GIVEN** a weekly portfolio report is generated
- **WHEN** the portfolio health agent completes analysis
- **THEN** the notification is created with:
  - `type = "report"`
  - `severity = "info"`
  - `title = "每周持仓诊断报告已生成"`
  - `body = "您的投资组合健康评分: 72/100。点击查看详细报告。"`
  - `data = { report_id: "xxx", health_score: 72 }`

#### Scenario: Insight notification

- **GIVEN** an opportunity is discovered matching user preferences
- **WHEN** the opportunity agent identifies a recommendation
- **THEN** the notification is created with:
  - `type = "insight"`
  - `severity = "info"`
  - `title = "发现投资机会: ABC Protocol"`
  - `body = "基于您对 DeFi 的偏好，发现 ABC 协议符合您的投资风格"`

### Requirement: Notification Delivery

The system SHALL ensure reliable notification delivery with appropriate rate limiting.

#### Scenario: Notification batching

- **GIVEN** multiple alerts trigger within a short period
- **WHEN** 5 price alerts trigger within 1 minute for the same user
- **THEN** the system batches them into a single notification
- **AND** the notification summarizes: "5 个价格预警触发"
- **AND** the user is not spammed with individual notifications

#### Scenario: Quiet hours

- **GIVEN** a user has configured quiet hours (e.g., 10 PM - 8 AM)
- **WHEN** a non-critical notification triggers during quiet hours
- **THEN** the system delays the push notification until quiet hours end
- **AND** the notification is still recorded in the database
- **AND** critical notifications bypass quiet hours

#### Scenario: Notification expiry

- **GIVEN** a time-sensitive notification (e.g., price alert)
- **WHEN** the notification is created
- **THEN** the system sets `expires_at` based on notification type
- **AND** expired notifications are not displayed prominently
- **AND** expired notifications may be auto-cleaned after retention period

### Requirement: Unread Badge

The system SHALL display unread notification count in the UI header.

#### Scenario: Real-time unread count

- **GIVEN** a user is viewing the dashboard
- **WHEN** a new notification arrives
- **THEN** the unread badge updates immediately (via polling or Supabase Realtime)
- **AND** the badge shows the current unread count

#### Scenario: Badge limit display

- **GIVEN** a user has 100+ unread notifications
- **WHEN** the badge is displayed
- **THEN** the badge shows "99+" instead of the exact number
