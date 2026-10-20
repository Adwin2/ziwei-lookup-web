# 紫微斗数查表服务

围绕 [Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu) 开源起盘引擎与 v4.0 解读数据集的确定性查表网站。服务端不调用 AI/LLM，也不在查询时重新计算命盘，只读取预先导入的 SQLite。

## 本地运行

```bash
python3 scripts/ingest.py --db data/ziwei.sqlite3 path/to/year-2004.jsonl
PYTHONPATH=backend ZIWEI_DB=$PWD/data/ziwei.sqlite3 python3 backend/app.py
```

打开 `http://localhost:8000`。API 示例：`/api/chart?date=2004-03-15&hour=7&gender=female`。

## 数据灌入

从上游 Release `v4.0-13d` 下载所需年份的 `year-YYYY.jsonl.zst`，按上游要求使用 zstd `--long=27` 解压，然后流式导入：

```bash
zstd -d --long=27 year-2004.jsonl.zst
python3 scripts/ingest.py --db data/ziwei.sqlite3 year-2004.jsonl
```

完整数据解压后约 56.6GB，建议只导入实际需要的年份。原始数据与生成的 SQLite 已在 `.gitignore` 中排除。`fixtures/sample.jsonl` 仅用于 Docker 连通性验收。

## Docker 部署

```bash
docker compose up --build
```

Compose 会先导入内置示例，再启动网站。生产部署时，把已下载并解压的年度 JSONL 放入自定义 ingest 镜像或挂载目录，并运行 `scripts/ingest.py` 生成持久化 SQLite，再启动 `web` 服务。服务器反向代理到容器 `8000` 端口即可。

## 来源与许可

数据集：紫微斗数开源解读数据集 v4.0（674,976 张命盘 × 13 维），来源 <https://github.com/Renhuai123/ziwei-doushu>，作者王多鱼AI，CC BY 4.0。起盘引擎代码来自该项目 `lib/ziwei/`，遵循其 MIT 许可。数据集中的特定引文仍受上游说明约束。
