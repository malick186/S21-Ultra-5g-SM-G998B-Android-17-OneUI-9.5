from pathlib import Path
import json,shutil
base=Path('/opt/codex-rom/monsterrom-p3s');src=base/'kernel-source';rec=base/'records/beta2-r5-kernel-fix2';rec.mkdir(exist_ok=True)
p=src/'init/main.c';before=p.read_text()
assert 'initcall_is_loading_module_entry' not in before
shutil.copyfile(p,rec/'main-before.c')
for n in ['.config','Module.symvers','System.map','include/generated/utsrelease.h']:shutil.copyfile(src/'out'/n,rec/('baseline-'+Path(n).name))
after=before.replace('call_builtin_init_nocfi','call_init_entry_nocfi')
start=after.index('/*\n * Built-in __init functions use raw .init.text addresses')
end=after.index('static noinline int __nocfi call_init_entry_nocfi',start)
after=after[:start]+'''/*
 * This tree marks __init functions __nocfi. Raw init-text entry addresses
 * can lack canonical CFI jump-table entries. Limit the uninstrumented
 * call to built-in init text or the exact init-text entry of a module
 * currently being loaded. All other targets retain their CFI checks.
 */
'''+after[end:]
anchor='static int call_initcall_target(initcall_t fn)\n'
helper='''#if defined(CONFIG_CFI_CLANG) && defined(CONFIG_MODULES)
static bool initcall_is_loading_module_entry(initcall_t fn)
{
	struct module *mod;
	unsigned long addr = (unsigned long)fn;
	bool is_entry = false;

	/* __module_address() requires module_mutex or disabled preemption. */
	preempt_disable();
	mod = __module_address(addr);
	if (mod && mod->state == MODULE_STATE_COMING && mod->init == fn &&
	    within_module_init(addr, mod) &&
	    addr < (unsigned long)mod->init_layout.base +
		   mod->init_layout.text_size)
		is_entry = true;
	preempt_enable();

	/* The loader owns this COMING module until its init call returns. */
	return is_entry;
}
#endif

'''
assert after.count(anchor)==1
after=after.replace(anchor,helper+anchor)
needle='\t\treturn call_init_entry_nocfi(fn);\n#endif\n\treturn fn();'
assert after.count(needle)==1
after=after.replace(needle,'''\t\treturn call_init_entry_nocfi(fn);
#ifdef CONFIG_MODULES
	if (initcall_is_loading_module_entry(fn))
		return call_init_entry_nocfi(fn);
#endif
#endif
	return fn();''')
p.write_text(after)
(rec/'change-proof.json').write_text(json.dumps({'scope':'Add only exact COMING-module init entry inside module init text to the validated initialization dispatcher','previous_result':'Builtin panic passed; Android first-stage init reached; watchdog module init CFI panic captured','global_CFI_disabled':False,'runtime_fix_verified':False},indent=2))
print('Module initialization entry guard added; arbitrary module callbacks remain CFI checked')
