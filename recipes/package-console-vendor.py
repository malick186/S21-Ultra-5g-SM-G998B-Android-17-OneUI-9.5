from pathlib import Path
import hashlib
import shlex
import struct
import subprocess

base = Path('/opt/codex-rom/monsterrom-p3s')
tools = base / 'source/out/tools/bin'
dtc = base / 'kernel-source/out/scripts/dtc/dtc'
release = Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5')
dest = release / 'console-diagnostic'
dest.mkdir(exist_ok=True)
original = release / 'driver-entry-fix/vendor_boot.img'
key = base / 'source/security/avb/testkey_rsa4096.pem'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(*args):
    return subprocess.check_output(args, text=True)

def unpack(image, folder):
    folder.mkdir(exist_ok=True)
    return shlex.split(run(tools / 'unpack_bootimg', '--boot_img', image, '--out', folder, '--format=mkbootimg'))

assert sha(original) == '25dd2b0f66cc7ac59951bc55fe2cd23770b54387fe6cd044cb8b0c623579826e'
baseline = dest / 'original'
args = unpack(original, baseline)
table = (baseline / 'dtb').read_bytes()
magic, size, header, entry_size, count, entries, page, version = struct.unpack_from('>8I', table)
assert (magic, size, header, entry_size, count, entries, version) == (0xd7b7ab1e,len(table),32,32,1,32,0)
length, offset = struct.unpack_from('>II', table, entries)
assert offset == 64 and offset + length == len(table)
fdt = dest / 'board.dtb'
fdt.write_bytes(table[offset:])
def decompile(path):
    return run(dtc, '-q', '-q', '-q', '-I', 'dtb', '-O', 'dts', path)

dts = decompile(fdt)
before = 'pmsg-size = <0x20000>;'
after = 'console-size = <0x20000>;'
assert dts.count(before) == 1 and after not in dts
node = dts.split('ramoops@8f000000 {', 1)[1].split('};', 1)[0]
assert before in node and 'record-size = <0x20000>;' in node
source = dest / 'console.dts'
source.write_text(dts.replace(before, after))
new_fdt = dest / 'console.dtb'
blob = bytearray(fdt.read_bytes())
_, _, tree, strings, _, _, _, _, string_size, tree_size = struct.unpack_from('>10I', blob)
assert strings + string_size <= len(blob) and not any(blob[strings + string_size:])
cursor = tree
path = []
matches = 0
while cursor < tree + tree_size:
    token, = struct.unpack_from('>I', blob, cursor)
    cursor += 4
    if token == 1:
        end = blob.index(0, cursor)
        path.append(blob[cursor:end].decode())
        cursor = (end + 4) & ~3
    elif token == 2:
        path.pop()
    elif token == 3:
        prop_size, name = struct.unpack_from('>II', blob, cursor)
        start = strings + name
        if path[-1] == 'ramoops@8f000000' and blob[start:blob.index(0,start)] == b'pmsg-size':
            struct.pack_into('>I', blob, cursor + 4, string_size)
            matches += 1
        cursor += 8 + ((prop_size + 3) & ~3)
    elif token == 9:
        break
    else:
        assert token == 4
assert matches == 1
name = b'console-size\0'
blob[strings + string_size:] = name
struct.pack_into('>I', blob, 32, string_size + len(name))
blob.extend(bytes(-len(blob) % 4))
struct.pack_into('>I', blob, 4, len(blob))
new_fdt.write_bytes(blob)
assert decompile(new_fdt) == source.read_text()
patched = bytearray(table[:offset]) + new_fdt.read_bytes()
struct.pack_into('>I', patched, 4, len(patched))
struct.pack_into('>I', patched, entries, len(patched)-offset)
new_table = dest / 'dtb.img'
new_table.write_bytes(patched)
args[args.index('--dtb')+1] = str(new_table)
new = dest / 'vendor_boot.img'
run(tools / 'mkbootimg', *args, '--vendor_boot', new)
run(tools / 'avbtool', 'add_hash_footer', '--image', new, '--partition_name', 'vendor_boot',
    '--partition_size', str(original.stat().st_size), '--algorithm', 'SHA256_RSA4096', '--hash_algorithm', 'sha256', '--key', key)
run(tools / 'avbtool', 'verify_image', '--image', new, '--key', key)
verified = dest / 'verified'
check = unpack(new, verified)
assert sha(verified / 'vendor_ramdisk') == sha(baseline / 'vendor_ramdisk')
assert (verified / 'dtb').read_bytes() == patched
for option in ['--dtb', '--vendor_ramdisk']:
    args[args.index(option)+1] = check[check.index(option)+1]
assert args == check
print(sha(new))
