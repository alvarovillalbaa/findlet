# First QMD keyword integration attempt: archive admission failed

7 November 2026. **Failed before Node execution or QMD integration.**
[Run 42383731437](https://github.com/alvarovillalbaa/findlet/actions/runs/42383731437),
job `128436593744`, used source
[`36ace0d39aa8f77648d7fb694fe068a2c3b4ff7f`](https://github.com/alvarovillalbaa/findlet/tree/36ace0d39aa8f77648d7fb694fe068a2c3b4ff7f)
and activation `cf0847b64455c3093bbfba696563ff733f116f0b`.

The two unchanged core files, four production services and app-less harness
compiled with Xcode 16.4/16F6, Swift 6.1.2 and SDK 15.5 on macOS 15.8.2 ARM64.
Six harness-build warnings concern NSLock calls from async contexts; the pass
does not establish Swift 6 language-mode readiness. The ten prior core cases
and full app build were not repeated.

The Node archive downloaded normally: 58,334,661 bytes, SHA256
`d38bd5e5a2ddce6bbb5ce45e46e208337da4d51fffe611e567fd32073d6439f6`.
Extraction stopped at `node_archive_size_bound`. The original guard combined
128 MiB/member, 256 MiB/total and 20,000 regular files; this receipt does not
identify the rejected member or exceeded sub-limit. Node/npm, Darwin native
binding admission and K01/K02 did not execute. No retrieval pass exists.

The [original JSON](qmd-keyword-integration-attempt-1.json) is 70,013 bytes,
SHA256 `adf79aee0b2f48766632f363703f1801bd10b9fd66f4984d68000cd2b7ef400f`.
The [full fetched log](qmd-keyword-integration-attempt-1.raw.log) is 87,219 bytes,
SHA256 `2d03d96363faf5bb0a7e0a1e920e89f2bb92b8f7fa6dbb2b98a59a83941ea9e1`.
The JSON is the single emitted original plus one LF. All 56 retained command
streams decode to their recorded original sizes and hashes; all 28 commands
exited zero with normal process/group/pipe closure and no signals. The finite
controller error keeps the overall attempt failed.

Three complete guards match all 48 source paths, Git modes, bodies and index
bindings. The seven-file export remained unchanged. Owned cleanup verified
5,965 entries / 166,392,401 regular bytes and removed scratch after zero owned
processes, unknown root references and groups were observed. These are boundary
observations, not continuous host-wide attestation. Workflow `410392262` was
disabled after termination.

Originals were retained before repair. A separately reviewed changed attempt
may inventory the same hash-pinned archive before extraction and use explicit
256 MiB/member, 512 MiB/total and 20,000-member bounds within the existing
2 GiB scratch and 20-minute job ceilings. No application code, lock, harness,
model, private corpus, account or paid resource change is implied. Inner QMD
stderr is not captured by this observer, and no QMD command ran in this attempt.
