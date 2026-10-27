# Proposed native source checks

Status: inactive; explicit approval pending under the user's supplied AGENTS.md §§7 and 14. The [example job](native-checks-ci.yml.example) is outside workflow discovery.

The local Storage Guard preflight on 2026-10-27 returned **23.4 GiB free / 34 GiB required**, exit 2. No local build, package installation, model download, indexing, native launch or test execution followed.

## Exact temporary CI scope

Use this public repository's standard `macos-15` GitHub runner with its preinstalled Swift toolchain. Install no dependency, external runtime or model. No account, secret, signing identity, device, personal folder or production service is used.

1. Compile the actual package and execute its ten pure-core XCTest cases. These validate literal argument boundaries, UTF-8 query limits, manifest identity, duplicate-chunk reduction, rejection of external/unregistered paths, relative owned paths, malformed output, duplicate manifest protection, and bounded output.
2. Run `script/build_and_run.sh --build-only`, which packages the executable into a real `.app`, validates its plist and locally ad-hoc signs/verifies it. Do not launch the app. No certificate or Developer ID enrollment is used.
3. Confirm the package contains its native executable and expected bundle identifier; record the exact SHA/toolchain/job result. Upload no downloadable app release.
4. Remove the temporary workflow after the approved run and publish the bounded result in the owning receipt. Keep failure evidence; fix source and rerun only within the same approved scope if necessary.

No QMD, Node, GGUF, model inference, private-content indexing, network-offline experiment, NSOpenPanel, global shortcut, search panel, file-provider or external Open/Reveal check is included. Those runtime checks require their own authored-folder scope and an actual prepared QMD installation. Passing these ten cases cannot establish retrieval quality or runtime readiness.

## Future runtime acceptance

Use an explicitly approved disposable authored directory, a version/integrity-recorded QMD 2.8.3/Node installation and legally prepared local models. Check exact keyword/semantic/hybrid results, actual index counts/embedding completion, query/cancel supersession, cancellation during rebuild, previous-generation retention on failure, symlink/placeholder exclusion, root removal/relaunch/forget, shortcut conflicts, Open/Reveal and file replacement. Measure network-blocked behavior before calling this strictly offline. Do not use personal folders or reuse another project's approval.
