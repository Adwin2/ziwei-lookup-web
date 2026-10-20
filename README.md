# 紫微斗数查表服务

围绕 [Renhuai123/ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu) 开源起盘引擎与 v4.0 解读数据集的确定性查表网站。服务端不调用 AI/LLM；查询时使用项目内接入的上游 `lib/ziwei/algorithm.ts` 起盘引擎生成完整十二宫，再读取预先导入 SQLite 中的 v4.0 解读文本。

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

## 起盘引擎

`engine/lib/ziwei/` 来自上游项目的 `lib/ziwei/`，通过 `engine/chart-runner.ts` 调用其 `generateChart()`。引擎依赖 `iztro` 和 `lunar-javascript`，按公历日期、0–11 时辰索引和性别生成完整宫位、主星、辅星、亮度及命身宫信息。

## 账户功能

游客可以直接查盘。注册后可以保存出生资料、查看最近 20 次查询，并从资料列表快速重新查盘。账户数据保存在 SQLite；密码只保存为 PBKDF2-SHA256 哈希，登录状态使用 HttpOnly、SameSite=Lax 会话 Cookie。生产环境应在 HTTPS 反向代理后运行，并定期备份 SQLite 数据卷。

账户接口：`POST /api/auth/register`、`POST /api/auth/login`、`POST /api/auth/logout`、`GET /api/auth/me`、`POST/DELETE /api/profiles`。
