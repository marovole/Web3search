# Agent System Specification

## ADDED Requirements

### Requirement: Agent Task Management

The system SHALL provide a complete lifecycle management for AI Agent tasks, including creation, execution, monitoring, and termination.

#### Scenario: User creates a price alert agent

- **GIVEN** an authenticated user with available quota
- **WHEN** the user creates a price alert task with token "SOL" and threshold "$100"
- **THEN** the system creates an `agent_task` record with status "active"
- **AND** the system schedules the first execution within 5 minutes
- **AND** the system returns the task ID and confirmation

#### Scenario: User creates agent via conversational interface

- **GIVEN** an authenticated Pro/Team user
- **WHEN** the user sends natural language instruction "监控 $ETH，如果跌破 $2000 通知我"
- **THEN** the Intent Parser extracts token, condition, and threshold
- **AND** if confidence >= 0.8, the system creates the task automatically
- **AND** if confidence < 0.8, the system asks for confirmation
- **AND** the system deducts one `monthly_agent_conversations` from quota

#### Scenario: User pauses an active agent

- **GIVEN** an authenticated user with an active agent task
- **WHEN** the user calls `POST /api/v1/agents/tasks/:id/pause`
- **THEN** the system updates the task status to "paused"
- **AND** the task is excluded from scheduled executions

#### Scenario: User deletes an agent task

- **GIVEN** an authenticated user with an existing agent task
- **WHEN** the user calls `DELETE /api/v1/agents/tasks/:id`
- **THEN** the system soft-deletes the task (or hard-deletes based on policy)
- **AND** all associated `agent_runs` are retained for audit

### Requirement: Agent Execution Engine

The system SHALL execute agent tasks according to their schedule and configuration using a ReAct-style loop.

#### Scenario: Cron triggers price alert check

- **GIVEN** active price alert tasks exist in the database
- **WHEN** the Cron trigger fires (`*/5 * * * *`)
- **THEN** the system queries all tasks where `next_run_at <= NOW()`
- **AND** the system batches API calls to minimize external requests
- **AND** for each task, the system evaluates the condition
- **AND** if the condition is met, the system triggers a notification
- **AND** the system updates `next_run_at` for the next cycle

#### Scenario: Agent execution with ReAct loop

- **GIVEN** an agent task requiring multi-step reasoning
- **WHEN** the agent executes
- **THEN** the agent performs Thought → Action → Observation cycle
- **AND** the system records each iteration in `agent_runs.iterations`
- **AND** the agent terminates after max 5 iterations or goal completion
- **AND** the system logs the final result

#### Scenario: Agent execution fails

- **GIVEN** an agent task encounters an error (e.g., API timeout)
- **WHEN** the execution fails
- **THEN** the system records the error in `agent_runs`
- **AND** the system sets `agent_runs.status` to "failed"
- **AND** the task remains "active" for retry in the next cycle
- **AND** after 3 consecutive failures, the task is set to "error" status

### Requirement: Watchlist Management

The system SHALL allow users to maintain a list of tokens they want to monitor.

#### Scenario: User adds token to watchlist

- **GIVEN** an authenticated user with available watchlist quota
- **WHEN** the user calls `POST /api/v1/watchlist` with token "AAVE"
- **THEN** the system validates the token exists in CoinGecko
- **AND** the system creates a watchlist entry
- **AND** the system returns the entry with current price

#### Scenario: User exceeds watchlist quota

- **GIVEN** a Free user with 5 tokens in watchlist (max for Free)
- **WHEN** the user attempts to add a 6th token
- **THEN** the system returns HTTP 403 with quota exceeded error
- **AND** the response includes upgrade prompt

### Requirement: Agent Activity Log

The system SHALL provide real-time visibility into agent execution for transparency (Glass Box principle).

#### Scenario: User views agent execution history

- **GIVEN** an authenticated user with existing agent tasks
- **WHEN** the user navigates to Agent Dashboard
- **THEN** the system displays all tasks with their status
- **AND** for each task, the system shows recent execution history
- **AND** the user can expand to see detailed ReAct iterations

#### Scenario: Real-time execution monitoring

- **GIVEN** an agent task is currently executing
- **WHEN** the user views the task details
- **THEN** the system streams execution events via SSE
- **AND** the UI updates in real-time with Thought/Action/Observation

### Requirement: Agent Task Types

The system SHALL support multiple predefined agent task types.

#### Scenario: Price Alert Agent

- **GIVEN** a price alert task with condition "SOL < $100"
- **WHEN** SOL price drops to $99.50
- **THEN** the agent triggers a notification
- **AND** the notification includes current price and change percentage

#### Scenario: Risk Monitor Agent

- **GIVEN** a risk monitor task for token "XYZ"
- **WHEN** the ScamMeter score increases by more than 20 points
- **THEN** the agent triggers a critical notification
- **AND** the notification includes the new risk factors

#### Scenario: News Brief Agent

- **GIVEN** a news brief task for user's watchlist
- **WHEN** the hourly Cron triggers
- **THEN** the agent fetches news from CryptoPanic for watchlist tokens
- **AND** the agent generates an LLM summary of important news
- **AND** if relevant news exists, the agent sends a notification

#### Scenario: Portfolio Health Agent (Pro/Team only)

- **GIVEN** a portfolio health task with user's holdings
- **WHEN** the weekly Cron triggers (Monday 9 AM)
- **THEN** the agent analyzes portfolio composition
- **AND** the agent generates a health report with recommendations
- **AND** the agent sends the report as a notification

### Requirement: Conversational Intent Parser

The system SHALL parse natural language instructions into structured agent task configurations.

#### Scenario: Parse simple price alert

- **GIVEN** user input "提醒我当 BTC 涨到 10 万美元"
- **WHEN** the Intent Parser processes the input
- **THEN** the parser extracts: token="BTC", condition="price > 100000", action="notify"
- **AND** the parser returns confidence score >= 0.9

#### Scenario: Parse complex multi-condition alert

- **GIVEN** user input "监控 ETH，如果价格跌破 2000 或者 24 小时跌幅超过 10%，立刻通知我"
- **WHEN** the Intent Parser processes the input
- **THEN** the parser extracts two conditions with OR relationship
- **AND** the parser returns structured config with both conditions

#### Scenario: Parse ambiguous instruction

- **GIVEN** user input "关注一下 AAVE 的情况"
- **WHEN** the Intent Parser processes the input
- **THEN** the parser returns confidence < 0.8
- **AND** the system asks clarifying questions: "您想监控 AAVE 的哪些指标？价格/TVL/风险评分？"
