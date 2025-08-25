
#!/usr/bin/env python3
import os, json, datetime, subprocess
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(root)
reports = os.path.join(repo_root, "reports")
status_dir = os.path.join(repo_root, "site_public")
def read_state():
  p=os.path.join(reports,"DEPLOY_STATE.json")
  try: return json.load(open(p,"r",encoding="utf-8"))
  except: return {}
def latest_tag():
  try:
    out = subprocess.check_output(["git","describe","--tags","--abbrev=0"], text=True).strip()
    return out
  except Exception:
    return None
def main():
  state=read_state()
  ver = latest_tag() or "n/a"
  now = datetime.datetime.utcnow().isoformat()+"Z"
  html = f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>StegVerse Status</title></head><body><h1>StegVerse Status</h1><p>Generated: {now}</p><p>Version: {ver}</p><pre>{json.dumps(state, indent=2)}</pre></body></html>"
  os.makedirs(status_dir, exist_ok=True)
  open(os.path.join(status_dir,"status.html"),"w",encoding="utf-8").write(html)
  os.makedirs(reports, exist_ok=True)
  json.dump({"generated": now, "version": ver, "deploy": state}, open(os.path.join(status_dir,"status.json"),"w",encoding="utf-8"))
  print("Status site generated.")
if __name__ == "__main__":
  main()
