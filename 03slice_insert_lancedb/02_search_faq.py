"""第 3 课 · 在已入库的 faq 表里做向量检索

前提：
  已运行 01_slice_embed_insert.py，.lancedb 里有表「faq」

运行：
  cd F:\\workspace\\ai_dmx\\xianglianghua\\03slice_insert_lancedb
  uv run python 02_search_faq.py
"""
import lancedb
from sentence_transformers import SentenceTransformer

# ========== 1. 连库、加载同一套模型 ==========
db = lancedb.connect("./.lancedb")
table = db.open_table("faq")
model = SentenceTransformer("../xianglianghuamoxing")

print(f"表 faq 共 {table.count_rows()} 条")
print("*" * 40)

# ========== 2. 改这里的查询词试试 ==========
query = "课程支持在公司和家里两台电脑看吗？"

# ========== 3. 向量搜索（默认 L2，越小越像） ==========
results = (
    table.search(model.encode(query).tolist())
    .limit(3)
    .to_list()
)

print(f"查询：{query}\n")
for i, r in enumerate(results, 1):
    print(f"--- Top {i}（L2距离 {r['_distance']:.3f}）---")
    print(r["text"])
    print()
