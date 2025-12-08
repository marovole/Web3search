/**
 * Deep Research Prompts
 * Optimized for Tongyi DeepResearch-30B-A3B ReAct capabilities
 */

/**
 * Main system prompt for deep research agent
 * Enables ReAct (Reasoning + Acting) mode for multi-step research
 */
export const DEEPRESEARCH_SYSTEM_PROMPT = `你是一个专业的深度研究代理，具备 ReAct (Reasoning + Acting) 能力。你的任务是对用户的查询进行全面、深入的研究分析。

## 研究方法论

### 第一阶段：问题分解
- 分析用户查询的核心需求和潜在意图
- 识别需要调研的关键维度（技术、市场、竞争、风险、趋势等）
- 制定精准的搜索策略

### 第二阶段：信息收集与验证
- 对每个信息来源进行可信度评估
- 交叉验证关键数据点
- 标注信息时效性和来源权威性

### 第三阶段：深度分析
- 识别信息之间的关联、矛盾和模式
- 提炼核心洞察和非显而易见的发现
- 评估信息完整度

### 第四阶段：结论综合
- 按逻辑结构组织发现
- 明确标注每个观点的证据来源 [Source N]
- 指出研究局限性和不确定性
- 提供可操作的建议

## 输出要求
- 所有观点必须有证据支持，使用 [Source N] 格式引用
- 区分事实陈述和推断分析
- 对不确定信息明确标注
- 使用结构化格式便于阅读`

/**
 * Prompt for generating research plan
 */
export const RESEARCH_PLAN_PROMPT = `## 研究任务
{query}

## 要求
请分析这个研究任务，并生成一个详细的研究计划。

你需要：
1. **理解查询意图**：分析用户真正想了解什么
2. **确定研究维度**：识别需要从哪些角度进行研究（如技术、市场、竞争格局、风险、发展趋势等）
3. **生成搜索策略**：为每个维度制定 1-2 个精准的搜索查询词
4. **评估优先级**：标注每个维度的重要性

请以 JSON 格式输出，结构如下：
{
  "query_understanding": "对用户查询的理解和分析",
  "research_dimensions": [
    {
      "dimension": "维度名称",
      "importance": "high/medium/low",
      "description": "该维度需要研究的内容"
    }
  ],
  "search_queries": [
    {
      "query": "搜索词",
      "purpose": "该搜索词的目的",
      "target_dimension": "对应的研究维度"
    }
  ],
  "expected_challenges": ["可能遇到的研究挑战"]
}`

/**
 * Prompt for analyzing sources
 */
export const SOURCE_ANALYSIS_PROMPT = `## 原始研究问题
{query}

## 研究计划
{plan}

## 收集到的信息来源
{sources}

## 分析任务
请对收集到的信息来源进行深度分析：

1. **来源可信度评估**：评估每个来源的权威性和可靠性
2. **关键信息提取**：从每个来源中提取与研究问题相关的关键信息
3. **信息交叉验证**：识别不同来源之间的一致性和矛盾之处
4. **信息缺口识别**：指出哪些方面的信息还不够充分

请以 JSON 格式输出：
{
  "source_evaluations": [
    {
      "source_id": 1,
      "credibility": "high/medium/low",
      "key_information": "提取的关键信息",
      "relevance": 0.0-1.0
    }
  ],
  "cross_validation": {
    "consistent_findings": ["多个来源一致的发现"],
    "contradictions": ["来源之间的矛盾"]
  },
  "information_gaps": ["信息缺口"],
  "preliminary_insights": ["初步洞察"]
}`

/**
 * Prompt for synthesizing findings into final report
 */
export const SYNTHESIS_PROMPT = `## 原始研究问题
{query}

## 研究计划
{plan}

## 信息来源
{sources}

## 任务
基于以上收集和分析的信息，生成一份全面的深度研究报告。

报告必须包含：

### 1. 执行摘要 (Executive Summary)
- 100字以内概述核心发现
- 直接回答用户的核心问题

### 2. 详细分析
按研究维度逐一展开分析：
- 每个观点必须标注证据来源 [Source N]
- 区分事实和推断
- 指出数据的时效性

### 3. 关键发现 (Key Findings)
- 列出 3-5 个最重要的发现
- 每个发现都要有充分的证据支持

### 4. 风险与不确定性
- 研究的局限性
- 信息的不确定性
- 可能存在的偏见

### 5. 结论与建议
- 基于证据的结论
- 可操作的建议（如适用）
- 后续研究方向

请以 JSON 格式输出：
{
  "executive_summary": "执行摘要",
  "detailed_analysis": {
    "sections": [
      {
        "title": "章节标题",
        "content": "详细内容，包含 [Source N] 引用",
        "dimension": "对应研究维度"
      }
    ]
  },
  "key_findings": [
    {
      "finding": "发现内容",
      "evidence": "支持证据",
      "sources": [1, 2],
      "confidence": 0.0-1.0
    }
  ],
  "risks_and_uncertainties": {
    "limitations": ["局限性"],
    "uncertainties": ["不确定因素"],
    "potential_biases": ["潜在偏见"]
  },
  "conclusion": {
    "summary": "总结性结论",
    "recommendations": ["建议"],
    "future_research": ["后续研究方向"]
  },
  "metadata": {
    "total_sources_analyzed": 0,
    "overall_confidence": 0.0-1.0,
    "research_depth": "quick/standard/deep"
  }
}`

/**
 * Research depth configurations
 */
export const RESEARCH_CONFIG = {
  quick: {
    max_queries: 3,
    max_sources: 5,
    plan_max_tokens: 800,
    synthesis_max_tokens: 2000,
    temperature: 0.3
  },
  standard: {
    max_queries: 5,
    max_sources: 12,
    plan_max_tokens: 1200,
    synthesis_max_tokens: 3500,
    temperature: 0.4
  },
  deep: {
    max_queries: 8,
    max_sources: 20,
    plan_max_tokens: 1500,
    synthesis_max_tokens: 5000,
    temperature: 0.5,
    enable_iteration: true
  }
} as const

export type ResearchDepthConfig = typeof RESEARCH_CONFIG[keyof typeof RESEARCH_CONFIG]

/**
 * Get research configuration by depth
 */
export function getResearchConfig(depth: 'quick' | 'standard' | 'deep'): ResearchDepthConfig {
  return RESEARCH_CONFIG[depth] || RESEARCH_CONFIG.standard
}

/**
 * Format sources for prompt injection
 */
export function formatSourcesForPrompt(sources: Array<{
  title: string
  url: string
  snippet: string
}>): string {
  return sources.map((s, i) => 
    `[Source ${i + 1}] ${s.title}
URL: ${s.url}
内容摘要: ${s.snippet}`
  ).join('\n\n---\n\n')
}

/**
 * Build research plan prompt with query
 */
export function buildResearchPlanPrompt(query: string): string {
  return RESEARCH_PLAN_PROMPT.replace('{query}', query)
}

/**
 * Build synthesis prompt with all context
 */
export function buildSynthesisPrompt(
  query: string,
  plan: string,
  sources: string
): string {
  return SYNTHESIS_PROMPT
    .replace('{query}', query)
    .replace('{plan}', plan)
    .replace('{sources}', sources)
}
