# SQLBot API 集成指南

本文档说明如何将 SQLBot 后端封装为独立 API，供外部前端平台调用。

---

## 目录

1. [集成方案对比](#1-集成方案对比)
2. [方案A：API Key 认证（推荐）](#2-方案a-api-key-认证推荐)
3. [方案B：创建简化端点](#3-方案b-创建简化端点)
4. [CORS 配置](#4-cors-配置)
5. [最小化依赖说明](#5-最小化依赖说明)
6. [完整调用示例](#6-完整调用示例)
7. [常见问题](#7-常见问题)
8. [总结](#8-总结)

---

## 1. 集成方案对比

| 方案 | 难度 | 安全性 | 适用场景 | 需要修改代码 |
|------|------|--------|---------|------------|
| **A. API Key 认证** | ⭐ 简单 | ⭐⭐⭐ 高 | 第三方集成、多客户端 | ❌ 否 |
| **B. 简化端点** | ⭐⭐ 中等 | ⭐⭐ 中 | 完全定制化需求 | ✅ 是 |

**推荐**：大部分场景使用 **方案A（API Key）**，无需修改代码，开箱即用。

---

## 2. 方案A: API Key 认证（推荐）

### 2.1 工作原理

SQLBot 内置了 API Key 认证机制，通过 `TokenMiddleware` 自动处理验证。

**认证流程**：
```
外部前端
    ↓ 携带 API Key Token
TokenMiddleware 验证
    ↓ 通过后自动注入 CurrentUser
核心业务逻辑
    ↓
返回结果
```

### 2.2 使用步骤

#### 步骤1：生成 API Key

在 SQLBot 后台或通过 API 生成：

```bash
# API 端点
POST /api/v1/system/apikey

# 响应（保存好，只显示一次）
{
  "access_key": "xxxxxxxxxxx",  # 公开密钥
  "secret_key": "yyyyyyyyyyy"   # 私密密钥
}
```

**限制**：每个用户最多 5 个 API Key （已修改，现在没有数量限制（位置：apps/system/api/apikey.py））

#### 步骤2：前端生成 Token

```python
import jwt
from datetime import datetime, timezone, timedelta

def generate_api_token(access_key: str, secret_key: str) -> str:
    """生成 API 请求 Token"""
    payload = {
        "access_key": access_key,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return f"sk {token}"
```

#### 步骤3：调用 API

```python
import requests
import json

# 配置
API_BASE_URL = "http://localhost:8000/api/v1"
access_key = zdKiZhsxZm9HisdP7vpLEw
secret_key = Wgq2KN9WBAbBuHW7osFMOzdPLHjW9PzYJSAdCTJj2uE

# 生成 token
api_token = generate_api_token(access_key, secret_key)

# 请求参数
headers = {
    "X-SQLBOT-ASK-TOKEN": api_token,
    "Content-Type": "application/json"
}

payload = {
    "question": "查询今日销售额",
    "chat_id": 1  # 必须是已存在的会话ID
}

# 发送请求（流式响应）
response = requests.post(
    f"{API_BASE_URL}/chat/question",
    json=payload,
    headers=headers,
    stream=True
)

# 处理 SSE 流式响应
for line in response.iter_lines():
    if line:
        data = json.loads(line.decode().replace('data:', ''))
        print(f"类型: {data['type']}, 内容: {data.get('content', '')}")
```

### 2.3 核心接口说明

#### 2.3.1 接口概览

| 接口 | 方法 | 说明 | 响应类型 |
|------|------|------|---------|
| `/chat/question` | POST | 提问（主接口） | SSE 流式 |
| `/chat/record/{id}/data` | GET | 获取查询数据 | JSON |
| `/chat/record/{id}/analysis` | POST | 数据分析 | SSE 流式 |
| `/chat/record/{id}/predict` | POST | 数据预测 | SSE 流式 |
| `/chat/list` | GET | 获取会话列表 | JSON |
| `/chat/start` | POST | 创建新会话 | JSON |

#### 2.3.2 主接口详解：`/chat/question`

**请求参数**：
```json
{
  "question": "查询今日销售额",  // 必填：用户问题
  "chat_id": 1                  // 必填：会话ID
}
```

**请求头**：
```
X-SQLBOT-ASK-TOKEN: sk eyJ0eXAiOiJKV1QiLCJhbGc...
Content-Type: application/json
```

**返回值说明**：

⚠️ **重要**：此接口返回 **SSE（Server-Sent Events）流式数据**，不是一次性 JSON 响应。

**SSE 事件流结构**：
```
data:{"type":"id","id":123}

data:{"type":"question","question":"查询今日销售额"}

data:{"type":"sql-result","content":"SELECT ","reasoning_content":"正在生成SQL..."}

data:{"type":"sql","content":"SELECT SUM(amount) FROM sales WHERE date = CURDATE()"}

data:{"type":"sql-data","content":"execute-success"}

data:{"type":"chart","content":"{\"type\":\"number\",\"title\":\"今日销售额\"}"}

data:{"type":"finish"}
```

**核心事件类型**：

| 事件类型 | 说明 | 示例数据 | 用途 |
|---------|------|---------|------|
| `id` | 记录ID（重要） | `{"type":"id","id":123}` | 用于后续调用 `/data` 接口 |
| `question` | 用户问题 | `{"type":"question","question":"..."}` | 展示用户输入 |
| `sql-result` | SQL生成中（流式） | `{"type":"sql-result","content":"SELECT "}` | 实时显示生成过程 |
| `sql` | 完整SQL语句 | `{"type":"sql","content":"SELECT * FROM..."}` | 最终生成的SQL |
| `sql-data` | **数据已准备** | `{"type":"sql-data","content":"execute-success"}` | **触发获取数据的信号** |
| `chart` | **图表配置** | `{"type":"chart","content":"{\\"type\\":\\"bar\\"}"}` | **包含图表类型、坐标轴等配置** |
| `chart-result` | 图表生成中 | `{"type":"chart-result","content":"生成图表中..."}` | 实时显示图表生成过程 |
| `brief` | 会话标题 | `{"type":"brief","brief":"销售额分析"}` | 更新会话标题 |
| `finish` | 处理完成 | `{"type":"finish"}` | 流结束标志 |
| `error` | 错误信息 | `{"type":"error","content":"SQL执行失败"}` | 错误处理 |

**Chart 事件的 JSON 结构**：
```json
{
  "type": "chart",
  "content": "{\"type\":\"bar\",\"title\":\"每日销售额\",\"axis\":{\"x\":{\"name\":\"日期\",\"value\":\"date\"},\"y\":{\"name\":\"销售额\",\"value\":\"amount\"}},\"style\":\"normal\"}"
}
```

解析后的图表配置：
```json
{
  "type": "bar",           // 图表类型：bar/line/pie/number/table/scatter等
  "title": "每日销售额",    // 图表标题
  "axis": {                // 坐标轴配置
    "x": {"name": "日期", "value": "date"},
    "y": {"name": "销售额", "value": "amount"}
  },
  "style": "normal"        // 样式：normal/stack等
}
```

#### 2.3.3 数据获取接口：`/chat/record/{record_id}/data`

**请求方式**：`GET`

**请求头**：
```
X-SQLBOT-ASK-TOKEN: sk eyJ0eXAiOiJKV1QiLCJhbGc...
```

**返回值**：
```json
{
  "fields": ["日期", "销售额", "订单数"],
  "data": [
    ["2024-01-01", 10000, 50],
    ["2024-01-02", 15000, 60],
    ["2024-01-03", 12000, 55]
  ]
}
```

**字段说明**：
- `fields`：列名数组
- `data`：二维数组，每行是一条记录

#### 2.3.4 完整调用流程

```
1. POST /chat/question
   ↓ 返回 SSE 流
   ├─ type: id → 保存 record_id
   ├─ type: sql → 显示生成的SQL
   ├─ type: sql-data → 数据已就绪（触发第2步）
   ├─ type: chart → 解析图表配置
   └─ type: finish → 流结束

2. GET /chat/record/{record_id}/data
   ↓ 返回 JSON
   └─ {fields: [...], data: [...]}

3. 根据 chart 配置和 data 数据渲染图表
```

**Python 完整示例**：
```python
import requests
import json

# 第1步：提问
response = requests.post(
    f"{API_BASE_URL}/chat/question",
    json={"question": "查询今日销售额", "chat_id": 1},
    headers={"X-SQLBOT-ASK-TOKEN": api_token},
    stream=True
)

record_id = None
chart_config = None

# 解析 SSE 流
for line in response.iter_lines():
    if line:
        event = json.loads(line.decode().replace('data:', ''))

        if event['type'] == 'id':
            record_id = event['id']

        elif event['type'] == 'chart':
            # 注意：content 是 JSON 字符串，需要再次解析
            chart_config = json.loads(event['content'])
            print(f"图表类型: {chart_config['type']}")
            print(f"图表标题: {chart_config.get('title')}")

        elif event['type'] == 'sql-data':
            print("数据已准备，可以获取")

# 第2步：获取数据
data_response = requests.get(
    f"{API_BASE_URL}/chat/record/{record_id}/data",
    headers={"X-SQLBOT-ASK-TOKEN": api_token}
)

result = data_response.json()
print(f"字段: {result['fields']}")
print(f"数据: {result['data']}")
```

**JavaScript/TypeScript 完整示例**：
```typescript
// 第1步：提问
const response = await fetch(`${API_BASE_URL}/chat/question`, {
  method: 'POST',
  headers: {
    'X-SQLBOT-ASK-TOKEN': apiToken,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: '查询今日销售额',
    chat_id: 1
  })
});

let recordId: number;
let chartConfig: any;

// 解析 SSE 流
const reader = response.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader!.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n\n');

  for (const line of lines) {
    if (line.startsWith('data:')) {
      const event = JSON.parse(line.replace('data:', ''));

      if (event.type === 'id') {
        recordId = event.id;
      } else if (event.type === 'chart') {
        // content 是 JSON 字符串，需要再次解析
        chartConfig = JSON.parse(event.content);
        console.log('图表配置:', chartConfig);
      } else if (event.type === 'sql-data') {
        console.log('数据已准备');
      }
    }
  }
}

// 第2步：获取数据
const dataResponse = await fetch(
  `${API_BASE_URL}/chat/record/${recordId}/data`,
  {
    headers: { 'X-SQLBOT-ASK-TOKEN': apiToken }
  }
);

const result = await dataResponse.json();
console.log('查询结果:', result);
// 返回：{ fields: ["日期", "销售额"], data: [["2024-01-01", 10000], ...] }
```

### 2.4 前置准备

在调用 API 前，需要在 SQLBot 中准备：

1. **创建用户**（通过 SQLBot 管理界面）
2. **配置数据源**（添加要查询的数据库）
3. **生成 API Key**（在用户设置中）
4. **创建会话**（调用 `/chat/start` 或在界面创建）

---

## 3. 方案B: 创建简化端点

### 3.1 适用场景

- 需要完全控制 API 行为
- 要简化请求参数
- 不需要完整的用户体系

### 3.2 实现步骤

#### 步骤1：创建新路由文件

**文件位置**：`backend/apps/chat/api/external_api.py`

```python
from fastapi import APIRouter
from common.core.deps import SessionDep, CurrentUser
from apps.chat.models.chat_model import ChatQuestion
from apps.chat.api.chat import question_answer_inner

router = APIRouter(tags=["External API"], prefix="/external")

@router.post("/ask")
async def simple_ask(
    session: SessionDep,
    current_user: CurrentUser,  # 从 API Key 自动获取
    question: str,               # 简化：只需问题文本
    datasource_id: int,          # 指定数据源
    chat_id: int = None          # 可选：会话ID
):
    """
    简化的提问接口

    请求示例:
    {
        "question": "查询今日销售额",
        "datasource_id": 1,
        "chat_id": 1
    }
    """
    # 构建标准 ChatQuestion 对象
    request_question = ChatQuestion(
        question=question,
        chat_id=chat_id or 0
    )

    # 调用核心逻辑（非流式响应）
    return await question_answer_inner(
        session,
        current_user,
        request_question,
        in_chat=False,
        stream=False,  # 返回 JSON 而非 SSE
        embedding=True
    )
```

#### 步骤2：注册路由

**文件位置**：`backend/apps/api.py`

```python
# 在文件开头导入
from apps.chat.api import external_api

# 在路由注册部分添加
api_router.include_router(external_api.router)
```

### 3.3 调用示例

```python
# 简化后的调用方式
response = requests.post(
    f"{API_BASE_URL}/external/ask",
    json={
        "question": "查询今日销售额",
        "datasource_id": 1,
        "chat_id": 1
    },
    headers={"X-SQLBOT-ASK-TOKEN": api_token}
)

result = response.json()
print(result)
```

### 3.4 需要修改的文件

| 文件 | 修改内容 |
|------|---------|
| `backend/apps/chat/api/external_api.py` | 创建新文件，添加简化端点 |
| `backend/apps/api.py` | 注册新路由 |

---

## 4. CORS 配置

### 4.1 允许外部前端跨域访问

**文件位置**：`.env` 或环境变量

```bash
# 方式1：指定具体域名（推荐）
BACKEND_CORS_ORIGINS=["http://localhost:3000","https://your-app.com"]

# 方式2：允许所有来源（不推荐）
BACKEND_CORS_ORIGINS=["*"]
```

### 4.2 CORS 配置代码位置

**文件**：`backend/main.py` (第 194-202 行)

```python
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

---

## 5. 最小化依赖说明

### 5.1 调用核心功能的必需条件

```
数据库中的必需数据：
├─ User（至少1个用户）
├─ AiModelDetail（LLM 配置，default_model=True）
├─ CoreDatasource（数据库连接配置）
├─ CoreTable（要查询的表信息）
├─ CoreField（表字段信息）
└─ Chat（会话记录）

运行时必需对象：
├─ Session（数据库会话）
├─ CurrentUser（用户对象）
└─ ChatQuestion（问题对象，包含 question 和 chat_id）
```

### 5.2 核心业务逻辑位置

| 功能 | 文件位置 | 说明 |
|------|---------|------|
| 提问入口 | `backend/apps/chat/api/chat.py:183` | `question_answer()` |
| LLM 服务 | `backend/apps/chat/task/llm.py:156` | `LLMService.create()` |
| 认证中间件 | `backend/apps/system/middleware/auth.py` | `TokenMiddleware` |
| API Key 管理 | `backend/apps/system/api/apikey.py` | API Key CRUD |
| 数据库会话 | `backend/common/core/db.py` | `get_session()` |

### 5.3 依赖注入说明

**方式1：使用现有依赖注入（推荐）**
```python
# FastAPI 自动注入
async def my_endpoint(
    session: SessionDep,         # 自动获取数据库会话
    current_user: CurrentUser,   # 自动获取已认证用户
):
    pass
```

**方式2：手动创建对象**
```python
# 手动创建（用于脱离 FastAPI 的场景）
from sqlmodel import Session, create_engine

engine = create_engine("postgresql://...")
session = Session(engine)

current_user = UserInfoDTO(
    id=1, account="admin", oid=1, language="zh-CN"
)
```

---

## 6. 完整调用示例

### 6.1 JavaScript/TypeScript 示例

```typescript
// 生成 API Token
import jwt from 'jsonwebtoken';

function generateApiToken(accessKey: string, secretKey: string): string {
  const payload = {
    access_key: accessKey,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 3600
  };
  const token = jwt.sign(payload, secretKey, { algorithm: 'HS256' });
  return `sk ${token}`;
}

// 调用 API
async function askQuestion(question: string, chatId: number) {
  const token = generateApiToken(ACCESS_KEY, SECRET_KEY);

  const response = await fetch('http://localhost:8000/api/v1/chat/question', {
    method: 'POST',
    headers: {
      'X-SQLBOT-ASK-TOKEN': token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      question: question,
      chat_id: chatId
    })
  });

  // 处理 SSE 流式响应
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader!.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n\n');

    for (const line of lines) {
      if (line.startsWith('data:')) {
        const data = JSON.parse(line.replace('data:', ''));
        console.log(data);
      }
    }
  }
}
```

### 6.2 Python 示例

```python
import requests
import jwt
import json
from datetime import datetime, timezone, timedelta

class SQLBotClient:
    def __init__(self, base_url, access_key, secret_key):
        self.base_url = base_url
        self.access_key = access_key
        self.secret_key = secret_key

    def _get_token(self):
        payload = {
            "access_key": self.access_key,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return f"sk {token}"

    def ask(self, question: str, chat_id: int):
        headers = {
            "X-SQLBOT-ASK-TOKEN": self._get_token(),
            "Content-Type": "application/json"
        }

        payload = {
            "question": question,
            "chat_id": chat_id
        }

        response = requests.post(
            f"{self.base_url}/chat/question",
            json=payload,
            headers=headers,
            stream=True
        )

        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode().replace('data:', ''))
                yield data

# 使用示例
client = SQLBotClient(
    base_url="http://localhost:8000/api/v1",
    access_key="your_access_key",
    secret_key="your_secret_key"
)

for event in client.ask("查询今日销售额", chat_id=1):
    print(f"事件类型: {event['type']}")
    if event.get('content'):
        print(f"内容: {event['content']}")
```

---

## 7. 常见问题

### Q1: `/chat/question` 返回的是什么格式？
**答**：返回 **SSE 流式数据**，不是一次性 JSON。每个事件都是独立的 JSON 对象。

**重要**：
- ✅ 包含图表配置（`chart` 事件）
- ✅ 包含 SQL 语句（`sql` 事件）
- ✅ 包含文字说明（`sql-result`、`chart-result` 事件）
- ❌ **不直接包含查询结果数据**，需要调用 `/chat/record/{id}/data`

详见本文档 [2.3.2 主接口详解](#232-主接口详解chatquestion)。

### Q2: 如何获取查询结果数据？
**答**：两步流程：
1. 监听 `/chat/question` 的 `id` 事件，获取 `record_id`
2. 调用 `GET /chat/record/{record_id}/data` 获取数据

```python
# 第1步：从 SSE 流获取 record_id
for event in sse_stream:
    if event['type'] == 'id':
        record_id = event['id']

# 第2步：获取数据
data = requests.get(f"/chat/record/{record_id}/data")
# 返回：{"fields": [...], "data": [...]}
```

### Q3: Chart 配置的 content 为什么需要二次解析？
**答**：`chart` 事件的 `content` 字段是 **JSON 字符串**，需要 `JSON.parse()` 或 `json.loads()`：

```python
# 错误示例
event = {"type": "chart", "content": "{\"type\":\"bar\"}"}
chart_type = event['content']['type']  # ❌ 报错！content 是字符串

# 正确示例
chart_config = json.loads(event['content'])  # ✅ 先解析
chart_type = chart_config['type']  # ✅ 正确
```

### Q4: 如何创建会话（chat_id）？
```bash
POST /api/v1/chat/start
{
  "datasource": 1  # 数据源ID
}

# 返回
{
  "id": 123,
  "brief": "新会话",
  "datasource": 1,
  ...
}
```

### Q5: 如何获取数据源列表？
需要先登录 SQLBot 管理界面配置数据源，或通过 API：
```bash
GET /api/v1/datasource/list
```

### Q6: SSE 流式响应包含哪些事件类型？
完整事件列表见 [2.3.2 核心事件类型](#232-主接口详解chatquestion)：
- `id`: 记录ID（用于后续请求）
- `sql`: 生成的SQL
- `sql-data`: 数据已就绪（触发获取数据）
- `chart`: 图表配置（JSON字符串）
- `finish`: 完成
- 详见 [SQLBot_Request_Workflow.md](SQLBot_Request_Workflow.md) 第3.3节

### Q7: 能否不使用流式响应？
可以，在方案B中设置 `stream=False` 返回完整 JSON：
```json
{
  "success": true,
  "record_id": 123,
  "sql": "SELECT ...",
  "chart": {"type": "bar", ...},
  "data": {"fields": [...], "data": [...]}
}
```

### Q8: API Key 如何管理？
- 生成：`POST /api/v1/system/apikey`（返回 `access_key` 和 `secret_key`，只显示一次）
- 列表：`GET /api/v1/system/apikey`
- 删除：`DELETE /api/v1/system/apikey/{id}`
- 启用/禁用：`PUT /api/v1/system/apikey/status`

**注意**：每个用户可创建的 API Key 数量无限制（已在代码中注释掉 5 个限制）。

### Q9: 前端如何知道数据何时可以获取？
**答**：监听 `sql-data` 事件：
```typescript
if (event.type === 'sql-data') {
  // 此时数据已准备好，可以调用 /data 接口
  fetchData(recordId);
}
```

---

## 8. 总结

### 推荐方案对照表

| 你的需求 | 推荐方案 |
|---------|---------|
| 第三方应用集成 | **方案A（API Key）** |
| 完全定制化 | **方案B（简化端点）** |
| 多租户SaaS | **方案A（API Key）** |
| 单一客户端 | **方案B（简化端点）** |

### 快速开始

**5分钟集成步骤**：
1. ✅ 在 SQLBot 后台生成 API Key
2. ✅ 配置 CORS 允许你的前端域名
3. ✅ 使用上述代码示例生成 Token
4. ✅ 调用 `/chat/question` 接口
5. ✅ 处理 SSE 流式响应

**无需修改任何 SQLBot 代码！**
