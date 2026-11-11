"""第 2 课 · 切片方式 2：按「问：」语义边界切（正则 split）

思路：
  - 这份语料是一条条「问：… 答：…」
  - 用正则在每个「问：」前面切一刀，保证一问一答完整落在同一片里
  - 优点：不会把问答拆开，检索时上下文完整
  - 缺点：只适合有固定格式的文档；没有「问：」就要换别的规则

运行：
  cd F:\\workspace\\ai_dmx\\xianglianghua\\02doc_pdf_md_slice
  uv run python 02_slice_by_qa.py
"""
import re

# 1. 读文档
with open("doc/咨询数据V2.md", encoding="utf-8") as f:
    text = f.read()

print(f"原文总字数：{len(text)}")
print("切片规则：在每个「问：」前面切一刀")
print("*" * 50)

# 2. re.split 切分
#    (?=问：) 是「零宽断言」：匹配「问：」前面的位置，但不把「问：」吃掉
#    这样每一片都还以「问：」开头
parts = re.split(r"(?=问：)", text)

# 3. 去掉空片、压掉多余空行
chunks = []
for p in parts:
    if not p.strip():
        continue
    cleaned = re.sub(r"\n\s*\n+", "\n", p).strip()
    chunks.append(cleaned)

# 4. 打印
print(f"共切成 {len(chunks)} 片\n")
for i, chunk in enumerate(chunks, 1):
    preview = chunk.replace("\n", " / ")
    if len(preview) > 100:
        preview = preview[:100] + "..."
    print(f"--- 第 {i} 片（{len(chunk)} 字）---")
    print(preview)
    print()
