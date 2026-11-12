"""Check publishable files without printing credentials; --staged reads Git blobs."""
import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess


PRIVATE_DIRS = {'data','venv','.venv','node_modules','__pycache__','artifacts',
                '.playwright-cli','output','.vscode','.idea'}
PRIVATE_NAMES = {'server.env','.session-secret','id_rsa','id_ed25519','Checkpoint2.pdf',
                 '141cf24c20339c48808160b946b4ea06.png'}
TOKEN_PATTERNS = (
    re.compile(rb'sk-[A-Za-z0-9_-]{24,}'),
    re.compile(rb'\b[0-9a-fA-F]{32}\.[A-Za-z0-9_-]{16,}\b'),
    re.compile(rb'-----BEGIN (?:RSA |OPENSSH |EC |DSA |ENCRYPTED )?PRIVATE KEY-----'),
    re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),
)
ASSIGNMENT = re.compile(
    rb'''\b(?:[A-Z0-9_]*API_KEY|DEEPSEEK_KEY|BIGMODEL_KEY|SECRET_KEY|[A-Z0-9_]*ACCESS_TOKEN)["']?\s*[:=]\s*["']([^"'\r\n]+)["']''')
EXAMPLE_SECRET = re.compile(r'^[A-Z0-9_]*(?:KEY|TOKEN|PASSWORD|SECRET)\s*=\s*(.*)$')


def path_issue(name: str) -> str | None:
    path = PurePosixPath(name)
    if (PRIVATE_DIRS.intersection(path.parts) or path.name in PRIVATE_NAMES
            or (path.name.startswith('.env') and path.name != '.env.example')
            or re.fullmatch(r'env.*\.txt',path.name)
            or re.search(r'\.(?:db(?:-.*)?|sqlite\d*(?:-.*)?|backup.*|pyc|pem|key|env)$',path.name)
            or re.fullmatch(r'credentials.*\.json',path.name)):
        return 'private/local artifact'
    return None


def content_issue(name: str, content: bytes) -> str | None:
    # Template credentials must be empty, including unquoted non-prefixed API keys.
    if PurePosixPath(name).name == '.env.example':
        for line in content.decode('utf-8',errors='replace').splitlines():
            match = EXAMPLE_SECRET.match(line.strip())
            if match and match[1].split('#',1)[0].strip().strip('\"\''):
                return 'nonempty credential in configuration template'
    if any(pattern.search(content) for pattern in TOKEN_PATTERNS):
        return 'credential-like literal or private key'
    for match in ASSIGNMENT.finditer(content):
        value = match[1]
        # Only explicit test fixtures are exempt, inside automated tests or CI.
        fixture = (name.startswith('tests/') or name.startswith('.github/workflows/')) and value.startswith(
            (b'test-',b'fixture-',b'legacy-fixture-',b'ci-only-'))
        expression = value.startswith((b'$(',b'${'))
        if value and not fixture and not expression:
            return 'literal credential assignment'
    return None


def check(root: Path, staged: bool = False) -> list[tuple[str,str]]:
    findings = []
    if staged:
        entries = subprocess.check_output(['git','ls-files','--stage','-z'],cwd=root).split(b'\0')
        for entry in filter(None,entries):
            meta,name = entry.split(b'\t',1)
            mode,oid,stage = meta.split()
            path = name.decode('utf-8',errors='replace')
            if stage != b'0' or mode == b'160000':
                findings.append((path,'unmerged path or unreviewed submodule'))
                continue
            issue = path_issue(path)
            if not issue:
                content = subprocess.check_output(['git','cat-file','blob',oid.decode()],cwd=root)
                issue = content_issue(path,content)
            if issue:
                findings.append((path,issue))
    else:
        entries = subprocess.check_output(
            ['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root).split(b'\0')
        for name in sorted(set(filter(None,entries))):
            path = name.decode('utf-8',errors='replace')
            issue = path_issue(path)
            if not issue and (root/path).is_file():
                issue = content_issue(path,(root/path).read_bytes())
            if issue:
                findings.append((path,issue))
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged',action='store_true',help='Inspect the exact index, not working files.')
    args = parser.parse_args()
    root = Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip())
    findings = check(root,args.staged)
    if findings:
        for path,reason in findings:
            print(f'{path}: {reason}')
        raise SystemExit('Repository hygiene failed. No credential values were printed.')
    target = 'staged snapshot' if args.staged else 'tracked and nonignored working files'
    print(f'Repository hygiene passed for {target}. History requires a separate audit; see SECURITY.md.')


if __name__ == '__main__':
    main()
