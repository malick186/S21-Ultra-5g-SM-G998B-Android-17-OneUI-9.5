from pathlib import Path
import hashlib
import json
import shlex
import subprocess

base = Path('/opt/codex-rom/monsterrom-p3s')
out = base / 'kernel-source/out'
records = base / 'records/beta2-r5-llseek'
baseline = base / 'records/beta2-r5-kernel-fix2'
release = Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5')
dest = release / 'llseek-fix'
dest.mkdir(exist_ok=True)
tools = base / 'source/out/tools/bin'
old = release / 'kernel-fix2/boot.img'
new = dest / 'boot.img'
key = base / 'source/security/avb/testkey_rsa4096.pem'

def run(*args):
    return subprocess.check_output(args, text=True)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert digest(old) == '444ebee94132f0500a5275efc9d06c916018749f1ac40aa7c3eb7b429e1372b5'
for path in ['.config', 'Module.symvers', 'include/generated/utsrelease.h']:
    assert (out / path).read_bytes() == (baseline / ('baseline-' + Path(path).name)).read_bytes(), path
symbols = {}
for line in (out / 'System.map').read_text().splitlines():
    address, _, name = line.split(maxsplit=2)
    symbols[name] = int(address, 16)
entry = symbols['default_llseek']
disasm = run('/opt/codex-kernel/p3s-v7/toolchain/clang-r596125/bin/llvm-objdump',
             f'--start-address={entry}', f'--stop-address={entry+4}', '-d', out / 'vmlinux')
assert 'default_llseek.cfi' in disasm and 'b\t' in disasm, disasm
(records / 'entry-disassembly.txt').write_text(disasm)

def unpack(image, folder):
    folder.mkdir(exist_ok=True)
    return shlex.split(run(tools / 'unpack_bootimg', '--boot_img', image, '--out', folder, '--format=mkbootimg'))

original = records / 'baseline-boot'
args = unpack(old, original)
payload = out / 'arch/arm64/boot/Image'
assert digest(original / 'kernel') != digest(payload)
args[args.index('--kernel') + 1] = str(payload)
run(tools / 'mkbootimg', *args, '--output', new)
run(tools / 'avbtool', 'add_hash_footer', '--image', new, '--partition_size', str(old.stat().st_size),
    '--partition_name', 'boot', '--hash_algorithm', 'sha256', '--algorithm', 'SHA256_RSA4096', '--key', key)
run(tools / 'avbtool', 'verify_image', '--image', new, '--key', key)
verified = records / 'verified'
check = unpack(new, verified)
assert digest(verified / 'ramdisk') == digest(original / 'ramdisk')
assert digest(verified / 'kernel') == digest(payload)
for option in ['--kernel', '--ramdisk']:
    args[args.index(option)+1] = check[check.index(option)+1]
assert args == check
(dest / 'proof.json').write_text(json.dumps({'boot_sha256': digest(new), 'previous_sha256': digest(old),
    'canonical_entry_disassembly': disasm}, indent=2))
print(digest(new))
