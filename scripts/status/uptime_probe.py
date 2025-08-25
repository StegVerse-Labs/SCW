
#!/usr/bin/env python3
import os, json, datetime, requests
STATE="reports/DEPLOY_STATE.json"; UPTIME="reports/uptime.json"
def get_target():
  if os.path.exists(STATE):
    try:
      st=json.load(open(STATE,"r",encoding="utf-8")); return st.get("url")
    except: return None
def probe(url, timeout=10):
  try:
    import requests
    r=requests.get(url, timeout=timeout); ok=r.ok
    return {"t": datetime.datetime.utcnow().isoformat()+"Z", "ok": ok, "code": r.status_code}
  except Exception as e:
    return {"t": datetime.datetime.utcnow().isoformat()+"Z", "ok": False, "err": str(e)}
def main():
  url=os.getenv("UPTIME_URL") or get_target()
  if not url: print("No target URL"); return
  rec=probe(url); data=[]
  if os.path.exists(UPTIME):
    try: data=json.load(open(UPTIME,"r",encoding="utf-8"))
    except: data=[]
  data.append(rec); data=data[-500:]
  json.dump(data, open(UPTIME,"w",encoding="utf-8"), indent=2)
  print("Probed", url, rec)
if __name__=="__main__": main()
