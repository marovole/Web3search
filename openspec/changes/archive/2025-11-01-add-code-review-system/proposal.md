## Why
Add code review capabilities to the Web3 research platform to help users analyze smart contracts, DeFi protocols, and blockchain codebases for security vulnerabilities, code quality, and architectural patterns.

## What Changes
- Add new `code-review` capability for smart contract analysis
- Extend `ai-analysis` to include code-specific analyzers
- Add new API endpoints for code submission and review
- Create frontend components for code input and review display
- Integrate with blockchain explorers for contract verification

## Impact
- Affected specs: ai-analysis, chat-interface, security
- Affected code: backend/app/services/, backend/app/api/v1/, frontend/src/components/
- New database models for code reviews and analysis results
