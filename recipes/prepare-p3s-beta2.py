from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile

base=Path('/opt/codex-rom/monsterrom-p3s');src=base/'source';record=base/'records/beta2-r3';record.mkdir(exist_ok=True)
before=record/'source-before';before.mkdir(exist_ok=True)
changed=['target/p3s/installer/assertions.edify','target/p3s/installer/install-end.edify','target/p3s/installer/customize.sh','scripts/make_rom.sh','scripts/internal/create_target_files_zip.sh','scripts/internal/build_full_ota_zip.sh']
for name in changed:
 p=src/name;save=before/name
 if save.exists():raise SystemExit('Before snapshot already exists: '+str(save))
 save.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,save)
kernel_before=record/'kernel-before';shutil.copytree(src/'out/target/p3s/work_dir/kernel',kernel_before)
reference=record/'stock-reference';reference.mkdir(exist_ok=True)
ap=next((Path('/mnt/d/Codex-ROM/p3s/odin-packages/SM-G998B_AUT')).glob('AP_G998BXXSJHZC2_*.tar.md5'))
provenance={}
with tarfile.open(ap) as tf:
 for name in ['boot.img','vendor_boot.img','dtbo.img','recovery.img','vbmeta.img','vbmeta_system.img']:
  packed=tf.extractfile(name+'.lz4').read();image=subprocess.run(['lz4','-d','-c'],input=packed,capture_output=True,check=True).stdout
  (reference/name).write_bytes(image);provenance[name]={'bytes':len(image),'sha256':hashlib.sha256(image).hexdigest()}
(reference/'PROVENANCE.json').write_text(json.dumps({'source':str(ap),'firmware':'G998BXXSJHZC2','images':provenance},indent=2))
helper=Path(__file__).with_name('normalize-p3s-boot-layout.py');shutil.copyfile(helper,src/'scripts/internal/normalize_p3s_boot_layout.py')
dest=src/'target/p3s/installer/avb';dest.mkdir(exist_ok=True)
for name in ['vbmeta.img','vbmeta_system.img']:
 image=bytearray((reference/name).read_bytes())
 if image[:4]!=b'AVB0' or len(image)>65536:raise SystemExit('Unexpected vbmeta input')
 if name=='vbmeta.img':
  proven=Path('/mnt/d/Codex-ROM/p3s/phone-rollback-current/system-partitions/vbmeta.img').read_bytes()
  if hashlib.sha256(proven).hexdigest()!='f111567249c567e73230fedbfc768c3b8398568de9efbb027f72d39b98ac619e':raise SystemExit('Top-level metadata provenance mismatch')
  image=bytearray(proven)
 elif int.from_bytes(image[120:124],'big')!=0:raise SystemExit('Chained AVB metadata flags must be zero')
 image+=bytes(65536-len(image));(dest/name).write_bytes(image)
shutil.copyfile(reference/'PROVENANCE.json',dest/'PROVENANCE.json')
(src/'target/p3s/installer/assertions.edify').write_text('''getprop("ro.boot.em.model") == "SM-G998B" || abort("E3004: This beta supports SM-G998B only.");
getprop("ro.boot.bootloader") == "G998BXXSJHZC2" || abort("E3003: Install the exact G998BXXSJHZC2 stock firmware before this beta. No automatic bootloader updates are provided.");
getprop("ro.boot.rp") == "19" || abort("E3003: Unexpected bootloader revision; no partition changes made.");
getprop("ro.boot.vbmeta.device_state") == "unlocked" || abort("E3003: This custom build requires an already-unlocked bootloader.");
getprop("ro.twrp.version") != "" || abort("E3000: A separately validated custom recovery is required.");
is_substring("afaneh92", getprop("ro.twrp.version")) && abort("E3000: This package retains its existing recovery compatibility restriction.");
ui_print("S21 Ultra personal BETA2-r3: experimental boot-layout correction; boot success is not certified.");
''')
(src/'target/p3s/installer/install-end.edify').write_text('''ui_print("Installing the explicit beta verification metadata...");
assert(package_extract_file("vbmeta.img", "/dev/block/by-name/vbmeta"));
assert(package_extract_file("vbmeta_system.img", "/dev/block/by-name/vbmeta_system"));
ui_print("Bootloader, modem, recovery and BOTA were not updated by this beta installer.");
''')
(src/'target/p3s/installer/customize.sh').write_text('''# Personal p3s beta: exact stock firmware is a precondition, never an OTA action.
for image in vbmeta.img vbmeta_system.img; do
    input="$SRC_DIR/target/p3s/installer/avb/$image"
    [ -f "$input" ] && [ "$(stat -c %s "$input")" = 65536 ] || return 1
    cp -a "$input" "$TMP_DIR/$image" || return 1
done
unset image input
''')
# Fix the boot packing path without changing the reviewed kernel/module cohort.
p=src/'scripts/make_rom.sh';text=p.read_text();marker='''        python3 "$SRC_DIR/scripts/internal/check_p3s_boot_metadata.py" \\
'''
insert='''        python3 "$SRC_DIR/scripts/internal/normalize_p3s_boot_layout.py" \\
            --work "$WORK_DIR/kernel" --reference "$FW_DIR/$TARGET_FIRMWARE_PATH/kernel/vendor_boot.img" \\
            --tools "$TOOLS_DIR/bin" || exit 1
'''
if text.count(marker)!=1:raise SystemExit('make_rom insertion point changed')
p.write_text(text.replace(marker,insert+marker))
# Keep large image/OTA staging on the user-selected D: drive when requested.
for name,subdir in [('scripts/internal/create_target_files_zip.sh','target-files'),('scripts/internal/build_full_ota_zip.sh','full-ota')]:
 p=src/name;text=p.read_text();marker='source "$SRC_DIR/scripts/utils/install_utils.sh" || exit 1\n'
 insertion='''if [ -n "${ROM_BUILD_TMP_ROOT:-}" ]; then
    [[ "$ROM_BUILD_TMP_ROOT" = /mnt/d/Codex-ROM/p3s/build-beta2-r3 ]] || { echo "Unreviewed build temporary root" >&2; exit 1; }
    TMP_DIR="$ROM_BUILD_TMP_ROOT/'''+subdir+'''"
fi
'''
 if name.endswith('build_full_ota_zip.sh'):
  original='TMP_DIR="$OUT_DIR/target/$TARGET_CODENAME/zip"\n'
  if text.count(original)!=1:raise SystemExit('OTA temporary root changed')
  text=text.replace(original,original+insertion)
 else:
  if text.count(marker)!=1:raise SystemExit('Target-files temporary root changed')
  text=text.replace(marker,marker+'\n'+insertion)
 p.write_text(text)
# Every raw boot partition write must fail the installer if extraction fails.
p=src/'scripts/internal/build_full_ota_zip.sh';text=p.read_text()
text=text.replace("echo -n 'package_extract_file(\"'","echo -n 'assert(package_extract_file(\"'")
text=text.replace("echo -n 'package_extract_file(\"boot.img\", '","echo -n 'assert(package_extract_file(\"boot.img\", '")
text=text.replace('echo    \");\\\""','echo    "));\\\""') if False else text
# Exact source line suffix occurs once in the generic loop and once for boot.
old='                echo    ");\\\""'
# Literal shell emits ");"; use explicit line replacement below.
lines=text.splitlines(True)
for i,line in enumerate(lines):
 if line.strip()==r'echo    ");"':lines[i]=line[:len(line)-len(line.lstrip())]+"echo    '));'\n"
p.write_text(''.join(lines))
print('Beta2 stock references and source installer/layout changes prepared: '+str(record))
