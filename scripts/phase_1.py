content = """fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
aiosqlite>=0.20.0
alembic==1.13.0
pydantic-settings==2.4.0
openai==1.50.0
sqlite-vec>=0.1.0
cachetools>=5.3.0
click>=8.1.0
httpx>=0.28.0
python-multipart>=0.0.12
"""
with open("backend/requirements.txt", "w", encoding="utf-8") as f:
    f.write(content)
print("Phase 1: requirements cleaned")
