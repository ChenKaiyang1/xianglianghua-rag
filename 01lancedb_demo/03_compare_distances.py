"""对应老师 09/10/11：同一批数据、同一个查询，对比三种距离

L2      默认距离，_distance 越小越像
cosine  余弦距离 = 1 - 余弦相似度，_distance 越小越像；打印时转成相似度
dot     点积（内积）：先归一化，归一化后点积≈余弦相似度；打印时转成得分
"""
import numpy as np
import lancedb
from sentence_transformers import SentenceTransformer


def normalize(v):
    v = np.asarray(v, dtype=float)
    return (v / np.linalg.norm(v)).tolist()


db = lancedb.connect("./.lancedb")
model = SentenceTransformer("../xianglianghuamoxing")

data = [
    {"text": "我喜欢在图书馆里安静地看书和学习。"},
    {"text": "篮球是我最喜欢的运动，我经常和朋友一起去球场。"},
    {"text": "今天天气真好，阳光明媚，适合去公园散步。"},
    {"text": "周末我习惯去咖啡馆点一杯拿铁，然后读一本小说。"},
    {"text": "傍晚的海边微风徐徐，沿着沙滩散步让我感觉很放松。"},
    {"text": "我热爱烹饪，尝试各种新菜谱是我最大的乐趣。"},
]

query = "户外运动"
print(f"查询：{query}")
print("*" * 40)


def run(distance_type: str, use_normalize: bool = False):
    rows = []
    for item in data:
        vec = model.encode(item["text"])
        if use_normalize:
            vec = normalize(vec)
        else:
            vec = vec.tolist()
        rows.append({"text": item["text"], "vector": vec})

    table_name = f"{distance_type}_demo"
    table = db.create_table(table_name, rows, mode="overwrite")

    qvec = model.encode(query)
    if use_normalize:
        qvec = normalize(qvec)
    else:
        qvec = qvec.tolist()

    results = (
        table.search(qvec)
        .distance_type(distance_type)
        .limit(3)
        .to_list()
    )

    print(f"\n【{distance_type}】")
    for i, r in enumerate(results, 1):
        d = r["_distance"]
        if distance_type == "l2":
            label = f"L2距离: {d:.3f}（越小越像）"
        elif distance_type == "cosine":
            label = f"余弦相似度: {1 - d:.3f}（越大越像）"
        else:  # dot
            label = f"点积得分: {1 - d:.3f}（越大越像）"
        print(f"  {i}. {r['text']}")
        print(f"     {label}")


run("l2")
run("cosine")
run("dot", use_normalize=True)

print("\n" + "*" * 40)
print("说明：三种尺子量同一批点，排序可能接近；")
print("L2 看绝对距离；余弦只看方向；点积在归一化后约等于余弦。")
