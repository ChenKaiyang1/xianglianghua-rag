from sentence_transformers import SentenceTransformer
import lancedb

# 1. 加载模型
model = SentenceTransformer("../xianglianghuamoxing")
print("模型加载成功，维度 =", model.get_embedding_dimension())

# 2. 试编码两句话
vecs = model.encode(["我喜欢在图书馆看书", "今天天气不错适合散步"])
print("向量形状 =", vecs.shape)  # 应为 (2, 384)

# 3. 连接本地向量库（就是一个文件夹）
db = lancedb.connect("./.lancedb")
print("LanceDB 连接成功，数据目录:", db.uri)
