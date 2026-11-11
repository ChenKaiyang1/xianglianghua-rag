from sentence_transformers import SentenceTransformer

model = SentenceTransformer("../xianglianghuamoxing")

text1 = "我喜欢在图书馆看书"
text2 = "今天天气不错适合散步"
text3 = "我想去球场打篮球"

v1, v2, v3 = model.encode([text1, text2, text3])

print("=== 第 1 句向量（前 8 维）===")
print(text1, "->", v1[:8], "...")
print()
print("=== 第 2 句向量（前 8 维）===")
print(text2, "->", v2[:8], "...")
print()

# 简单余弦相似度：-1~1，越接近 1 越像
import numpy as np

def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

print("=== 语义相似度（余弦）===")
print(f"「{text1}」 vs 「{text2}」 = {cosine(v1, v2):.3f}  （都偏生活，应较高）")
print(f"「{text1}」 vs 「{text3}」 = {cosine(v1, v3):.3f}  （看书 vs 篮球，应较低）")
