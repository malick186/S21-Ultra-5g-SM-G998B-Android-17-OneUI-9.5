from pathlib import Path
import hashlib,json,shutil
base=Path('/opt/codex-rom/monsterrom-p3s')
src=base/'kernel-source'
rec=base/'records/beta2-r5-kernel-fix1'
rec.mkdir(exist_ok=True)
p=src/'init/main.c'
before=p.read_text()
if 'call_builtin_init_nocfi' in before:raise SystemExit('Existing fix retained; refusing duplicate edit')
shutil.copyfile(p,rec/'main-before.c')
for name in ['.config','Module.symvers','System.map','include/generated/utsrelease.h']:
 dest=rec/('baseline-'+Path(name).name)
 shutil.copyfile(src/'out'/name,dest)
anchor='#if IS_BUILTIN(CONFIG_SEC_BOOTSTAT)\nstatic bool __init_or_module initcall_sec_debug = true;'
assert before.count(anchor)==1
helper='''/*
 * Built-in __init functions use raw .init.text addresses and are marked
 * __nocfi in this tree.  They may not have CFI canonical jump-table entries.
 * Only dispatch targets inside the built-in init-text range through this
 * non-inlined thunk.  Module init and other targets keep their CFI checks.
 */
static noinline int __nocfi call_builtin_init_nocfi(initcall_t fn)
{
	return fn();
}

static int call_initcall_target(initcall_t fn)
{
#ifdef CONFIG_CFI_CLANG
	unsigned long addr = (unsigned long)fn;

	if (addr >= (unsigned long)__inittext_begin &&
	    addr < (unsigned long)__inittext_end)
		return call_builtin_init_nocfi(fn);
#endif
	return fn();
}

'''
after=before.replace(anchor,helper+anchor)
# Exactly two existing initcall dispatch sites, not arbitrary callbacks.
assert before.count('ret = fn();')==2
after=after.replace('ret = fn();','ret = call_initcall_target(fn);')
p.write_text(after)
report={'scope':'Built-in init-text dispatch only; module and other indirect-call CFI retained','config_changed':False,'userspace_changed':False,'source_before_sha256':hashlib.sha256(before.encode()).hexdigest(),'source_after_sha256':hashlib.sha256(after.encode()).hexdigest(),'observed_panic':'CFI failure at ikconfig_init during do_one_initcall; persistent record partly damaged','runtime_fix_verified':False}
(rec/'change-proof.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
