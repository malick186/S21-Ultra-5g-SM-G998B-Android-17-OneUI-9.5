from pathlib import Path
import hashlib
import json
import shlex
import subprocess

base = Path('/opt/codex-rom/monsterrom-p3s')
out = base / 'kernel-source/out'
records = base / 'records/ikconfig-cfi'
baseline = base / 'records/beta2-r5-kernel-fix2'
release = Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5')
dest = release / 'ikconfig-fix'
dest.mkdir(exist_ok=True)
tools = base / 'source/out/tools/bin'
old = release / 'llseek-fix/boot.img'
new = dest / 'boot.img'
key = base / 'source/security/avb/testkey_rsa4096.pem'

def run(*args):
    return subprocess.check_output(args, text=True)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert digest(old) == '17aea91bb2149507c6a6ddf0ee5bee255868550e71ae6e4d446a320055ec1509'
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

import struct
import gzip
elf = (out/'vmlinux').read_bytes()
phoff = struct.unpack_from('<Q',elf,32)[0]
size, count = struct.unpack_from('<HH',elf,54)
def read_va(address, length):
    for i in range(count):
        kind, flags, offset, start, _, filesz, _, _ = struct.unpack_from('<IIQQQQQQ',elf,phoff+i*size)
        if kind == 1 and start <= address and address+length <= start+filesz:
            return elf[offset+address-start:offset+address-start+length]
    raise ValueError(hex(address))
tables = [addr for name, addr in symbols.items() if name.startswith('ikconfig_read_current') and name.endswith('.cfi_jt')]
assert len(set(tables)) == 1, tables
ops = next(addr for name,addr in symbols.items() if name.split('.')[0] == 'ikconfig_file_ops')
assert struct.unpack('<Q',read_va(ops+16,8))[0] == tables[0], 'wrong read callback'
lo,hi=symbols['kernel_config_data'],symbols['kernel_config_data_end']
assert read_va(lo-8,8)==b'IKCFG_ST' and read_va(hi,8)==b'IKCFG_ED'
assert gzip.decompress(read_va(lo,hi-lo))==(out/'.config').read_bytes()

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

