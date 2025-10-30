## Context
Web3search是一个加密货币AI研究平台，当前用户数据存储在浏览器localStorage中，无法跨设备访问。用户希望在不同设备上访问自己的对话历史、报告和偏好设置。现有的Conversation模型已预留user_id字段，但缺乏完整的用户认证和管理系统。项目已具备基础的安全设施（速率限制、CORS），但需要添加用户认证层以支持个性化功能。

## Goals / Non-Goals
### Goals
- 提供安全可靠的用户注册和登录功能
- 实现用户数据的跨设备同步和持久化存储
- 将localStorage数据迁移到数据库
- 支持用户个性化设置和偏好管理
- 确保用户历史记录和报告的完整保存
- 实现JWT Token认证和无状态的API访问

### Non-Goals
- 不支持OAuth 2.0之外的第三方登录方式（如Web3钱包登录）
- 不实现复杂的权限管理系统（仅区分登录/未登录用户）
- 不实现用户间的社交功能（分享、协作等）
- 不实现订阅和付费功能
- 不替换现有的速率限制机制（认证用户仍受速率限制保护）

## Decisions
- **认证方式**: JWT Token（Access Token + Refresh Token），Access Token 24小时过期，Refresh Token 30天过期
- **密码加密**: 使用bcrypt，盐值强度12轮
- **数据库设计**: 新增users表存储用户基本信息，user_preferences表存储偏好设置，sessions表管理Token刷新
- **前端状态管理**: 使用React Context API创建AuthContext，管理登录状态和用户信息
- **数据迁移策略**: 提供一键迁移工具，将localStorage数据导入到用户账号
- **第三方登录**: 优先支持Google OAuth，后续可扩展GitHub
- **Token存储**: Access Token存储在内存和localStorage（用于刷新），Refresh Token仅存储在HttpOnly Cookie
- **用户标识**: 使用UUID作为user_id，避免泄露个人信息

## Risks / Trade-offs
- **安全风险**: JWT Token在localStorage存在XSS风险，需要通过CSP和输入验证缓解
- **数据迁移复杂度**: 需要处理localStorage数据格式不统一的问题
- **用户体验**: 强制登录可能降低新用户试用意愿，需要提供"稍后登录"选项
- **性能影响**: 每个API请求需要验证JWT，增加少量延迟（<10ms）
- **第三方依赖**: OAuth登录依赖Google API，需要管理API密钥和回调URL

## Migration Plan
1. **Phase 1**: 后端用户模型和认证API（注册、登录、Token刷新）
2. **Phase 2**: 前端认证界面和AuthContext集成
3. **Phase 3**: API中间件和用户上下文注入
4. **Phase 4**: 数据迁移工具和偏好设置同步
5. **Phase 5**: 历史记录关联和测试验证

## Open Questions
- 是否需要邮箱验证？建议：是，但允许未验证用户使用基本功能
- 是否需要密码重置功能？建议：是，通过邮箱发送重置链接
- localStorage数据如何迁移？建议：登录后提示用户迁移，支持批量导入
- 匿名用户数据如何处理？建议：保留30天，登录后自动关联
- 是否需要账户删除功能？建议：是，支持数据导出后删除（GDPR合规）

