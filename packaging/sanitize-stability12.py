"""Create a key-free Stability 1.2 installer from the pinned private ZIP."""

import argparse
from copy import copy, deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile

from sdk37_images import mounted


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("stability12_assembler", HERE / "assemble-stability12.py")
assembler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assembler)
PINS = assembler.PINS
ODM_ENTRY = "odm.new.dat.br"
RUNTIME = Path("etc/p3s-runtime")
REMOVED = {RUNTIME / "adb_keys", RUNTIME / "debug-adb.sh"}
INIT = Path("etc/init/p3s-startup.rc")
PROFILE = RUNTIME / "shell-profile.sh"
UPDATED = {INIT, PROFILE}
PARTITION_BYTES = PINS["manifest"]["images"]["odm"]["bytes"]


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Expected one exact development-only configuration block")
    return text.replace(old, new, 1)


def sanitize_runtime(tree):
    for name in REMOVED:
        (tree / name).unlink()
    init = tree / INIT
    debug_service = """service p3s-debug-adb /system/bin/sh /odm/etc/p3s-runtime/debug-adb.sh
    disabled
    oneshot
    user root
    group root
    seclabel u:r:ksu:s0

on boot
    start p3s-debug-adb

"""
    init.write_text(replace_once(init.read_text(), debug_service, ""))
    profile = tree / PROFILE
    script = profile.read_text()
    for line in (
        " timeout 10 settings put global development_settings_enabled 1\n",
        " timeout 10 settings put global adb_enabled 1\n",
        " timeout 10 svc usb setFunctions mtp,adb\n",
    ):
        script = replace_once(script, line, "")
    subprocess.run(["sh", "-n"], input=script.encode(), check=True)
    profile.write_text(script)


def permissions(reference, tree, scratch):
    contexts = []
    fs_config = []
    for path in [tree, *sorted(tree.rglob("*"))]:
        relative = path.relative_to(tree)
        original = reference / relative
        metadata = original.lstat()
        name = "" if relative == Path(".") else relative.as_posix()
        label = os.getxattr(original, "security.selinux", follow_symlinks=False).rstrip(b"\0").decode()
        caps = 0
        if "security.capability" in os.listxattr(original, follow_symlinks=False):
            value = os.getxattr(original, "security.capability", follow_symlinks=False)
            caps = int.from_bytes(value[4:8], "little") | int.from_bytes(value[12:16], "little") << 32
        context_name = "/odm/" + name if name else "/odm"
        contexts.append(f"{re.escape(context_name).replace(chr(92) + '-', '-')} {label}")
        filename = "odm/" + name if name else ""
        mode = stat.S_IMODE(metadata.st_mode)
        fs_config.append(f"{filename} {metadata.st_uid} {metadata.st_gid} {mode:o} capabilities={caps:#x}")
    (scratch / "contexts").write_text("\n".join(contexts) + "\n")
    (scratch / "fs_config").write_text("\n".join(fs_config) + "\n")


def verify_odm(old, new, tree):
    with mounted(old) as before, mounted(new) as after:
        old_paths = {p.relative_to(before) for p in before.rglob("*")}
        new_paths = {p.relative_to(after) for p in after.rglob("*")}
        if old_paths - new_paths != REMOVED or new_paths - old_paths:
            raise ValueError("Unexpected paths changed in the sanitized ODM")
        changed = set()
        for relative in new_paths | {Path(".")}:
            a, b = before / relative, after / relative
            source, result = a.lstat(), b.lstat()
            left = (source.st_mode, source.st_uid, source.st_gid)
            right = (result.st_mode, result.st_uid, result.st_gid)
            attrs = set(os.listxattr(a, follow_symlinks=False))
            if left != right or attrs != set(os.listxattr(b, follow_symlinks=False)):
                raise ValueError(f"ODM metadata mismatch for {relative}")
            for attr in attrs:
                if os.getxattr(a, attr, follow_symlinks=False) != os.getxattr(b, attr, follow_symlinks=False):
                    raise ValueError(f"ODM attribute mismatch for {relative}")
            if a.is_symlink() and os.readlink(a) != os.readlink(b):
                raise ValueError(f"ODM symlink changed: {relative}")
            if not a.is_symlink() and a.is_file() and a.read_bytes() != b.read_bytes():
                changed.add(relative)
        if changed != UPDATED:
            raise ValueError(f"Unexpected ODM file changes: {sorted(changed)}")
        for relative in UPDATED:
            if (after / relative).read_bytes() != (tree / relative).read_bytes():
                raise ValueError(f"ODM did not contain the intended sanitized {relative}")
        with (before / RUNTIME / "adb_keys").open("rb") as key:
            fingerprint_input = key.read().split()[0]
        for relative in new_paths:
            path = after / relative
            if not path.is_symlink() and path.is_file() and fingerprint_input in path.read_bytes():
                raise ValueError("The old tester key still exists in ODM")


def rebuild_odm(archive, tools, key, scratch):
    original = scratch / "original/odm.img"
    rebuilt = scratch / "key-free/odm.img"
    original.parent.mkdir()
    rebuilt.parent.mkdir()
    with archive.open(ODM_ENTRY) as payload, original.open("wb") as out:
        compressed = scratch / "original.br"
        with compressed.open("wb") as dest:
            shutil.copyfileobj(payload, dest, assembler.BUFFER)
        subprocess.run(["brotli", "-d", "-c", compressed], stdout=out, check=True)
    assembler.check_file(original, PINS["manifest"]["images"]["odm"]["sha256"], PARTITION_BYTES)
    tree = scratch / "tree"
    subprocess.run([tools / "fsck.erofs", f"--extract={tree}", original], check=True)
    sanitize_runtime(tree)
    with mounted(original) as reference:
        permissions(reference, tree, scratch)
    with (scratch / "mkfs.log").open("w") as log:
        subprocess.run([tools / "mkfs.erofs", "-zlz4hc,9", "-T1640995200", "--mount-point=/odm",
                        "--file-contexts=" + str(scratch / "contexts"),
                        "--fs-config-file=" + str(scratch / "fs_config"), rebuilt, tree],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    details = subprocess.check_output([tools / "avbtool", "info_image", "--image", original], text=True)
    salt = re.search(r"^\s*Salt:\s*([0-9a-f]+)$", details, flags=re.M)
    if not salt:
        raise ValueError("Original ODM AVB salt is missing")
    subprocess.run([tools / "avbtool", "add_hashtree_footer", "--image", rebuilt,
                    "--partition_size", str(PARTITION_BYTES), "--partition_name", "odm",
                    "--hash_algorithm", "sha256", "--algorithm", "SHA256_RSA4096",
                    "--key", key, "--salt", salt[1]], check=True)
    subprocess.run([tools / "avbtool", "verify_image", "--image", rebuilt, "--key", key], check=True)
    verify_odm(original, rebuilt, tree)
    print("ODM verified with the tester key and automatic ADB startup removed", flush=True)
    return rebuilt


def copy_archive(archive, path, odm, changes):
    omit = set(changes) | {ODM_ENTRY, assembler.CERT_ENTRY}
    with zipfile.ZipFile(path, "w", allowZip64=True) as out:
        for entry in archive.infolist():
            if entry.filename in omit:
                continue
            with archive.open(entry) as src, out.open(copy(entry), "w", force_zip64=entry.file_size >= 2**31) as dest:
                shutil.copyfileobj(src, dest, assembler.BUFFER)
        for name, data in changes.items():
            out.writestr(name, data)
        with subprocess.Popen(["brotli", "-q", "2", "-c", odm], stdout=subprocess.PIPE) as codec:
            with out.open(ODM_ENTRY, "w") as dest:
                shutil.copyfileobj(codec.stdout, dest, assembler.BUFFER)
            if codec.wait():
                raise ValueError("Compressing the test-key-free ODM failed")


def sign_archive(tools, cert, key, unsigned, signed):
    # Batch the signer's small writes before they reach the output drive.
    with tempfile.TemporaryDirectory(prefix="p3s-sign-") as local:
        pipe = Path(local) / "signing.pipe"
        os.mkfifo(pipe, 0o600)
        with signed.open("wb") as stream, subprocess.Popen(
            ["dd", f"if={pipe}", "iflag=fullblock", "bs=8M", "status=none"], stdout=stream
        ) as drain:
            try:
                subprocess.run([tools / "signapk", "-w", cert, key, unsigned, pipe], check=True)
                if drain.wait(timeout=60):
                    raise ValueError("Could not write signed ZIP")
            finally:
                if drain.poll() is None:
                    drain.kill()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path, help="locally owned pinned Stability 1.2 ZIP")
    parser.add_argument("--source", required=True, type=Path, help="MonsterROM tree with built Linux host tools")
    parser.add_argument("--output", required=True, type=Path, help="new local ZIP path in an existing directory")
    args = parser.parse_args()
    reference = PINS["reference_archive"]
    assembler.check_file(args.archive, reference["sha256"], reference["bytes"])
    if args.output.exists() or args.output.with_suffix(".zip.sha256").exists():
        raise FileExistsError(f"Output already exists: {args.output}")

    tools = args.source / "out/tools/bin"
    security = args.source / "security"
    certificate = security / "aosp_testkey.x509.pem"
    os.environ["PATH"] = str(tools) + os.pathsep + os.environ["PATH"]
    with tempfile.TemporaryDirectory(prefix="build-", dir=args.output.parent) as folder:
        scratch = Path(folder)
        unsigned, signed = scratch / "unsigned.zip", scratch / "signed.zip"
        with zipfile.ZipFile(args.archive) as archive:
            odm = rebuild_odm(archive, tools, security / "avb/testkey_rsa4096.pem", scratch)
            pins = deepcopy(PINS)
            manifest = pins["manifest"]
            with odm.open("rb") as stream:
                digest, size = assembler.sha256(stream)
            if size != PARTITION_BYTES:
                raise ValueError("Sanitized ODM size differs from the installer layout")
            manifest["images"]["odm"]["sha256"] = digest
            manifest["version"] = "stability-1.2-key-free-local"
            manifest["personalized_adb_public_key"] = False
            manifest["full_clean_installer_device_tested"] = False
            manifest["adb_enabled_by_installer"] = False
            changes = {
                assembler.UPDATER: archive.read(assembler.UPDATER).replace(b"LOCAL DEVELOPMENT", b"KEY-FREE LOCAL"),
                "build_info.txt": archive.read("build_info.txt").replace(b"STABILITY-1.2-DEV-LOCAL", b"STABILITY-1.2-KEY-FREE-LOCAL"),
                "STABILITY_BUILD.json": (json.dumps(manifest, indent=2) + "\n").encode(),
            }
            for name, data in changes.items():
                pins["entry_sha256"][name] = hashlib.sha256(data).hexdigest()
            copy_archive(archive, unsigned, odm, changes)
        print("Key-free archive assembled; signing", flush=True)
        sign_archive(tools, certificate, security / "aosp_testkey.pk8", unsigned, signed)
        assembler.verify_archive(signed, certificate, scratch, pins)
        with signed.open("rb") as stream:
            digest, size = assembler.sha256(stream)
        signed.rename(args.output)
        args.output.with_suffix(".zip.sha256").write_text(f"{digest}  {args.output.name}\n")
        proof = {"archive": args.output.name, "sha256": digest, "bytes": size, "manifest": manifest,
                 "odm_removed": sorted(str(path) for path in REMOVED),
                 "odm_edited": sorted(str(path) for path in UPDATED)}
        args.output.with_suffix(".verification.json").write_text(json.dumps(proof, indent=2) + "\n")
        print(f"{digest}  {args.output}", flush=True)


if __name__ == "__main__":
    main()
