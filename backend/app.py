from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import json, os, re
from database import get_chart
from engine import build_chart

ROOT = os.path.dirname(os.path.dirname(__file__))
ATTRIBUTION = {
  "dataset": "紫微斗数开源解读数据集 v4.0（674,976 张命盘 × 13 维）",
  "source": "https://github.com/Renhuai123/ziwei-doushu",
  "author": "王多鱼AI",
  "license": "CC BY 4.0"
}
DIMENSIONS = {"overview":"命格总览","personality":"性格","love":"感情","career":"事业","wealth":"财运","health":"健康","family":"兄弟","children":"子女","move":"迁移","friends":"人际","home":"田宅","spirit":"福德","parents":"父母"}

def send_json(handler, status, body):
    raw = json.dumps(body, ensure_ascii=False).encode()
    handler.send_response(status); handler.send_header("Content-Type", "application/json; charset=utf-8"); handler.send_header("Content-Length", str(len(raw))); handler.end_headers(); handler.wfile.write(raw)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path)
        if path.path == "/api/health": return send_json(self, 200, {"ok": True, "attribution": ATTRIBUTION})
        if path.path == "/api/chart": return self.chart(parse_qs(path.query))
        if path.path in ("/", "/index.html"):
            return self.static("frontend/index.html", "text/html; charset=utf-8")
        if path.path.startswith("/static/"):
            return self.static("frontend/" + path.path[len("/static/"):], {".js":"text/javascript; charset=utf-8", ".css":"text/css; charset=utf-8"}.get(os.path.splitext(path.path)[1], "application/octet-stream"))
        send_json(self, 404, {"error":"未找到页面"})
    def chart(self, q):
        date = q.get("date", [""])[0]; hour = q.get("hour", [""])[0]; gender = q.get("gender", [""])[0]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) or not hour.isdigit() or int(hour) not in range(12) or gender not in ("male", "female"):
            return send_json(self, 400, {"error":"请提供有效的日期、0–11 时辰索引和性别。"})
        key=f"{date}-{hour}-{gender}"; row=get_chart(key)
        if not row: return send_json(self, 404, {"error":"未找到对应命盘，请检查日期、时辰和性别。", "key":key, "attribution":ATTRIBUTION})
        interpretations=row.get("interpretations", row.get("c", {}))
        try: chart=build_chart(int(date[:4]),int(date[5:7]),int(date[8:10]),int(hour),gender)
        except ValueError as exc: return send_json(self,422,{"error":str(exc),"key":key})
        return send_json(self, 200, {"key":key,"date":date,"hour":int(hour),"gender":gender,"palaces":chart["palaces"],"engine":{"source":"Renhuai123/ziwei-doushu","mingGongBranch":chart["mingGongBranch"],"shenGongBranch":chart["shenGongBranch"],"wuxingJuName":chart["wuxingJuName"],"mingZhu":chart.get("mingZhu"),"shenZhu":chart.get("shenZhu")},"interpretations":[{"key":k,"title":DIMENSIONS.get(k,k),"text":v} for k,v in interpretations.items()],"attribution":ATTRIBUTION})
    def static(self, rel, content_type):
        p=os.path.join(ROOT, rel)
        if not os.path.isfile(p): return send_json(self,404,{"error":"文件不存在"})
        data=open(p,"rb").read(); self.send_response(200); self.send_header("Content-Type",content_type); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self, *_): pass

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
