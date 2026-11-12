from pathlib import Path
import hashlib,io,json,shutil,struct,tarfile,zipfile
base=Path('/opt/codex-rom/monsterrom-p3s');src=base/'source';release=Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5');record=base/'records/beta2-r5';record.mkdir(exist_ok=True);release.mkdir(exist_ok=True)
stage=release/'installer-update';stage.mkdir(exist_ok=True);target=release/'target-update';target.mkdir(exist_ok=True);avb=src/'target/p3s/installer/avb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=(avb/'vbmeta.img').read_bytes();child=(avb/'vbmeta_system.img').read_bytes()
if sha(avb/'vbmeta.img')!='f111567249c567e73230fedbfc768c3b8398568de9efbb027f72d39b98ac619e' or struct.unpack_from('>I',root,120)[0]!=2:raise SystemExit('Unexpected top-level metadata')
original=(base/'records/beta2-r3/stock-reference/vbmeta_system.img').read_bytes()
if child!=original+bytes(65536-len(original)) or struct.unpack_from('>I',child,120)[0]!=0:raise SystemExit('Chained metadata signature/flags must be preserved')
p=src/'target/p3s/installer/assertions.edify';new=p.read_text().replace('BETA2-r4','BETA2-r5');p.write_text(new)
with zipfile.ZipFile('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r3/MonsterROM_A17_p3s_SM-G998B_BETA2_r3_TEST.zip') as z:
 script=z.read('META-INF/com/google/android/updater-script').decode();old=(base/'records/beta2-r4/assertions-before-r4.edify').read_text().strip()
 if script.count(old)!=1:raise SystemExit('Expected exact r3 guard block')
 script=script.replace(old,new.strip()).replace('BETA2-r3','BETA2-r5')
 if script.count('assert(package_extract_file(')!=5 or '/dev/block/by-name/bota' in script:raise SystemExit('Unexpected partition writer')
 # Guard-only runtime test uses the same script prefix and updater binary.
 update=stage/'META-INF/com/google/android/updater-script';update.parent.mkdir(parents=True,exist_ok=True);update.write_text(script);(release/'BETA2_R5-updater-script.txt').write_text(script)
 (stage/'build_info.txt').write_text(z.read('build_info.txt').decode().replace('BETA2-r3','BETA2-r5'))
 proof=json.loads(z.read('BETA2_BUILD_PROOF.json'));proof.update(release='BETA2-r5',top_level_vbmeta_flags=2,chained_vbmeta_flags=0,chained_signed_metadata_preserved=True,recovery_boot_repack_hook_disabled=True,recovery_entry_and_no_boot_mutation_tested=True,recovery_return_to_stock_requires_original_metadata_restore=True,runtime_boot_verified=False,flash_qualification='Experimental clean-ROM test candidate; full Android17 boot and new AVB profile not yet runtime-qualified')
 for name in ['vbmeta.img','vbmeta_system.img']:shutil.copyfile(avb/name,stage/name);proof['files'][name]=sha(avb/name)
 (stage/'BETA2_BUILD_PROOF.json').write_text(json.dumps(proof,indent=2));(release/'BUILD_PROOF.json').write_text(json.dumps(proof,indent=2))
 (record/'guard-only-updater').write_bytes(z.read('META-INF/com/google/android/update-binary'))
with zipfile.ZipFile('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r3/p3s_A17_BETA2_r3-target_files.zip') as z:
 (target/'build_info.txt').write_text(z.read('build_info.txt').decode().replace('BETA2-r3','BETA2-r5'));(target/'BETA2_BUILD_PROOF.json').write_text(json.dumps(proof,indent=2))
recovery=Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r4/RECOVERY_NO_BOOT_PATCH.img');stock=base/'records/beta2-r4/stock-rescue-inputs'
bundles={'CUSTOM_RECOVERY_AVB_R5_SM-G998B.tar':{'recovery.img':recovery,'vbmeta.img':avb/'vbmeta.img','vbmeta_system.img':avb/'vbmeta_system.img'},'STOCK_BOOT_RECOVERY_AVB_RESCUE_R5_SM-G998B.tar':{n:stock/n for n in ['boot.img','recovery.img','vbmeta.img','vbmeta_system.img']}}
bundle_proof={'revision':'R5','recovery_image_runtime_booted':True,'recovery_boot_modification_disabled':True,'new_metadata_cohort_runtime_tested':False,'bundles':{}}
for name,files in bundles.items():
 tar=release/name;final=tar.with_suffix('.tar.md5')
 if tar.exists() or final.exists():raise SystemExit('Existing R5 bundle retained')
 contents={}
 with tarfile.open(tar,'w',format=tarfile.USTAR_FORMAT) as tf:
  for member,path in files.items():b=path.read_bytes();h=tarfile.TarInfo(member);h.size=len(b);h.mode=0o644;tf.addfile(h,io.BytesIO(b));contents[member]=hashlib.sha256(b).hexdigest()
 with tarfile.open(tar) as tf:
  for member,digest in contents.items():
   if hashlib.sha256(tf.extractfile(member).read()).hexdigest()!=digest:raise SystemExit('Bundle payload mismatch')
 b=tar.read_bytes();final.write_bytes(b+(hashlib.md5(b).hexdigest()+'  '+tar.name+'\n').encode());bundle_proof['bundles'][final.name]={'sha256':sha(final),'contents':contents}
(release/'RECOVERY_AND_RESCUE_PROOF.json').write_text(json.dumps(bundle_proof,indent=2))
correction=json.loads((record/'AVB_CORRECTION_PROOF.json').read_text());correction.pop('verification_state_change_compatible_with_existing_stock_data',None);correction.update(previous_r4_metadata_stock_data_return_passed=False,new_metadata_stock_data_compatibility='Not yet tested');(record/'AVB_CORRECTION_PROOF.json').write_text(json.dumps(correction,indent=2));(release/'AVB_CORRECTION_PROOF.json').write_text(json.dumps(correction,indent=2))
print('R5 full-installer updates and matched recovery/rescue staged; original chained AVB signature preserved')
