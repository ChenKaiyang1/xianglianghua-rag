"""第 2 课 · 切片方式 1：按字数硬切（固定长度 + 重叠）

思路：
  - 不理解内容，只按「每 N 个字切一刀」
  - 相邻两片故意重叠几个字，避免一句话刚好被切断后检索不到前半截
  - 优点：简单、快、不花钱、结果稳定
  - 缺点：可能把「问」和「答」切到两片里，语义被切断

运行：
  cd F:\\workspace\\ai_dmx\\xianglianghua\\02doc_pdf_md_slice
  uv run python 01_slice_by_size.py
"""

# 每片 200 字，相邻两片重叠 40 字（老师演示常用 1024/50，这里调小方便看）
CHUNK_SIZE = 200
CHUNK_OVERLAP = 40

# 1. 读 Markdown（本身就是纯文本，open 就够）
with open("doc/咨询数据V2.md", encoding="utf-8") as f:
    text = f.read()

print(f"原文总字数：{len(text)}")
print(f"切片参数：每片 {CHUNK_SIZE} 字，重叠 {CHUNK_OVERLAP} 字")
print("*" * 50)

# 2. 滑动窗口切片
#    步长 = CHUNK_SIZE - CHUNK_OVERLAP = 160
#    即每次从上一片起点往后挪 160 个字，再取 200 个字
#    所以相邻两片会有 40 个字重复
step = CHUNK_SIZE - CHUNK_OVERLAP
chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), step)]

# 3. 打印每一片（只打印前 80 字 + 字数，避免刷屏）
print(f"共切成 {len(chunks)} 片\n")
for i, chunk in enumerate(chunks, 1):
    preview = chunk.replace("\n", " ")
    if len(preview) > 80:
        preview = preview[:80] + "..."
    print(f"--- 第 {i} 片（{len(chunk)} 字）---")
    print(preview)
    print()
