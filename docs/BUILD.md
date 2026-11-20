# Building and validating Beta 2 r7

The release was assembled from a hash-pinned r5 installer and the fixes retained on the reference SM-G998B. The public checkout contains patches, scripts, kernel configuration and test material. Reassembly also requires the binary inputs below. A build starting only from the public checkout has not been demonstrated.

## Prepare the two source trees

Use Linux with Git, Bash, Python 3.11 or newer, Brotli, OpenSSL and the MonsterROM Java/signapk build environment. Use a fresh destination. The helper checks out the two pinned upstream commits and stages the local patches; inspect them with `git diff --cached` inside each checkout.

```sh
bash packaging/checkout-sources.sh /work/p3s-sources
```

See the [upstream build guide](https://github.com/devcore94/MonsterROM/tree/9353588dce5cd12baebbb0effa124372e45544cf) for building the host tools. The assembler expects the signapk launcher at `rom/out/tools/bin/signapk` and its development key pair under `rom/security/`. Keep any private release keys outside the checkout. The published candidate uses the upstream AOSP test certificate. This signature verifies package integrity; the shared test key does not authenticate a unique publisher. Compare against the independently published release hash.

For kernel development, use the [resolved configuration](../kernel.config), the [compiler and input manifest](kernel-inputs.json) and the [kernel patch](../patches/kernel.patch) together. The historical recipes record intermediate operations and can reference the original maintainer workspace. For a ROM source build, supply the matching target and donor firmware and the pinned vbmeta.img and vbmeta_system.img in rom/target/p3s/installer/avb/. The source-build path requires separate integration testing.

## Build the corrected system and product OTA streams

Use a Linux root shell with read-only EROFS loop mounts available, liblz4, Brotli and the pinned Android host tools (including fec, avbtool, dump.erofs and simg2img). Allow approximately 35 GiB of free scratch space plus the release destination. Start with the matching system and product sparse images from the retained r5 target-files ZIP. The image builder checks their expanded SHA-256 against the r6 reference before any edits. The compressed files under each EROFS property path are patched at their existing extents. The helper checks that the complete file differs only at its expected property assignments, mounts the image to verify the result, then recreates the AVB footer using the original salt, partition size and development key. Other devices keep the upstream build profile.

```sh
mkdir -p /work/p3s-scratch /work/p3s-release
for p in system product; do
    unzip -p /inputs/r5-target_files.zip "$p.img" > "/work/p3s-scratch/$p.sparse" || exit 1
    /work/p3s-sources/rom/out/tools/bin/simg2img "/work/p3s-scratch/$p.sparse" "/work/p3s-scratch/$p.raw" || exit 1
done
python3 packaging/sdk37_images.py /work/p3s-sources/rom /work/p3s-scratch
```

The two generated block streams are pinned in [the r7 block manifest](../packaging/r7-blocks.json). The full-source build helper applies the p3s property correction after the existing ROM patch. The optional upstream QPR2 software-codec experiment still requires API 37.2 and should remain disabled on p3s.

## Assemble from retained release inputs

Supply the original r5 recovery installer with SHA-256 `dee1fe80a482051961ec062ce282653c60d72e23a4d7d2beb46b17cbdaedfe9c`. Put all nine non-shell files from [inputs.json](../packaging/inputs.json) into one input directory using their exact filenames. The assembler reads the four shell scripts from this checkout. Keep the source installer and output on local storage. Allow space for at least two simultaneous installer-sized temporary files plus the final output.

```sh
mkdir -p /work/p3s-scratch /work/p3s-release
python3 packaging/assemble.py --base /inputs/r5.zip --inputs /inputs/r6 \
  --source /work/p3s-sources/rom --blocks /work/p3s-scratch --scratch /work/p3s-scratch \
  --output /work/p3s-release/MonsterROM-p3s-SM-G998B-A17-beta2-r7.zip
python3 packaging/verify.py \
  --archive /work/p3s-release/MonsterROM-p3s-SM-G998B-A17-beta2-r7.zip \
  --cert /work/p3s-sources/rom/security/aosp_testkey.x509.pem --scratch /work/p3s-scratch
```

New ZIP entry timestamps can differ between builds. The checksum in this repository identifies the particular release candidate assembled by the maintainer. For another build, verify its signature and reconstructed partition hashes independently.

## r7 verification

The 8,647,756,440-byte local installer passed the checks below on 14 November 2026. The final archive contains five verified SDK-full assignments at 37.0 across three property files. Vendor and ODM still match the reference handset. The previous r6 installer is retained locally. No device was flashed for this release.

The release verifier checks the recovery signature and reconstructs the four logical partitions. It verifies both revised AVB footers and hash trees and mounts the reconstructed system and product to check every public minor-SDK assignment. The [r7 block manifest](../packaging/r7-blocks.json) records the exact changed partition hashes. The existing chained Samsung metadata and unlocked-device installation restrictions are retained. This is not a locked-bootloader image.

## Historical r6 verification record

The 8,394,602,613-byte candidate passed ZIP CRC, duplicate-entry, payload readback and whole-file CMS checks. The validator reconstructed these logical partitions from the signed recovery ZIP and compared them with the running handset.

| Partition | SHA-256 |
|---|---|
| system | 817465cab2e0f42c50ec123d28fb1a18afc47516cb606fba032e4c6b47afa270 |
| vendor | 8f47ed72049897f0b881909d5a26514b3be8b42a79b9311533ce25bedda21b8b |
| product | b15e0e89368cdc863854b8df24cfdbdd6a3ece7833e659d1af9822f3b09d3e3d |
| odm | 0fd56399794f138a176e7a63e757e8aa89a76a0574d0bc26ada1e0b831957a64 |

A clean installation on a second or disposable SM-G998B remains the next validation step. Confirm the firmware and rescue prerequisites in the README before a destructive test. Record recovery staging and readback, first setup, a PIN unlock after restart, carrier registration, physical screen fit at QHD+/640 dpi, and notification shade behavior at 60 and 120 Hz. Keep personal logs, handset identifiers, PINs and radio backups private.

## Optional post-r7 Bluetooth workaround

The [SBC offload workaround](BLUETOOTH-SBC-OFFLOAD.md#future-clean-build-integration) includes a product-property source fragment and explicit future-build validation steps. It is not automatically incorporated into the r7 assembler or release ZIP. Laptop media playback and reconnect passed; clean-install and reboot testing remain required.
