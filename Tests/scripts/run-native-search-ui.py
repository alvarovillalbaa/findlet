"""One actual Findlet UI journey on an owned public macOS runner; never local."""
import base64
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import signal
import stat
import sys
import tempfile
import time

REPO = Path.cwd().resolve()
SOURCE = os.environ.get("FINDLET_UI_SOURCE", "")
BASE = "ec4565c5bd0953eef95b472e6f6a6926faa82946"
HELPER = "Tests/scripts/run-keyword-integration.py"
HELPER_SHA = "6e860f582ded76240c03dd188448571b433b06722a29708093e2db5d95bd9981"
BRANCH = "qa/findlet-native-ui-20261113-1"
LOCK = "Tests/fixtures/qmd-darwin-arm64-package-lock.json"
CASE = "FindletAcceptance/FindletAcceptance/testNUI01ConfigureSearchReopenAndForget"
FILES = {
    "orchard.txt": b"# Orchard Notes\n\nquartzvelvetnative is an authored orchard observation.\n",
    "harbor.md": b"# Harbor Notes\n\ncobaltlilacnative is an authored harbor observation.\n",
}
PRIVATE = (b"quartzvelvetnative", b"cobaltlilacnative", b"noauthoredmatchnative",
           b"Orchard Notes", b"Harbor Notes") + tuple(FILES.values())
EXPECTED_PHASES = ["firstLaunchSetup", "nativePickersAndActualRebuild", "shortcutOpensSearch",
    "actualKeywordHitAndFinderReveal", "escapeAndShortcutReopen", "emptyAndUnpreparedStates",
    "normalQuit", "persistentReopenAndSecondSearch", "nativeForgetConfirmation"]
raw_helper = (REPO / HELPER).read_bytes()
assert hashlib.sha256(raw_helper).hexdigest() == HELPER_SHA
spec = importlib.util.spec_from_file_location("findlet_native_owned_support", REPO / HELPER)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)  # Definitions only; no old preflight/main/case.
g.repo, g.source, g.ROOT_LIMIT = REPO, SOURCE, 4 * 1024**3
g.STREAM_LIMIT, g.ZIP_LIMIT, g.ALL_ZIP_LIMIT = 8 * 1024**2, 2 * 1024**2, 16 * 1024**2
g.report = {"kind": "findlet.native-search-ui", "source": SOURCE, "base": BASE, "caseId": "NUI01",
    "accepted": False, "commands": [], "guards": [], "errors": [], "cleanup": {},
    "scope": {"tier": "T3", "appUI": True, "actualQMD": True, "oldCasesReplayed": False,
              "models": False, "privateFolders": False, "paidService": False}}
need, sha, read = g.need, g.sha, g.read
source_vector = None
export_vector = {}
library = Path.home() / "Library/Application Support/com.alvarovillalbaa.Findlet"
library_identity = None
evidence = None
ui_result = None
owned_exec = set()
original_observe = g.observe_processes
original_command = g.command


def observe(rows=None):
    rows = g.process_snapshot() if rows is None else rows
    # GUI apps launch through testmanager/launchd, outside xcodebuild's group.
    # Admit only exact binaries in the owner-created build/runtime, absent at
    # baseline, with UID/start identity. Never signal by a bare process name.
    for pid, row in rows.items():
        if (row["uid"] == os.getuid() and g.baseline_processes.get(pid) != row["start"]
                and any(row["command"] == binary or row["command"].startswith(binary + " ") for binary in owned_exec)):
            g.attributed[pid] = {key: row[key] for key in ("pid", "ppid", "pgid", "uid", "start")}
    return original_observe(rows)


g.observe_processes = observe


def redact_bytes(data):
    result = data
    for token in PRIVATE:
        result = result.replace(token, b"[authored fixture withheld]")
    if g.root is not None:
        result = result.replace(str(g.root).encode(), b"[scratch]")
    return result.replace(str(Path.home()).encode(), b"[runner-home]")


def command(*args, **kwargs):
    try:
        return original_command(*args, **kwargs)
    finally:
        if g.report["commands"]:
            row = g.report["commands"][-1]
            for name in ["stdout", "stderr"]:
                stream = row.get(name, {})
                if stream.get("encoding") != "gzip-base64" or "data" not in stream:
                    continue
                raw = gzip.decompress(base64.b64decode(stream["data"], validate=True))
                redacted = redact_bytes(raw)
                stream["originalSha256"] = sha(raw)
                stream["originalBytes"] = len(raw)
                stream["fixtureAndPathRedactionApplied"] = redacted != raw
                if redacted != raw:
                    compressed = gzip.compress(redacted, mtime=0)
                    stream.update(encoding="redacted-gzip-base64", data=base64.b64encode(compressed).decode(),
                                  retainedBytes=len(redacted), retainedSha256=sha(redacted),
                                  compressedBytes=len(compressed), unredactedOriginalRetained=False)
                need(not any(token in redacted for token in PRIVATE), "public_stream_privacy_refused")
        if g.root is not None and g.root.exists():
            allocated = apparent = entries = 0
            for directory, dirs, files in os.walk(g.root, followlinks=False):
                for name in dirs + files:
                    value = (Path(directory) / name).lstat(); entries += 1
                    if stat.S_ISREG(value.st_mode):
                        allocated += value.st_blocks * 512; apparent += value.st_size
            need(allocated <= g.ROOT_LIMIT and entries <= 150000, "owned_storage_bound")
            need(shutil.disk_usage(g.root).free >= 2 * 1024**3, "remote_disk_reserve_exhausted")
            g.report.setdefault("storageObservations", []).append({"label": args[0], "allocatedBytes": allocated,
                "apparentBytes": apparent, "entries": entries})


g.command = command  # The reused installer receives the same guarded supervisor.


def guard(label, cleanup=False):
    global source_vector
    head, _, _ = command(label + "_head", ["/usr/bin/git", "rev-parse", "HEAD"], cleanup=cleanup)
    need(head.decode().strip() == SOURCE, "source_head_changed")
    tree, _, _ = command(label + "_tree", ["/usr/bin/git", "ls-tree", "-r", "-z", "HEAD"], cleanup=cleanup)
    rows = []
    for name, expected in sorted(g.parse_tree(tree).items()):
        current = g.source_file(name)
        need({key: current[key] for key in ["mode", "gitBlob"]} == expected, "source_bytes_or_mode_changed")
        rows.append(current)
    status, _, _ = command(label + "_status", ["/usr/bin/git", "status", "--porcelain", "--untracked-files=all", "--ignored=matching"], cleanup=cleanup)
    need(status == b"", "source_residue")
    if source_vector is None:
        source_vector = rows
        g.report["sourceFiles"] = rows
    need(rows == source_vector, "full_source_vector_changed")
    g.report["guards"].append({"label": label, "files": len(rows), "bytes": sum(row["bytes"] for row in rows),
                              "sha256": sha(json.dumps(rows, sort_keys=True).encode()), "passed": True})


def export_source():
    selected = [row for row in source_vector if row["path"] == "Package.swift"
        or row["path"].startswith(("Sources/", "Resources/", "Tests/e2e/", "Tests/FindletAcceptance.xcodeproj/"))]
    for row in selected:
        target = g.root / "source" / row["path"]
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(read(REPO / row["path"]))
        target.chmod(0o755 if row["mode"] == "100755" else 0o644)
        export_vector[row["path"]] = g.fingerprint(target)
    g.report["exportedSource"] = [{"path": path, **value} for path, value in export_vector.items()]


def export_guard():
    for name, expected in export_vector.items():
        need(g.fingerprint(g.root / "source" / name) == expected, "compiled_source_export_changed")


def preflight():
    global evidence, library_identity
    need(platform.system() == "Darwin" and platform.machine() == "arm64" and platform.mac_ver()[0].split(".")[0] == "15",
         "macos15_arm64_required")
    need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, "isolated_python_required")
    need(re.fullmatch(r"[a-f0-9]{40}", SOURCE) and os.environ.get("CI") == "true"
         and os.environ.get("GITHUB_REPOSITORY") == g.REPOSITORY and os.environ.get("GITHUB_REF") == "refs/heads/" + BRANCH
         and os.environ.get("GITHUB_EVENT_NAME") == "create", "owned_public_ci_required")
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_bytes())
    need(event["repository"]["private"] is False and event["ref"] == BRANCH and event["ref_type"] == "branch", "public_branch_required")
    started = int(os.environ["FINDLET_UI_JOB_STARTED_MS"]) / 1000
    remaining = started + 1200 - time.time()
    need(450 <= remaining <= 1200, "job_window_unavailable")
    g.work_end = time.monotonic() + min(900, remaining - 150)
    g.job_end = time.monotonic() + remaining
    parent = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    need(shutil.disk_usage(parent).free >= 6 * 1024**3 and Path(g.DEVELOPER).is_dir(), "remote_storage_or_toolchain_unavailable")
    need(not os.path.lexists(library) and library.parent.resolve() == library.parent, "existing_findlet_profile_preserved")
    g.root = Path(tempfile.mkdtemp(prefix="findlet-native-ui-", dir=parent)).resolve(); g.root.chmod(0o700)
    current = g.root.stat(); g.root_identity = (current.st_dev, current.st_ino)
    g.nonce = os.urandom(16).hex()
    (g.root / ".owner").write_text(g.nonce); (g.root / ".owner").chmod(0o600)
    current = (g.root / ".owner").stat(); g.marker_identity = (current.st_dev, current.st_ino)
    for name in ["source", "build", "runtime", "runtime/node", "runtime/tools", "tmp", "cache", "config", "input",
                 "cache/swift", "cache/clang", "cache/npm", "cache/xdg", "cache/data", "cache/state"]:
        g.make_directory(name)
    for name in ["npmrc", "global-npmrc"]:
        g.owned_write("config/" + name, b"")
    g.env = {"HOME": str(Path.home()), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "en_US.UTF-8", "LC_ALL": "C", "TZ": "UTC",
        "CI": "true", "DEVELOPER_DIR": g.DEVELOPER, "TMPDIR": str(g.root / "tmp") + "/",
        "XDG_CONFIG_HOME": str(g.root / "config"), "XDG_CACHE_HOME": str(g.root / "cache/xdg"),
        "XDG_DATA_HOME": str(g.root / "cache/data"), "XDG_STATE_HOME": str(g.root / "cache/state"),
        "SWIFTPM_MODULECACHE_OVERRIDE": str(g.root / "cache/swift"), "CLANG_MODULE_CACHE_PATH": str(g.root / "cache/clang"),
        "NPM_CONFIG_CACHE": str(g.root / "cache/npm"), "NPM_CONFIG_USERCONFIG": str(g.root / "config/npmrc"),
        "NPM_CONFIG_GLOBALCONFIG": str(g.root / "config/global-npmrc"), "NPM_CONFIG_REGISTRY": "https://registry.npmjs.org/",
        "NPM_CONFIG_IGNORE_SCRIPTS": "true", "NPM_CONFIG_AUDIT": "false", "NPM_CONFIG_FUND": "false",
        "NPM_CONFIG_UPDATE_NOTIFIER": "false", "NODE_LLAMA_CPP_SKIP_DOWNLOAD": "true", "NO_COLOR": "1", "QMD_FORCE_CPU": "1",
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0"}
    g.baseline_processes = {pid: row["start"] for pid, row in g.process_snapshot().items()}
    need(not any("Findlet.app/Contents/MacOS/Findlet" in row["command"] for row in g.process_snapshot().values()), "existing_findlet_process_preserved")
    evidence = parent / ("findlet-native-ui-evidence-" + os.environ["GITHUB_RUN_ID"])
    need(not evidence.exists(), "evidence_path_exists"); evidence.mkdir(mode=0o700)
    g.report["runtime"] = {"macOS": platform.mac_ver()[0], "architecture": platform.machine(), "homePreserved": True,
                           "helperSha256": HELPER_SHA, "remoteFreeBytes": shutil.disk_usage(parent).free}
    guard("before_setup"); export_source()
    library.mkdir(mode=0o700); library_identity = library.stat()
    (library / ".native-ui-owner").write_text(g.nonce); (library / ".native-ui-owner").chmod(0o600)


def prepare():
    global ui_result
    g.install_runtime()  # Exact frozen keyword installer; no old query/case.
    owned_exec.add(str(g.node))
    folder = g.root / "input/authored-findlet"; folder.mkdir(mode=0o700)
    for name, body in FILES.items():
        (folder / name).write_bytes(body); (folder / name).chmod(0o600)
    g.report["fixtureFiles"] = {name: g.fingerprint(folder / name) for name in FILES}
    config = {"folder": str(folder), "node": str(g.node), "package": str(g.package)}
    (g.root / "source/Tests/e2e/FixtureConfig.json").write_text(json.dumps(config))
    output, _, _ = command("xcode_version", ["/usr/bin/xcodebuild", "-version"])
    need(output.strip() == b"Xcode 16.4\nBuild version 16F6", "selected_xcode_changed")
    common = ["/usr/bin/xcodebuild", "-project", "Tests/FindletAcceptance.xcodeproj", "-scheme", "FindletAcceptance",
        "-configuration", "Debug", "-destination", "platform=macOS,arch=arm64", "-derivedDataPath", str(g.root / "build/derived")]
    command("build_for_testing", common + ["build-for-testing"], seconds=300, cwd=g.root / "source")
    products = g.root / "build/derived/Build/Products"
    run_files = list(products.glob("*.xctestrun")); need(len(run_files) == 1, "xctestrun_binding_missing")
    run_file = run_files[0]
    app = products / "Debug/Findlet.app"
    runner = products / "Debug/FindletAcceptance-Runner.app"
    owned_exec.update([str(app / "Contents/MacOS/Findlet"), str(runner / "Contents/MacOS/FindletAcceptance-Runner")])
    pending = [plistlib.loads(run_file.read_bytes())]; targets = []
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if "UITargetAppPath" in value: targets.append(value["UITargetAppPath"])
            pending.extend(value.values())
        elif isinstance(value, list): pending.extend(value)
    need(len(targets) == 1 and Path(targets[0].replace("__TESTROOT__", str(run_file.parent))).resolve() == app.resolve(), "wrong_native_target")
    need(plistlib.loads((app / "Contents/Info.plist").read_bytes())["CFBundleIdentifier"] == "com.alvarovillalbaa.Findlet", "wrong_bundle")
    command("production_style_signature", ["/usr/bin/codesign", "--force", "--sign", "-", str(app)])
    out, err, _ = command("app_entitlements", ["/usr/bin/codesign", "-d", "--entitlements", ":-", str(app)])
    need(not out.strip() or plistlib.loads(out) == {}, "app_entitlements_changed")
    command("strict_signature", ["/usr/bin/codesign", "--verify", "--strict", str(app)])
    g.report["compiledApp"] = {"binary": g.fingerprint(app / "Contents/MacOS/Findlet"), "xctestrunSha256": sha(run_file.read_bytes()), "productionEntitlementsEmpty": True}
    export_guard(); guard("after_build")
    ui_result = g.root / "build/native.xcresult"
    command("native_ui", ["/usr/bin/xcodebuild", "test-without-building", "-xctestrun", str(run_file),
        "-destination", "platform=macOS,arch=arm64", "-resultBundlePath", str(ui_result), "-only-testing:" + CASE,
        "-parallel-testing-enabled", "NO", "-test-timeouts-enabled", "YES", "-default-test-execution-time-allowance", "360",
        "-maximum-test-execution-time-allowance", "420"], seconds=480, cwd=g.root / "source")
    g.report["nativeTestCommandPassed"] = True


def collect_result():
    if ui_result is None or not ui_result.exists():
        return
    summary, _, _ = command("native_summary", ["/usr/bin/xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(ui_result)], cleanup=True)
    identities, _, _ = command("native_identities", ["/usr/bin/xcrun", "xcresulttool", "get", "test-results", "tests", "--path", str(ui_result)], cleanup=True)
    g.report["testSummary"] = json.loads(summary)
    tree = json.loads(identities); pending = list(tree.get("testNodes", [])); cases = []
    while pending:
        node = pending.pop()
        if node.get("nodeType") == "Test Case": cases.append(node)
        pending.extend(node.get("children", []))
    g.report["nativeCases"] = cases
    attachment_root = g.root / "build/attachments"
    command("native_attachments", ["/usr/bin/xcrun", "xcresulttool", "export", "attachments", "--path", str(ui_result), "--output-path", str(attachment_root)], seconds=60, cleanup=True)
    manifest = json.loads((attachment_root / "manifest.json").read_bytes())
    # The manifest format/filename mapping is read from the actual result.
    g.report["attachmentManifest"] = manifest
    accepted_images = {}
    for path in attachment_root.rglob("*"):
        if not path.is_file() or path.is_symlink(): continue
        if path.suffix == ".json" and path.name != "manifest.json":
            try: value = json.loads(path.read_bytes())
            except (ValueError, OSError): continue
            if isinstance(value, dict) and value.get("caseId") == "NUI01":
                need(value.get("phases") == EXPECTED_PHASES and value.get("status") == "passed", "incomplete_native_journey")
                g.report["uiObservations"] = value
    # Human attachment names live in the manifest; exported filenames are IDs.
    pending = [manifest]
    while pending:
        item = pending.pop()
        if isinstance(item, list): pending.extend(item)
        elif isinstance(item, dict):
            human = item.get("suggestedHumanReadableName", "")
            exported = item.get("exportedFileName", "")
            match = re.fullmatch(r"(01-empty-setup|02-ready-empty|03-reopened-empty|04-forgotten-empty)_[0-9]+_[A-F0-9-]{36}\.png", human)
            if match and exported:
                target = attachment_root / exported
                need(target.is_file() and not target.is_symlink() and target.stat().st_size < 4 * 1024**2, "image_bound")
                destination = evidence / (match[1] + ".png"); destination.write_bytes(target.read_bytes())
                accepted_images[match[1]] = {"bytes": destination.stat().st_size, "sha256": sha(destination.read_bytes())}
            pending.extend(item.values())
    g.report["emptyQueryImages"] = accepted_images
    if g.report.get("nativeTestCommandPassed"):
        summary = g.report["testSummary"]
        need(summary.get("result") == "Passed" and summary.get("totalTestCount") == summary.get("passedTests") == 1
             and summary.get("failedTests") == summary.get("skippedTests") == 0 and not summary.get("testFailures"), "native_summary_refused")
        need(len(cases) == 1 and cases[0].get("result") == "Passed"
             and cases[0].get("name") == "testNUI01ConfigureSearchReopenAndForget()", "native_case_identity_refused")
        need(g.report.get("uiObservations") and len(accepted_images) == 4, "native_evidence_incomplete")


def verify_state():
    need(g.report.get("nativeTestCommandPassed") and g.report.get("uiObservations"), "native_ui_unaccepted")
    for name, expected in g.report["fixtureFiles"].items():
        need(g.fingerprint(g.root / "input/authored-findlet" / name) == expected, "original_document_changed")
    setup = json.loads(read(library / "settings.json"))
    need(len(setup["settings"]["folders"]) == 1 and setup["settings"]["runtime"]["nodePath"] == str(g.node)
         and setup["settings"]["runtime"]["qmdPackagePath"] == str(g.package), "native_settings_not_retained")
    need(not os.path.lexists(library / "current.json") and not list((library / "generations").iterdir()), "native_forget_incomplete")
    g.verify_runtime("after_native_ui"); export_guard(); guard("after_native_ui", cleanup=True)
    g.report["hostVerification"] = {"originalsUnchanged": True, "runtimeUnchanged": True, "settingsRetained": True,
                                     "currentPointerAbsent": True, "generationsEmpty": True}


def cleanup():
    if g.root is None:
        return
    g.cleanup_end = min(time.monotonic() + 120, g.job_end - 30)
    try:
        # Close only identity-attributed binaries/descendants. launchd GUI groups
        # can contain unrelated processes, so native cleanup signals single PIDs.
        for sig, wait_seconds in [(signal.SIGTERM, 5), (signal.SIGKILL, 5)]:
            rows, live, unknown = observe()
            for row in live:
                old = g.attributed[row["pid"]]
                need(old["start"] == row["start"] and row["uid"] == os.getuid(), "native_signal_identity_changed")
                try: os.kill(row["pid"], sig)
                except ProcessLookupError: pass
            end = time.monotonic() + wait_seconds
            while time.monotonic() < end:
                _, live, unknown = observe()
                if not live and not unknown: break
                time.sleep(.05)
        rows, live, unknown = observe()
        need(not live and not unknown and all(child["process"].poll() is not None and g.absent(child["process"].pid) for child in g.children), "owned_native_process_remains")
        g.report["cleanup"]["ownedProcessIdentitiesAbsent"] = True
        if library_identity is not None:
            now = library.lstat()
            need(not library.is_symlink() and (now.st_dev, now.st_ino) == (library_identity.st_dev, library_identity.st_ino)
                 and now.st_uid == os.getuid() and read(library / ".native-ui-owner", 32) == g.nonce.encode(), "native_profile_owner_changed")
            shutil.rmtree(library); need(not os.path.lexists(library), "owned_native_profile_remains")
        g.report["cleanup"]["ownedProfileAbsent"] = True
        if "fixtureFiles" in g.report:
            for name, expected in g.report["fixtureFiles"].items():
                need(g.fingerprint(g.root / "input/authored-findlet" / name) == expected, "authored_original_changed_before_cleanup")
            g.report["cleanup"]["authoredOriginalsVerifiedBeforeRemoval"] = True
        export_guard()
        if g.runtime_vector is not None: g.verify_runtime("before_cleanup")
        guard("before_cleanup", cleanup=True)
        allocated = apparent = entries = 0
        for directory, dirs, files in os.walk(g.root, followlinks=False):
            for name in dirs + files:
                value = (Path(directory) / name).lstat(); entries += 1
                need(value.st_uid == os.getuid(), "scratch_owner_changed")
                if stat.S_ISREG(value.st_mode):
                    allocated += value.st_blocks * 512; apparent += value.st_size
        need(allocated <= g.ROOT_LIMIT and entries <= 150000, "owned_allocated_storage_bound")
        need(shutil.disk_usage(g.root).free >= 2 * 1024**3, "remote_disk_reserve_exhausted")
        g.report["scratchInventory"] = {"allocatedBytes": allocated, "apparentBytes": apparent, "entries": entries}
        g.owner(); shutil.rmtree(g.root); need(not os.path.lexists(g.root), "owned_scratch_remains")
        g.report["cleanup"]["ownedScratchAbsent"] = True
    except Exception as error:
        g.report["errors"].append(g.finite(error)); g.report["cleanup"]["unverified"] = True


completed = False
try:
    preflight(); prepare(); completed = True
except Exception as error:
    g.report["errors"].append(g.finite(error)); g.report["errorType"] = type(error).__name__
    trace = error.__traceback__
    while trace is not None and trace.tb_next is not None: trace = trace.tb_next
    g.report["errorLocation"] = {"file": Path(trace.tb_frame.f_code.co_filename).name, "line": trace.tb_lineno} if trace else None
finally:
    if g.root is not None:
        g.cleanup_end = min(time.monotonic() + 120, g.job_end - 30)
        try:
            collect_result()
            if completed: verify_state()
        except Exception as error:
            g.report["errors"].append(g.finite(error))
        cleanup()
    g.report["accepted"] = completed and not g.report["errors"] and g.report["cleanup"].get("ownedScratchAbsent") is True
    if evidence is None:
        evidence = Path(os.environ["RUNNER_TEMP"]) / ("findlet-native-ui-evidence-" + os.environ["GITHUB_RUN_ID"])
        evidence.mkdir(mode=0o700, exist_ok=True)
    # No original activity/query/setup paths or private xcresult is exported.
    encoded = redact_bytes(json.dumps(g.report, indent=2).encode())
    for token in PRIVATE: need(token not in encoded, "public_receipt_privacy_refused")
    encoded = encoded.replace(str(Path.home()).encode(), b"[runner-home]")
    if g.root is not None: encoded = encoded.replace(str(g.root).encode(), b"[scratch]")
    (evidence / "receipt.json").write_bytes(encoded + b"\n")
    print(json.dumps({"accepted": g.report["accepted"], "caseId": "NUI01", "errors": g.report["errors"], "cleanup": g.report["cleanup"]}))
raise SystemExit(0 if g.report["accepted"] else 1)
