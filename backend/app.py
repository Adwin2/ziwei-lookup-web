from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import json, os, re
import database
from database import get_chart
from engine import build_chart

ROOT = os.path.dirname(os.path.dirname(__file__))
ATTRIBUTION={"dataset":"紫微斗数开源解读数据集 v4.0（674,976 张命盘 × 13 维）","source":"https://github.com/Renhuai123/ziwei-doushu","author":"王多鱼AI","license":"CC BY 4.0"}
DIMENSIONS={"overview":"命格总览","personality":"性格","love":"感情","career":"事业","wealth":"财运","health":"健康","family":"兄弟","children":"子女","move":"迁移","friends":"人际","home":"田宅","spirit":"福德","parents":"父母"}
EMAIL_RE=re.compile(r"^[^@\s]{1,80}@[^@\s]{1,80}\.[^@\s]{2,30}$")

def send_json(h,status,body,headers=None):
    raw=json.dumps(body,ensure_ascii=False).encode(); h.send_response(status); h.send_header("Content-Type","application/json; charset=utf-8"); h.send_header("Cache-Control","no-store"); h.send_header("Content-Length",str(len(raw)))
    for k,v in (headers or {}).items(): h.send_header(k,v)
    h.end_headers(); h.wfile.write(raw)

def cookie(h):
    value=h.headers.get("Cookie","")
    for item in value.split(";"):
        if item.strip().startswith("session="): return item.strip().split("=",1)[1]
    return None

def body(h):
    try: return json.loads(h.rfile.read(int(h.headers.get("Content-Length","0"))))
    except (ValueError,json.JSONDecodeError): return {}

def user_required(h):
    user=database.user_from_token(cookie(h))
    if not user: send_json(h,401,{"error":"请先登录。"}); return None
    return user

def valid_chart(q):
    date=q.get("date",[""])[0]; hour=q.get("hour",[""])[0]; gender=q.get("gender",[""])[0]
    return date,hour,gender, bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}",date) and hour.isdigit() and int(hour) in range(12) and gender in ("male","female"))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=urlparse(self.path)
        if path.path=="/api/health": return send_json(self,200,{"ok":True,"attribution":ATTRIBUTION})
        if path.path=="/api/auth/me": return self.me()
        if path.path=="/api/chart": return self.chart(parse_qs(path.query))
        if path.path in ("/","/index.html"): return self.static("frontend/index.html","text/html; charset=utf-8")
        if path.path.startswith("/static/"): return self.static("frontend/"+path.path[len("/static/"):],{".js":"text/javascript; charset=utf-8",".css":"text/css; charset=utf-8"}.get(os.path.splitext(path.path)[1],"application/octet-stream"))
        send_json(self,404,{"error":"未找到页面"})
    def do_POST(self):
        path=urlparse(self.path).path; data=body(self)
        if path=="/api/auth/register": return self.register(data)
        if path=="/api/auth/login": return self.login(data)
        if path=="/api/auth/logout": return self.logout()
        if path=="/api/profiles": return self.profile(data)
        send_json(self,404,{"error":"未找到接口"})
    def do_DELETE(self):
        path=urlparse(self.path)
        if path.path=="/api/profiles":
            user=user_required(self)
            if user:
                try: database.delete_profile(user["id"],int(parse_qs(path.query).get("id",[0])[0])); send_json(self,200,{"ok":True})
                except ValueError: send_json(self,400,{"error":"资料编号无效。"})
            return
        send_json(self,404,{"error":"未找到接口"})
    def register(self,d):
        email=str(d.get("email","")).strip().lower(); password=str(d.get("password","")); name=str(d.get("display_name","")).strip()[:40] or email.split("@")[0]
        if not EMAIL_RE.fullmatch(email) or len(password)<8 or len(password)>128: return send_json(self,400,{"error":"请输入有效邮箱，密码需为 8–128 位。"})
        try: user=database.create_user(email,password,name)
        except Exception as e:
            if "UNIQUE" in str(e): return send_json(self,409,{"error":"该邮箱已注册，请直接登录。"})
            raise
        token=database.create_session(user["id"]); return send_json(self,201,{"user":user,"profiles":[],"history":[]},{"Set-Cookie":f"session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000"})
    def login(self,d):
        user=database.authenticate(str(d.get("email","")).strip().lower(),str(d.get("password","")))
        if not user: return send_json(self,401,{"error":"邮箱或密码不正确。"})
        token=database.create_session(user["id"]); profiles,history=database.get_user_data(user["id"])
        return send_json(self,200,{"user":user,"profiles":profiles,"history":history},{"Set-Cookie":f"session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000"})
    def logout(self):
        database.delete_session(cookie(self)); return send_json(self,200,{"ok":True},{"Set-Cookie":"session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"})
    def me(self):
        user=database.user_from_token(cookie(self))
        if not user: return send_json(self,200,{"user":None,"profiles":[],"history":[]})
        profiles,history=database.get_user_data(user["id"]); return send_json(self,200,{"user":user,"profiles":profiles,"history":history})
    def profile(self,d):
        user=user_required(self)
        if not user: return
        label=str(d.get("label","")).strip()[:40]; date=str(d.get("birth_date","")).strip(); hour=d.get("hour"); gender=d.get("gender")
        if not label or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date) or not isinstance(hour,int) or hour not in range(12) or gender not in ("male","female"): return send_json(self,400,{"error":"资料信息不完整。"})
        database.save_profile(user["id"],label,date,hour,gender); profiles,history=database.get_user_data(user["id"]); return send_json(self,201,{"profiles":profiles,"history":history})
    def chart(self,q):
        date,hour,gender,ok=valid_chart(q)
        if not ok: return send_json(self,400,{"error":"请提供有效的日期、0–11 时辰索引和性别。"})
        key=f"{date}-{hour}-{gender}"; row=get_chart(key)
        if not row: return send_json(self,404,{"error":"未找到对应命盘，请检查日期、时辰和性别。","key":key,"attribution":ATTRIBUTION})
        try: chart=build_chart(int(date[:4]),int(date[5:7]),int(date[8:10]),int(hour),gender)
        except ValueError as exc: return send_json(self,422,{"error":str(exc),"key":key})
        user=database.user_from_token(cookie(self))
        if user: database.add_history(user["id"],key,date,int(hour),gender)
        interpretations=row.get("interpretations",row.get("c",{}))
        return send_json(self,200,{"key":key,"date":date,"hour":int(hour),"gender":gender,"palaces":chart["palaces"],"engine":{"source":"Renhuai123/ziwei-doushu","mingGongBranch":chart["mingGongBranch"],"shenGongBranch":chart["shenGongBranch"],"wuxingJuName":chart["wuxingJuName"],"mingZhu":chart.get("mingZhu"),"shenZhu":chart.get("shenZhu")},"interpretations":[{"key":k,"title":DIMENSIONS.get(k,k),"text":v} for k,v in interpretations.items()],"attribution":ATTRIBUTION})
    def static(self,rel,content_type):
        p=os.path.join(ROOT,rel)
        if not os.path.isfile(p): return send_json(self,404,{"error":"文件不存在"})
        data=open(p,"rb").read(); self.send_response(200); self.send_header("Content-Type",content_type); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self,*_): pass

if __name__=="__main__":
    database.init_auth(); ThreadingHTTPServer(("0.0.0.0",int(os.environ.get("PORT","8000"))),Handler).serve_forever()
