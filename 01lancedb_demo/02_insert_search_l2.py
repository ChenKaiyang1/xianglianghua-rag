"""对应老师 05：建表、插入、按默认 L2 距离搜索

查询词：户外运动
预期：篮球那条排最前（语义最相关）
"""
import lancedb
from sentence_transformers import SentenceTransformer

# 1. 连接数据库
db = lancedb.connect("./.lancedb")

# 2. 加载模型（我们用已下载的多语言模型）
model = SentenceTransformer("../xianglianghuamoxing")

# 3. 准备数据并生成向量
data = [
    {"text": "我喜欢在图书馆里安静地看书和学习。"},
    {"text": "篮球是我最喜欢的运动，我经常和朋友一起去球场。"},
    {"text": "今天天气真好，阳光明媚，适合去公园散步。"},
    {"text": "周末我习惯去咖啡馆点一杯拿铁，然后读一本小说。"},
    {"text": "傍晚的海边微风徐徐，沿着沙滩散步让我感觉很放松。"},
    {"text": "我热爱烹饪，尝试各种新菜谱是我最大的乐趣。"},
]

for item in data:
    item["vector"] = model.encode(item["text"]).tolist()

print(f"已向量化 {len(data)} 条文本，向量维度 {len(data[0]['vector'])}")
print("*" * 30)

# 4. 创建表并插入数据（表名 documents，已存在则覆盖）
table = db.create_table("documents", data, mode="overwrite")
print("表创建成功，行数 =", table.count_rows())

# 5. 搜索（LanceDB 默认是 L2：距离越小越相似）
query = "户外运动"
results = table.search(model.encode(query).tolist()).limit(3).to_list()

# 6. 查看结果
print(f"查询：{query}")
print("*" * 30)
for i, r in enumerate(results, 1):
    print(f"{i}. {r['text']}  (L2距离: {r['_distance']:.3f}，越小越像)")
