#!/usr/bin/env python3
"""Assemble the SM-G998B r7 recovery candidate from a verified local r5 and fixed inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
BASE_SHA = "dee1fe80a482051961ec062ce282653c60d72e23a4d7d2beb46b17cbdaedfe9c"
SCRIPT = "META-INF/com/google/android/updater-script"

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def build(base, inputs, source, output, scratch, blocks):
    if output.exists():
        raise FileExistsError(output)
    hashes = json.loads((HERE / "inputs.json").read_text())
    files = {name: (HERE.parent / "runtime" if name.endswith(".sh") else inputs) / name for name in hashes}
    if digest(base) != BASE_SHA or any(digest(files[n]) != h for n, h in hashes.items()):
        raise ValueError("Base installer or payload hash differs from release inputs")
    partitions = json.loads((HERE / "r7-blocks.json").read_text())
    for part, record in partitions.items():
        if digest(blocks / (part+".new.dat.br")) != record["brotli_sha256"]:
            raise ValueError("Unverified block payload: "+part)
    with tempfile.TemporaryDirectory(dir=scratch) as staging:
        tmp = Path(staging)
        unsigned = tmp / "unsigned.zip"
        signed = tmp / "signed.zip"
        with zipfile.ZipFile(base) as src, zipfile.ZipFile(unsigned, "w", allowZip64=True) as dst:
            script = src.read(SCRIPT).decode()
            cut = script.index("ui_print(")
            guards = script[:cut]
            first = script.index("assert(update_dynamic_partitions")
            last = script.index('ui_print("Bootloader, modem')
            install = script[first:last]
            if '/dev/block/by-name/recovery' in install or 'firmware/' in install:
                raise ValueError("Unexpected physical partition writer")
            runtime = sorted(n for n in files if not n.endswith(".img"))
            edify = guards + 'ui_print("MonsterROM p3s A17 beta 2 r7 - SM-G998B clean-install candidate");\n'
            edify += 'assert(package_extract_dir("p3s-runtime", "/tmp/p3s-r7"));\n'
            edify += 'run_program("/sbin/sh", "/tmp/p3s-r7/stage-runtime.sh") == 0 || abort("E3005: runtime staging failed before partition writes; inspect recovery log, Data and Metadata mounts.");\n'
            edify += install + 'set_progress(1.0);\nui_print("r7 installed. Reboot System; preserve Data after installation.");\n'
            changes = {SCRIPT: edify.encode(), "build_info.txt": src.read("build_info.txt").replace(b"BETA2-r5",b"BETA2-r7"),
                       "p3s-runtime/stage-runtime.sh": (HERE/"stage-runtime.sh").read_bytes(),
                       "p3s-runtime/runtime.sha256": "".join(f"{hashes[n]}  {n}\n" for n in runtime).encode()}
            for n in runtime:
                changes["p3s-runtime/"+n] = files[n].read_bytes()
            for n in ("boot.img","vendor_boot.img","dtbo.img","vbmeta.img","vbmeta_system.img"):
                changes[n] = files[n].read_bytes()
            odm = files["odm.img"].read_bytes()
            size = len(odm)
            if size % 4096 or f"resize odm {size}\n".encode() not in src.read("dynamic_partitions_op_list"):
                raise ValueError("ODM partition size mismatch")
            odm_blocks = size // 4096
            changes["odm.new.dat.br"] = subprocess.run(["brotli","-q","6","-c"],input=odm,capture_output=True,check=True).stdout
            changes["odm.transfer.list"] = f"4\n{odm_blocks}\n0\n0\nnew 2,0,{odm_blocks}\n".encode()
            block_payloads = {}
            for part, record in partitions.items():
                count = record["bytes"] // 4096
                if f"resize {part} {record['bytes']}\n".encode() not in src.read("dynamic_partitions_op_list"):
                    raise ValueError("Unexpected logical partition size: "+part)
                changes[part+".transfer.list"] = f"4\n{count}\n0\n0\nnew 2,0,{count}\n".encode()
                block_payloads[part+".new.dat.br"] = blocks/(part+".new.dat.br")
            for e in src.infolist():
                if e.filename in changes or e.filename in block_payloads or e.filename in ("BETA2_BUILD_PROOF.json","META-INF/com/android/otacert") or e.filename.startswith("firmware/"):
                    continue
                with src.open(e) as old, dst.open(e, "w", force_zip64=e.file_size>=2**31) as new:
                    shutil.copyfileobj(old,new,8*1024*1024)
            for name, path in block_payloads.items():
                dst.write(path, name, compress_type=zipfile.ZIP_STORED)
            for name,data in changes.items():
                dst.writestr(name,data,compress_type=zipfile.ZIP_DEFLATED if not name.endswith(".br") else zipfile.ZIP_STORED)
        subprocess.run([source/"out/tools/bin/signapk","-w",source/"security/aosp_testkey.x509.pem",source/"security/aosp_testkey.pk8",unsigned,signed],check=True)
        unsigned.unlink()
        with zipfile.ZipFile(signed) as z:
            if z.testzip() or len(z.namelist()) != len(set(z.namelist())):
                raise ValueError("Signed ZIP integrity failure")
            for n,data in changes.items():
                if z.read(n)!=data: raise ValueError("Payload mismatch: "+n)
        value=digest(signed)
        pending=output.with_suffix(".partial")
        with pending.open("xb") as dest, signed.open("rb") as src:
            shutil.copyfileobj(src,dest,8*1024*1024)
        if digest(pending)!=value: raise ValueError("Transport hash mismatch")
        pending.rename(output)
        output.with_suffix(".zip.sha256").write_text(f"{value}  {output.name}\n")
        print(output.name,value,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("base","inputs","source","output","scratch","blocks"): p.add_argument("--"+name,type=Path,required=True)
    build(**vars(p.parse_args()))
