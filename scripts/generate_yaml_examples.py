#!/usr/bin/env python3
"""Generate YAML examples from JSON examples."""
import json
import yaml
from pathlib import Path

examples_dir = Path(__file__).parent.parent / 'examples'
json_files = list(examples_dir.glob('*.json'))

for jf in json_files:
    yaml_path = jf.with_suffix('.yaml')
    if yaml_path.exists():
        print(f'SKIP: {yaml_path.name}')
        continue
    
    with open(jf, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    print(f'CREATED: {yaml_path.name}')

print('Done!')
