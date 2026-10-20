#!/usr/bin/env python3
"""流式导入 v4 JSONL（支持 .jsonl 和 zstd 解压后的文件）。"""
import argparse, json, pathlib, sqlite3, sys

def rows(paths):
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for n,line in enumerate(f,1):
                if not line.strip(): continue
                try: obj=json.loads(line)
                except json.JSONDecodeError as e: raise SystemExit(f"{path}:{n}: JSON 无效: {e}")
                key=obj.get("k")
                if not key: continue
                yield key, json.dumps({"k":key,"y":obj.get("y"),"m":obj.get("m"),"d":obj.get("d"),"h":obj.get("h"),"g":obj.get("g"),"ms":obj.get("ms"),"interpretations":obj.get("c",{})},ensure_ascii=False)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--db", required=True); ap.add_argument("files", nargs="+"); args=ap.parse_args()
    db=sqlite3.connect(args.db); db.execute("PRAGMA journal_mode=WAL"); db.execute("CREATE TABLE IF NOT EXISTS charts (chart_key TEXT PRIMARY KEY, payload TEXT NOT NULL)")
    count=0
    with db:
        for key,payload in rows(args.files): db.execute("INSERT OR REPLACE INTO charts VALUES (?,?)",(key,payload)); count+=1
    print(f"已导入 {count} 条命盘")
if __name__ == "__main__": main()
