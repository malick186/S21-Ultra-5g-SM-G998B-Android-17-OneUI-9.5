#!/usr/bin/env python3
"""Stage the verified proprietary payload locally; never flash or download it."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ARCHIVE_SHA256 = 'ac6b3275922a38ec7ab9ae2b7b622d291e5c6ea9e8accf830b1c8c39fcc4d596'
ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        ap.error('Output must not already exist')
    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        ap.error('Unrecognized upstream archive')
    source = ROOT / 'runtime/gpu-r38p1'
    manifest = json.loads((source / 'manifest.json').read_text())
    payload = {}
    with zipfile.ZipFile(args.archive) as archive:
        for entry in manifest:
            target = entry['path']
            if not target.startswith('/vendor/') or '..' in Path(target).parts:
                ap.error('Invalid manifest path')
            data = archive.read('system' + target)
            if hashlib.sha256(data).hexdigest() != entry['new']:
                ap.error('Payload checksum mismatch: ' + target)
            payload[target] = data
    args.output.mkdir(parents=True)
    for target, data in payload.items():
        dest = args.output / 'payload' / target.lstrip('/')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    for name in ('mount.sh', 'post-fs-data.sh'):
        shutil.copyfile(source / name, args.output / name)
    (args.output / 'manifest.txt').write_text(''.join(
        f"{e['old']} {e['new']} {e['path']}\n" for e in manifest))
    print('Eight files verified and staged locally; nothing installed on a device.')

if __name__ == '__main__':
    main()
