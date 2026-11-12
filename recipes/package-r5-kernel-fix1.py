from pathlib import Path
import hashlib,json,shlex,shutil,subprocess,zipfile
base=Path('/opt/codex-rom/monsterrom-p3s');src=base/'source';kernel=base/'kernel-source';rec=base/'records/beta2-r5-kernel-fix1'
release=Path('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5/kernel-fix1');release.mkdir(exist_ok=True)
run=lambda args:subprocess.check_output([str(a) for a in args],stderr=subprocess.STDOUT,text=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (kernel/'out/.config').read_bytes()==(rec/'baseline-.config').read_bytes(),'Kernel config changed'
assert (kernel/'out/Module.symvers').read_bytes()==(rec/'baseline-Module.symvers').read_bytes(),'Exported module ABI changed'
assert (kernel/'out/include/generated/utsrelease.h').read_bytes()==(rec/'baseline-utsrelease.h').read_bytes(),'Kernel release changed'
objdump=Path('/opt/codex-kernel/p3s-v7/toolchain/clang-r596125/bin/llvm-objdump')
symbols=(kernel/'out/System.map').read_text()
assert 'call_builtin_init_nocfi' in symbols,'Non-inlined thunk missing'
thunk=run([objdump,'--disassemble-symbols=call_builtin_init_nocfi',kernel/'out/vmlinux'])
assert 'br\t' in thunk or 'blr\t' in thunk,'Thunk indirect call missing'
assert '__cfi_slowpath' not in thunk,'Thunk still has CFI instrumentation'
(rec/'initcall-thunk-disassembly.txt').write_text(thunk)
dispatcher=run([objdump,'--disassemble-symbols=do_one_initcall',kernel/'out/vmlinux'])
assert '__cfi_slowpath' in dispatcher,'Fallback CFI checks missing'
assert 'call_builtin_init_nocfi' in dispatcher,'Thunk not used by dispatcher'
(rec/'initcall-dispatch-disassembly.txt').write_text(dispatcher)
tools=src/'out/tools/bin';unpack=rec/'boot-unpacked';unpack.mkdir(exist_ok=True)
with zipfile.ZipFile('/mnt/d/Codex-ROM/p3s/releases/a17-beta2-r5/MonsterROM_A17_p3s_SM-G998B_BETA2_r5_TEST.zip') as z:
 old=rec/'previous-boot.img';old.write_bytes(z.read('boot.img'))
args=shlex.split(run([tools/'unpack_bootimg','--boot_img',old,'--out',unpack,'--format=mkbootimg']))
newkernel=kernel/'out/arch/arm64/boot/Image'
assert newkernel.is_file() and sha(newkernel)!=sha(unpack/'kernel'),'Kernel payload did not change'
args[args.index('--kernel')+1]=str(newkernel)
image=release/'boot.img'
run([tools/'mkbootimg',*args,'--output',image])
verify=rec/'boot-verified';verify.mkdir(exist_ok=True)
verify_args=shlex.split(run([tools/'unpack_bootimg','--boot_img',image,'--out',verify,'--format=mkbootimg']))
assert (verify/'kernel').read_bytes()==newkernel.read_bytes()
assert (verify/'ramdisk').read_bytes()==(unpack/'ramdisk').read_bytes(),'Boot ramdisk changed'
for key in ['--cmdline','--os_version','--os_patch_level','--header_version']:
 assert args[args.index(key)+1]==verify_args[verify_args.index(key)+1],key+' changed'
run([tools/'avbtool','add_hash_footer','--image',image,'--partition_size',67108864,'--partition_name','boot','--hash_algorithm','sha256','--algorithm','SHA256_RSA4096','--key',src/'security/avb/testkey_rsa4096.pem'])
run([tools/'avbtool','verify_image','--image',image,'--key',src/'security/avb/testkey_rsa4096.pem'])
proof={'purpose':'Targeted built-in initcall CFI panic correction','boot_sha256':sha(image),'kernel_sha256':sha(newkernel),'module_export_abi_unchanged':True,'kernel_config_unchanged':True,'kernel_release_unchanged':True,'ramdisk_unchanged':True,'module_and_non_init_fallback_CFI_retained':True,'recovery_vendor_boot_dtbo_userspace_not_changed':True,'avb_test_signature_verified':True,'runtime_boot_verified':False}
(release/'BUILD_PROOF.json').write_text(json.dumps(proof,indent=2));shutil.copyfile(kernel/'init/main.c',release/'main.c');shutil.copyfile(rec/'change-proof.json',release/'CHANGE_PROOF.json')
print(json.dumps(proof,indent=2))
