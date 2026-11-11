"""作业3 · Dify 自定义工具服务（天气 / 读网页 / 查数据库）

三个接口（OpenAPI，可被 Dify「自定义工具」导入）：
  GET /weather?city=北京     —— Open-Meteo 免费天气，无需 API Key
  POST /read_url            —— 抓取网页正文（简化版）
  GET /db_faq?q=退款        —— 在本地 SQLite 里做关键词查询

运行：
  cd F:\\workspace\\ai_dmx\\xianglianghua\\05custom_tools
  uv run python 01_custom_tools_server.py

服务地址（Dify 在 Docker 里时用 host.docker.internal）：
  http://host.docker.internal:8100
  OpenAPI 文档：/openapi.json
"""
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Custom Tools for Dify",
    version="1.0.0",
    description="天气 / 读网页 / FAQ 数据库查询，供 Dify Agent 调用",
    servers=[
        {"url": "http://host.docker.internal:8100", "description": "Dify Docker -> host"},
        {"url": "http://127.0.0.1:8100", "description": "local debug"},
    ],
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "faq_demo.db"


# ============ 初始化演示用 SQLite ============
def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
        """
    )
    cur.execute("SELECT COUNT(*) FROM faq")
    if cur.fetchone()[0] == 0:
        rows = [
            ("课程可以在几台电脑上看？", "默认绑定一台电脑；可联系客服申请两台。"),
            ("课程支持退款吗？", "具体退款政策请以购买页面说明或咨询客服为准。"),
            ("有没有证书？", "目前不提供官方认证证书，更看重实战能力。"),
            ("可以投屏到电视吗？", "不支持直接投屏，可用 HDMI 等有线方式连接。"),
        ]
        cur.executemany(
            "INSERT INTO faq (question, answer) VALUES (?, ?)", rows
        )
        conn.commit()
    conn.close()


init_db()


# ============ 1. 天气（Open-Meteo，免费） ============
@app.get(
    "/weather",
    summary="查询城市当前天气",
    description="使用 Open-Meteo 免费接口，无需 API Key。返回温度、湿度、风速、天气描述。",
)
async def get_weather(
    city: str = Query(..., description="城市中文或英文名，例如：北京 / Shenzhen"),
) -> Dict[str, Any]:
    # 1) 地理编码：城市名 -> 经纬度
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    async with httpx.AsyncClient(timeout=20) as client:
        geo_resp = await client.get(
            geo_url, params={"name": city, "count": 1, "language": "zh"}
        )
        if geo_resp.status_code != 200 or not geo_resp.json().get("results"):
            raise HTTPException(status_code=404, detail=f"找不到城市：{city}")
        loc = geo_resp.json()["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        name_en = loc.get("name", city)
        # results 里可能有多种语言名，优先保留英文名
        city_label = name_en

        # 2) 当前天气
        wx_url = "https://api.open-meteo.com/v1/forecast"
        wx_resp = await client.get(
            wx_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            },
        )
        if wx_resp.status_code != 200:
            raise HTTPException(status_code=502, detail="weather service unavailable")
        current = wx_resp.json().get("current", {})

    code = current.get("weather_code", 0)
    payload = {
        "city": city_label,
        "query_city": city,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": current.get("temperature_2m"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "weather_code": code,
        "description": weather_code_to_text(code, lang="en"),
        "summary": (
            f"{city_label}: {current.get('temperature_2m')}C, "
            f"{weather_code_to_text(code, lang='en')}, "
            f"humidity {current.get('relative_humidity_2m')}%, "
            f"wind {current.get('wind_speed_10m')} km/h"
        ),
    }
    # 明确 UTF-8，避免部分客户端误判编码
    return JSONResponse(content=payload, media_type="application/json; charset=utf-8")


def weather_code_to_text(code: int, lang: str = "en") -> str:
    en = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Rime fog",
        51: "Light drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Rain showers",
        95: "Thunderstorm",
    }
    zh = {
        0: "晴",
        1: "基本晴",
        2: "多云",
        3: "阴",
        45: "雾",
        48: "雾凇",
        51: "毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        80: "阵雨",
        95: "雷暴",
    }
    table = zh if lang == "zh" else en
    return table.get(code, f"unknown code {code}")


# ============ 2. 读网页 ============
class ReadUrlRequest(BaseModel):
    url: str = Field(..., description="要抓取的 http/https 网址")
    max_chars: int = Field(2000, description="最多返回多少字，默认 2000")


@app.post(
    "/read_url",
    summary="抓取网页正文",
    description="请求网页，去掉标签后返回纯文本摘要，供 Agent 阅读。",
)
async def read_url(req: ReadUrlRequest) -> Dict[str, Any]:
    if not req.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="url 必须以 http/https 开头")
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(
            req.url, headers={"User-Agent": "Mozilla/5.0 (compatible; DifyTool/1.0)"}
        )
    html = resp.text
    # 极简去标签：生产可用 trafilatura/readability，这里够作业演示
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return {
        "url": str(req.url),
        "status_code": resp.status_code,
        "content": text[: req.max_chars],
    }


# ============ 3. FAQ 数据库查询 ============
@app.get(
    "/db_faq",
    summary="查询 FAQ 数据库",
    description="在本地 SQLite 的 faq 表里按关键词匹配问题和答案。",
)
async def db_faq(
    q: str = Query(..., description="关键词，例如：退款 / 电脑 / 证书"),
) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT question, answer FROM faq WHERE question LIKE ? OR answer LIKE ?",
        (f"%{q}%", f"%{q}%"),
    )
    rows = [{"question": r[0], "answer": r[1]} for r in cur.fetchall()]
    conn.close()
    return JSONResponse(
        content={"query": q, "count": len(rows), "results": rows},
        media_type="application/json; charset=utf-8",
    )


@app.get("/")
async def health():
    return {"status": "ok", "service": "custom-tools", "port": 8100}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8100)
