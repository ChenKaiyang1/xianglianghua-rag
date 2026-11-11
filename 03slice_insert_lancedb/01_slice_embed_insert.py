"""第 3 课 · 切片 → 向量化 → 写入 LanceDB

完整入库流程：
  1. 读「咨询数据V2.md」
  2. 按「问：」切片（本地规则，不花钱、结果稳定）
  3. 用你下载的嵌入模型，给每一片算一个 384 维向量
  4. 整批写入 LanceDB 表「faq」

说明：
  - 入库和查询必须用同一个模型，否则向量空间对不上
  - 也可以把第 2 步换成 MiMo 切片结果；本脚本用本地切法，方便反复跑

运行：
  cd F:\\workspace\\ai_dmx\\xianglianghua\\03slice_insert_lancedb
  uv run python 01_slice_embed_insert.py
"""
import re

import lancedb
from sentence_transformers import SentenceTransformer

# ========== 1. 读文档 ==========
with open("doc/咨询数据V2.md", encoding="utf-8") as f:
    text = f.read()
print(f"原文总字数：{len(text)}")

# ========== 2. 按「问：」切片 ==========
parts = re.split(r"(?=问：)", text)
chunks = []
for p in parts:
    if not p.strip():
        continue
    cleaned = re.sub(r"\n\s*\n+", "\n", p).strip()
    chunks.append(cleaned)

print(f"切片完成：{len(chunks)} 片")

# ========== 3. 加载模型并编码 ==========
model = SentenceTransformer("../xianglianghuamoxing")
print(f"模型加载成功，维度 = {model.get_embedding_dimension()}")

# 一片一个向量；正文和向量放同一行，方便后面搜出正文
vectors = model.encode(chunks, show_progress_bar=True)
data = [
    {"text": chunk, "vector": vec.tolist()}
    for chunk, vec in zip(chunks, vectors)
]
print(f"已向量化 {len(data)} 条")

# ========== 4. 写入 LanceDB ==========
db = lancedb.connect("./.lancedb")
# mode=overwrite：表已存在则覆盖，方便反复调试
table = db.create_table("faq", data, mode="overwrite")

print("*" * 40)
print("表名：faq")
print("行数：", table.count_rows())
print("数据目录：", db.uri)
print("入库完成。下一步可用问题检索。")
