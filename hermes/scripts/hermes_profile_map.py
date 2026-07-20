#!/usr/bin/env python3
from pathlib import Path
import re
import sys

profiles_dir = Path(sys.argv[1]).expanduser()

def q(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"')

def norm(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]', '_', name)

print('# auto-generated; do not edit')
print('HERMES_PROFILE_NAMES :=')
found = False
for env_path in sorted(profiles_dir.glob('*/.env')):
    profile = env_path.parent.name
    vals = {}
    for raw in env_path.read_text(errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    if vals.get('API_SERVER_ENABLED', '').lower() != 'true':
        continue
    found = True
    host = vals.get('API_SERVER_HOST', '127.0.0.1') or '127.0.0.1'
    port = vals.get('API_SERVER_PORT', '8642') or '8642'
    token = vals.get('API_SERVER_KEY', '')
    key = norm(profile)
    print(f'HERMES_PROFILE_NAMES += {profile}')
    print(f'HERMES_PROFILE_{key}_HOST := {q(host)}')
    print(f'HERMES_PROFILE_{key}_PORT := {q(port)}')
    print(f'HERMES_PROFILE_{key}_TOKEN := {q(token)}')
    print(f'HERMES_PROFILE_{key}_URL := http://{q(host)}:{q(port)}')
if not found:
    print('# no API_SERVER_ENABLED=true profiles found')
