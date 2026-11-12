from pathlib import Path
import gzip, hashlib, os, shlex, subprocess

base = Path('/opt/codex-rom/monsterrom-p3s')
out = Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5/driver-entry-fix')
os.chdir(out)
tools = base / 'source/out/tools/bin'
key = base / 'source/security/avb/testkey_rsa4096.pem'
def run(*args):
    return subprocess.check_output(args, text=True)
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
assert digest('original.img') == 'ed82daad6eb97b9b0d7bba7ecdf45ad204db86fc0fe836216158598e25b3b475'
args = shlex.split(run(tools/'unpack_bootimg', '--boot_img','original.img','--out','unpack','--format=mkbootimg'))
raw = gzip.decompress(Path('unpack/vendor_ramdisk').read_bytes())
module = base/'kernel-source/out/drivers/optics/flicker_test.ko'
strip = '/opt/codex-kernel/p3s-v7/toolchain/clang-r596125/bin/llvm-strip'
run(strip,'--strip-debug','-o','new.ko',module)
def records(data):
    pos=0
    while pos+110 <= len(data):
        h=data[pos:pos+110]
        assert h[:6]==b'070701'
        size=int(h[54:62],16)
        name_end=pos+110+int(h[94:102],16)
        name=data[pos+110:name_end-1].decode()
        body=(name_end+3)&~3
        end=(body+size+3)&~3
        yield name,pos,body,end,size
        if name=='TRAILER!!!': return
        pos=end
items=[r for r in records(raw) if r[0].endswith('/flicker_test.ko')]
assert len(items)==1
name,pos,body,end,size=items[0]
new=Path('new.ko').read_bytes()
assert raw[body:body+4]==new[:4]==b'\x7fELF'
assert 'CONFIG_MODULE_SIG_FORCE=y' not in (base/'kernel-source/out/.config').read_text()
patched=raw[:pos+54]+('%08x'%len(new)).encode()+raw[pos+62:body]+new+bytes((-len(new))%4)+raw[end:]
Path('patched.gz').write_bytes(gzip.compress(patched,mtime=0))
args[args.index('--vendor_ramdisk')+1]='patched.gz'
run(tools/'mkbootimg',*args,'--vendor_boot','vendor_boot.img')
run(tools/'avbtool','add_hash_footer','--image','vendor_boot.img','--partition_name','vendor_boot','--partition_size','67108864','--algorithm','SHA256_RSA4096','--hash_algorithm','sha256','--key',key)
run(tools/'avbtool','verify_image','--image','vendor_boot.img','--key',key)
run(tools/'unpack_bootimg','--boot_img','vendor_boot.img','--out','verify')
assert gzip.decompress(Path('verify/vendor_ramdisk').read_bytes())==patched
assert digest('verify/dtb')==digest('unpack/dtb')
print(name, digest('vendor_boot.img'))
