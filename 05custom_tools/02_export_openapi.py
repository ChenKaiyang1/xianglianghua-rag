"""导出 OpenAPI JSON，供 Dify「自定义工具」导入。

运行：
  cd F:\\workspace\\ai_dmx\\xianglianghua\\05custom_tools
  uv run python 02_export_openapi.py

生成 openapi_for_dify.json。
Dify 导入时：Schema 类型选 OpenAPI，粘贴 JSON；
或「从 URL 中导入」：http://host.docker.internal:8100/openapi.json
"""
import importlib.util
import json
from pathlib import Path

server_path = Path(__file__).parent / "01_custom_tools_server.py"
spec = importlib.util.spec_from_file_location("custom_tools", server_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

schema = mod.app.openapi()

# Dify 自定义工具需要 servers，否则不知道请求打到哪里
# Docker 里的 Dify 访问宿主机用 host.docker.internal
schema["servers"] = [
    {"url": "http://host.docker.internal:8100", "description": "Dify Docker -> host"},
    {"url": "http://127.0.0.1:8100", "description": "本机调试"},
]

out = Path(__file__).parent / "openapi_for_dify.json"
out.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"已导出：{out}")
print("Dify：工具 → 自定义 → 创建自定义工具")
print("  1) Schema 类型选 OpenAPI")
print("  2) 粘贴 openapi_for_dify.json 内容")
print("  3) 或从 URL 导入 http://host.docker.internal:8100/openapi.json")
