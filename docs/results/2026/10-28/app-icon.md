# App-icon source

28 October 2026. Original icon artwork and bundle-resource wiring are published
on GitHub. Native compilation, app behavior and distribution remain
unverified.

The [SVG master](../../../../artwork/app-icon.svg) shows a gold magnifying glass
over an ivory document on an indigo tile, with transparent outer padding.
The [PNG artwork reference](../../../../artwork/app-icon.png) is not an actual
Finder or application screenshot. The [export helper](../../../../script/render_app_icon.sh)
uses a bounded [Python standard-library renderer](../../../../script/render_app_icon.py) for the SVG's rounded
rectangles, outlined circular lens and round-capped handle, then writes the ten
PNG representations into an ICNS container. Direct `sips` SVG extraction failed
despite advertised format support; `iconutil` also rejected encoding the valid
PNG set. Those failures are not reported as passes. The container's big-endian
lengths and PNG type/size mapping follow the SDK icon-family layout and the
maintained [Pillow format implementation](https://github.com/python-pillow/Pillow/blob/75d6d6db2fa61940552fe2df0a54943a5596702b/src/PIL/IcnsImagePlugin.py).
No Pillow import/install, image model, external artwork or package dependency
is used. `--check` compares fresh files on the current Python/zlib toolchain;
compression changes between toolchains can require reviewed regeneration.

Apple's archived [high-resolution guide](https://developer.apple.com/library/archive/documentation/GraphicsAnimation/Conceptual/HighResolutionOSX/Optimizing/Optimizing.html)
documents the 16/32/128/256/512-point 1x/2x iconset representations and manual
`iconutil` conversion conventions. Its current [CFBundleIconFile reference](https://developer.apple.com/documentation/bundleresources/information-property-list/cfbundleiconfile)
identifies the bundle icon file. This SwiftPM app uses its existing manual
bundle-packaging path, with `CFBundleIconFile = AppIcon.icns` and a copy into
`Contents/Resources` before the unchanged local ad-hoc signing commands.

## Checks and limits

On macOS 26.5.2 (25F84), Python 3.14.7 exported the PNG/ICNS files; a fresh
`--check` matched both outputs. Independent checks verified the ten canonical
slot names and dimensions, PNG chunk checksums, sRGB metadata, eight-bit RGBA,
transparent/opaque/antialiased pixels and expected artwork colors. The ICNS
family/chunk lengths and original embedded PNG payloads were checked directly.
Apple's `iconutil` decoder then returned all ten representations at the expected
16–1024 pixel dimensions as eight-bit RGBA. Native extraction re-encodes PNGs;
byte identity is claimed for the stored payloads, not those extracted files.

The 1024 reference and 16-pixel representation were inspected directly. `sips`
independently reports 1024-square RGB with alpha for the reference. Shell syntax,
plist lint and `git diff --check` passed. Removing only the icon key/resource
staging additions reproduces the original plist and packaging helper exactly,
including every build guard, signing command and launch mode. The copy occurs
before the original signing step.

| Artifact | Bytes | SHA256 |
| --- | --- | --- |
| SVG master | 775 | `d32849ac774a861a174398321159804a6598a73f66ccb549843328704ab57644` |
| PNG reference | 19,175 | `f544b5cf22b8e8b8a2e300ca8f0eef23d862afb311f8d778f9ebd9b26aa2d9da` |
| ICNS resource | 44,769 | `c8210c84f9a370102687c8f5f1a0138149134f8aed9a6e413ebe1d37b203f748` |

## Source publication

Published [source commit 5868216](https://github.com/alvarovillalbaa/findlet/commit/586821616a9efd8bb22afc68b06fcd7b8cfea824).
Immutable GitHub readback matched the local Git blobs below; `main` was identical
to that source commit at readback. Independent final checks confirmed all ten
ICNS mappings, embedded PNG checksums and reference bytes, unchanged original
plist values/packaging commands after removing the icon additions, ten local
documentation links and the nine-file change scope. The shell exporter is
executable; `git diff --check` passed.

| Published file | Git blob |
| --- | --- |
| SVG | `dab4941d288968ec5fa635265899bbc00744fe86` |
| PNG | `9bbed1f2821a3db257c5c1cdc44f946316e70811` |
| ICNS | `62cdf6e802e10a34745fbbb95bff6eba038f267a` |
| Info.plist | `13c2701623ca4973167969b548f87c8e726c0f3d` |
| Packaging helper | `cb5f48a423cd7b2e901e61a6ada979dc4c46a79c` |
| Python exporter | `178fe3626c00e256e80a8efa6b59a4d70e23fe9e` |
| Shell exporter | `e6865867379203b604e9f1d4db74ac5e3a63f8d3` |

No native build, existing package helper, signing, app launch, QMD invocation,
search/index, model inference, permission prompt, app/core test, CI or install
ran. No actual built bundle was available for icon loading or OS appearance
checks. Runtime/core/test/CI code and `Package.swift` remain unchanged.
Owned source/decoded iconset fixtures and the pinned format-reference download
were removed after evidence capture.
