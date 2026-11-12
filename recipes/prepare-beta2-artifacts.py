from pathlib import Path
import hashlib,json,shlex,shutil,subprocess,tarfile,io,zipfile
base=Path('/opt/codex-rom/monsterrom-p3s');src=base/'source';rec=base/'records/beta2-r3';release=Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r3');release.mkdir(exist_ok=True)
stage=release/'installer-update';stage.mkdir(exist_ok=True);target=release/'target-update';target.mkdir(exist_ok=True)
work=src/'out/target/p3s/work_dir/kernel';tools=src/'out/tools/bin';stock=rec/'stock-reference'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Keep the kernel project's direct p3s packing entry point consistent too.
kp=base/'kernel-source/build/scripts/images.sh';text=kp.read_text();marker='    local VENDOR_CMDLINE="${VENDOR_CMDLINE:-loop.max_part=7}"\n'
if text.count(marker)!=1:raise SystemExit('Kernel packer insertion changed')
shutil.copyfile(kp,rec/'kernel-images-before.sh')
text=text.replace(marker,marker+'''    local P3S_VENDOR_LAYOUT=()
    if [ "$CODENAME" = p3s ]; then
        P3S_VENDOR_LAYOUT=(--pagesize 4096 --base 0 \\
            --kernel_offset 0x80008000 --ramdisk_offset 0x84000000 \\
            --tags_offset 0x80000000 --dtb_offset 0x81f00000 \\
            --board SRPTH19D019KU)
    fi
''')
marker='        --vendor_boot "$OUT_VENDORBOOTIMG" \\\n'
if text.count(marker)!=1:raise SystemExit('Vendor image packing command changed')
kp.write_text(text.replace(marker,marker+'        "${P3S_VENDOR_LAYOUT[@]}" \\\n'))
# Recovery is a separate control-test artifact, never installed by the ROM ZIP.
recovery=rec/'recovery-layout';recovery.mkdir(exist_ok=True)
unpacked={};arguments={}
for name,path in [('original',Path('/mnt/d/Codex-ROM/p3s/phone-rollback-current/recovery.img')),('stock',stock/'recovery.img')]:
 d=recovery/name;d.mkdir(exist_ok=True);unpacked[name]=d
 result=subprocess.run([str(tools/'unpack_bootimg'),'--boot_img',str(path),'--out',str(d),'--format=mkbootimg'],capture_output=True,text=True,check=True);arguments[name]=shlex.split(result.stdout)
new=arguments['original'][:]
for key in ['--pagesize','--base','--kernel_offset','--ramdisk_offset','--second_offset','--tags_offset','--dtb_offset','--board']:
 if key not in arguments['stock']:raise SystemExit('Missing stock recovery argument '+key)
 new[new.index(key)+1]=arguments['stock'][arguments['stock'].index(key)+1]
image=recovery/'recovery.img';subprocess.run([str(tools/'mkbootimg'),*new,'--output',str(image)],check=True)
verified=recovery/'verified';verified.mkdir(exist_ok=True)
subprocess.run([str(tools/'unpack_bootimg'),'--boot_img',str(image),'--out',str(verified)],check=True,capture_output=True)
for payload in ['kernel','ramdisk','recovery_dtbo','dtb']:
 if (unpacked['original']/payload).read_bytes()!=(verified/payload).read_bytes():raise SystemExit('Recovery payload changed '+payload)
saved=Path('/mnt/d/Codex-ROM/p3s/phone-rollback-current/recovery.img').read_bytes();marker=b'SEANDROIDENFORCE';offset=saved.find(marker)
if offset!=image.stat().st_size:raise SystemExit('Unexpected recovery trailer/padding layout')
payload=image.read_bytes()+marker;image.write_bytes(payload+bytes(len(saved)-len(payload)))
dest=release/'RECOVERY_LAYOUT_CONTROL_SM-G998B.tar';data=image.read_bytes()
with tarfile.open(dest,'w',format=tarfile.USTAR_FORMAT) as tf:
 h=tarfile.TarInfo('recovery.img');h.size=len(data);h.mode=0o644;tf.addfile(h,io.BytesIO(data))
b=dest.read_bytes();dest.with_suffix('.tar.md5').write_bytes(b+(hashlib.md5(b).hexdigest()+'  '+dest.name+'\n').encode())
recovery_proof={'runtime_tested':False,'stock_geometry_used':True,'all_original_kernel_ramdisk_dtbo_dtb_payloads_unchanged':True,'original_ramoops_layout_unchanged':True,'recovery_sha256':sha(image),'odin_archive_sha256':sha(dest.with_suffix('.tar.md5')),'normal_rom_zip_changes_recovery':False}
(release/'RECOVERY_CONTROL_PROOF.json').write_text(json.dumps(recovery_proof,indent=2))
shutil.copyfile(image,release/'RECOVERY_LAYOUT_CONTROL.img')
# New full installer reuses the exact old OS image data, with audited boot and
# installer corrections. It is not represented as new Android userspace code.
oldzip=Path('/mnt/d/Codex-ROM/p3s/releases/a17-r2/MonsterROM_A17_p3s_SM-G998B_r2_TEST.zip')
with zipfile.ZipFile(oldzip) as z:
 old=z.read('META-INF/com/google/android/updater-script').decode()
 prefix=(rec/'source-before/target/p3s/installer/assertions.edify').read_text().strip()
 footer=(rec/'source-before/target/p3s/installer/install-end.edify').read_text().strip()
 if old.count(prefix)!=1 or old.count(footer)!=1:raise SystemExit('Original installer blocks changed')
 updated=old.replace(prefix,(src/'target/p3s/installer/assertions.edify').read_text().strip()).replace(footer,(src/'target/p3s/installer/install-end.edify').read_text().strip())
 for name in ['boot.img','vendor_boot.img','dtbo.img']:
  original='package_extract_file("'+name+'", "/dev/block/by-name/'+name[:-4]+'");'
  if updated.count(original)!=1:raise SystemExit('Expected exactly one raw write '+name)
  updated=updated.replace(original,'assert('+original[:-1]+');')
 if '/dev/block/by-name/bota' in updated or 'write_data_bt(' in updated or 'modem.bin' in updated:raise SystemExit('Unexpected firmware update survived')
 if updated.count('assert(package_extract_file(')!=5:raise SystemExit('Incorrect raw-write assertion count')
 for guarded in ['ro.boot.em.model','ro.boot.bootloader','ro.boot.rp','ro.boot.vbmeta.device_state','ro.twrp.version']:
  if updated.index(guarded)>updated.index('update_dynamic_partitions('):raise SystemExit('Late installation guard')
 props=(src/'out/target/p3s/work_dir/system/system/build.prop').read_text()
 oldversion=next(v.split('=',1)[1] for v in props.splitlines() if v.startswith('ro.unica.version='))
 updated=updated.replace('UN1CA '+oldversion,'UN1CA '+oldversion+'-BETA2-r3')
 destination=stage/'META-INF/com/google/android/updater-script';destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(updated)
 (release/'BETA2-updater-script.txt').write_text(updated)
 for n in ['build_info.txt']:
  content=z.read(n).decode();(stage/n).write_text(content.replace(oldversion,oldversion+'-BETA2-r3'))
for name in ['boot.img','vendor_boot.img','dtbo.img']:
 shutil.copyfile(work/name,stage/name);shutil.copyfile(work/name,target/name)
for name in ['vbmeta.img','vbmeta_system.img']:shutil.copyfile(src/'target/p3s/installer/avb'/name,stage/name)
with zipfile.ZipFile('/mnt/d/Codex-ROM/p3s/releases/a17-r2/p3s_A17_VINTF_r2-target_files.zip') as z:
 content=z.read('build_info.txt').decode();(target/'build_info.txt').write_text(content.replace(oldversion,oldversion+'-BETA2-r3'))
proof={'release':'BETA2-r3','purpose':'Corrected Samsung boot-container and installer beta','base':'Failed r2 Android17 port','stock_reference_firmware':'G998BXXSJHZC2','userspace_os_images_changed':False,'kernel_binary_and_modules_changed':False,'kernel_packaging_changed':True,'kernel_diagnostic_boot_settings_changed':True,'recovery_control_included_separately':True,'normal_installer_writes_recovery':False,'explicit_verification_metadata_installed':True,'firmware_bootloader_modem_ota_removed':True,'runtime_boot_verified':False,'flash_qualification':'HOLD: recovery control and kernel-only control must pass before full-ROM test','files':{n:sha(stage/n) for n in ['boot.img','vendor_boot.img','dtbo.img','vbmeta.img','vbmeta_system.img']},'boot_geometry_proof':json.loads((work/'p3s-boot-layout-proof.json').read_text()),'regression_tests':json.loads((rec/'regression-proof.json').read_text())}
(stage/'BETA2_BUILD_PROOF.json').write_text(json.dumps(proof,indent=2));(target/'BETA2_BUILD_PROOF.json').write_text(json.dumps(proof,indent=2));(release/'BUILD_PROOF.json').write_text(json.dumps(proof,indent=2))
print('Signed boot images, separate corrected recovery and complete installer updates staged: '+str(release))
