# chat-interface Specification Delta

## MODIFIED Requirements

### Requirement: TypeScript类型安全
系统**SHALL**确保所有前端代码具有完整的TypeScript类型定义，无类型错误和警告。

#### Scenario: 代码构建无类型错误
- **WHEN** 开发者运行`npm run build`构建前端应用
- **THEN** 构建过程无TypeScript类型错误（TS2339、TS2769、TS6133等）
- **AND** 无类型相关的编译警告
- **AND** 构建成功生成dist目录

#### Scenario: 组件类型定义完整
- **WHEN** 开发者使用React组件（如MessageBubble、ReportViewer）
- **THEN** 所有props具有明确的TypeScript接口定义
- **AND** 所有事件处理器具有正确的类型签名
- **AND** 不使用`@ts-ignore`注释绕过类型检查
- **AND** 不使用`any`类型（除非有充分理由）

#### Scenario: 第三方库类型正确
- **WHEN** 使用第三方库（如react-markdown、react-syntax-highlighter）
- **THEN** 导入正确的类型定义（如`@types/react-syntax-highlighter`）
- **AND** 组件props与库的类型定义匹配
- **AND** 自定义组件正确实现库的接口要求

#### Scenario: Vite环境变量类型安全
- **WHEN** 代码中使用`import.meta.env.VITE_*`环境变量
- **THEN** vite-env.d.ts中定义ImportMetaEnv接口
- **AND** 所有使用的环境变量在接口中声明
- **AND** TypeScript能正确识别环境变量类型
- **AND** 不出现"Property 'env' does not exist"错误

#### Scenario: 代码编辑器类型提示
- **WHEN** 开发者在VSCode或其他IDE中编写代码
- **THEN** 编辑器提供准确的类型提示和自动补全
- **AND** 编辑器实时显示类型错误（无需运行构建）
- **AND** 鼠标悬停显示准确的类型信息

### Requirement: 代码质量标准
系统**SHALL**遵循代码质量最佳实践，避免未使用的变量和导入。

#### Scenario: 无未使用的导入
- **WHEN** 代码文件中导入了模块或组件
- **THEN** 所有导入都在代码中被实际使用
- **AND** React 18的JSX文件不需要显式导入React
- **AND** 构建时不出现"is declared but its value is never read"警告

#### Scenario: 无未使用的变量
- **WHEN** 代码中声明了变量或参数
- **THEN** 所有声明的变量都被实际使用
- **AND** 如果参数未使用，使用下划线前缀（如`_unused`）或从签名移除
- **AND** 构建时不出现未使用变量的警告

#### Scenario: Lint检查通过
- **WHEN** 开发者运行`npm run lint`
- **THEN** ESLint检查通过，无错误
- **AND** Prettier格式检查通过
- **AND** 代码符合项目配置的代码规范

## ADDED Requirements

### Requirement: 代码块渲染类型安全
系统**SHALL**提供类型安全的代码块渲染组件，支持Markdown中的代码高亮。

#### Scenario: CodeBlock组件类型定义
- **WHEN** 创建CodeBlock组件用于渲染代码块
- **THEN** 组件具有明确的Props接口定义：
  ```typescript
  interface CodeBlockProps {
    inline?: boolean        // 是否为行内代码
    className?: string      // 语言类型（如language-javascript）
    children: React.ReactNode  // 代码内容
  }
  ```
- **AND** 组件正确区分inline和block代码（inline用`<code>`，block用`<SyntaxHighlighter>`）
- **AND** 正确解析className提取语言类型（如"language-javascript" → "javascript"）

#### Scenario: ReactMarkdown集成无类型错误
- **WHEN** 在MessageBubble或ReportViewer中使用ReactMarkdown
- **THEN** ReactMarkdown的components.code配置使用CodeBlock组件
- **AND** 类型签名与ReactMarkdown的code组件接口匹配
- **AND** 不需要使用`@ts-ignore`注释
- **AND** SyntaxHighlighter的props类型正确（style、language、PreTag等）

#### Scenario: 代码高亮样式正确应用
- **WHEN** Markdown内容包含代码块（如```javascript```）
- **THEN** 代码块应用SyntaxHighlighter的tomorrow主题样式
- **AND** 行内代码显示为灰色背景的`<code>`标签
- **AND** 块级代码显示为带语法高亮的代码块
- **AND** 渲染性能良好（无明显卡顿）
