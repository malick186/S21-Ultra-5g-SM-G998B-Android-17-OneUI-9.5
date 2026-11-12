from pathlib import Path
import importlib.util,json,shutil,subprocess
base=Path('/opt/codex-rom/monsterrom-p3s');src=base/'source';record=base/'records/beta2-r5';local=Path(__file__).parent
helper=src/'scripts/internal/check_p3s_avb_metadata.py';shutil.copyfile(local/'check-p3s-avb-metadata.py',helper)
spec=importlib.util.spec_from_file_location('avbcheck',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
avb=src/'target/p3s/installer/avb';root=(avb/'vbmeta.img').read_bytes();child=(avb/'vbmeta_system.img').read_bytes();module.validate(root,child)
tests={'reviewed_pair_passed':True}
mutations=[]
b=bytearray(child);b[120:124]=(3).to_bytes(4,'big');mutations.append(('nonzero_chained_flags_rejected',root,bytes(b)))
b=bytearray(child);b[512]^=1;mutations.append(('changed_chained_signed_payload_rejected',root,bytes(b)))
b=bytearray(root);b[120:124]=(3).to_bytes(4,'big');mutations.append(('different_root_profile_rejected',bytes(b),child))
mutations.append(('truncated_metadata_rejected',root[:1024],child))
for name,r,c in mutations:
 try:module.validate(r,c)
 except ValueError:tests[name]=True
 else:raise SystemExit('Unsafe AVB pair accepted: '+name)
p=src/'scripts/internal/build_full_ota_zip.sh';text=p.read_text();before=record/'build_full_ota_zip-before-avb-gate.sh'
if before.exists():raise SystemExit('AVB gate snapshot exists; refusing duplicate insertion')
shutil.copyfile(p,before);marker='LOG "- Creating zip"\n'
insert='''if [ "$TARGET_CODENAME" = p3s ] && [ "$SOURCE_PLATFORM_SDK_VERSION" -eq 37 ]; then
    python3 "$SRC_DIR/scripts/internal/check_p3s_avb_metadata.py" "$TMP_DIR" || exit 1
fi

'''
if text.count(marker)!=1:raise SystemExit('OTA AVB insertion point changed')
p.write_text(text.replace(marker,insert+marker));subprocess.run(['bash','-n',str(p)],check=True)
(record/'AVB_REGRESSION_PROOF.json').write_text(json.dumps(tests,indent=2));Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5/AVB_REGRESSION_PROOF.json').write_text(json.dumps(tests,indent=2));print(json.dumps(tests,indent=2))
