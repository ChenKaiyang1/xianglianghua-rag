"""第 2 课 · 切片方式 3：小米 MiMo 语义切片（AI 判断在哪里切）

和前两个本地切法的区别：
  - 按字数：不管内容，固定 N 字一刀，可能把问答切断
  - 按「问：」：格式固定才好用
  - 这里：把「在哪儿切」交给大模型按语义判断，适合没有固定格式的文档

小米 MiMo（OpenAI 兼容）：
  base_url = https://api.xiaomimimo.com/v1
  model    = mimo-v2.5

前提：
  环境变量 MIMO_API_KEY 已配置（你机器上已有，无需再设）

运行（PowerShell）：
  cd F:\\workspace\\ai_dmx\\xianglianghua\\02doc_pdf_md_slice
  uv run python 03_slice_by_mimo.py
"""
import json
import os

from openai import OpenAI

# ========== 1. 读文档 ==========
with open("doc/咨询数据V2.md", encoding="utf-8") as f:
    text = f.read()

print(f"原文总字数：{len(text)}")

# ========== 2. 提示词：告诉模型切什么、怎么切、返回什么格式 ==========
PROMPT = """把下面的资料切片，供知识库检索使用：
1、资料是一条条「问：/答：」的问答记录，按语义切片，不要把问题和回答截断；
2、只输出 JSON，格式：{"chunks": ["片段1", "片段2"]}

资料：
"""

# ========== 3. 调小米 MiMo（OpenAI 兼容协议） ==========
# 优先用你机器上已有的 MIMO_API_KEY
api_key = os.environ.get("MIMO_API_KEY") or os.environ.get("XIAOMI_MIMO_API_KEY")
if not api_key:
    raise SystemExit(
        "请先设置环境变量 MIMO_API_KEY\n"
        "PowerShell 示例：$env:MIMO_API_KEY = \"sk-你的key\""
    )

client = OpenAI(
    api_key=api_key,
    base_url="https://api.xiaomimimo.com/v1",  # 小米 MiMo OpenAI 兼容地址
)

print("正在调用 MiMo 切片，请稍等...")
resp = client.chat.completions.create(
    model="mimo-v2.5",
    messages=[{"role": "user", "content": PROMPT + text}],
    # 优先要求 JSON；若模型/接口不支持 response_format，会自动退回纯文本提示
    response_format={"type": "json_object"},
)

# ========== 4. 解析并打印 ==========
content = resp.choices[0].message.content
# 兼容：万一带了 markdown 代码块，先剥掉
if content.strip().startswith("```"):
    content = content.strip().strip("`")
    if content.startswith("json"):
        content = content[4:]
    content = content.strip()

chunks = json.loads(content)["chunks"]

print(f"共切成 {len(chunks)} 片\n")
for i, chunk in enumerate(chunks, 1):
    preview = chunk.replace("\n", " / ")
    if len(preview) > 100:
        preview = preview[:100] + "..."
    print(f"--- 第 {i} 片（{len(chunk)} 字）---")
    print(preview)
    print()
