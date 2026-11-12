from pathlib import Path
import hashlib
import os
import shutil
import subprocess

base = Path('/opt/codex-rom/monsterrom-p3s')
tools = base / 'source/out/tools/bin'
os.environ['PATH'] = str(tools) + ':' + os.environ['PATH']
release = Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5/startup-records')
original = release / 'original-odm.img'
work = base / 'records/persistent-startup'
tree = work / 'input'
new = release / 'odm-diagnostic.img'
key = base / 'source/security/avb/testkey_rsa4096.pem'

def run(*args):
    return subprocess.check_output(args, text=True)

def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()

assert sha(original) == '4bb1427e05402df2419d1ea3481c2f11cc4ef2a1f2b58dfda1f4db9192e7fe70'
def verify_avb(image, name):
    directory = work/name
    directory.mkdir(exist_ok=True)
    partition = directory/'odm.img'
    shutil.copyfile(image, partition)
    run(tools/'avbtool', 'verify_image', '--image', partition, '--key', key)

verify_avb(original, 'stock-avb')
if not tree.exists():
    run(tools/'fsck.erofs', '--extract=' + str(tree), original)
cfg = base / 'source/out/target/p3s/work_dir/configs'
fs = work/'fs_config'
ctx = work/'contexts'
fs.write_text((cfg/'fs_config-odm').read_text().rstrip() + '\nodm/etc/init 0 0 755 capabilities=0x0\nodm/etc/init/p3s-startup.rc 0 0 644 capabilities=0x0\n')
ctx.write_text((cfg/'file_context-odm').read_text() + '\n/odm/etc/init(/.*)? u:object_r:vendor_configs_file:s0\n')
rc = tree/'etc/init/p3s-startup.rc'
rc.parent.mkdir(exist_ok=True)
folder = '/metadata/p3s-startup'
events = [('early-init', 'early'), ('post-fs', 'filesystems'), ('zygote-start','zygote'),
          ('property:init.svc.bootanim=running', 'animation'), ('property:sys.boot_completed=1','complete')]
lines = []
for event, name in events:
    lines += ['on ' + event, '    mkdir ' + folder + ' 0700 root root',
              f'    write {folder}/{name}.stage {name}',
              f'    copy /proc/uptime {folder}/{name}.uptime']
    if name in ('early','animation'):
        lines.append(f'    copy /proc/sec_log {folder}/{name}.kernel')
    if name == 'early':
        for src in ['console-ramoops-0','dmesg-ramoops-0']:
            lines.append(f'    copy /sys/fs/pstore/{src} {folder}/previous-{src}')
    lines.append('')
rc.write_text('\n'.join(lines))
shutil.copyfile(rc, release/'p3s-startup.rc')
run(tools/'mkfs.erofs', '-zlz4hc,9', '-b','4096','--mount-point','odm',
    '--fs-config-file',fs,'--file-contexts',ctx,'-T','1640995200',new,tree)
run(tools/'avbtool','add_hashtree_footer','--image',new,'--partition_name','odm',
    '--partition_size',str(original.stat().st_size),'--hash_algorithm','sha256',
    '--algorithm','SHA256_RSA4096','--key',key)
verify_avb(new, 'test-avb')
assert new.stat().st_size == original.stat().st_size
verify = work/'verify'
run(tools/'fsck.erofs','--extract=' + str(verify),new)
for f in tree.rglob('*'):
    if f.is_file():
        assert sha(f) == sha(verify/f.relative_to(tree)), f
print(sha(new))

