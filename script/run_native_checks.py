#!/usr/bin/env python3
"""One public-CI Findlet compilation/10-case/package check; never launch the app."""
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

BRANCH = "qa/findlet-native-20261105"
ACTIVE = ".github/workflows/findlet-native-checks.yml"
DEVELOPER = "/Applications/Xcode_16.4.app/Contents/Developer"
STREAM_LIMIT, GZIP_LIMIT, RECEIPT_LIMIT = 524288, 131072, 1048576


def need(value, code):
    if not value:
        raise RuntimeError(code)


def sha(data, algorithm="sha256"):
    return hashlib.new(algorithm, data).hexdigest()


need(len(sys.argv) == 3 and sys.argv[1] == "--source-commit"
     and re.fullmatch(r"[a-f0-9]{40}", sys.argv[2]), "immutable_source_required")
SOURCE = sys.argv[2]
need(platform.system() == "Darwin" and platform.mac_ver()[0].split(".")[0] == "15"
     and os.environ.get("GITHUB_ACTIONS") == "true"
     and os.environ.get("GITHUB_REPOSITORY") == "alvarovillalbaa/findlet"
     and os.environ.get("GITHUB_EVENT_NAME") == "push"
     and os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH
     and os.environ.get("FINDLET_PUBLIC_REPOSITORY") == "true", "public_runner_scope_required")
repo = Path.cwd().resolve()
parent = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
root = Path(tempfile.mkdtemp(prefix="findlet-native-", dir=parent))
root.chmod(0o700)
root_identity = root.stat()
need(root_identity.st_uid == os.getuid(), "scratch_owner_invalid")
marker = os.urandom(24).hex()
(root / "owner").write_text(marker)
(root / "owner").chmod(0o600)
for name in ("tmp", "source", "cache", "config", "security"):
    (root / name).mkdir(mode=0o700)
scratch_directories = {name: ((root / name).stat().st_dev, (root / name).stat().st_ino)
                       for name in ("tmp", "source", "cache", "config", "security")}
env = {"HOME": os.environ["HOME"]} if "HOME" in os.environ else {}
env.update({"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "DEVELOPER_DIR": DEVELOPER, "LANG": "en_US.UTF-8", "TZ": "UTC", "CI": "true",
            "TMPDIR": str(root / "tmp") + "/", "TMP": str(root / "tmp"), "TEMP": str(root / "tmp"),
            "XDG_CACHE_HOME": str(root / "cache"), "SWIFTPM_MODULECACHE_OVERRIDE": str(root / "cache" / "manifest"),
            "CLANG_MODULE_CACHE_PATH": str(root / "cache" / "modules")})
report = {"schemaVersion": "findlet.native-checks.v2", "sourceCommit": SOURCE, "status": "failed",
          "startedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "runtime": {"python": platform.python_version(), "macOS": platform.mac_ver()[0], "architecture": platform.machine()},
          "commands": [], "guards": [], "errors": [], "generated": [],
          "scope": {"expectedCases": 10, "appLaunch": False, "qmdExecution": False, "nodeExecution": False, "models": False, "userFolders": False,
                    "dependenciesInstalled": False, "accounts": False, "trustedDistribution": False},
          "proofLimits": ["Ten pure-core XCTest cases use in-memory data/URLs only. No QMD, Node, models, authored-folder indexing, app launch, permission prompt or native UI is exercised.",
                          "The exact native input subset is exported under owned scratch, not a full-repository/fresh-install build. The package has a local ad-hoc signature, no sandbox entitlement, Developer ID or notarization.",
                          "Direct children and their original process groups are checked; separately detached sessions and compiler/system caches outside the owned paths are not inventoried.",
                          "Userspace deadlines cannot interrupt a blocked kernel filesystem call. GitHub owns final runner teardown."]}
work_end = time.monotonic() + 720
cleanup_end = work_end + 90
interrupted = False
global_expired = False
children = []
generated_preabsent = False
generated_identity = {}
export = root / "source"
export_files = []
export_directories = {}
baseline = None
raw_compressed = 0


def clean(value, maximum=1800):
    text = str(value).replace(str(root), "[scratch]").replace(str(repo), "[repository]")
    if env.get("HOME"):
        text = text.replace(env["HOME"], "[runner-home]")
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)[:maximum]


def owner():
    current = root.lstat()
    need(stat.S_ISDIR(current.st_mode) and not root.is_symlink()
         and current.st_uid == os.getuid() and (current.st_dev, current.st_ino) == (root_identity.st_dev, root_identity.st_ino)
         and not (root / "owner").is_symlink() and (root / "owner").read_text() == marker, "scratch_owner_changed")


def absent(pid):
    try:
        os.killpg(pid, 0)
        return False
    except ProcessLookupError:
        return True
    except PermissionError:
        return False


def stop(child, reason):
    if child.get("released"):
        return
    child["reason"] = child["reason"] or reason
    if child["stopAt"] is None:
        child["stopAt"] = time.monotonic()
        try:
            os.killpg(child["process"].pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    elif time.monotonic() - child["stopAt"] >= 3:
        try:
            os.killpg(child["process"].pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def interrupted_handler(_signum, _frame):
    global interrupted
    interrupted = True
    for child in children:
        stop(child, "interrupted")


def alarm_handler(_signum, _frame):
    global global_expired
    global_expired = True
    report["errors"].append("controller_global_deadline")
    interrupted_handler(_signum, _frame)


for received in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
    signal.signal(received, interrupted_handler)
signal.signal(signal.SIGALRM, alarm_handler)
signal.setitimer(signal.ITIMER_REAL, 810)


def packed(data, complete=True):
    global raw_compressed
    compressed = gzip.compress(data, mtime=0)
    retained = {"bytes": len(data), "sha256": sha(data), "complete": complete, "compressedBytes": len(compressed)}
    if len(compressed) <= GZIP_LIMIT and raw_compressed + len(compressed) <= 524288:
        raw_compressed += len(compressed)
        retained.update({"encoding": "gzip-base64", "data": base64.b64encode(compressed).decode()})
    else:
        retained["omittedForBound"] = True
        report["errors"].append("raw_output_compression_bound")
    return retained


def command(label, args, seconds=30, cleanup=False, allowed=(0,), cwd=None):
    owner()
    need(cleanup or not interrupted, "interrupted_before_command")
    deadline = min(time.monotonic() + seconds, (cleanup_end if cleanup else work_end) - 8)
    need(time.monotonic() < deadline and not global_expired, "command_budget_exhausted")
    process = subprocess.Popen(args, cwd=cwd or repo, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    child = {"process": process, "reason": None, "stopAt": None, "released": False}
    children.append(child)
    streams = [process.stdout, process.stderr]
    output, counts, digests, eof = [bytearray(), bytearray()], [0, 0], [hashlib.sha256(), hashlib.sha256()], [False, False]
    selector = selectors.DefaultSelector()
    for index, stream in enumerate(streams):
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ, index)
    grace = None
    forced_drain = False
    try:
        while True:
            now = time.monotonic()
            if (interrupted and not cleanup) or global_expired:
                stop(child, "interrupted")
            if now >= deadline:
                stop(child, "timeout")
            if child["stopAt"] is not None:
                stop(child, child["reason"])
                if now - child["stopAt"] >= 6:
                    forced_drain = not all(eof)
                    break
            for key, _ in selector.select(0.025):
                index = key.data
                try:
                    data = os.read(key.fileobj.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not data:
                    eof[index] = True
                    selector.unregister(key.fileobj)
                    continue
                counts[index] += len(data)
                digests[index].update(data)
                output[index].extend(data[:max(0, STREAM_LIMIT - len(output[index]))])
                if counts[index] > STREAM_LIMIT:
                    stop(child, "stream_limit")
            code = process.poll()
            if code is not None and all(eof):
                if absent(process.pid):
                    break
                if grace is None:
                    grace = time.monotonic()
                if child["reason"] is None and time.monotonic() - grace < 2:
                    continue
                stop(child, "process_group_remaining")
    finally:
        selector.close()
        for stream in streams:
            stream.close()
        if process.poll() is None:
            stop(child, "unreaped_child")
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
    group_absent = absent(process.pid)
    child["released"] = process.returncode is not None and group_absent and all(eof) and not forced_drain
    raw = [bytes(value) for value in output]
    row = {"label": label, "args": [clean(arg, 220) for arg in args], "exitCode": process.returncode,
           "stopReason": child["reason"], "exitObservedAndReaped": process.returncode is not None,
           "pipesEOF": eof, "forcedDrain": forced_drain, "originalProcessGroupAbsent": group_absent, "released": child["released"],
           "streamsClosed": [stream.closed for stream in streams],
           "streams": [{"name": name, "observedBytes": counts[index], "observedSha256": digests[index].hexdigest(),
                        "raw": packed(raw[index], eof[index] and counts[index] == len(raw[index])),
                        "head": clean(raw[index].decode("utf8", "replace"), 1000)} for index, name in enumerate(("stdout", "stderr"))]}
    report["commands"].append(row)
    need(process.returncode in allowed and child["reason"] is None and all(eof) and group_absent
         and all(counts[i] == len(raw[i]) for i in (0, 1)), label + "_failed")
    return raw


def guard(label, cleanup=False):
    global baseline
    row = {"label": label, "passed": False}
    report["guards"].append(row)
    need(command(label + "_head", ["git", "rev-parse", "HEAD"], cleanup=cleanup)[0].decode().strip() == SOURCE, "head_changed")
    tree = command(label + "_tree", ["git", "ls-tree", "-r", "-z", "HEAD"], cleanup=cleanup)[0]
    index_raw = command(label + "_index", ["git", "ls-files", "--stage", "-z"], cleanup=cleanup)[0]
    index = {}
    for entry in index_raw.split(b"\0"):
        if entry:
            header, name = entry.split(b"\t", 1)
            mode, blob_id, stage = header.decode().split()
            need(stage == "0" and name not in index, "index_invalid")
            index[name] = (mode, blob_id)
    vectors = []
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        header, name = entry.split(b"\t", 1)
        mode, kind, blob_id = header.decode().split()
        relative = name.decode("utf8")
        need(not Path(relative).is_absolute() and all(part not in ("", ".", "..") for part in relative.split("/")), "tracked_path_invalid")
        need(kind == "blob" and relative != ACTIVE and not relative.startswith(".github/workflows/"), "unexpected_source_entry")
        file = repo / relative
        for ancestor in file.parents:
            if ancestor == repo:
                break
            need(ancestor.is_dir() and not ancestor.is_symlink(), "tracked_ancestor_changed")
        item = file.lstat()
        need(item.st_size <= 16777216, "tracked_file_bound")
        actual_mode = "120000" if stat.S_ISLNK(item.st_mode) else "100755" if stat.S_ISREG(item.st_mode) and item.st_mode & 0o111 else "100644" if stat.S_ISREG(item.st_mode) else "invalid"
        data = os.fsencode(os.readlink(file)) if actual_mode == "120000" else file.read_bytes()
        git_hash = sha(b"blob " + str(len(data)).encode() + b"\0" + data, "sha1")
        need(mode == actual_mode and blob_id == git_hash and index.get(name) == (mode, blob_id), "working_bytes_or_index_changed")
        vectors.append({"path": relative, "mode": mode, "gitBlob": blob_id, "bytes": len(data), "sha256": sha(data)})
    need(len(vectors) == len(index), "source_path_count_changed")
    need(command(label + "_ignored", ["git", "status", "--porcelain=v1", "-z", "--ignored=matching", "--untracked-files=all"], cleanup=cleanup)[0] == b"", "canonical_generated_output")
    need(command(label + "_status", ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cleanup=cleanup)[0] == b"", "worktree_changed")
    if baseline is None:
        baseline = vectors
        report["sourceFiles"] = vectors
    need(vectors == baseline, "source_vector_changed")
    row.update({"passed": True, "trackedFiles": len(vectors), "trackedBytes": sum(v["bytes"] for v in vectors),
                "treeSha256": sha(tree), "vectorSha256": sha(json.dumps(vectors, separators=(",", ":")).encode()),
                "fullHeadIndexWorkingModesAndBytes": True, "noUntrackedOrIgnoredOutput": True})



def export_source():
    global export_files
    selected = [dict(row) for row in baseline if row["path"] == "Package.swift" or row["path"] == "script/build_and_run.sh"
                or row["path"].startswith(("Sources/", "Tests/", "Resources/"))]
    need(selected and sum(row["bytes"] for row in selected) <= 2097152, "native_export_bound")
    need(any(row["path"] == "Resources/AppIcon.icns" for row in selected)
         and any(row["path"] == "Tests/FindletCoreTests/QMDContractTests.swift" for row in selected), "native_export_incomplete")
    for row in selected:
        need(row["mode"] in ("100644", "100755"), "native_export_symlink_rejected")
        target = export / row["path"]
        current = export
        for part in Path(row["path"]).parent.parts:
            current = current / part
            if not os.path.lexists(current):
                current.mkdir(mode=0o700)
            item = current.lstat()
            need(stat.S_ISDIR(item.st_mode) and not current.is_symlink() and item.st_uid == os.getuid(), "native_export_ancestor")
            export_directories[str(current.relative_to(export))] = (item.st_dev, item.st_ino)
        data = (repo / row["path"]).read_bytes()
        need(len(data) == row["bytes"] and sha(data) == row["sha256"]
             and sha(b"blob " + str(len(data)).encode() + b"\0" + data, "sha1") == row["gitBlob"], "native_source_changed_during_export")
        with target.open("xb") as stream:
            stream.write(data)
        target.chmod(0o755 if row["mode"] == "100755" else 0o644)
    export_files = selected
    report["sourceExport"] = {"kind": "exact-native-input-subset", "fileCount": len(selected),
                             "totalBytes": sum(row["bytes"] for row in selected), "byteLimit": 2097152,
                             "files": selected, "guards": [],
                             "qualification": "Package.swift, all tracked Sources/Tests/Resources and the unchanged build script only; no .git, dependencies, documentation or prior evidence is copied."}
    verify_export("before_tool_work")


def verify_export(label):
    need(export_files, "native_export_missing")
    for relative, identity in export_directories.items():
        folder = export / relative
        item = folder.lstat()
        need(stat.S_ISDIR(item.st_mode) and not folder.is_symlink() and item.st_uid == os.getuid()
             and (item.st_dev, item.st_ino) == identity, "native_export_directory_changed")
    actual_paths = set()
    for name in ("Sources", "Tests", "Resources", "script"):
        for directory, folders, files in os.walk(export / name, followlinks=False):
            for child in folders:
                need(not (Path(directory) / child).is_symlink(), "native_export_extra_symlink")
            actual_paths.update(str((Path(directory) / child).relative_to(export)) for child in files)
    actual_paths.add("Package.swift")
    need(actual_paths == {row["path"] for row in export_files}, "native_export_input_set_changed")
    for row in export_files:
        file = export / row["path"]
        item = file.lstat()
        need(stat.S_ISREG(item.st_mode) and not file.is_symlink() and item.st_uid == os.getuid()
             and ("100755" if item.st_mode & 0o111 else "100644") == row["mode"], "native_export_mode_changed")
        data = file.read_bytes()
        after = file.lstat()
        need((item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns)
             == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
             and len(data) == row["bytes"] and sha(data) == row["sha256"]
             and sha(b"blob " + str(len(data)).encode() + b"\0" + data, "sha1") == row["gitBlob"], "native_export_bytes_changed")
    report["sourceExport"]["guards"].append({"label": label, "passed": True, "files": len(export_files),
                                            "vectorSha256": sha(json.dumps(export_files, separators=(",", ":")).encode())})


def capture_generated():
    need(generated_preabsent, "generated_preabsence_unverified")
    for name in ("dist", ".build", ".swiftpm", "artifacts"):
        file = export / name
        if not os.path.lexists(file):
            continue
        item = file.lstat()
        need(stat.S_ISDIR(item.st_mode) and not file.is_symlink() and item.st_uid == os.getuid(), "generated_type_invalid")
        if name not in generated_identity:
            generated_identity[name] = (item.st_dev, item.st_ino)
            report["generated"].append({"path": "source/" + name, "preAbsent": True, "removed": False})
        need(generated_identity[name] == (item.st_dev, item.st_ino), "generated_identity_changed")


def capture_xunit(expected):
    xml_path = root / "tests.xml"
    need(xml_path.is_file() and not xml_path.is_symlink() and xml_path.stat().st_size <= 262144, "xunit_file_missing_or_invalid")
    xml_bytes = xml_path.read_bytes()
    report["xunit"] = {"raw": packed(xml_bytes), "accepted": False}
    need(b"<!DOCTYPE" not in xml_bytes and b"<!ENTITY" not in xml_bytes, "xunit_declaration_invalid")
    xml = ET.fromstring(xml_bytes)
    suites, cases = list(xml.iter("testsuite")), list(xml.iter("testcase"))
    actual = [(case.get("classname"), case.get("name", "").removesuffix("()")) for case in cases]
    report["xunit"]["cases"] = [{"class": group, "name": name,
                                 "status": "failed" if list(case.iter("failure")) or list(case.iter("error")) else "skipped" if list(case.iter("skipped")) else "passed"}
                                for case, (group, name) in zip(cases, actual)]
    command_row = next((row for row in report["commands"] if row["label"] == "core_tests"), {})
    need(command_row.get("exitCode") == 0 and len(suites) == 1 and suites[0].get("tests") == "10"
         and suites[0].get("errors") == "0" and suites[0].get("failures") == "0"
         and len(actual) == 10 and len(set(actual)) == 10
         and all(name in expected and group == "FindletCoreTests.QMDContractTests" for group, name in actual)
         and not any(list(xml.iter(tag)) for tag in ("failure", "error", "skipped")), "xunit_verdict_failed")
    report["xunit"].update({"accepted": True, "total": 10, "passed": 10, "failed": 0, "errors": 0, "skipped": 0})


def macho_identity(label, file):
    output = command(label, ["/usr/bin/xcrun", "dwarfdump", "--uuid", str(file)])[0].decode()
    rows = re.findall(r"^UUID: ([0-9a-fA-F-]{36}) \(([^)]+)\) ", output, re.M)
    need(0 < len(rows) <= 4 and len(set(rows)) == len(rows), "macho_uuid_invalid")
    return sorted([{"uuid": uuid.lower(), "architecture": architecture} for uuid, architecture in rows],
                  key=lambda row: row["architecture"])


expected = []
try:
    need(Path(DEVELOPER).is_dir(), "selected_xcode_missing")
    guard("before")
    xcode = command("xcode", ["/usr/bin/xcodebuild", "-version"])[0].decode().strip()
    need(xcode == "Xcode 16.4\nBuild version 16F6", "xcode_profile_changed")
    swift = command("swift", ["/usr/bin/xcrun", "swift", "--version"])[0].decode()
    need(re.search(r"Swift version 6\.1\.2\b", swift), "swift_profile_changed")
    sdk = command("macos_sdk", ["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-version"])[0].decode().strip()
    need(sdk == "15.5", "sdk_profile_changed")
    report["toolchain"] = {"xcode": xcode, "swift": swift.strip(), "sdk": sdk}
    command("shell_syntax_build", ["/bin/bash", "-n", "script/build_and_run.sh"])
    command("plist_syntax", ["/usr/bin/plutil", "-lint", "Resources/Info.plist"])
    export_source()
    for name in ("dist", ".build", ".swiftpm", "artifacts"):
        need(not os.path.lexists(export / name), "preexisting_export_generated_path")
    generated_preabsent = True
    command("build_and_package_without_launch", ["/bin/bash", "script/build_and_run.sh", "--build-only"], 300, cwd=export)
    capture_generated()
    options = ["--scratch-path", str(export / ".build"), "--cache-path", str(root / "cache" / "swiftpm"),
               "--config-path", str(root / "config"), "--security-path", str(root / "security")]
    binary_path = command("binary_path", ["/usr/bin/xcrun", "swift", "build", *options, "--show-bin-path"], cwd=export)[0].decode().strip()
    binary = Path(binary_path) / "Findlet"
    need(binary.is_file() and not binary.is_symlink() and binary.resolve().is_relative_to(export / ".build")
         and os.access(binary, os.X_OK), "built_binary_invalid")
    app = export / "dist/Findlet.app"
    executable = app / "Contents/MacOS/Findlet"
    need(app.is_dir() and not app.is_symlink() and os.access(executable, os.X_OK), "packaged_app_invalid")
    for file in (executable, app / "Contents/Info.plist", app / "Contents/Resources/AppIcon.icns"):
        need(file.is_file() and not file.is_symlink() and file.resolve().is_relative_to(export), "packaged_file_invalid")
    info = (app / "Contents/Info.plist").read_bytes()
    icon = (app / "Contents/Resources/AppIcon.icns").read_bytes()
    need(info == (repo / "Resources/Info.plist").read_bytes() and icon == (repo / "Resources/AppIcon.icns").read_bytes(), "packaged_resource_changed")
    metadata = plistlib.loads(info)
    need(metadata["CFBundleIdentifier"] == "com.alvarovillalbaa.Findlet" and metadata["CFBundleExecutable"] == "Findlet"
         and metadata["CFBundleName"] == metadata["CFBundleDisplayName"] == "Findlet" and metadata["CFBundlePackageType"] == "APPL"
         and metadata["CFBundleShortVersionString"] == "0.1.0" and metadata["CFBundleVersion"] == "1"
         and metadata["CFBundleIconFile"] == "AppIcon.icns" and metadata["LSMinimumSystemVersion"] == "15.0"
         and metadata["NSPrincipalClass"] == "NSApplication" and metadata["LSUIElement"] is True
         and metadata["LSMultipleInstancesProhibited"] is True and metadata["NSHighResolutionCapable"] is True, "bundle_metadata_invalid")
    built_identity, signed_identity = macho_identity("built_macho_identity", binary), macho_identity("signed_macho_identity", executable)
    need(built_identity == signed_identity, "packaged_macho_identity_changed")
    need(icon[:4] == b"icns" and int.from_bytes(icon[4:8], "big") == len(icon), "icns_header_invalid")
    offset, chunks = 8, []
    while offset < len(icon):
        need(offset + 8 <= len(icon), "icns_chunk_invalid")
        length = int.from_bytes(icon[offset + 4:offset + 8], "big")
        need(length >= 8 and offset + length <= len(icon), "icns_chunk_invalid")
        chunks.append(icon[offset:offset + 4].decode("ascii")); offset += length
    need(chunks == ["icp4", "ic11", "icp5", "ic12", "ic07", "ic13", "ic08", "ic14", "ic09", "ic10"], "icns_representation_set_changed")
    command("signature_verify", ["/usr/bin/codesign", "--verify", "--strict", str(app)])
    signature = command("signature_identity", ["/usr/bin/codesign", "-d", "--verbose=4", str(app)])[1].decode()
    need("Signature=adhoc" in signature and "Authority=" not in signature, "signature_not_local_adhoc")
    entitlements_bytes = command("effective_entitlements", ["/usr/bin/codesign", "-d", "--entitlements", ":-", str(app)])[0]
    entitlements = plistlib.loads(entitlements_bytes) if entitlements_bytes.strip() else {}
    need(entitlements == {}, "unexpected_effective_entitlements")
    report["package"] = {"verified": True, "bundleIdentifier": metadata["CFBundleIdentifier"], "builtBinarySha256": sha(binary.read_bytes()),
                         "signedExecutableSha256": sha(executable.read_bytes()), "infoSha256": sha(info), "iconSha256": sha(icon),
                         "resourceBytesEqualSource": True, "effectiveEntitlements": entitlements, "sandboxEnforced": False,
                         "machoIdentity": signed_identity, "sourceIconRepresentations": chunks, "metadata": metadata,
                         "binaryQualification": "The actual exported build script packages before tests. Ad-hoc signing may change signature bytes; UUID/architecture identity is compared, not executable byte equality."}
    source = (export / "Tests/FindletCoreTests/QMDContractTests.swift").read_text()
    expected = re.findall(r"^\s*func (test\w+)\(", source, re.M)
    need(len(expected) == 10 and len(set(expected)) == 10 and "XCTSkip" not in source, "authored_case_set_changed")
    report["expectedCases"] = ["FindletCoreTests.QMDContractTests/" + name for name in expected]
    xml_path = root / "tests.xml"
    command("core_tests", ["/usr/bin/xcrun", "swift", "test", *options, "--parallel", "--num-workers", "1",
                           "--enable-xctest", "--disable-swift-testing", "--filter", "FindletCoreTests.QMDContractTests",
                           "--xunit-output", str(xml_path)], 240, allowed=(0, 1), cwd=export)
    capture_xunit(expected)
    report["fixtureCleanup"] = {"passed": True, "filesystemFixturesCreated": 0,
                               "basis": "The ten exact pure-core cases use in-memory models/JSON and lexical URL construction; the named path is not created."}
    command("post_tests_signature_verify", ["/usr/bin/codesign", "--verify", "--strict", str(app)])
    verify_export("after_tool_work")
    guard("after_checks")
except Exception as error:
    report["errors"].append(str(error) if re.fullmatch(r"[a-z0-9_]+", str(error)) else type(error).__name__)
finally:
    cleanup_end = min(time.monotonic() + 90, work_end + 90)
    if "xunit" not in report and (root / "tests.xml").is_file():
        try:
            capture_xunit(expected)
        except Exception as error:
            report["errors"].append(str(error) if re.fullmatch(r"[a-z0-9_]+", str(error)) else "xunit_capture_failed")
    report["processCleanup"] = {"passed": all(child.get("released") for child in children), "started": len(children)}
    try:
        need(report["processCleanup"]["passed"], "owned_process_cleanup_unverified")
        owner()
        if export_files:
            verify_export("before_cleanup")
        capture_generated()
        for name, identity in reversed(list(generated_identity.items())):
            file, item = export / name, (export / name).lstat()
            need(not file.is_symlink() and item.st_uid == os.getuid() and (item.st_dev, item.st_ino) == identity, "generated_cleanup_owner_changed")
            shutil.rmtree(file)
            need(not os.path.lexists(file), "generated_path_remaining")
            next(row for row in report["generated"] if row["path"] == "source/" + name)["removed"] = True
        report["generatedCleanup"] = "passed"
    except Exception as error:
        report["generatedCleanup"] = "unverified"
        report["errors"].append(str(error) if re.fullmatch(r"[a-z0-9_]+", str(error)) else "generated_cleanup_error")
    try:
        guard("after_cleanup", cleanup=True)
        ignored = command("final_ignored", ["git", "status", "--porcelain=v1", "-z", "--ignored=matching", "--untracked-files=all"], cleanup=True)[0]
        report["ignoredOutput"] = {"bytes": len(ignored), "sha256": sha(ignored), "text": clean(ignored.decode("utf8", "replace"))}
        need(not ignored, "unexpected_ignored_output")
    except Exception as error:
        report["errors"].append(str(error) if re.fullmatch(r"[a-z0-9_]+", str(error)) else "post_guard_error")
    try:
        need(report.get("generatedCleanup") == "passed" and all(child.get("released") for child in children), "cleanup_unverified")
        owner()
        for name, identity in scratch_directories.items():
            item = (root / name).lstat()
            need(stat.S_ISDIR(item.st_mode) and not (root / name).is_symlink()
                 and item.st_uid == os.getuid() and (item.st_dev, item.st_ino) == identity, "scratch_child_identity_changed")
        shutil.rmtree(root)
        need(not os.path.lexists(root), "scratch_remaining")
        report["scratchCleanup"] = "passed"
    except Exception:
        report["scratchCleanup"] = "unverified"
        report["errors"].append("scratch_cleanup_unverified")

signal.setitimer(signal.ITIMER_REAL, 0)
report["interrupted"] = interrupted
report["processCleanup"] = {"passed": all(child.get("released") for child in children), "started": len(children)}
report["completedAtUtc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
report["status"] = "passed" if not report["errors"] and not interrupted and not global_expired and report.get("xunit", {}).get("accepted") and report.get("package", {}).get("verified") and len(report["guards"]) == 3 and all(row["passed"] for row in report["guards"]) and report.get("scratchCleanup") == "passed" else "failed"
encoded = json.dumps(report, separators=(",", ":")).encode()
if len(encoded) > RECEIPT_LIMIT:
    encoded = json.dumps({"status": "failed", "errors": ["receipt_bound"], "fullReportBytes": len(encoded), "fullReportSha256": sha(encoded)}).encode()
    report["status"] = "failed"
# Catchable interruption remains installed through the bounded final write.
signal.setitimer(signal.ITIMER_REAL, 2)
try:
    os.set_blocking(sys.stdout.fileno(), False)
    view = memoryview(encoded + b"\n")
    stdout_end = min(time.monotonic() + 2, cleanup_end + 2)
    while view and time.monotonic() < stdout_end:
        try:
            count = os.write(sys.stdout.fileno(), view)
            view = view[count:]
        except BlockingIOError:
            time.sleep(0.01)
    success = not view and report["status"] == "passed" and not interrupted and not global_expired
finally:
    signal.setitimer(signal.ITIMER_REAL, 0)
sys.exit(0 if success else 1)
