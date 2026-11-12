"""Remove the confirmed automatic boot-repack hook; preserve other payloads."""
from pathlib import Path
import gzip,hashlib,io,json,shlex,shutil,stat,struct,subprocess,tarfile
base=Path('/opt/codex-rom/monsterrom-p3s');src=base/'source';tools=src/'out/tools/bin';rec=base/'records/beta2-r4';rec.mkdir(exist_ok=True)
release=Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r4');release.mkdir(exist_ok=True)
original=Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r3/build-intermediates/RECOVERY_LAYOUT_CONTROL.img')
if (release/'RECOVERY_NO_BOOT_PATCH.img').exists():raise SystemExit('Existing r4 recovery retained; refusing overwrite')
unpacked=rec/'recovery-input';unpacked.mkdir(exist_ok=True)
result=subprocess.run([str(tools/'unpack_bootimg'),'--boot_img',str(original),'--out',str(unpacked),'--format=mkbootimg'],capture_output=True,text=True,check=True);args=shlex.split(result.stdout)
ramdisk=unpacked/'ramdisk';packed=ramdisk.read_bytes()
if packed[:2]!=b'\x1f\x8b':raise SystemExit('Unreviewed recovery ramdisk compression')
raw=gzip.decompress(packed)
def entries(data):
 offset=0;result=[]
 while offset+110<=len(data):
  start=offset;h=data[offset:offset+110]
  if h[:6] not in (b'070701',b'070702'):raise ValueError('Invalid cpio magic')
  fields=[int(h[6+i*8:14+i*8],16) for i in range(13)];namesize=fields[11];size=fields[6]
  if not namesize:raise ValueError('Empty cpio name')
  name=data[offset+110:offset+110+namesize-1].decode();body=(offset+110+namesize+3)//4*4;end=(body+size+3)//4*4
  if end>len(data):raise ValueError('Truncated cpio')
  result.append((name,h,fields,data[body:body+size],data[start:end],data[start:body]))
  offset=end
  if name=='TRAILER!!!':return result,data[offset:]
 raise ValueError('No cpio trailer')
old,tail=entries(raw);target='system/bin/postrecoveryboot.sh';matches=[e for e in old if e[0].removeprefix('./')==target]
if len(matches)!=1 or not stat.S_ISREG(matches[0][2][1]):raise SystemExit('Expected one regular inherited boot hook')
oldscript=matches[0][3]
if b'magiskboot repack' not in oldscript or b'of="/dev/block/by-name/boot"' not in oldscript:raise SystemExit('Unexpected hook contents')
prefix=oldscript.split(b'mkdir -p "/tmp/vendor";',1)[0]
replacement=prefix+b'# Personal recovery control: never modify boot automatically.\n'+b'echo "I:postrecoveryboot: automatic boot repacking disabled for control testing." >> /tmp/recovery.log\nexit 0\n'
output=[]
for name,h,fields,data,record,prebody in old:
 if name.removeprefix('./')!=target:output.append(record);continue
  # Preserve file identity, mode, ownership, timestamp and all other fields.
 header=bytearray(h);header[54:62]=f'{len(replacement):08x}'.encode()
 if h[:6]==b'070702':header[102:110]=f'{sum(replacement)&0xffffffff:08x}'.encode()
 output.append(bytes(header)+prebody[110:]+replacement+bytes((-len(replacement))%4))
newraw=b''.join(output)+tail;new,_=entries(newraw)
if len(old)!=len(new):raise SystemExit('CPIO entry count changed')
for previous,current in zip(old,new):
 if previous[0]!=current[0]:raise SystemExit('CPIO entry order changed')
 if previous[0].removeprefix('./')!=target and (previous[1]!=current[1] or previous[3]!=current[3]):raise SystemExit('Unrelated recovery entry changed')
 if previous[0].removeprefix('./')==target:
  for i,(a,b) in enumerate(zip(previous[2],current[2])):
   if i not in (6,12) and a!=b:raise SystemExit('Hook identity metadata changed')
  if current[3]!=replacement:raise SystemExit('Hook replacement mismatch')
patched=rec/'ramdisk-no-boot-patch.gz';patched.write_bytes(gzip.compress(newraw,compresslevel=9,mtime=0));args[args.index('--ramdisk')+1]=str(patched)
image=release/'RECOVERY_NO_BOOT_PATCH.img';subprocess.run([str(tools/'mkbootimg'),*args,'--output',str(image)],check=True)
payload=image.read_bytes()
if b'SEANDROIDENFORCE' not in original.read_bytes():raise SystemExit('Original recovery trailer missing')
payload+=b'SEANDROIDENFORCE'
if len(payload)>67108864:raise SystemExit('Recovery exceeds target size')
image.write_bytes(payload+bytes(67108864-len(payload)))
verify=rec/'recovery-verified';verify.mkdir(exist_ok=True)
subprocess.run([str(tools/'unpack_bootimg'),'--boot_img',str(image),'--out',str(verify)],check=True,capture_output=True)
for name in ['kernel','dtb','recovery_dtbo']:
 if (unpacked/name).read_bytes()!=(verify/name).read_bytes():raise SystemExit('Recovery core payload changed: '+name)
if (verify/'ramdisk').read_bytes()!=patched.read_bytes():raise SystemExit('Repacked ramdisk differs')
(rec/'inherited-postrecoveryboot.sh').write_bytes(oldscript);(rec/'disabled-postrecoveryboot.sh').write_bytes(replacement)
shutil.copyfile(src/'target/p3s/installer/assertions.edify',rec/'assertions-before-r4.edify')
p=src/'target/p3s/installer/assertions.edify';text=p.read_text();oldguard='getprop("ro.boot.vbmeta.device_state") == "unlocked" || abort("E3003: This custom build requires an already-unlocked bootloader.");'
newguard='''getprop("ro.boot.verifiedbootstate") == "orange" || abort("E3003: Bootloader must report unlocked/orange verified-boot state.");
(getprop("ro.boot.vbmeta.device_state") == "" || getprop("ro.boot.vbmeta.device_state") == "unlocked") || abort("E3003: Conflicting locked bootloader state.");'''
if text.count(oldguard)!=1:raise SystemExit('Installer unlock guard changed unexpectedly')
text=text.replace(oldguard,newguard).replace('BETA2-r3','BETA2-r4');p.write_text(text)
# Exercise the actual recovery property case and fail-closed alternatives.
def allowed(model,bootloader,rp,verified,state,twrp):return model=='SM-G998B' and bootloader=='G998BXXSJHZC2' and rp=='19' and verified=='orange' and state in ('','unlocked') and bool(twrp) and 'afaneh92' not in twrp
tests={}
for name,values,expected in [
 ('observed_recovery_with_missing_optional_state',('SM-G998B','G998BXXSJHZC2','19','orange','','3.7.1_12-Chiclet_v2'),True),
 ('explicit_unlocked',('SM-G998B','G998BXXSJHZC2','19','orange','unlocked','3.7.1_12-Chiclet_v2'),True),
 ('locked_green_rejected',('SM-G998B','G998BXXSJHZC2','19','green','locked','3.7.1_12-Chiclet_v2'),False),
 ('missing_both_states_rejected',('SM-G998B','G998BXXSJHZC2','19','','','3.7.1_12-Chiclet_v2'),False),
 ('conflicting_locked_rejected',('SM-G998B','G998BXXSJHZC2','19','orange','locked','3.7.1_12-Chiclet_v2'),False),
 ('wrong_model_rejected',('SM-G998N','G998BXXSJHZC2','19','orange','','3.7.1_12-Chiclet_v2'),False),
 ('wrong_firmware_rejected',('SM-G998B','other','19','orange','','3.7.1_12-Chiclet_v2'),False),
 ('wrong_revision_rejected',('SM-G998B','G998BXXSJHZC2','18','orange','','3.7.1_12-Chiclet_v2'),False)]:
 if allowed(*values)!=expected:raise SystemExit('Guard case failed '+name)
 tests[name]=True
stock=base/'records/beta2-r3/stock-reference';avb=src/'target/p3s/installer/avb';rescue=rec/'stock-rescue-inputs';rescue.mkdir(exist_ok=True)
for name in ['boot.img','recovery.img','vbmeta.img','vbmeta_system.img']:
 b=(stock/name).read_bytes()
 if name.startswith('vbmeta'):b+=bytes(65536-len(b))
 (rescue/name).write_bytes(b)
bundles={
 'CUSTOM_RECOVERY_NO_BOOT_PATCH_R4_SM-G998B.tar':{'recovery.img':image,'vbmeta.img':avb/'vbmeta.img','vbmeta_system.img':avb/'vbmeta_system.img'},
 'STOCK_BOOT_RECOVERY_AVB_RESCUE_R4_SM-G998B.tar':{n:rescue/n for n in ['boot.img','recovery.img','vbmeta.img','vbmeta_system.img']}
}
proof={'revision':'BETA2-r4 recovery control','inherited_boot_repack_hook_disabled':True,'only_changed_cpio_entry':target,'all_other_recovery_entries_unchanged':True,'kernel_dtb_recovery_dtbo_unchanged':True,'guard_regression_cases':tests,'encrypted_stock_data_support_verified':False,'runtime_tested':False,'bundles':{}}
for name,files in bundles.items():
 tar=release/name;final=tar.with_suffix('.tar.md5');hashes={}
 with tarfile.open(tar,'w',format=tarfile.USTAR_FORMAT) as tf:
  for member,path in files.items():
   b=path.read_bytes();h=tarfile.TarInfo(member);h.size=len(b);h.mode=0o644;tf.addfile(h,io.BytesIO(b));hashes[member]=hashlib.sha256(b).hexdigest()
 with tarfile.open(tar) as tf:
  for member,digest in hashes.items():
   if hashlib.sha256(tf.extractfile(member).read()).hexdigest()!=digest:raise SystemExit('Archive mismatch')
 b=tar.read_bytes();final.write_bytes(b+(hashlib.md5(b).hexdigest()+'  '+tar.name+'\n').encode());proof['bundles'][final.name]={'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'contents':hashes}
(release/'RECOVERY_CONTROL_PROOF.json').write_text(json.dumps(proof,indent=2));shutil.copyfile(p,release/'INSTALLER_GUARDS_R4.edify')
print(json.dumps(proof,indent=2))
