"""Check the current index without printing secret values; historical findings are in SECURITY.md."""
import re
import subprocess
from pathlib import Path

files = subprocess.check_output(['git','ls-files'],text=True).splitlines()
forbidden = [name for name in files if name.startswith(('data/','venv/','.venv/'))
             or '__pycache__' in name or name.endswith(('.db','.backup','.pyc'))
             or (Path(name).name.startswith('.env') and name != '.env.example')
             or re.fullmatch(r'env.*\.txt',Path(name).name)]
# Only exact credential-looking literals, not variable names or examples.
pattern = re.compile(rb'(?:sk-[A-Za-z0-9]{24,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)')
for name in files:
    if Path(name).suffix in ('.py','.txt','.md','.yaml','.yml','.toml') and pattern.search(Path(name).read_bytes()):
        forbidden.append(name)
if forbidden:
    raise SystemExit('Repository hygiene failed (paths only): ' + ', '.join(sorted(set(forbidden))))
print('Repository hygiene passed; no forbidden local artifacts or credential-like literals in tracked text.')
