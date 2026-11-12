"""Use the previously working p3s top-level disabled-verification container.

Never modify flags or signatures in a chained vbmeta_system image.
"""
from pathlib import Path
import hashlib,json,shutil,struct,subprocess
base=Path('/opt/codex-rom/monsterrom-p3s');src=base/'source';record=base/'records/beta2-r5';record.mkdir(exist_ok=True);release=Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5');release.mkdir(exist_ok=True)
dest=src/'target/p3s/installer/avb'
for name in ['vbmeta.img','vbmeta_system.img']:shutil.copyfile(dest/name,record/('before-'+name))
root=Path('/mnt/d/Codex-ROM/p3s/phone-rollback-current/system-partitions/vbmeta.img').read_bytes()
if hashlib.sha256(root).hexdigest()!='f111567249c567e73230fedbfc768c3b8398568de9efbb027f72d39b98ac619e':raise SystemExit('Known-working top-level metadata mismatch')
if root[:4]!=b'AVB0' or len(root)!=65536 or struct.unpack_from('>I',root,120)[0]!=2:raise SystemExit('Unexpected top-level metadata format')
if struct.unpack_from('>I',root,28)[0]!=0:raise SystemExit('Expected empty, unsigned disabled-verification top-level image')
child=(base/'records/beta2-r3/stock-reference/vbmeta_system.img').read_bytes()
if child[:4]!=b'AVB0' or struct.unpack_from('>I',child,120)[0]!=0:raise SystemExit('Original chained metadata must have zero flags')
padded=child+bytes(65536-len(child));(dest/'vbmeta.img').write_bytes(root);(dest/'vbmeta_system.img').write_bytes(padded)
# Replace the earlier helper's unsupported per-child flag mutation at source.
preparer=Path(__file__).with_name('prepare-p3s-beta2.py');text=preparer.read_text()
old=" image[120:124]=(3).to_bytes(4,'big');image+=bytes(65536-len(image));(dest/name).write_bytes(image)"
new=""" if name=='vbmeta.img':
  proven=Path('/mnt/d/Codex-ROM/p3s/phone-rollback-current/system-partitions/vbmeta.img').read_bytes()
  if hashlib.sha256(proven).hexdigest()!='f111567249c567e73230fedbfc768c3b8398568de9efbb027f72d39b98ac619e':raise SystemExit('Top-level metadata provenance mismatch')
  image=bytearray(proven)
 elif int.from_bytes(image[120:124],'big')!=0:raise SystemExit('Chained AVB metadata flags must be zero')
 image+=bytes(65536-len(image));(dest/name).write_bytes(image)"""
if text.count(old)!=1:raise SystemExit('Prepare-helper flag mutation changed unexpectedly')
preparer.write_text(text.replace(old,new))
checker=Path(__file__).with_name('qualify-p3s-beta2.py');text=checker.read_text();old="struct.unpack_from('>I',data,120)[0]!=3";new="struct.unpack_from('>I',data,120)[0]!=(2 if name=='vbmeta.img' else 0)"
if text.count(old)!=1:raise SystemExit('Expected old metadata check not found')
checker.write_text(text.replace(old,new))
report={'top_level_flags':2,'top_level_algorithm':'NONE','top_level_sha256':hashlib.sha256(root).hexdigest(),'top_level_source':'Verified previously working pre-r2 p3s metadata backup','chained_flags':0,'chained_signed_payload_preserved':True,'chained_padded_sha256':hashlib.sha256(padded).hexdigest(),'previous_error':'Non-zero chained vbmeta flags violate AVB load_and_verify_vbmeta validation','previous_r4_metadata_stock_data_return_passed':False,'new_metadata_stock_data_compatibility':'Not tested; do not assume compatibility','note':'Existing encrypted stock Data did not boot under the previous r4 test metadata. Original stock boot/recovery/verification restoration returned Android without a format. This does not prove r2 initial failure cause.'}
(record/'AVB_CORRECTION_PROOF.json').write_text(json.dumps(report,indent=2));(release/'AVB_CORRECTION_PROOF.json').write_text(json.dumps(report,indent=2))
for name in ['vbmeta.img','vbmeta_system.img']:
 result=subprocess.run([str(src/'out/tools/bin/avbtool'),'info_image','--image',str(dest/name)],capture_output=True,text=True,check=True);(record/(name+'.info.txt')).write_text(result.stdout)
print(json.dumps(report,indent=2))
