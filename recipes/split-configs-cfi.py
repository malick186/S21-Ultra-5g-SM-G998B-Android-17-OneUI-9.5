from pathlib import Path
import shutil
base=Path('/opt/codex-rom/monsterrom-p3s')
root=base/'kernel-source/kernel'
r=base/'records/ikconfig-cfi'
r.mkdir(exist_ok=True)
src=root/'configs.c'
s=src.read_text()
mk=root/'Makefile'
m=mk.read_text()
assert 'CFLAGS_REMOVE_configs.o += $(CC_FLAGS_LTO)' in m
assert not (root/'configs_proc.c').exists()
shutil.copyfile(src,r/'configs-before.c')
shutil.copyfile(mk,r/'Makefile-before')
start=s.index('/*\n * "IKCFG_ST"')
end=s.index('#ifdef CONFIG_IKCONFIG_PROC',start)
(root/'configs_proc.c').write_text(s[:start]+s[end:])
(root/'configs_data.S').write_text("""/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Keep the extraction markers adjacent to the compressed kernel configuration. */
.section .rodata, "a"
.ascii "IKCFG_ST"
.global kernel_config_data
kernel_config_data:
.incbin "kernel/config_data.gz"
.global kernel_config_data_end
kernel_config_data_end:
.ascii "IKCFG_ED"
""")
mk.write_text(m.replace('$(obj)/configs.o: $(obj)/config_data.gz\nCFLAGS_REMOVE_configs.o += $(CC_FLAGS_LTO)','configs-y := configs_proc.o configs_data.o\n$(obj)/configs_data.o: $(obj)/config_data.gz'))
src.unlink()
