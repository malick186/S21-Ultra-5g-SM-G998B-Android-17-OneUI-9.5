"""Reassemble or verify the SM-G998B Stability 1.2 local installer."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from verify import signature


HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / "stability12-inputs.json").read_text())
MANIFEST = PINS["manifest"]
IMAGES = MANIFEST["images"]
UPDATER = "META-INF/com/google/android/updater-script"
CERT_ENTRY = "META-INF/com/android/otacert"
BUFFER = 8 << 20


def sha256(stream):
    digest = hashlib.sha256()
    size = 0
    while block := stream.read(BUFFER):
        digest.update(block)
        size += len(block)
    return digest.hexdigest(), size


def check_file(path, expected_hash, expected_size=None):
    with path.open("rb") as stream:
        digest, size = sha256(stream)
    if digest != expected_hash or (expected_size is not None and size != expected_size):
        raise ValueError(f"Unexpected SHA-256 or size for {path}")


def payload_info(archive, name):
    with subprocess.Popen(["brotli", "-d", "-c"], stdin=subprocess.PIPE, stdout=subprocess.PIPE) as codec:
        def feed():
            with archive.open(name) as source, codec.stdin:
                shutil.copyfileobj(source, codec.stdin, BUFFER)

        with ThreadPoolExecutor(max_workers=1) as worker:
            sent = worker.submit(feed)
            result = sha256(codec.stdout)
            sent.result()
        if codec.wait():
            raise ValueError(f"Brotli decode failed for {name}")
    return result


def verify_archive(path, certificate, scratch):
    entries = PINS["entry_sha256"]
    expected = set(entries) | {CERT_ENTRY} | {f"{part}.new.dat.br" for part in IMAGES}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(expected) or set(names) != expected:
            raise ValueError("The ZIP has missing, duplicate or unexpected entries")
        if archive.read(CERT_ENTRY).strip() != certificate.read_bytes().strip():
            raise ValueError("The ZIP certificate differs from the expected certificate")
        for name, expected_hash in entries.items():
            with archive.open(name) as stream:
                if sha256(stream)[0] != expected_hash:
                    raise ValueError(f"Unexpected ZIP entry content: {name}")
        for part, image in IMAGES.items():
            if payload_info(archive, f"{part}.new.dat.br") != (image["sha256"], image["bytes"]):
                raise ValueError(f"Decoded image mismatch for {part}")
            print(f"Verified full {part} payload", flush=True)
    signature(path, certificate, scratch)
    print("Recovery signature, entry hashes and all partition images verified", flush=True)


def assemble(args):
    check_file(args.base, MANIFEST["template_zip_sha256"])
    images = {part: args.images / f"{part}.img" for part in ("system", "vendor", "odm")}
    for part, path in images.items():
        check_file(path, IMAGES[part]["sha256"], IMAGES[part]["bytes"])

    tools = args.source / "out/tools/bin"
    certificate = args.source / "security/aosp_testkey.x509.pem"
    signing_key = args.source / "security/aosp_testkey.pk8"
    payloads = {f"{part}.new.dat.br": image for part, image in images.items()}
    output = args.output
    if output.exists() or output.with_suffix(".zip.sha256").exists():
        raise FileExistsError(f"Output already exists: {output}")
    with tempfile.TemporaryDirectory(dir=output.parent) as work:
        scratch = Path(work)
        unsigned = scratch / "unsigned.zip"
        signed = scratch / "signed.zip"
        with zipfile.ZipFile(args.base) as base, zipfile.ZipFile(unsigned, "w", allowZip64=True) as out:
            preflight = (HERE / "stage-stability-runtime.sh").read_text().encode()
            if base.read("p3s-stability-preflight.sh") != preflight:
                raise ValueError("Base clean-storage preflight differs from its source")
            changes = {
                UPDATER: base.read(UPDATER).replace(b"stability 1.1", b"stability 1.2")
                .replace(b"Stability 1.1", b"Stability 1.2"),
                "build_info.txt": base.read("build_info.txt").replace(b"STABILITY-1.1-DEV-LOCAL", b"STABILITY-1.2-DEV-LOCAL"),
                "STABILITY_BUILD.json": (json.dumps(MANIFEST, indent=2) + "\n").encode(),
            }
            for entry in base.infolist():
                if entry.filename in changes or entry.filename in payloads or entry.filename == CERT_ENTRY:
                    continue
                with base.open(entry) as src, out.open(copy(entry), "w", force_zip64=entry.file_size >= 2**31) as dest:
                    shutil.copyfileobj(src, dest, BUFFER)
            for name, contents in changes.items():
                out.writestr(name, contents)
            for name, image in payloads.items():
                with subprocess.Popen(["brotli", "-q", "2", "-c", image], stdout=subprocess.PIPE) as codec:
                    with out.open(name, "w", force_zip64=True) as dest:
                        shutil.copyfileobj(codec.stdout, dest, BUFFER)
                    if codec.wait():
                        raise ValueError(f"Brotli encode failed for {name}")
                print(f"Packed {name}", flush=True)
        subprocess.run([tools / "signapk", "-w", certificate, signing_key, unsigned, signed], check=True)
        verify_archive(signed, certificate, scratch)
        with signed.open("rb") as stream:
            digest, _ = sha256(stream)
        signed.rename(output)
        output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n")
        print(f"{digest}  {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("assemble")
    build.add_argument("--base", required=True, type=Path, help="private Stability 1.1 ZIP")
    build.add_argument("--images", required=True, type=Path, help="directory of pinned system.img, vendor.img and odm.img")
    build.add_argument("--source", required=True, type=Path, help="MonsterROM tree with built host tools")
    build.add_argument("--output", required=True, type=Path, help="new ZIP path in an existing local directory")
    verify = commands.add_parser("verify")
    verify.add_argument("--archive", required=True, type=Path)
    verify.add_argument("--cert", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "assemble":
        assemble(args)
    else:
        with tempfile.TemporaryDirectory() as folder:
            verify_archive(args.archive, args.cert, Path(folder))


if __name__ == "__main__":
    main()
