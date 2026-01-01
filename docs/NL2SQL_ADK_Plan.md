# 基于 Google ADK 的轻量 NL2SQL Bot 方案（对比 SQLBot 工作流）

## 1. 背景与目标
本项目目标是在 `adk_nl2sql` 中实现一个**更轻量的 NL2SQL Bot**，相比 SQLBot 去掉复杂的图表渲染、SSE 流式交互、权限过滤等重功能，仅保留：
- 获取目标表的列信息（schema）
- 生成只读 SQL
- 执行 SQL 获取结果
- 由代理解释结果或做简要分析

使用 **Google ADK + Azure OpenAI**（从 `.env` 提供 API 信息）。
理想用户体验：
- 仅提供模型 API、数据库信息、目标表名
- 其余流程由代理自动完成（schema → SQL → 查询 → 解释）

## 2. SQLBot 工作流简析（来自 SQLBot Request Workflow + 后端源码）
SQLBot 的链路较复杂，核心流程包括：
1) **选择数据源**（LLM 调用 #1）
2) **生成 SQL**（LLM 调用 #2）
3) **行级权限过滤**（LLM 调用 #3，可选）
4) **动态数据源 SQL**（LLM 调用 #4，可选）
5) **执行 SQL**（db.py）
6) **图表配置生成**（LLM 调用 #5）
7) **可选分析/预测**（LLM 调用 #6/#7）
8) **SSE 流式前端展示**（SQL、图表、数据逐步下发）

关键实现参考：
- `backend/apps/chat/task/llm.py`：LLMService 负责多段 LLM 调用与日志
- `backend/apps/datasource/crud/datasource.py:get_table_schema`：拼接表结构并使用 embedding 选择相关表
- `backend/templates/template.yaml`：SQL/Chart/Permission/Dynamic SQL Prompt 模板
- SSE 与图表渲染：前端 ChartAnswer.vue + chart 事件解析

**复杂点**（我们将削减）：
- 多阶段 LLM 调用链 + 图表配置
- 行级权限过滤 / 动态数据源
- SSE 流式输出 + 图表渲染

## 3. 简化方案原则
- **聚焦最小闭环**：schema → SQL → 执行 → 解释
- **只读安全**：只允许 SELECT，禁止 DML/DDL
- **轻量交互**：不做图表，不强依赖 SSE
- **结果可用**：返回数据并由代理解释/分析
- **SQL 安全校验前置**：只读校验在 SQL 执行工具内部完成，不引入新工具

## 4. 目标架构（Google ADK 版）

### 4.1 角色与职责
- **RootAgent（顶层编排）**：只负责路由与最终答复，不直接处理 SQL 细节。
- **SQLTaskAgent（子代理）**：负责 SQL 全流程（schema → SQL → 执行），带重试与纠错。
- **SchemaInspector Tool**：连接数据库并返回目标表列名（可含类型/注释）。
- **SQLGeneratorTool（工具）**：封装 SQLGeneratorAgent，工具输出 JSON，代理只输出 SQL。
- **SQLRunner Tool**：执行 SQL 并返回结果（rows/columns）；在执行前完成 SELECT-only 校验。
- **ResultInterpreterAgent（子代理）**：基于数据回答问题或做简要分析。

### 4.2 高层流程图
```
用户问题
   ↓
RootAgent
   ↓ 调用 SQLTaskAgent
SQLTaskAgent:
   ↓ 调用 SchemaInspector
   ↓ 调用 SQLGeneratorTool → 生成 SQL（JSON）
   ↓ 调用 SQLRunner Tool → 执行 SQL
   ↓（必要时）重试一次 SQL 生成与执行
   ↓ 返回 rows/columns + SQL
   ↓
RootAgent → 调用 ResultInterpreterAgent
传入完整原始结果（columns + rows + row_count + SQL），输出最终答案/分析
```

## 5. 会话状态设计（session.state）
建议持久化以下状态，便于调试与复用：
- `selected_table`: 目标表名
- `table_columns`: 列名/类型/注释
- `generated_sql`: 最近一次生成的 SQL
- `sql_result`: 最近一次查询结果（rows + columns）
- `last_error`: 最近一次执行错误（如有）

### 5.1 如何存储与更新 state
- **工具优先**：在工具内通过 `tool_context.state[...] = ...` 写入，确保写入与执行结果一致。
- **代理写入**：如需保存代理最终回答，可使用 `output_key` 自动写入 state。
- **覆盖策略**：同一 key 默认覆盖（如 `generated_sql`），确保 state 始终指向最新结果。

建议写入点：
- `inspect_table_schema`：写 `selected_table`、`table_columns`
- `SQLGeneratorTool`：写 `generated_sql`、可选 `last_error`
- `SQLRunner`：写 `sql_result`、`row_count`、可选 `last_error`
- Root/ResultInterpreterAgent：如需保存最终答复，用 `output_key`

### 5.2 使用 state 做代理间通信
在 RootAgent → SQLTaskAgent → ResultInterpreterAgent 流程中，state 可作为“共享上下文”，建议如下：
- **SQLTaskAgent**：读取 `table_columns` 作为生成 SQL 的约束；读取 `last_error` 进行重试修正。
- **ResultInterpreterAgent**：读取 `sql_result` 与 `generated_sql`，确保分析基于原始数据。
- **RootAgent**：只负责路由与最终输出，避免在 state 中写入与 SQL 无关的信息。

### 5.3 风险与边界
- **会话隔离**：state 与 session_id 绑定，避免不同用户交叉污染。
- **体积控制**：避免把超大结果写入 state；必要时写入摘要或限制 rows。
- **一致性**：工具写入 state 后，保证返回值与 state 一致，便于复盘与调试。

## 6. 工具设计（建议签名）

### 6.1 SchemaInspector Tool
用途：获取目标表的列信息。
```python
# Tool: inspect_table_schema(table_name: str, tool_context: ToolContext) -> dict
# 返回示例
{
  "table": "orders",
  "columns": [
    {"name": "order_id", "type": "int"},
    {"name": "amount", "type": "decimal"},
    {"name": "created_at", "type": "timestamp"}
  ]
}
```
- 将结果写入 `tool_context.state["table_columns"]`

### 6.2 SQLRunner Tool
用途：执行 SQL 并返回结果。
```python
# Tool: run_sql(query: str, tool_context: ToolContext) -> dict
{
  "columns": ["order_id", "amount"],
  "rows": [[1, 99.8], [2, 104.2]],
  "row_count": 2
}
```
- **在执行前完成 SQL 安全校验**（SELECT only，禁止 DDL/DML）
- **强制 LIMIT**（例如 200，若缺失则自动补）
- 可将执行结果写入 `tool_context.state["sql_result"]`

### 6.3 SQLGeneratorTool
用途：封装 SQLGeneratorAgent，返回结构化 JSON，便于主流程处理。
```python
# Tool: generate_sql(question: str, schema: dict) -> dict
{
  "success": true,
  "sql": "SELECT ... LIMIT 200",
  "reason": "简要说明"
}
```
说明：
- 工具内部调用 SQLGeneratorAgent
- 代理仅输出 SQL 字符串，工具负责 JSON 包装与错误处理

## 7. 子代理设计

### 7.1 SQLTaskAgent（新增，承接 SQL 全流程）
职责：
- 按步骤调用 SchemaInspector → SQLGeneratorTool → SQLRunner
- 处理失败与重试（最多 1 次）
- 返回 SQL 与结果给 RootAgent

建议重试策略：
- 仅在 SQL 执行失败或空结果且疑似条件过严时重试
- 重试时附带错误信息或建议放宽条件

### 7.2 SQLGeneratorAgent
**输入**：用户问题 + 表列信息  
**输出**：仅输出 SQL 字符串（不输出 JSON）  
示例：
```
SELECT amount FROM orders WHERE created_at >= '2024-01-01' LIMIT 200
```
约束建议：
- 只生成 SELECT
- 不使用 SELECT *
- 必须使用 LIMIT
- 列名必须来自 schema

### 7.3 ResultInterpreterAgent
**输入**：用户问题 + SQL + 查询结果（完整原始数据，含 columns + rows + row_count）  
**输出**：自然语言回答或简要分析
- 如果结果为空，明确告知并建议调整条件
- 可进行简单统计（如求均值/总和）或解释字段含义

## 8. Azure OpenAI 配置建议（.env）
根据你现有 `.env`，当前配置要点如下（不写入敏感值）：  
- 模型配置：`AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_VERSION`  
- 模型名：`MODEL=gpt-4o-mini`（可改为 Azure Deployment）  
- 数据库连接：`POSTGRES_CONNECTION_STRING=...`（Supabase Postgres）  
- 目标表：`users`（你已标注“can access table: users”）  

推荐变量（值用真实配置替换）：
```
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=<deployment_name>
```

**Google ADK + LiteLLM 方式（伪代码）：**
```python
from google.adk.models.lite_llm import LiteLlm

model = LiteLlm(
  model="azure/<deployment_name>",
  api_key=os.getenv("AZURE_OPENAI_API_KEY"),
  api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
  api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)
```
> 说明：具体 `model` 命名与参数需按 LiteLLM Azure 规范调整。

## 9. 错误处理与重试策略
- SQL 执行失败：将错误写入 state，允许 SQLGeneratorAgent 基于错误信息修正一次
- 超时或结果过大：要求 agent 降低范围或增加过滤条件
- 表/列未命中：提示用户确认目标表或字段

## 10. 安全与约束
- 禁止 DDL/DML（CREATE/UPDATE/DELETE/INSERT 等）
- 必须限制返回行数（LIMIT）
- 仅允许白名单表
- 仅允许白名单列（来自 schema）

## 11. 在 adk_nl2sql 内的落地建议（不改动 .py，仅规划）
建议目录结构（参考 `weather_bot_v3/v4`）：
```
adk_nl2sql/
  nl2sql/
    agent.py (root_agent)
    agents/
      sql_generator_agent.py
      result_interpreter_agent.py
    prompts/
      root_agent.txt
      sql_generator_agent.txt
      result_interpreter_agent.txt
    tools/
      schema_tools.py
      sql_tools.py
  docs/
    NL2SQL_ADK_Plan.md  (本文件)
```

## 12. 下一步建议
1) 固化目标表清单（当前为 `users`），确认是否需要多表查询
2) 明确 SQLRunner 工具的数据库连接方式（直连/SQLAlchemy/ODBC）
3) 确认 SQLGeneratorTool 的 JSON 输出字段（success/sql/reason）
4) 在确认后再开始写 .py 实现
