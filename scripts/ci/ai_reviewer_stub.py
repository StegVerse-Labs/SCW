
#!/usr/bin/env python3
import subprocess, re, os
def get_changed_files():
  base = os.environ.get("GITHUB_BASE_REF","main")
  out = subprocess.check_output(["git","diff","--name-only","origin/"+base,"HEAD"], text=True)
  return [x.strip() for x in out.splitlines() if x.strip()]
def check_msgs():
  base = os.environ.get("GITHUB_BASE_REF","main")
  out = subprocess.check_output(["git","log","--pretty=%s","origin/"+base+"..HEAD"], text=True)
  bad=[l for l in out.splitlines() if not re.match(r"^(feat|fix|docs|chore|refactor|test|ci|build)(\(.+\))?: ", l)]
  return bad
def main():
  files = get_changed_files()
  bad = check_msgs()
  notes=[]
  if bad: notes.append("❗ Non‑conventional commits:\n- " + "\n- ".join(bad[:10]))
  if any(f.endswith(".md") for f in files): notes.append("📝 Docs changed — update README/TOC if needed.")
  if any(f.startswith("scripts/") for f in files): notes.append("🔧 Scripts changed — run pre-commit & CI locally.")
  print("\n\n".join(notes) if notes else "Looks good. ✅")
if __name__=="__main__": main()
