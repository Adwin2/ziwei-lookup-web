"""SQLite 查询层：服务端只读预先计算的数据。"""
import json, os, sqlite3

DB_PATH = os.environ.get("ZIWEI_DB", "/app/data/ziwei.sqlite3")

def get_chart(key: str):
    if not os.path.exists(DB_PATH):
        return None
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT payload FROM charts WHERE chart_key = ?", (key,)).fetchone()
        return json.loads(row["payload"]) if row else None
