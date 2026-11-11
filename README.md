# xianglianghua-rag · 企业知识库 RAG 检索服务

从零实现的 RAG 检索链路：**文档解析 → 多策略切分 → 本地 Embedding 向量化 → LanceDB 入库 → FastAPI 服务化**，并按 **Dify 外部知识库协议**（`POST /retrieval`）对外提供带出处的知识召回，可直接被 Dify 知识库 / Agent 引用。

## 项目结构（五步递进）

| 目录 | 内容 |
|------|------|
| `01lancedb_demo/` | LanceDB 最小闭环：写入、检索，对比 L2 / cosine / dot 三种距离 |
| `02doc_pdf_md_slice/` | 三种切分策略实现与选型对比：① 固定长度滑动窗口（`01_slice_by_size.py`）② 按「问：」结构边界正则切（`02_slice_by_qa.py`）③ 大模型语义切分（`03_slice_by_deepseek.py` / `03_slice_by_mimo.py`，读环境变量 Key） |
| `03slice_insert_lancedb/` | 切片 → 批量 encode → 写入 LanceDB（`mode="overwrite"` 全量重建）→ L2 距离检索脚本 |
| `04fastapi_lancedb_embeding/` | **核心服务**：FastAPI 实现 Dify 外部知识库规范 `POST /retrieval`，Bearer 鉴权 + `top_k` / `score_threshold` 参数 |
| `05custom_tools/` | Dify 自定义工具三件套（天气 / 读网页 / SQLite FAQ 关键词查询）+ 导出的 `openapi_for_dify.json` |

## 模型准备（必读）

本仓库**不含**本地 Embedding 模型目录（`xianglianghuamoxing/`，约 900MB）。模型为 **`paraphrase-multilingual-MiniLM-L12-v2`（384 维）**，克隆后执行一次即可生成：

```powershell
uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2').save('xianglianghuamoxing')"
```

> 入库和查询必须使用同一个模型目录：换模型不会报错，只会静默搜不准。

## 快速开始

```powershell
# 1. 安装依赖（Python >= 3.12，推荐 uv）
uv sync

# 2. 准备模型（见上）

# 3. 入库（读 02 产出的切片，写入 03 的 .lancedb）
cd 03slice_insert_lancedb
uv run python 01_slice_embed_insert.py

# 4. 启动 Dify 外部知识库服务
cd ..\04fastapi_lancedb_embeding
uv run python 01_dify_external_knowledge.py
```

服务默认监听 `0.0.0.0:8000`，自测：

```powershell
curl -X POST http://127.0.0.1:8000/retrieval `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer dify-demo-key" `
  -d '{"knowledge_id":"faq","query":"能在两台电脑看吗","retrieval_setting":{"top_k":3,"score_threshold":0}}'
```

## 接入 Dify

1. Dify → 知识库 → 外部知识库，填写服务地址与 `dify-demo-key`（演示 Key，生产请改为环境变量）。
2. 或在 Dify「自定义工具」中导入 `05custom_tools/openapi_for_dify.json`。

## 设计要点

- **三种切分策略可切换**：有结构（FAQ / Markdown 标题）按结构切，无结构再用模型语义切，超长块二次切分。
- **检索默认返回 Top-3**（`top_k` 可由请求方配置），score 由 cosine 距离换算为 0~1 并按 `score_threshold` 过滤。
- **返回带出处**：每条 record 附来源文件与标题，答案可溯源，不是「只给答案不给依据」。
- **模型启动时单例加载**，避免每个请求重复加载导致响应变慢。

## 已知边界

- 当前为**纯向量检索**，无 BM25 / 重排序 / 混合召回（在 roadmap 中）。
- 入库为 `overwrite` 全量重建，暂不支持按 `doc_id` 增量更新。
- 暂无自动化测试，验证依赖上述手动脚本与 curl。

## 依赖

FastAPI · LanceDB · sentence-transformers · pypdf · python-docx · pandas · uvicorn（完整见 `pyproject.toml` / `uv.lock`）
