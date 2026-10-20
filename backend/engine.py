"""调用上游 Renhuai123/ziwei-doushu 的真实起盘引擎。"""
import json, os, subprocess
ROOT=os.path.dirname(os.path.dirname(__file__))
def build_chart(year,month,day,hour,gender):
 payload={"year":year,"month":month,"day":day,"hour":hour,"gender":gender}
 try: r=subprocess.run(["npx","tsx","engine/chart-runner.ts",json.dumps(payload)],cwd=ROOT,text=True,capture_output=True,check=True,timeout=20)
 except subprocess.CalledProcessError as e: raise ValueError(e.stderr.strip() or "上游起盘引擎执行失败") from e
 except subprocess.TimeoutExpired as e: raise ValueError("上游起盘引擎响应超时") from e
 return json.loads(r.stdout)
