# Night camera dependencies and selectable resolutions

Historical candidate from 19 November 2026. The later [Stability 1.2
release](STABILITY-1.2.md) records the clean-install result and the final
320/480/640 dpi profile. The literal 640 dpi proposal below was superseded.

The first MPI-wrapper update removed a fatal native-node load error, but a
saved Night photo did not establish successful multi-frame processing. A
subsequent trace identified an absent DT_NEEDED dependency:
`libMultiFrameProcessing30.snapwrapper.camera.samsung.so`.

The follow-up audit traversed 30 libraries from the MPI wrapper, MultiFrame30,
LocalTM and software-ISP roots, including their recursive ELF dependencies and
the live phone's four bionic runtime libraries. One library needed adding.
Strong camera/SNAP imports were checked against the selected providers with
no unresolved symbol names. This static check does not prove runtime namespace,
symbol-version, service or image-quality compatibility; Night capture must
still be tested. Optional runtime plugins beyond these known roots are not
claimed covered.

The added library comes from SM-G998B AUT G998BXXSJHZC2 stock firmware, SHA256
`8d12e774b10b1670bab81a5d0c432ab95afeb6fc82fd41f00086e71b01c999e5`.
Samsung retains ownership of the proprietary implementation. No binary is
included in the public source tree.

The resolution candidate removes the legacy QHD-only boot guard. The shell
profile retains the selected 720×1600, 1080×2400 or 1440×3200 resolution and
synchronizes the physical mode and logical dimensions at the owner's explicit
640 dpi preference. It does not force every resolution back to QHD+. At lower
resolutions literal 640 dpi creates larger UI elements than Samsung's normal
proportional densities. All three choices and both display edges need device
validation. No data format, encryption change or SELinux relaxation is used.

Host checks passed: filesystem content/metadata diff, AVB image verification,
exact changed-block reconstruction, ZIP CRC and CMS signature. Package guards
require the exact preceding system and ODM hashes and writable existing
logical mappings before writing. Device readback and functional tests pending.

Local candidate SHA256:
`aed2bd0c62d06c6f705603374516d4517ba99ed5cd35424083180fb906f9ee0a`.
Expected system SHA256:
`c3ecba51fdcafe8168e9440de76bbda9195f100df320c5df5b34310feb3b2819`.
Expected ODM SHA256:
`acc50311652897498e1fc62bf7b0ee8d4076a9ea06954a10b75e671a5d85fb44`.

Keep full firmware and signed installer local. Existing camera/ODM images are
retained as rollback inputs. Video-freezing work remains deferred.
