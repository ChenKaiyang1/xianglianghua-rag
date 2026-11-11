"""第 4 课 · Dify 外部知识库 API（FastAPI + LanceDB）

对接 Dify「外部知识库」规范：
  POST /retrieval
  Authorization: Bearer <API_KEY>
  请求体: knowledge_id / query / retrieval_setting.top_k / score_threshold
  响应:   records: [{content, score, title, metadata}]

数据来自第 3 课入库的表：03slice_insert_lancedb/.lancedb 里的 faq

运行：
  cd F:\\workspace\\ai_dmx\\xianglianghua\\04fastapi_lancedb_embeding
  uv run python 01_dify_external_knowledge.py

本机自测（另开一个终端）：
  curl -X POST http://127.0.0.1:8000/retrieval `
    -H "Content-Type: application/json" `
    -H "Authorization: Bearer dify-demo-key" `
    -d '{"knowledge_id":"faq","query":"能在两台电脑看吗","retrieval_setting":{"top_k":2,"score_threshold":0}}'
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

import lancedb
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# ============ 配置 ============
PORT = 8000
API_KEY = "dify-demo-key"  # Dify 里填的 Key 要和这里一致；生产环境请改用环境变量

# 向量库与模型路径（相对本文件）
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = (BASE_DIR / ".." / "03slice_insert_lancedb" / ".lancedb").resolve()
MODEL_PATH = (BASE_DIR / ".." / "xianglianghuamoxing").resolve()
TABLE_NAME = "faq"

# ============ 启动时加载一次（避免每个请求都加载模型） ============
print("加载嵌入模型...")
embed_model = SentenceTransformer(str(MODEL_PATH))
print("连接 LanceDB...")
db = lancedb.connect(str(DB_PATH))
table = db.open_table(TABLE_NAME)
print(f"就绪：表 {TABLE_NAME}，共 {table.count_rows()} 条")

app = FastAPI(title="Dify External Knowledge API")


# ============ 请求/响应模型 ============
class RetrievalSetting(BaseModel):
    top_k: Optional[int] = 3
    score_threshold: Optional[float] = 0.0
    score_threshold_enabled: Optional[bool] = None


class RetrievalRequest(BaseModel):
    knowledge_id: Optional[str] = None
    query: Optional[str] = None
    retrieval_setting: Optional[RetrievalSetting] = None


class Record(BaseModel):
    content: str
    score: float
    title: str
    metadata: Dict[str, Any] = {}


class RetrievalResponse(BaseModel):
    records: List[Record]


# ============ 鉴权 ============
def authenticate(authorization: Optional[str] = Header(None)) -> bool:
    """要求 Authorization: Bearer <API_KEY>"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[len("Bearer "):].strip()
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return True


# ============ 业务接口 ============
@app.post("/retrieval", response_model=RetrievalResponse)
async def retrieval(
    req: RetrievalRequest,
    _: bool = Depends(authenticate),
):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=422, detail="query is required")

    setting = req.retrieval_setting or RetrievalSetting()
    top_k = setting.top_k or 3
    threshold = setting.score_threshold or 0.0

    # 1. 问题向量化（必须和入库同一个模型）
    qvec = embed_model.encode(req.query).tolist()

    # 2. 向量检索（这里用 cosine，方便转成 0~1 的 score 给 Dify）
    hits = (
        table.search(qvec)
        .distance_type("cosine")
        .limit(top_k)
        .to_list()
    )

    records: List[Record] = []
    for hit in hits:
        # LanceDB cosine: _distance = 1 - 余弦相似度
        # Dify 里 score 越大越相关，所以用 1 - distance
        score = max(0.0, 1.0 - float(hit["_distance"]))
        if score < threshold:
            continue
        text = hit["text"]
        # 标题：取第一行问句，方便 Dify 展示
        title = text.split("\n", 1)[0][:80]
        records.append(
            Record(
                content=text,
                score=round(score, 4),
                title=title,
                metadata={
                    "source": "咨询数据V2.md",
                    "table": TABLE_NAME,
                    "knowledge_id": req.knowledge_id or "",
                },
            )
        )

    return RetrievalResponse(records=records)


@app.get("/")
async def health():
    return {"status": "ok", "service": "dify-external-knowledge", "rows": table.count_rows()}


if __name__ == "__main__":
    # host=0.0.0.0 便于 Dify 容器/局域网访问
    uvicorn.run(app, host="0.0.0.0", port=PORT)
