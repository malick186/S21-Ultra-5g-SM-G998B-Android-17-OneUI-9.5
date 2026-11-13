"""Build p3s r7 block payloads from hash-pinned raw r6 images on a Linux host."""
import ctypes
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from verify import hashfile

BASE = {"system": "817465cab2e0f42c50ec123d28fb1a18afc47516cb606fba032e4c6b47afa270",
        "product": "b15e0e89368cdc863854b8df24cfdbdd6a3ece7833e659d1af9822f3b09d3e3d"}
FILES = {
    "system": {"system/build.prop": ["ro.system.build.version.sdk_full", "ro.build.version.sdk_full"],
               "system/system_ext/etc/build.prop": ["ro.system_ext.build.version.sdk_full"]},
    "product": {"etc/build.prop": ["ro.product.build.version.sdk_full", "ro.build.version.sdk_full"]},
}


@contextmanager
def mounted(image):
    with tempfile.TemporaryDirectory() as folder:
        subprocess.run(["mount", "-t", "erofs", "-o", "ro,loop", image, folder], check=True)
        try:
            yield Path(folder)
        finally:
            subprocess.run(["umount", folder], check=True)


def correct(data, keys):
    for key in keys:
        data, count = re.subn(rb"^" + re.escape(key.encode()) + rb"=37\.2$", key.encode() + b"=37.0", data, flags=re.M)
        if count != 1:
            raise ValueError(key)
    return data


def rewrite_extents(tools, image, name, before, after):
    listing = subprocess.check_output([tools/"dump.erofs", "-e", "--path=/"+name, image], text=True)
    ranges = re.findall(r"^\s*\d+:\s*(\d+)\.\.\s*(\d+)\s*\|\s*\d+\s*:\s*(\d+)\.\.\s*(\d+)", listing, re.M)
    consumed = 0
    with image.open("r+b") as stream:
        for left, right, start, end in ranges:
            left, right, start, end = map(int, (left, right, start, end))
            if left != consumed:
                raise ValueError("Noncontiguous file extent")
            consumed = right
            old, new = before[left:right], after[left:right]
            if old == new:
                continue
            size = end-start
            stream.seek(start)
            encoded = stream.read(size)
            if encoded.startswith(old):
                chunk = new + encoded[len(old):]
            else:
                lz4 = ctypes.CDLL("liblz4.so.1")
                out = ctypes.create_string_buffer(size)
                length = lz4.LZ4_compress_HC(new, out, len(new), size, 12)
                if not length or encoded[0] != 0:
                    raise ValueError("Unsupported EROFS compression layout")
                chunk = out.raw[:length].rjust(size, b"\0")
            stream.seek(start)
            stream.write(chunk)
    if consumed != len(before):
        raise ValueError("Incomplete file map")


def prepare(name, source, folder):
    tools = source/"out/tools/bin"
    env = dict(os.environ, PATH=str(tools)+":"+os.environ["PATH"])
    original = folder/(name+".raw")
    if hashfile(original) != BASE[name]:
        raise ValueError("Base image mismatch: "+name)
    info = subprocess.check_output([tools/"avbtool", "info_image", "--image", original], text=True)
    salt = re.search(r"Salt:\s*([0-9a-f]+)", info)[1]
    with mounted(original) as root:
        old = {p: (root/p).read_bytes() for p in FILES[name]}
    new = {p: correct(data, FILES[name][p]) for p, data in old.items()}
    with tempfile.TemporaryDirectory(dir=folder) as tmp:
        image = Path(tmp)/"patched.img"
        shutil.copyfile(original, image)
        for p in old:
            rewrite_extents(tools, image, p, old[p], new[p])
        with mounted(image) as root:
            for p, expected in new.items():
                if (root/p).read_bytes() != expected:
                    raise ValueError("EROFS readback failed: "+p)
        avb = tools/"avbtool"
        subprocess.run([avb,"erase_footer","--image",image],check=True)
        subprocess.run([avb,"add_hashtree_footer","--image",image,"--partition_size",str(original.stat().st_size),
                        "--partition_name",name,"--hash_algorithm","sha256","--algorithm","SHA256_RSA4096",
                        "--key",source/"security/avb/testkey_rsa4096.pem","--salt",salt],env=env,check=True)
        # avbtool resolves the descriptor's partition name relative to the image.
        final = image.rename(Path(tmp)/(name+".img"))
        subprocess.run([avb,"verify_image","--image",final,"--key",source/"security/avb/testkey_rsa4096.pem"],env=env,check=True)
        print(name,hashfile(final),flush=True)
        with (folder/(name+".new.dat.br")).open("wb") as output:
            subprocess.run(["brotli","-q","2","-c",final],stdout=output,check=True)
        blocks = final.stat().st_size//4096
        (folder/(name+".transfer.list")).write_text(f"4\n{blocks}\n0\n0\nnew 2,0,{blocks}\n")


if __name__ == "__main__":
    for part in FILES:
        prepare(part, Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
