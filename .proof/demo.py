import json
from pathlib import Path
data = json.loads(Path('projects.json').read_text())
print(json.dumps({'type': type(data).__name__, 'entries': len(data), 'catalog': data}, sort_keys=True))
assert data
