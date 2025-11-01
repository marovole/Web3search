## Context
Adding code review capabilities to the Web3 research platform to analyze smart contracts for security vulnerabilities, code quality, and architectural patterns. This extends the existing AI analysis system to handle Solidity and other blockchain code.

## Goals / Non-Goals
- Goals: 
  - Comprehensive smart contract security analysis
  - Integration with existing AI pipeline
  - Support for multiple blockchain languages
  - Real-time vulnerability detection
- Non-Goals:
  - Full code compilation and execution
  - Formal verification
  - Gas optimization analysis (initial phase)

## Decisions
- Decision: Use existing OpenRouter models with specialized prompts for code analysis
- Alternatives considered: Dedicated code analysis models (too costly), Static analysis tools (limited AI insights)
- Decision: Extend current analyzer pattern with code-specific analyzers
- Alternatives considered: Separate microservice (adds complexity), External API integration (vendor lock-in)

## Risks / Trade-offs
- Risk: False positives in vulnerability detection → Mitigation: Multi-model validation and confidence scoring
- Risk: Large contract processing timeouts → Mitigation: Chunked processing and progress indicators
- Trade-off: Analysis depth vs response time → Configurable analysis modes (quick vs thorough)

## Migration Plan
1. Add new database tables for code reviews
2. Extend AI analysis service with code analyzers
3. Add new API endpoints alongside existing chat endpoints
4. Update frontend with new code review components
5. Gradual rollout with feature flags

## Open Questions
- Should we support code file uploads or only contract addresses?
- How to handle private repositories vs verified public contracts?
- What's the maximum contract size we can process effectively?
