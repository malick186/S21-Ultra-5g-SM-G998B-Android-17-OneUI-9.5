# Building and validating Beta 2 r6

The release was assembled from a hash-pinned r5 installer and the fixes retained on the reference SM-G998B. The public checkout contains patches, scripts, kernel configuration and test material. Reassembly also requires the binary inputs below. A build starting only from the public checkout has not been demonstrated.

## Prepare the two source trees

Use Linux with Git, Bash, Python 3.11 or newer, Brotli, OpenSSL and the MonsterROM Java/signapk build environment. Use a fresh destination. The helper checks out the two pinned upstream commits and stages the local patches; inspect them with `git diff --cached` inside each checkout.

```sh
bash packaging/checkout-sources.sh /work/p3s-sources
```

See the [upstream build guide](https://github.com/devcore94/MonsterROM/tree/9353588dce5cd12baebbb0effa124372e45544cf) for building the host tools. The assembler expects the signapk launcher at `rom/out/tools/bin/signapk` and its development key pair under `rom/security/`. Keep any private release keys outside the checkout. The published candidate uses the upstream AOSP test certificate. This signature verifies package integrity; the shared test key does not authenticate a unique publisher. Compare against the independently published release hash.

For kernel development, use the [resolved configuration](../kernel.config), the [compiler and input manifest](kernel-inputs.json) and the [kernel patch](../patches/kernel.patch) together. The historical recipes record intermediate operations and can reference the original maintainer workspace. For a ROM source build, supply the matching target and donor firmware and the pinned vbmeta.img and vbmeta_system.img in rom/target/p3s/installer/avb/. The source-build path requires separate integration testing.

## Assemble from retained release inputs

Supply the original r5 recovery installer with SHA-256 `dee1fe80a482051961ec062ce282653c60d72e23a4d7d2beb46b17cbdaedfe9c`. Put all nine non-shell files from [inputs.json](../packaging/inputs.json) into one input directory using their exact filenames. The assembler reads the four shell scripts from this checkout. Keep the source installer and output on local storage. Allow space for at least two simultaneous installer-sized temporary files plus the final output.

```sh
mkdir -p /work/p3s-scratch /work/p3s-release
python3 packaging/assemble.py --base /inputs/r5.zip --inputs /inputs/r6 \
  --source /work/p3s-sources/rom --scratch /work/p3s-scratch \
  --output /work/p3s-release/MonsterROM-p3s-SM-G998B-A17-beta2-r6.zip
python3 packaging/verify.py \
  --archive /work/p3s-release/MonsterROM-p3s-SM-G998B-A17-beta2-r6.zip \
  --cert /work/p3s-sources/rom/security/aosp_testkey.x509.pem --scratch /work/p3s-scratch
```

New ZIP entry timestamps can differ between builds. The checksum in this repository identifies the particular release candidate assembled by the maintainer. For another build, verify its signature and reconstructed partition hashes independently.

## Verification record

The 8,394,602,613-byte candidate passed ZIP CRC, duplicate-entry, payload readback and whole-file CMS checks. The validator reconstructed these logical partitions from the signed recovery ZIP and compared them with the running handset.

| Partition | SHA-256 |
|---|---|
| system | 817465cab2e0f42c50ec123d28fb1a18afc47516cb606fba032e4c6b47afa270 |
| vendor | 8f47ed72049897f0b881909d5a26514b3be8b42a79b9311533ce25bedda21b8b |
| product | b15e0e89368cdc863854b8df24cfdbdd6a3ece7833e659d1af9822f3b09d3e3d |
| odm | 0fd56399794f138a176e7a63e757e8aa89a76a0574d0bc26ada1e0b831957a64 |

A clean installation on a second or disposable SM-G998B remains the next validation step. Confirm the firmware and rescue prerequisites in the README before a destructive test. Record recovery staging and readback, first setup, a PIN unlock after restart, carrier registration, physical screen fit at QHD+/640 dpi, and notification shade behavior at 60 and 120 Hz. Keep personal logs, handset identifiers, PINs and radio backups private.
