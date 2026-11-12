#!/usr/bin/env python3
"""Reconstruct new/zero/erase full-OTA block maps, verify live reference hashes and OTA signer."""
import argparse,hashlib,json,re,shutil,struct,subprocess,tempfile,zipfile
from pathlib import Path
EXPECTED={"system":"817465cab2e0f42c50ec123d28fb1a18afc47516cb606fba032e4c6b47afa270","vendor":"8f47ed72049897f0b881909d5a26514b3be8b42a79b9311533ce25bedda21b8b","product":"b15e0e89368cdc863854b8df24cfdbdd6a3ece7833e659d1af9822f3b09d3e3d"}
HERE=Path(__file__).resolve().parent
def hashfile(path):
    with path.open("rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
def signature(path, cert, tmp):
    with path.open("rb") as f:
        f.seek(-6,2); start,magic,comment=struct.unpack("<HHH",f.read(6))
        if magic!=65535 or not 6<start<=comment: raise ValueError("Bad OTA footer")
        f.seek(-comment-22,2); eocd=f.read(22)
        if eocd[:4]!=b"PK\x05\x06" or int.from_bytes(eocd[20:22],"little")!=comment: raise ValueError("Bad EOCD")
        f.seek(-start,2); sig=tmp/"ota.der"; sig.write_bytes(f.read(start-6))
        size=path.stat().st_size-comment-2
        f.seek(0)
        p=subprocess.Popen(["openssl","cms","-verify","-binary","-inform","DER","-in",sig,"-noverify","-nointern","-certfile",cert,"-content","/dev/stdin","-out","/dev/null"],stdin=subprocess.PIPE)
        with p.stdin as dest:
            while size:
                chunk=f.read(min(size,8<<20))
                if not chunk: raise EOFError()
                dest.write(chunk);size-=len(chunk)
        if p.wait(): raise ValueError("OTA signature verification failed")
def verify(archive, cert, scratch):
    hashes=json.loads((HERE/"inputs.json").read_text())
    with tempfile.TemporaryDirectory(dir=scratch) as work, zipfile.ZipFile(archive) as z:
        tmp=Path(work)
        signature(archive,cert,tmp)
        sizes=dict((n,int(s)) for n,s in re.findall(r'^resize (\w+) (\d+)$',z.read("dynamic_partitions_op_list").decode(),re.M))
        for name,expected in {**EXPECTED,"odm":hashes["odm.img"]}.items():
            with z.open(name+".new.dat.br") as src, (tmp/"payload.br").open("wb") as dest: shutil.copyfileobj(src,dest,8<<20)
            with (tmp/"image").open("w+b") as img, subprocess.Popen(["brotli","-d","-c",tmp/"payload.br"],stdout=subprocess.PIPE) as proc:
                img.truncate(sizes[name])
                lines=z.read(name+".transfer.list").decode().splitlines()
                if lines[0]!="4" or lines[2:4]!=["0","0"]: raise ValueError("Unexpected transfer header")
                for line in lines[4:]:
                    op,r=line.split()
                    count,*ends=map(int,r.split(","))
                    if count!=len(ends) or count%2 or op not in ("new","zero","erase"): raise ValueError(line)
                    for a,b in zip(ends[::2],ends[1::2]):
                        if not 0<=a<b<=sizes[name]//4096: raise ValueError(line)
                        if op!="new": continue
                        img.seek(a*4096); remaining=(b-a)*4096
                        while remaining:
                            data=proc.stdout.read(min(remaining,4<<20))
                            if not data: raise EOFError()
                            img.write(data);remaining-=len(data)
                if proc.stdout.read(1) or proc.wait(): raise ValueError("Bad compressed payload")
                img.flush()
            actual=hashfile(tmp/"image")
            print(name,actual,"match" if actual==expected else "DIFFERS",flush=True)
            if actual!=expected: raise ValueError(name+" differs from the running reference device")
        for name,h in hashes.items():
            if name=="odm.img": continue
            member=name if name.endswith(".img") else "p3s-runtime/"+name
            with z.open(member) as f:
                if hashlib.file_digest(f,"sha256").hexdigest()!=h: raise ValueError(member)
    print("Verified recovery signature, partition maps and pinned payloads.",flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    for n in ("archive","cert","scratch"):p.add_argument("--"+n,type=Path,required=True)
    verify(**vars(p.parse_args()))
