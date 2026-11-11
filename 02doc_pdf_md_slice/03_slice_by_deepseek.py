"""第 2 课 · 切片方式 3：DeepSeek 语义切片（AI 判断在哪里切）

和前两个本地切法的区别：
  - 按字数：不管内容，固定 N 字一刀，可能把问答切断
  - 按「问：」：格式固定才好用
  - 这里：把「在哪儿切」交给大模型按语义判断，适合没有固定格式的文档

前提：
  1. 已安装 openai 库（项目依赖里已有）
  2. 设置环境变量 DEEPSEEK_API_KEY（不要把 Key 写进代码文件）

运行（PowerShell）：
  $env:DEEPSEEK_API_KEY = "sk-你的key"
  cd F:\\workspace\\ai_dmx\\xianglianghua\\02doc_pdf_md_slice
  uv run python 03_slice_by_deepseek.py
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

# ========== 3. 调 DeepSeek（OpenAI 兼容接口，只换 base_url） ==========
api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    raise SystemExit(
        "请先设置环境变量 DEEPSEEK_API_KEY\n"
        "PowerShell 示例：$env:DEEPSEEK_API_KEY = \"sk-你的key\""
    )

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

print("正在调用 DeepSeek 切片，请稍等...")
resp = client.chat.completions.create(
    model="deepseek-chat",              # 也可试 deepseek-reasoner；老师脚本里写过 deepseek-flash
    messages=[{"role": "user", "content": PROMPT + text}],
    response_format={"type": "json_object"},  # 强制返回 JSON，省得从长文本里抠
)

# ========== 4. 解析并打印 ==========
content = resp.choices[0].message.content
chunks = json.loads(content)["chunks"]

print(f"共切成 {len(chunks)} 片\n")
for i, chunk in enumerate(chunks, 1):
    preview = chunk.replace("\n", " / ")
    if len(preview) > 100:
        preview = preview[:100] + "..."
    print(f"--- 第 {i} 片（{len(chunk)} 字）---")
    print(preview)
    print()
