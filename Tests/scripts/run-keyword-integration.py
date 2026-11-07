#!/usr/bin/env python3
"""One owned macOS keyword-engine integration; no app UI, models or old suite."""
import base64
import collections
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import selectors
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
import uuid


REPOSITORY = "alvarovillalbaa/findlet"
BRANCH = "refs/heads/qa/findlet-qmd-keyword-20261107-2"
ACTIVE = ".github/workflows/qmd-keyword-integration.yml"
BASE = "227e93e2eb324e21950e591e6912492cd0c94a5a"
BASE_TREE = "6bf681a401dc2e99bf3a4daa629d42403ceacbb4"
BASE_STUB = {"bytes": 343, "gitBlob": "a492b7f30b5859274ad13344e56f4733db30d6a1",
             "sha256": "e6e7e19fefdb58c216408b8c8fe77d05cf613500ab249e246e7d6ad78cce0468"}
AGENTS = {"bytes": 4558, "sha256": "5f5c4503b449e354ff37e33d0ac68bc600ff5133c158b3c9d7518e3bf4aff9e5"}
HARNESS = "Tests/integration/KeywordPipelineHarness.swift"
LOCK = "Tests/fixtures/qmd-darwin-arm64-package-lock.json"
ADDED = {HARNESS, LOCK, "Tests/scripts/run-keyword-integration.py", "Tests/README.md",
         "docs/proposals/qmd-keyword-integration.md", "docs/proposals/qmd-keyword-integration.workflow.yml.example"}
CORE = ["Sources/FindletCore/QMDContract.swift", "Sources/FindletCore/SearchModels.swift"]
SERVICES = ["Sources/Findlet/Services/CorpusBuilder.swift", "Sources/Findlet/Services/SourceFileAccess.swift",
            "Sources/Findlet/Services/FindletEngine.swift", "Sources/Findlet/Services/QMDProcessRunner.swift"]
DEVELOPER = "/Applications/Xcode_16.4.app/Contents/Developer"
NODE_URL = "https://nodejs.org/dist/v26.13.0/node-v26.13.0-darwin-arm64.tar.gz"
NODE_SHA256 = "d38bd5e5a2ddce6bbb5ce45e46e208337da4d51fffe611e567fd32073d6439f6"
NODE_MEMBER_LIMIT, NODE_TOTAL_LIMIT, NODE_ENTRY_LIMIT = 256 * 1024**2, 512 * 1024**2, 20000
LOCK_SHA256 = "c7fbb1cb91ac025f79861db970aab98eb4604ec91f8115fcd67d09e9b9176df2"
HARNESS_SHA256 = "411636b44a1946be346864cbc10c30e54157c91ea31d6e6e7cba0310dc1303a2"
STREAM_LIMIT, ZIP_LIMIT, ALL_ZIP_LIMIT, REPORT_LIMIT = 1048576, 262144, 2097152, 8388608
WORK_SECONDS, CLEANUP_SECONDS, MARGIN_SECONDS = 900, 120, 30
ROOT_LIMIT = 2 * 1024**3
INDEX_CHECKS = {"rebuildThreeDocumentsWithoutModels", "summaryMatchesRebuild", "pointerStateStableAcrossSearch",
                "hiddenAndSymlinkExcluded", "authoredSourcesUnchanged", "runtimeSelectedFilesUnchanged",
                "privateProofCreated", "rootOwnershipFinal"}
LIFECYCLE_CHECKS = {"authoredSourcesMatchPriorSession", "runtimeMatchesPriorSession", "pointerStateMatchPriorSession",
                    "newEngineReadsThreeDocuments", "invalidUTF8RefusalObserved", "failedRebuildPreservesFullPointerAndState",
                    "failedGenerationRemoved", "missingOriginalRefused", "sameInodeOriginalRestored", "restoredOriginalResolves",
                    "originalBytesModesInodesAndMTimePreserved", "forgetSummaryEmpty", "currentPointerAbsent",
                    "generationAndCacheEmpty", "quarantineEmpty", "sourcesRemainAfterForget", "runtimeSelectedFilesUnchanged",
                    "rootOwnershipFinal"}
STAGES = {"index": ["create_authored_fixture", "production_rebuild", "production_keyword_queries_and_resolution",
                    "persist_private_handoff", "index_complete_preserved_for_parent"],
          "lifecycle": ["load_private_handoff", "reopen_production_engine", "invalid_utf8_rebuild_preserves_generation",
                        "missing_original_resolver_refusal", "production_forget_index", "lifecycle_complete"]}
FIXTURE_FILES = {
    "authored/alpha.md": (67, "5fbf9e256785c9572bae22013541cf7d7de8ea50930b5d1bc13a049f5c0c40b4"),
    "authored/notes-東京.markdown": (72, "34b5c943c2e437946e5a843987b8678eaa891d8b1b1a16e5600f2865d242cadf"),
    "authored/plain.txt": (58, "26526b2900517793c4bf1f0dc90e5b3135c9513f49f2e9639963ee2b8581c21b"),
    "authored/.hidden.md": (61, "32e428b2955a4d3e5f4f1379accd535d195eb6333b676ae7ee175a8a6d76584f"),
    "decoy/outside.md": (56, "186f15cef9c5ade4ced2aefd9dedc6a6c6d1f927ca59790091e7a0ff53f6ed71")}
DOCUMENTS = [
    {"id": "0556f1ae-5314-898a-bf90-51767e53472d", "relativePath": "alpha.md"},
    {"id": "7dea72c0-3913-89fa-827e-4f110b7595f7", "relativePath": "notes-東京.markdown"},
    {"id": "65cf6866-2808-8628-9bde-5609beb4a53d", "relativePath": "plain.txt"}]
for document in DOCUMENTS:
    document.update({"folderID": "d47af59c-6411-4baa-9824-c6a2b1d8e27b", "snapshotName": document["id"] + ".md",
                     "title": document["relativePath"]})
source = sys.argv[2] if len(sys.argv) == 3 and sys.argv[1] == "--source-commit" else None
repo = Path.cwd().resolve()
root = None
root_identity = marker_identity = None
nonce = None
env = {}
work_end = cleanup_end = job_end = None
interrupted = False
children = []
attributed = {}
baseline_processes = {}
source_vector = baseline_tree = None
export_vector = []
known_directories = {}
compressed_total = 0
node = package = harness_binary = None
runtime_vector = None
report = {"schemaVersion": "findlet.qmd-keyword-integration.v1", "sourceCommit": source,
          "canonicalBaseCommit": BASE, "status": "failed", "accepted": False,
          "commands": [], "guards": [], "sourceFiles": [], "phases": [], "errors": [],
          "scope": {"tier": "tier3", "cases": ["K01", "K02"], "qmdVersion": "2.8.3", "keywordOnly": True,
                    "appUI": False, "oldCoreCasesRepeated": False, "fullAppBuild": False,
                    "models": False, "privateFolders": False, "accounts": False},
          "proofLimits": [
              "Two new app-less production-engine sessions use owned authored folders. No app launch, macOS UI, private corpus, semantic model, inference or distribution is exercised.",
              "The outer harness stdout/stderr are retained. The unchanged production QMDProcessRunner discards QMD stderr and bounds internal streams; this receipt does not contain those discarded originals.",
              "Native Node/SQLite/vec admission is macOS ARM64-specific. Earlier Linux evidence is not substituted for actual Darwin loading.",
              "PID/start/UID/group, file identities and hashes are boundary observations, not a continuous host-wide attestation. External runner termination can prevent teardown.",
          ]}


def need(value, code):
    if not value:
        raise RuntimeError(code)


def sha(data, algorithm="sha256"):
    return hashlib.new(algorithm, data).hexdigest()


def budget():
    end = cleanup_end if cleanup_end is not None else work_end
    need(end is None or time.monotonic() < end - 2, "controller_deadline")


def finite(error):
    text = str(error)
    return text if re.fullmatch(r"[a-z0-9_]{1,100}", text) else "controller_operation_failed"


def clean(value):
    text = str(value)
    for path, label in ((root, "[scratch]"), (repo, "[source]")):
        if path is not None:
            text = text.replace(str(path), label)
    if env.get("HOME"):
        text = text.replace(env["HOME"], "[runner-home]")
    return text[:800]


def file_identity(value):
    return {"device": str(value.st_dev), "inode": str(value.st_ino), "uid": value.st_uid,
            "mode": format(stat.S_IMODE(value.st_mode), "04o"), "bytes": value.st_size,
            "mtimeNs": str(value.st_mtime_ns), "ctimeNs": str(value.st_ctime_ns)}


def read(file, maximum=16 * 1024**2):
    file = Path(file)
    before = file.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size <= maximum, "regular_file_bound")
    descriptor = os.open(file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        need(file_identity(os.fstat(descriptor)) == file_identity(before), "file_changed_at_open")
        chunks, remaining = [], before.st_size
        while remaining:
            budget()
            chunk = os.read(descriptor, min(remaining, 1048576))
            need(bool(chunk), "file_truncated")
            chunks.append(chunk)
            remaining -= len(chunk)
        need(os.read(descriptor, 1) == b"" and file_identity(os.fstat(descriptor)) == file_identity(before)
             == file_identity(file.lstat()), "file_changed_during_read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def fingerprint(file):
    file = Path(file)
    before = file.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid(), "owned_regular_file_required")
    descriptor = os.open(file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    digest = hashlib.sha256()
    try:
        need(file_identity(os.fstat(descriptor)) == file_identity(before), "fingerprint_open_changed")
        while True:
            budget()
            chunk = os.read(descriptor, 1048576)
            if not chunk:
                break
            digest.update(chunk)
        need(file_identity(os.fstat(descriptor)) == file_identity(before) == file_identity(file.lstat()),
             "fingerprint_source_changed")
    finally:
        os.close(descriptor)
    return {**file_identity(before), "sha256": digest.hexdigest()}


def strict_json(data):
    def pairs(values):
        result = {}
        for key, value in values:
            need(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    def constant(_):
        raise RuntimeError("nonfinite_json")
    value = json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=pairs, parse_constant=constant)
    pending, visited = [(value, 0)], 0
    while pending:
        current, depth = pending.pop()
        visited += 1
        need(depth <= 32 and visited <= 100000, "json_structure_bound")
        if isinstance(current, dict):
            for key, item in current.items():
                key.encode("utf-8", errors="strict")
                pending.append((item, depth + 1))
        elif isinstance(current, list):
            pending.extend((item, depth + 1) for item in current)
        elif isinstance(current, str):
            current.encode("utf-8", errors="strict")
        elif isinstance(current, float):
            need(math.isfinite(current), "nonfinite_json")
    return value


def owner():
    need(root is not None, "owned_root_unavailable")
    current = root.lstat()
    need(stat.S_ISDIR(current.st_mode) and current.st_uid == os.getuid()
         and stat.S_IMODE(current.st_mode) == 0o700
         and (current.st_dev, current.st_ino) == root_identity and root.resolve(strict=True) == root,
         "scratch_owner_changed")
    marker = root / ".owner"
    value = marker.lstat()
    need(stat.S_ISREG(value.st_mode) and value.st_uid == os.getuid() and stat.S_IMODE(value.st_mode) == 0o600
         and (value.st_dev, value.st_ino) == marker_identity and read(marker, 32) == nonce.encode(), "scratch_marker_changed")


def process_snapshot():
    # Observation only: do not retain unrelated host command lines.
    result = subprocess.run(["/bin/ps", "-axo", "pid=,ppid=,pgid=,uid=,lstart=,command="],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3, env={"LC_ALL": "C", "PATH": "/usr/bin:/bin"})
    need(result.returncode == 0 and len(result.stdout) <= 2 * 1024**2, "process_observation_failed")
    rows = {}
    for line in result.stdout.decode("utf-8", errors="replace").splitlines():
        parts = line.split(None, 9)
        if len(parts) != 10 or not all(x.isdigit() for x in parts[:4]):
            continue
        pid, parent, group, uid = map(int, parts[:4])
        rows[pid] = {"pid": pid, "ppid": parent, "pgid": group, "uid": uid,
                     "start": " ".join(parts[4:9]), "command": parts[9]}
    return rows


def observe_processes(rows=None):
    rows = process_snapshot() if rows is None else rows
    changed = True
    while changed:
        changed = False
        for pid, row in rows.items():
            if pid in attributed or row["uid"] != os.getuid() or baseline_processes.get(pid) == row["start"]:
                continue
            parent = attributed.get(row["ppid"])
            if parent is not None and row["ppid"] in rows and rows[row["ppid"]]["start"] == parent["start"]:
                attributed[pid] = {key: row[key] for key in ("pid", "ppid", "pgid", "uid", "start")}
                changed = True
    live = [row for pid, row in rows.items() if pid in attributed and row["start"] == attributed[pid]["start"]]
    unknown = [row for pid, row in rows.items() if root is not None and str(root) in row["command"]
               and row["uid"] == os.getuid() and pid != os.getpid()
               and (pid not in attributed or row["start"] != attributed[pid]["start"])
               and baseline_processes.get(pid) != row["start"]]
    return rows, live, unknown


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
    rows, _, _ = observe_processes()
    if child["stopAt"] is None:
        child["stopAt"] = time.monotonic()
    members = [value for value in rows.values() if value["pgid"] == child["process"].pid]
    if not members:
        need(absent(child["process"].pid), "unknown_process_group_remaining")
        return
    need(all(value["uid"] == os.getuid() and value["pid"] in attributed
             and attributed[value["pid"]]["start"] == value["start"]
             and attributed[value["pid"]]["pgid"] == value["pgid"] for value in members), "signal_attribution_refused")
    if not child["signals"]:
        try:
            os.killpg(child["process"].pid, signal.SIGTERM)
            child["signals"].append("TERM")
        except ProcessLookupError:
            need(absent(child["process"].pid), "signal_group_recheck_failed")
    elif time.monotonic() - child["stopAt"] >= 5 and "KILL" not in child["signals"]:
        try:
            os.killpg(child["process"].pid, signal.SIGKILL)
            child["signals"].append("KILL")
        except ProcessLookupError:
            need(absent(child["process"].pid), "signal_group_recheck_failed")


def packed(data, observed, digest, complete):
    global compressed_total
    compressed = gzip.compress(data, mtime=0)
    value = {"encoding": "gzip-base64", "bytes": len(data), "sha256": sha(data),
             "observedBytes": observed, "observedSha256": digest,
             "complete": complete and len(data) == observed}
    if len(compressed) <= ZIP_LIMIT and compressed_total + len(compressed) <= ALL_ZIP_LIMIT:
        compressed_total += len(compressed)
        value.update({"compressedBytes": len(compressed), "data": base64.b64encode(compressed).decode(), "retained": True})
    else:
        value.update({"retained": False, "complete": False})
    return value


def command(label, arguments, seconds=30, *, cwd=None, allowed=(0,), cleanup=False, post_root=False):
    if post_root:
        need(cleanup and report.get("scratchCleanup") == "passed" and root is not None
             and not os.path.lexists(root), "post_root_cleanup_unverified")
    else:
        owner()
    need(cleanup or not interrupted, "interrupted_before_command")
    deadline = min(time.monotonic() + seconds, (cleanup_end if cleanup else work_end) - 10)
    need(time.monotonic() < deadline, "command_budget_exhausted")
    child_env = env if not post_root else {key: env[key] for key in ("PATH", "HOME", "LANG", "LC_ALL", "TZ", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL", "GIT_OPTIONAL_LOCKS")}
    process = subprocess.Popen(arguments, cwd=cwd or repo, env=child_env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    child = {"process": process, "reason": None, "stopAt": None, "released": False, "signals": []}
    children.append(child)
    row = {"label": label, "arguments": [clean(x) for x in arguments], "pid": process.pid, "start": None}
    report["commands"].append(row)
    states = [{"data": bytearray(), "digest": hashlib.sha256(), "bytes": 0, "eof": False} for _ in range(2)]
    selector = selectors.DefaultSelector()
    forced = False
    exited_at = None
    try:
        rows = process_snapshot()
        need(process.pid in rows and rows[process.pid]["uid"] == os.getuid()
             and rows[process.pid]["pgid"] == process.pid, "direct_child_identity_unavailable")
        attributed[process.pid] = {key: rows[process.pid][key] for key in ("pid", "ppid", "pgid", "uid", "start")}
        row["start"] = rows[process.pid]["start"]
        observe_processes(rows)
        for index, pipe in enumerate((process.stdout, process.stderr)):
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, index)
        sampled = time.monotonic()
        while True:
            now = time.monotonic()
            code = process.poll()
            if code is not None and exited_at is None:
                exited_at = now
            if code is not None and all(s["eof"] for s in states) and absent(process.pid):
                break
            if now - sampled >= 0.5:
                observe_processes()
                sampled = now
            if ((interrupted and not cleanup) or now >= deadline or any(s["bytes"] > STREAM_LIMIT for s in states)
                    or exited_at is not None and now - exited_at > 2 and not absent(process.pid)):
                stop(child, "interrupted" if interrupted else "timeout" if now >= deadline else "output_or_group_limit")
            if child["stopAt"] is not None:
                stop(child, child["reason"])
                if now - child["stopAt"] > 11:
                    forced = True
                    break
            for key, _ in selector.select(0.025):
                chunk = os.read(key.fileobj.fileno(), 65536)
                state = states[key.data]
                if not chunk:
                    state["eof"] = True
                    selector.unregister(key.fileobj)
                    continue
                state["bytes"] += len(chunk)
                state["digest"].update(chunk)
                state["data"].extend(chunk[:max(0, STREAM_LIMIT - len(state["data"]))])
    finally:
        selector.close()
        for pipe in (process.stdout, process.stderr):
            pipe.close()
        if process.poll() is None:
            try:
                stop(child, "finally_unreaped")
                process.wait(timeout=5)
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                try:
                    stop(child, "finally_unreaped")
                    process.wait(timeout=5)
                except (OSError, RuntimeError, subprocess.TimeoutExpired):
                    pass
        row.update({"exitCode": process.returncode, "exitObservedAndReaped": process.returncode is not None,
                    "pipesEOF": [s["eof"] for s in states], "streamsClosed": [process.stdout.closed, process.stderr.closed],
                    "originalProcessGroupAbsent": absent(process.pid), "forcedDrain": forced,
                    "signalsSent": list(child["signals"]), "stopReason": child["reason"],
                    "stdout": packed(bytes(states[0]["data"]), states[0]["bytes"], states[0]["digest"].hexdigest(), states[0]["eof"]),
                    "stderr": packed(bytes(states[1]["data"]), states[1]["bytes"], states[1]["digest"].hexdigest(), states[1]["eof"])})
        child["released"] = (row["exitObservedAndReaped"] and row["originalProcessGroupAbsent"]
                             and all(row["pipesEOF"]) and all(row["streamsClosed"]) and not forced)
        row["normallyClosed"] = child["released"] and child["reason"] is None and not child["signals"]
    need(row["normallyClosed"] and all(row[s]["complete"] and row[s]["retained"] for s in ("stdout", "stderr")), "command_lifecycle_failed")
    need(row["exitCode"] in allowed, "command_exit_refused")
    return bytes(states[0]["data"]), bytes(states[1]["data"]), row


def parse_tree(data, index=False, sizes=False):
    result = {}
    for value in data.split(b"\0"):
        if not value:
            continue
        header, raw_name = value.split(b"\t", 1)
        name = raw_name.decode("utf-8", errors="strict")
        need(name and not name.startswith("/") and all(x not in ("", ".", "..") for x in name.split("/"))
             and name not in result, "git_path_invalid")
        parts = header.decode().split()
        if index:
            mode, blob, stage = parts
            need(stage == "0", "git_index_stage")
        else:
            mode, kind, blob = parts[:3]
            need(kind == "blob", "git_entry_type")
        need(mode in ("100644", "100755", "120000") and re.fullmatch(r"[a-f0-9]{40}", blob), "git_entry_mode")
        result[name] = {"mode": mode, "gitBlob": blob}
        if sizes:
            result[name]["bytes"] = int(parts[3])
    return result


def source_file(name):
    file = repo / name
    for parent in file.parents:
        if parent == repo:
            break
        need(parent.is_dir() and not parent.is_symlink(), "source_ancestor_changed")
    info = file.lstat()
    if stat.S_ISLNK(info.st_mode):
        mode, data = "120000", os.fsencode(os.readlink(file))
    else:
        need(stat.S_ISREG(info.st_mode), "source_file_type")
        mode, data = "100755" if info.st_mode & 0o111 else "100644", read(file)
    return {"path": name, "mode": mode, "bytes": len(data), "sha256": sha(data),
            "gitBlob": sha(b"blob " + str(len(data)).encode() + b"\0" + data, "sha1")}


def canonical_base():
    global baseline_tree
    output, _, _ = command("canonical_parent", ["/usr/bin/git", "rev-parse", "HEAD^"])
    need(output.decode().strip() == BASE, "canonical_parent_changed")
    output, _, _ = command("canonical_tree", ["/usr/bin/git", "ls-tree", "-r", "-l", "-z", BASE])
    baseline_tree = parse_tree(output, sizes=True)
    need(len(baseline_tree) == 42 and sum(x["bytes"] for x in baseline_tree.values()) == 396021
         and baseline_tree[ACTIVE] == {"mode": "100644", "gitBlob": BASE_STUB["gitBlob"], "bytes": BASE_STUB["bytes"]}
         and not ADDED.intersection(baseline_tree), "canonical_baseline_changed")
    output, _, _ = command("canonical_tree_id", ["/usr/bin/git", "rev-parse", BASE + "^{tree}"])
    need(output.decode().strip() == BASE_TREE, "canonical_tree_id_changed")
    report["canonicalBaseline"] = {"commit": BASE, "tree": BASE_TREE, "files": 42, "bytes": 396021,
                                   "modifiedPriorPaths": ["AGENTS.md"], "addedPaths": sorted(ADDED),
                                   "inertWorkflowRequiredUnchanged": True}


def guard(label, cleanup=False, post_root=False):
    global source_vector
    item = {"label": label, "passed": False}
    report["guards"].append(item)
    options = {"cleanup": cleanup, "post_root": post_root}
    output, _, _ = command(label + "_head", ["/usr/bin/git", "rev-parse", "HEAD"], **options)
    need(output.decode().strip() == source, "source_head_changed")
    tree, _, _ = command(label + "_tree", ["/usr/bin/git", "ls-tree", "-r", "-z", "HEAD"], **options)
    index, _, _ = command(label + "_index", ["/usr/bin/git", "ls-files", "--stage", "-z"], **options)
    tree, index = parse_tree(tree), parse_tree(index, index=True)
    need(len(tree) == len(index) == 48 and set(tree) == set(baseline_tree) | ADDED, "source_paths_changed")
    vector = []
    for name, expected in sorted(tree.items()):
        actual = source_file(name)
        need({key: actual[key] for key in ("mode", "gitBlob")} == expected == index[name], "source_body_or_index_changed")
        if name in baseline_tree:
            previous = baseline_tree[name]
            need(actual["mode"] == previous["mode"], "source_mode_changed")
            if name == "AGENTS.md":
                need(actual["bytes"] == AGENTS["bytes"] and actual["sha256"] == AGENTS["sha256"], "scoped_agents_changed")
            else:
                need(actual["gitBlob"] == previous["gitBlob"], "prior_source_changed")
        vector.append(actual)
    need(sha(read(repo / ACTIVE)) == BASE_STUB["sha256"] and sha(read(repo / LOCK)) == LOCK_SHA256
         and sha(read(repo / HARNESS)) == HARNESS_SHA256, "pinned_scope_changed")
    for suffix, args in (("status", ["status", "--porcelain=v1", "-z", "--untracked-files=all"]),
                         ("ignored", ["status", "--porcelain=v1", "-z", "--ignored=matching", "--untracked-files=all"])):
        output, _, _ = command(label + "_" + suffix, ["/usr/bin/git", *args], **options)
        need(output == b"", "source_generated_or_dirty")
    command(label + "_diff", ["/usr/bin/git", "-c", "core.filemode=true", "diff", "--no-ext-diff", "--no-textconv", "--quiet", "HEAD", "--"], **options)
    if source_vector is None:
        source_vector = vector
        report["sourceFiles"] = vector
    need(vector == source_vector, "source_vector_changed")
    item.update({"passed": True, "files": len(vector), "bytes": sum(x["bytes"] for x in vector),
                 "vectorSha256": sha(json.dumps(vector, separators=(",", ":")).encode()), "fullHeadIndexNativeBindings": True})


def make_directory(relative):
    owner()
    path = root / relative
    need(not os.path.lexists(path), "owned_directory_not_absent")
    path.mkdir(mode=0o700)
    value = path.lstat()
    known_directories[relative] = (value.st_dev, value.st_ino)
    return path


def owned_write(relative, data, executable=False):
    owner()
    path = root / relative
    need(isinstance(data, bytes) and len(data) <= 2 * 1024**2 and not os.path.lexists(path)
         and path.parent.is_dir() and not path.parent.is_symlink(), "owned_write_arguments")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o700 if executable else 0o600)
    with os.fdopen(descriptor, "wb") as target:
        target.write(data)
        target.flush()
        os.fsync(target.fileno())
    return fingerprint(path)


def export_source():
    global export_vector
    selected = CORE + SERVICES + [HARNESS]
    by_path = {x["path"]: x for x in source_vector}
    for name in selected:
        record = by_path[name]
        need(record["mode"] == "100644", "export_source_mode")
        parent = Path(name).parent
        for current in list(reversed(parent.parents)) + [parent]:
            if str(current) == ".":
                continue
            path = "source/" + str(current)
            if not (root / path).exists():
                make_directory(path)
        value = read(repo / name)
        need(len(value) == record["bytes"] and sha(value) == record["sha256"], "export_source_changed")
        own = owned_write("source/" + name, value)
        export_vector.append({**record, "identity": own})
    report["sourceExport"] = {"files": export_vector, "count": 7, "guards": [],
                               "qualification": "Only two Core files, four actual services and the new harness; copied permissions are owner-only, original Git modes remain recorded."}
    verify_export("before_compile")


def verify_export(label):
    expected = {x["path"] for x in export_vector}
    actual = {str((Path(folder) / name).relative_to(root / "source")) for folder, dirs, files in
              os.walk(root / "source", followlinks=False) for name in files}
    need(actual == expected, "export_path_set_changed")
    for value in export_vector:
        need(fingerprint(root / "source" / value["path"]) == value["identity"], "export_identity_or_bytes_changed")
    report["sourceExport"]["guards"].append({"label": label, "passed": True, "files": len(expected)})


def tree_vector(base):
    owner()
    rows, total = [], 0
    for folder, directories, files in os.walk(base, topdown=True, followlinks=False):
        budget()
        for name in sorted(directories + files):
            path = Path(folder) / name
            info = path.lstat()
            need(info.st_uid == os.getuid(), "tree_owner_changed")
            relative = str(path.relative_to(root))
            value = {"relativePath": relative, **file_identity(info)}
            if stat.S_ISLNK(info.st_mode):
                target = os.readlink(path)
                need((path.parent / target).resolve().is_relative_to(root), "tree_symlink_outside_root")
                value["symlink"] = target
            elif stat.S_ISREG(info.st_mode):
                value = {"relativePath": relative, **fingerprint(path)}
                total += info.st_size
            else:
                need(stat.S_ISDIR(info.st_mode), "unknown_tree_entry")
            rows.append(value)
            need(total <= ROOT_LIMIT and len(rows) <= 100000, "owned_storage_bound")
    return sorted(rows, key=lambda row: row["relativePath"])


def verify_runtime(label):
    need(runtime_vector is not None, "runtime_vector_missing")
    current = tree_vector(root / "runtime")
    need(current == runtime_vector, "runtime_files_changed")
    report.setdefault("runtimeChecks", []).append({"label": label, "passed": True,
        "files": len(current), "vectorSha256": sha(json.dumps(current, separators=(",", ":")).encode())})


def compile_harness():
    global harness_binary
    xcode, _, _ = command("xcode_version", ["/usr/bin/xcodebuild", "-version"])
    swift, _, _ = command("swift_version", ["/usr/bin/xcrun", "swiftc", "--version"])
    sdk, _, _ = command("sdk_version", ["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-version"])
    sdk_path, _, _ = command("sdk_path", ["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-path"])
    need(xcode.decode().strip() == "Xcode 16.4\nBuild version 16F6" and b"Swift version 6.1.2" in swift
         and sdk.decode().strip() == "15.5", "toolchain_profile_changed")
    sdk_path = Path(sdk_path.decode().strip())
    need(sdk_path.is_dir() and sdk_path.resolve().is_relative_to(Path(DEVELOPER)), "sdk_path_outside_selected_xcode")
    report["toolchain"] = {"xcode": xcode.decode().strip(), "swift": swift.decode().strip(), "sdk": "15.5", "sdkPath": str(sdk_path),
                           "target": "arm64-apple-macosx15.0", "swiftLanguageMode": "5"}
    shared = ["/usr/bin/xcrun", "swiftc", "-swift-version", "5", "-target", "arm64-apple-macosx15.0",
              "-sdk", str(sdk_path), "-module-cache-path", str(root / "cache/swift"),
              "-Xcc", "-fmodules-cache-path=" + str(root / "cache/clang"), "-parse-as-library"]
    build = root / "build"
    command("compile_core", [*shared, "-emit-module", "-emit-library", "-module-name", "FindletCore",
                             "-emit-module-path", str(build / "FindletCore.swiftmodule"),
                             *[str(root / "source" / name) for name in CORE], "-o", str(build / "libFindletCore.dylib")], 120)
    harness_binary = build / "KeywordPipelineHarness"
    command("compile_harness", [*shared, "-I", str(build), "-L", str(build), "-lFindletCore",
                                "-Xlinker", "-rpath", "-Xlinker", "@executable_path",
                                *[str(root / "source" / name) for name in SERVICES + [HARNESS]], "-o", str(harness_binary)], 180)
    report["compiledFiles"] = [{"relativePath": str(path.relative_to(root)), **fingerprint(path)}
                              for path in (harness_binary, build / "libFindletCore.dylib", build / "FindletCore.swiftmodule")]
    need(os.access(harness_binary, os.X_OK), "compiled_harness_not_executable")
    verify_export("after_compile")


def verify_compiled(label):
    rows = report.get("compiledFiles", [])
    need(len(rows) == 3, "compiled_files_missing")
    for row in rows:
        current = fingerprint(root / row["relativePath"])
        need(current == {key: value for key, value in row.items() if key != "relativePath"}, "compiled_binary_changed")
    report.setdefault("compiledChecks", []).append({"label": label, "passed": True, "files": 3})


def macho(file):
    descriptor = os.open(file, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        header = os.pread(descriptor, 4096, 0)
    finally:
        os.close(descriptor)
    need(len(header) >= 32, "macho_header_truncated")
    magic = struct.unpack_from("<I", header)[0]
    if magic == 0xfeedfacf:
        cpus = [struct.unpack_from("<I", header, 4)[0]]
    else:
        big = struct.unpack_from(">I", header)[0]
        need(big in (0xcafebabe, 0xcafebabf), "macho_format_required")
        count = struct.unpack_from(">I", header, 4)[0]
        stride = 20 if big == 0xcafebabe else 32
        need(1 <= count <= 8 and 8 + stride * count <= len(header), "macho_fat_bound")
        cpus = [struct.unpack_from(">I", header, 8 + stride * index)[0] for index in range(count)]
    need(0x0100000c in cpus, "macho_arm64_required")
    return {"cpuTypes": cpus, "arm64Present": True, **fingerprint(file)}


def node_archive_header(member):
    return {"name": member.name, "type": member.type.hex(), "bytes": member.size,
            "mode": member.mode, "link": member.linkname,
            "headerOffset": member.offset, "dataOffset": member.offset_data}


def inventory_node_archive(archive):
    prefix = "node-v26.13.0-darwin-arm64"
    inventory = {"complete": False, "extractionStarted": False, "entries": 0, "regularFiles": 0,
                 "regularBytes": 0, "directories": 0, "symbolicLinks": 0, "hardLinks": 0,
                 "limits": {"perRegularMemberBytes": NODE_MEMBER_LIMIT, "totalRegularBytes": NODE_TOTAL_LIMIT,
                            "allMembers": NODE_ENTRY_LIMIT, "pathUtf8Bytes": 4096},
                 "largestRegularMembers": [], "orderedHeaderSha256": None,
                 "proofLimit": "Digest and summary bind decoded tar member headers, not retained original tar-header bytes."}
    report["nodeArchive"]["headerInventory"] = inventory
    headers, seen, digest = [], {}, hashlib.sha256()
    current = None
    try:
        with tarfile.open(archive, "r:gz") as package_archive:
            for member in package_archive:
                budget()
                current = node_archive_header(member)
                encoded = (json.dumps(current, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
                digest.update(encoded)
                inventory["entries"] += 1
                inventory["orderedHeaderSha256"] = digest.hexdigest()
                need(inventory["entries"] <= NODE_ENTRY_LIMIT, "node_archive_entry_count_bound")
                need(len(member.name.encode("utf-8")) <= 4096 and len(member.linkname.encode("utf-8")) <= 4096,
                     "node_archive_name_bound")
                parts = Path(member.name).parts
                need(parts and parts[0] == prefix and all(x not in (".", "..") for x in parts)
                     and not member.name.startswith("/"), "node_archive_path")
                relative = Path(*parts[1:])
                need(relative not in seen, "node_archive_duplicate_path")
                if relative == Path("."):
                    need(member.isdir(), "node_archive_root")
                else:
                    need(relative.parent == Path(".") or seen.get(relative.parent) == "directory",
                         "node_archive_parent_order")
                if member.isdir():
                    kind = "directory"
                    inventory["directories"] += 1
                elif member.isfile():
                    kind = "regular"
                    inventory["regularFiles"] += 1
                    inventory["regularBytes"] += member.size
                    largest = inventory["largestRegularMembers"] + [{"name": member.name, "bytes": member.size}]
                    inventory["largestRegularMembers"] = sorted(largest, key=lambda row: (-row["bytes"], row["name"]))[:8]
                    need(0 <= member.size <= NODE_MEMBER_LIMIT, "node_archive_member_size_bound")
                    need(inventory["regularBytes"] <= NODE_TOTAL_LIMIT, "node_archive_total_size_bound")
                elif member.issym():
                    kind = "symlink"
                    inventory["symbolicLinks"] += 1
                    destination = root / "runtime/node"
                    need(not Path(member.linkname).is_absolute()
                         and (destination / relative.parent / member.linkname).resolve().is_relative_to(destination),
                         "node_archive_link")
                elif member.islnk():
                    kind = "hardlink"
                    inventory["hardLinks"] += 1
                    source_parts = Path(member.linkname).parts
                    need(source_parts and source_parts[0] == prefix and ".." not in source_parts
                         and seen.get(Path(*source_parts[1:])) in ("regular", "hardlink"), "node_archive_hardlink")
                else:
                    need(False, "node_archive_entry_type")
                seen[relative] = kind
                headers.append(sha(encoded))
        need(headers, "node_archive_empty")
        need(fingerprint(archive) == report["nodeArchive"]["file"], "node_archive_changed_during_inventory")
        inventory["complete"] = True
        return headers
    except Exception as error:
        inventory["rejection"] = {"code": finite(error), "ordinal": inventory["entries"],
                                  "regularBytesAtRejection": inventory["regularBytes"]}
        if current is not None:
            inventory["rejection"]["member"] = {**{key: current[key] for key in ("type", "bytes", "headerOffset", "dataOffset")},
                                                "name": current["name"][:512],
                                                "nameSha256": sha(current["name"].encode("utf-8", errors="surrogatepass"))}
        raise


def extract_node(archive):
    destination = root / "runtime/node"
    prefix = "node-v26.13.0-darwin-arm64"
    headers = inventory_node_archive(archive)
    report["nodeArchive"]["headerInventory"]["extractionStarted"] = True
    total, files, entries, links = 0, 0, 0, []
    with tarfile.open(archive, "r:gz") as package_archive:
        for member in package_archive:
            budget()
            encoded = (json.dumps(node_archive_header(member), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
            need(entries < len(headers) and sha(encoded) == headers[entries], "node_archive_header_changed")
            entries += 1
            parts = Path(member.name).parts
            need(parts and parts[0] == prefix and all(x not in (".", "..") for x in parts)
                 and not member.name.startswith("/"), "node_archive_path")
            relative = Path(*parts[1:])
            target = destination / relative
            if relative == Path("."):
                need(member.isdir(), "node_archive_root")
                continue
            need(target.is_relative_to(destination) and target.parent.is_dir()
                 and not target.parent.is_symlink() and not os.path.lexists(target), "node_archive_target")
            if member.isdir():
                target.mkdir(mode=0o700)
            elif member.isfile():
                total += member.size
                files += 1
                need(0 <= member.size <= NODE_MEMBER_LIMIT and total <= NODE_TOTAL_LIMIT and entries <= NODE_ENTRY_LIMIT,
                     "node_archive_size_bound")
                input_file = package_archive.extractfile(member)
                need(input_file is not None, "node_archive_member_unavailable")
                descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                     0o700 if member.mode & 0o111 else 0o600)
                with input_file, os.fdopen(descriptor, "wb") as output:
                    remaining = member.size
                    while remaining:
                        budget()
                        data = input_file.read(min(remaining, 1048576))
                        need(bool(data), "node_archive_member_truncated")
                        output.write(data)
                        remaining -= len(data)
                    need(input_file.read(1) == b"", "node_archive_member_grew")
            elif member.issym():
                need(not Path(member.linkname).is_absolute()
                     and (target.parent / member.linkname).resolve().is_relative_to(destination), "node_archive_link")
                target.symlink_to(member.linkname)
                links.append(target)
            elif member.islnk():
                source_parts = Path(member.linkname).parts
                need(source_parts and source_parts[0] == prefix and ".." not in source_parts, "node_archive_hardlink")
                source_file = destination.joinpath(*source_parts[1:])
                need(source_file.is_file() and not source_file.is_symlink(), "node_archive_hardlink_source")
                os.link(source_file, target, follow_symlinks=False)
            else:
                need(False, "node_archive_entry_type")
    need(entries == len(headers), "node_archive_header_count_changed")
    need(all(path.resolve(strict=True).is_relative_to(destination) for path in links), "node_archive_link_changed")
    need(fingerprint(archive) == report["nodeArchive"]["file"], "node_archive_changed_during_extraction")
    report["nodeArchive"]["headerInventory"]["extractionHeadersMatched"] = True
    report["nodeArchive"].update({"unpackedBytes": total, "regularFiles": files, "symbolicLinks": len(links)})


NATIVE_PROGRAM = r"""
const fs = require('node:fs');
const path = require('node:path');
const {createRequire} = require('node:module');
const tools = process.argv[1];
const ownRequire = createRequire(path.join(tools,'package.json'));
const Database = ownRequire('better-sqlite3');
const vec = ownRequire('sqlite-vec');
let db;
try {
  db = new Database(':memory:');
  vec.load(db);
  const versions = db.prepare('SELECT sqlite_version() AS sqliteVersion, vec_version() AS vecVersion').get();
  const addons = Object.keys(require.cache).filter(x=>x.endsWith('.node'));
  const vector = fs.realpathSync(vec.getLoadablePath());
  const selected = {};
  for(const name of ['@tobilu/qmd','better-sqlite3','sqlite-vec','sqlite-vec-darwin-arm64','node-llama-cpp']) {
    selected[name] = JSON.parse(fs.readFileSync(path.join(tools,'node_modules',name,'package.json'),'utf8')).version;
  }
  db.close();
  process.stdout.write(JSON.stringify({node:process.version,platform:process.platform,architecture:process.arch,
    modules:process.versions.modules,napi:process.versions.napi,versions,addons,
    vector,selected,databaseClosed:db.open===false}));
} finally {
  if(db?.open) db.close();
}
"""


def install_runtime():
    global node, package, runtime_vector
    archive = root / "runtime/node.tar.gz"
    command("download_pinned_node", ["/usr/bin/curl", "--disable", "--fail", "--show-error", "--location", "--max-redirs", "0",
             "--proto", "=https", "--connect-timeout", "10", "--max-time", "120", "--max-filesize", str(64 * 1024**2),
             "--output", str(archive), NODE_URL], 130)
    report["nodeArchive"] = {"url": NODE_URL, "expectedSha256": NODE_SHA256, "file": fingerprint(archive)}
    need(report["nodeArchive"]["file"]["sha256"] == NODE_SHA256, "node_archive_hash_changed")
    extract_node(archive)
    node = root / "runtime/node/bin/node"
    npm = root / "runtime/node/lib/node_modules/npm/bin/npm-cli.js"
    report["nodeBinary"] = macho(node)
    env["PATH"] = str(node.parent) + ":/usr/bin:/bin:/usr/sbin:/sbin"
    output, error, _ = command("node_version", [str(node), "--version"])
    need(output == b"v26.13.0\n" and error == b"", "node_version_changed")
    output, error, _ = command("npm_version", [str(node), str(npm), "--version"])
    need(output == b"11.20.0\n" and error == b"", "npm_version_changed")
    raw_lock = read(repo / LOCK, 262144)
    need(sha(raw_lock) == LOCK_SHA256, "runtime_lock_source_changed")
    lock = strict_json(raw_lock)
    dependencies = {"@tobilu/qmd": "2.8.3", "better-sqlite3": "13.0.3", "sqlite-vec": "0.1.9", "sqlite-vec-darwin-arm64": "0.1.9"}
    need(lock["lockfileVersion"] == 3 and lock["name"] == "findlet-qmd-owned-ci"
         and lock["packages"][""]["dependencies"] == dependencies, "runtime_lock_roots_changed")
    for name, value in lock["packages"].items():
        if not name:
            continue
        url = urllib.parse.urlsplit(value["resolved"])
        need(url.scheme == "https" and url.hostname == "registry.npmjs.org" and url.port is None
             and not url.username and not url.password and not url.query and not url.fragment
             and value["integrity"].startswith("sha512-"), "runtime_lock_resolution_not_pinned")
    manifest = {"name": lock["name"], "version": "0.0.0", "private": True, "dependencies": dependencies}
    tools = root / "runtime/tools"
    owned_write("runtime/tools/package.json", (json.dumps(manifest, indent=2) + "\n").encode())
    owned_write("runtime/tools/package-lock.json", raw_lock)
    report["runtimeLock"] = {"sourcePath": LOCK, "original": packed(raw_lock, len(raw_lock), sha(raw_lock), True),
                             "sha256": sha(raw_lock), "bytes": len(raw_lock), "packages": len(lock["packages"])}
    need(report["runtimeLock"]["original"]["retained"] is True
         and report["runtimeLock"]["original"]["complete"] is True, "runtime_lock_original_not_retained")
    command("runtime_frozen_install", [str(node), str(npm), "ci", "--ignore-scripts", "--omit=optional",
                                      "--no-audit", "--no-fund", "--progress=false"], 300, cwd=tools)
    need(read(tools / "package-lock.json", 262144) == raw_lock, "runtime_install_rewrote_lock")
    scope = tools / "node_modules/@node-llama-cpp"
    need(not scope.exists() or not list(scope.iterdir()), "optional_model_binary_package_installed")
    output, _, _ = command("runtime_resolved_tree", [str(node), str(npm), "ls", "--all", "--json"], 60, cwd=tools)
    tree = strict_json(output)
    report["runtimeTree"] = tree
    installed = []
    for name, expected in lock["packages"].items():
        if not name or expected.get("optional") is True:
            continue
        path = tools / name / "package.json"
        value = strict_json(read(path, 1048576))
        need(value["version"] == expected["version"], "installed_locked_version_changed")
        installed.append({"path": name, "version": value["version"], "resolved": expected["resolved"],
                          "integrity": expected["integrity"], "manifestSha256": fingerprint(path)["sha256"]})
    report["installedLockedPackages"] = installed
    output, error, _ = command("darwin_native_admission", [str(node), "-e", NATIVE_PROGRAM, str(tools)])
    value = strict_json(output)
    report["nativeAdmission"] = {"value": value, "accepted": False}
    addon = tools / "node_modules/better-sqlite3/prebuilds/darwin-arm64.node"
    extension = Path(value["vector"])
    vector_root = tools / "node_modules/sqlite-vec-darwin-arm64"
    need(error == b"" and value["node"] == "v26.13.0" and value["platform"] == "darwin"
         and value["architecture"] == "arm64" and value["databaseClosed"] is True
         and value["addons"] == [str(addon)] and extension.resolve(strict=True).is_relative_to(vector_root.resolve(strict=True))
         and value["versions"]["vecVersion"] == "v0.1.9"
         and value["selected"] == {**dependencies, "node-llama-cpp": "3.20.0"}, "darwin_native_admission_failed")
    report["nativeAdmission"].update({"accepted": True, "betterSqlite": macho(addon), "sqliteVec": macho(extension)})
    package = tools / "node_modules/@tobilu/qmd"
    need(package.is_dir() and (package / "dist/cli/qmd.js").is_file() and (package / "dist/index.js").is_file(), "qmd_installed_entries_missing")
    runtime_vector = tree_vector(root / "runtime")
    report["runtimeFiles"] = runtime_vector
    verify_runtime("after_admission")


def preflight():
    global root, root_identity, marker_identity, nonce, env, work_end, job_end, baseline_processes
    need(re.fullmatch(r"[a-f0-9]{40}", source or "") and re.fullmatch(r"[a-f0-9]{64}", HARNESS_SHA256)
         and re.fullmatch(r"[a-f0-9]{64}", LOCK_SHA256), "reviewed_source_and_payload_pins_required")
    need(platform.system() == "Darwin" and platform.machine() == "arm64"
         and platform.mac_ver()[0].split(".")[0] == "15" and sys.version_info >= (3, 11)
         and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, "isolated_macos15_arm64_required")
    need(os.environ.get("CI") == "true" and os.environ.get("GITHUB_ACTIONS") == "true"
         and os.environ.get("GITHUB_REPOSITORY") == REPOSITORY and os.environ.get("GITHUB_REF") == BRANCH
         and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and os.environ.get("SOURCE_COMMIT") == source
         and os.environ.get("FINDLET_PUBLIC_REPOSITORY") == "true", "approved_public_ci_required")
    event = strict_json(read(os.environ["GITHUB_EVENT_PATH"], 262144))
    need(event.get("repository", {}).get("private") is False
         and event.get("repository", {}).get("full_name") == REPOSITORY
         and event.get("inputs", {}) in ({}, None)
         and event.get("ref", BRANCH) in (BRANCH, BRANCH.removeprefix("refs/heads/")), "approved_dispatch_event_required")
    started = os.environ.get("FINDLET_KEYWORD_JOB_STARTED_MS", "")
    need(re.fullmatch(r"[0-9]{13}", started or ""), "earliest_job_clock_required")
    now, monotonic = time.time(), time.monotonic()
    started = int(started) / 1000
    need(started <= now and now - started < 1200, "earliest_job_clock_invalid")
    allowed = min(WORK_SECONDS, started + 1200 - CLEANUP_SECONDS - MARGIN_SECONDS - now)
    need(allowed >= 300, "remaining_job_window_unavailable")
    work_end, job_end = monotonic + allowed, monotonic + started + 1200 - now
    report["timing"] = {"earliestStepEpochMs": int(started * 1000), "entryEpochMs": round(now * 1000),
                        "setupElapsedMs": round((now - started) * 1000), "admittedWorkMs": round(allowed * 1000),
                        "cleanupReservedMs": CLEANUP_SECONDS * 1000, "marginReservedMs": MARGIN_SECONDS * 1000}
    home = os.environ.get("HOME", "")
    need(Path(home).is_absolute() and Path(home).is_dir() and Path(DEVELOPER).is_dir(), "host_profile_unavailable")
    parent = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    need(parent.is_dir() and parent.is_absolute() and repo not in parent.parents and parent != repo, "runner_temp_invalid")
    root = Path(tempfile.mkdtemp(prefix="fk-", dir=parent))
    root.chmod(0o700)
    info = root.lstat()
    root_identity = (info.st_dev, info.st_ino)
    nonce = os.urandom(16).hex()
    descriptor = os.open(root / ".owner", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as target:
        target.write(nonce.encode())
    marker = (root / ".owner").lstat()
    marker_identity = (marker.st_dev, marker.st_ino)
    for name in ("source", "build", "runtime", "tmp", "cache", "config", "runtime/node", "runtime/tools",
                 "cache/swift", "cache/clang", "cache/npm", "cache/xdg", "cache/data", "cache/state"):
        make_directory(name)
    for name in ("npmrc", "global-npmrc"):
        owned_write("config/" + name, b"")
    env = {"HOME": home, "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "en_US.UTF-8", "LC_ALL": "C", "TZ": "UTC",
           "CI": "true", "DEVELOPER_DIR": DEVELOPER, "TMPDIR": str(root / "tmp") + "/", "TMP": str(root / "tmp"),
           "TEMP": str(root / "tmp"), "XDG_CONFIG_HOME": str(root / "config"), "XDG_CACHE_HOME": str(root / "cache/xdg"),
           "XDG_DATA_HOME": str(root / "cache/data"), "XDG_STATE_HOME": str(root / "cache/state"),
           "SWIFTPM_MODULECACHE_OVERRIDE": str(root / "cache/swift"), "CLANG_MODULE_CACHE_PATH": str(root / "cache/clang"),
           "NPM_CONFIG_CACHE": str(root / "cache/npm"), "NPM_CONFIG_USERCONFIG": str(root / "config/npmrc"),
           "NPM_CONFIG_GLOBALCONFIG": str(root / "config/global-npmrc"), "NPM_CONFIG_REGISTRY": "https://registry.npmjs.org/",
           "NPM_CONFIG_IGNORE_SCRIPTS": "true", "NPM_CONFIG_AUDIT": "false", "NPM_CONFIG_FUND": "false",
           "NPM_CONFIG_UPDATE_NOTIFIER": "false", "NODE_LLAMA_CPP_SKIP_DOWNLOAD": "true", "NO_COLOR": "1",
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
           "SOURCE_COMMIT": source, "FINDLET_QMD_KEYWORD_NONCE": nonce}
    owner()
    baseline_processes = {pid: value["start"] for pid, value in process_snapshot().items()}
    report["runtime"] = {"macOS": platform.mac_ver()[0], "architecture": platform.machine(), "python": platform.python_version(),
                         "homePreserved": env["HOME"] == home, "environmentKeys": sorted(env)}
    canonical_base()
    guard("before_setup")
    export_source()


def phase(name):
    output, error, row = command("harness_" + name, [str(harness_binary), "--phase", name,
                                "--root", str(root), "--node", str(node), "--qmd", str(package)], 180,
                                cwd=root, allowed=(0, 1, 2))
    marker = b"FINDLET_QMD_KEYWORD_RESULT="
    need(output.startswith(marker) and output.endswith(b"\n") and output.count(marker) == 1, "harness_result_marker")
    value = strict_json(output[len(marker):-1])
    report["phases"].append(value)
    need(row["exitCode"] == 0 and error == b"" and value.get("schemaVersion") == 1
         and value.get("sourceCommit") == source and value.get("phase") == name
         and value.get("case") == ("K01" if name == "index" else "K02") and value.get("accepted") is True,
         "harness_phase_failed")
    need(value.get("errors") == [] and type(value.get("checks")) is dict
         and set(value["checks"]) == (INDEX_CHECKS if name == "index" else LIFECYCLE_CHECKS)
         and all(item is True for item in value["checks"].values()), "harness_checks_failed")
    need(value.get("engineRootRelative") == "engine" and value.get("fixtureRootRelative") == "authored"
         and [row["stage"] for row in value["stageEvents"]] == STAGES[name]
         and all(type(row["elapsedMs"]) is int and 0 <= row["elapsedMs"] <= 180000 for row in value["stageEvents"])
         and [row["elapsedMs"] for row in value["stageEvents"]] == sorted(row["elapsedMs"] for row in value["stageEvents"]),
         "harness_stage_sequence")
    validate_harness(value)
    return value


def swift_identity(current):
    return {"device": current["device"], "inode": current["inode"], "uid": current["uid"], "mode": current["mode"],
            "bytes": current["bytes"], "mtimeSeconds": str(int(current["mtimeNs"]) // 1000000000),
            "mtimeNanoseconds": str(int(current["mtimeNs"]) % 1000000000),
            "ctimeSeconds": str(int(current["ctimeNs"]) // 1000000000),
            "ctimeNanoseconds": str(int(current["ctimeNs"]) % 1000000000)}


def validate_file_proof(value, relative, *, label=None):
    path = root / relative
    before = path.lstat()
    if stat.S_ISLNK(before.st_mode):
        target = os.readlink(path)
        need(value["kind"] == "symlink" and target == value.get("linkTargetRelative")
             and sha(os.fsencode(target)) == value["sha256"] and file_identity(path.lstat()) == file_identity(before),
             "harness_symlink_proof")
        current = file_identity(before)
    else:
        need(value["kind"] == "regular" and "linkTargetRelative" not in value, "harness_regular_kind")
        current = fingerprint(path)
        need(current["sha256"] == value["sha256"], "harness_file_hash_mismatch")
    need(value["relativePath"] == (label or relative) and value["identity"] == swift_identity(current),
         "harness_file_identity_mismatch")


def validate_harness(value):
    expected_names = set(FIXTURE_FILES) | {"authored/outside-link.md"}
    files = value["expectedFiles"]
    need(len(files) == 6 and {row["relativePath"] for row in files} == expected_names, "harness_original_set")
    for row in files:
        relative = row["relativePath"]
        validate_file_proof(row, relative)
        if relative in FIXTURE_FILES:
            size, digest = FIXTURE_FILES[relative]
            need(row["identity"]["bytes"] == size and row["sha256"] == digest and row["identity"]["mode"] == "0600",
                 "harness_authored_bytes_changed")
        else:
            need(row["linkTargetRelative"] == "../decoy/outside.md", "harness_decoy_link_changed")
    runtime = value["runtime"]
    roles = {"node": (str(node.relative_to(root)), "selected-node"),
             "packageJSON": (str((package / "package.json").relative_to(root)), "selected-qmd-package-json"),
             "cliEntry": (str((package / "dist/cli/qmd.js").relative_to(root)), "selected-qmd-cli"),
             "sdk": (str((package / "dist/index.js").relative_to(root)), "selected-qmd-sdk")}
    need(set(runtime) == set(roles), "harness_runtime_roles")
    for role, (relative, label) in roles.items():
        validate_file_proof(runtime[role], relative, label=label)
    state, pointer = value["state"], value["pointer"]
    generation = str(uuid.UUID(pointer["generation"]))
    prefix = "engine/generations/" + generation
    need(pointer["version"] == state["version"] == 1 and pointer["generation"] == state["generation"] == generation
         and state["documentCount"] == 3 and state["embeddingReady"] is False and state["documents"] == DOCUMENTS
         and state["corpusRelative"] == prefix + "/corpus" and state["databaseRelative"] == prefix + "/index.sqlite"
         and state["configRelative"] == prefix + "/config/findlet.yml", "harness_document_mapping")
    proof = value["proofFile"]
    validate_file_proof(proof, "ledger/index-proof.json")
    if value["phase"] == "index":
        validate_file_proof(pointer["file"], "engine/current.json")
        validate_file_proof(state["file"], prefix + "/state.json")
    else:
        first = report["phases"][0]
        need(pointer == first["pointer"] and state == first["state"] and runtime == first["runtime"]
             and proof == first["proofFile"] and env["FINDLET_QMD_KEYWORD_INDEX_PROOF_SHA256"] == proof["sha256"],
             "harness_prior_session_binding")
        previous = {row["relativePath"]: row for row in first["expectedFiles"]}
        for row in files:
            before = previous[row["relativePath"]]
            if row["relativePath"] == "authored/alpha.md":
                left, right = dict(row["identity"]), dict(before["identity"])
                for key in ("ctimeSeconds", "ctimeNanoseconds"):
                    left.pop(key); right.pop(key)
                need(left == right and row["sha256"] == before["sha256"], "harness_same_inode_roundtrip")
            else:
                need(row == before, "harness_unrelated_source_changed")
    queries = value["queryProofs"]
    need(len(queries) == (2 if value["phase"] == "index" else 4), "harness_query_count")
    for number, row in enumerate(queries):
        document = DOCUMENTS[number % 2]
        size, digest = FIXTURE_FILES["authored/" + document["relativePath"]]
        need(row["ordinal"] == number % 2 + 1 and row["documentID"] == document["id"]
             and row["relativePath"] == document["relativePath"] and row["sourceBytes"] == size and row["sourceSHA256"] == digest
             and type(row["snippetBytes"]) is int and 0 < row["snippetBytes"] <= 65536
             and re.fullmatch(r"[a-f0-9]{64}", row["snippetSHA256"]) and type(row["line"]) is int and row["line"] >= 1
             and row["scoreFinite"] is True and row["resolvedExactOwnedOriginal"] is True, "harness_query_binding")


def independent_index_audit(index):
    owner()
    pointer_file = root / "engine/current.json"
    pointer_before = fingerprint(pointer_file)
    pointer = strict_json(read(pointer_file, 4096))
    need(set(pointer) == {"version", "generation"} and type(pointer["version"]) is int and pointer["version"] == 1,
         "index_pointer_schema")
    generation = str(uuid.UUID(pointer["generation"]))
    directory = root / "engine/generations" / generation
    state_file = directory / "state.json"
    state = strict_json(read(state_file, 4 * 1024**2))
    manifest = state["manifest"]
    documents, folders = manifest["documents"], manifest["folders"]
    need(type(manifest["version"]) is int and manifest["version"] == 1 and str(uuid.UUID(manifest["generation"])) == generation
         and len(documents) == 3 and len({d["id"] for d in documents}) == 3 and len(folders) == 1
         and all(d["folderID"] == folders[0]["id"] for d in documents) and manifest["embeddingReady"] is False,
         "index_manifest_schema")
    snapshots = {str(uuid.UUID(d["id"])) + ".md": d for d in documents}
    corpus = directory / "corpus"
    need({p.name for p in corpus.iterdir()} == set(snapshots), "index_corpus_file_set")
    config_file = directory / "config/findlet.yml"
    config = strict_json(read(config_file, 65536))
    need(config == {"collections": {"findlet_documents": {"path": str(corpus), "pattern": "**/*.md", "includeByDefault": True}}},
         "index_curated_configuration")
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = directory / ("index.sqlite" + suffix)
        need(not os.path.lexists(sidecar) or sidecar.is_file() and not sidecar.is_symlink() and sidecar.stat().st_size == 0,
             "index_uncheckpointed_sidecar")
    before = tree_vector(root / "engine")
    database = directory / "index.sqlite"
    uri = "file:" + urllib.parse.quote(str(database), safe="/") + "?mode=ro&immutable=1"
    sql = "SELECT d.collection,d.path,d.hash,c.hash AS content_hash FROM documents d LEFT JOIN content c ON c.hash=d.hash WHERE d.active=1 ORDER BY d.collection,d.path;"
    output, error, _ = command("independent_readonly_index", ["/usr/bin/sqlite3", "-readonly", "-json", uri, sql])
    rows = strict_json(output)
    need(error == b"" and len(rows) == 3 and {r["path"] for r in rows} == set(snapshots)
         and all(r["collection"] == "findlet_documents" and re.fullmatch(r"[a-f0-9]{64}", r["hash"])
                 and r["content_hash"] == r["hash"] for r in rows), "independent_index_metadata_mismatch")
    corpus_rows = [{"snapshotName": name, "documentID": document["id"], "relativePath": document["relativePath"],
                    "title": document["title"], "file": fingerprint(corpus / name)} for name, document in sorted(snapshots.items())]
    observed_documents = [{"id": str(uuid.UUID(d["id"])), "folderID": str(uuid.UUID(d["folderID"])),
                           "relativePath": d["relativePath"], "snapshotName": str(uuid.UUID(d["id"])) + ".md", "title": d["title"]}
                          for d in documents]
    need(observed_documents == DOCUMENTS and index["state"]["generation"] == generation, "independent_document_contract")
    for row in corpus_rows:
        size, digest = FIXTURE_FILES["authored/" + row["relativePath"]]
        need(row["file"]["bytes"] == size and row["file"]["sha256"] == digest, "corpus_bytes_differ_from_original")
    need(tree_vector(root / "engine") == before and fingerprint(pointer_file) == pointer_before,
         "readonly_audit_changed_index")
    proof = root / "ledger/index-proof.json"
    value = fingerprint(proof)
    need(value["mode"] == "0600" and value["sha256"] == index["proofFile"]["sha256"], "index_proof_mode_or_hash")
    env["FINDLET_QMD_KEYWORD_INDEX_PROOF_SHA256"] = value["sha256"]
    report["independentIndexAudit"] = {"accepted": True, "generation": generation, "documents": corpus_rows,
                                       "database": fingerprint(database), "configurationSha256": fingerprint(config_file)["sha256"],
                                       "pointer": pointer_before, "stateSha256": fingerprint(state_file)["sha256"],
                                       "rows": rows, "proofFile": value, "immutableReadOnly": True,
                                       "engineTreeUnchanged": True}


def independent_empty_audit():
    owner()
    engine = root / "engine"
    need(not os.path.lexists(engine / "current.json")
         and {p.name for p in engine.iterdir()} == {"engine.lock", "generations", "cache"}
         and not list((engine / "generations").iterdir()) and not list((engine / "cache").iterdir()),
         "forgotten_engine_not_empty")
    need((engine / "engine.lock").is_file() and not (engine / "engine.lock").is_symlink(), "engine_lock_changed")
    report["independentEmptyAudit"] = {"accepted": True, "currentPointerAbsent": True,
                                       "generationsEmpty": True, "cacheEmpty": True, "lockFileRetained": True}


def cleanup():
    global cleanup_end
    if root is None:
        report["scratchCleanup"] = "not_created"
        return
    cleanup_end = min(time.monotonic() + CLEANUP_SECONDS, job_end - MARGIN_SECONDS)
    try:
        for child in children:
            if child["process"].poll() is None or not absent(child["process"].pid):
                stop(child, "cleanup_remaining")
        until = min(cleanup_end - 15, time.monotonic() + 12)
        while time.monotonic() < until:
            for child in children:
                if child["process"].poll() is None or not absent(child["process"].pid):
                    stop(child, "cleanup_remaining")
            _, live, unknown = observe_processes()
            if not live and not unknown and all(child["process"].poll() is not None and absent(child["process"].pid) for child in children):
                break
            time.sleep(0.05)
        for child in children:
            if child["process"].poll() is not None:
                child["process"].wait(timeout=0.1)
        _, live, unknown = observe_processes()
        report["processCleanup"] = {"observedOwnedProcesses": list(attributed.values()),
                                    "remaining": [{k: p[k] for k in ("pid", "ppid", "pgid", "uid", "start")} for p in live],
                                    "unknownRootReferences": [{k: p[k] for k in ("pid", "ppid", "pgid", "uid", "start")} for p in unknown],
                                    "signalsSent": [s for child in children for s in child["signals"]]}
        need(not live and not unknown and all(child["process"].returncode is not None and absent(child["process"].pid) for child in children),
             "process_closure_unverified")
        owner()
        if export_vector:
            verify_export("before_cleanup")
        if runtime_vector is not None:
            verify_runtime("before_cleanup")
        guard("before_cleanup", cleanup=True)
        allowed = {".owner", "source", "build", "runtime", "tmp", "cache", "config", "authored", "decoy", "engine", "ledger", "quarantine"}
        need({p.name for p in root.iterdir()} <= allowed, "unclassified_scratch_entry_preserved")
        inventory = tree_vector(root)
        for relative, expected in known_directories.items():
            info = (root / relative).lstat()
            need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                 and (info.st_dev, info.st_ino) == expected, "scratch_directory_identity_changed")
        report["scratchInventory"] = {"entries": len(inventory), "regularBytes": sum(r["bytes"] for r in inventory if "sha256" in r),
                                       "vectorSha256": sha(json.dumps(inventory, separators=(",", ":")).encode()),
                                       "knownDirectoryIdentitiesVerified": len(known_directories)}
        owner()
        _, live, unknown = observe_processes()
        need(not live and not unknown and all(child["process"].returncode is not None and absent(child["process"].pid) for child in children),
             "predelete_process_closure_unverified")
        report["processCleanup"]["predeleteZeroObserved"] = True
        shutil.rmtree(root)
        need(not os.path.lexists(root), "scratch_remaining")
        report["scratchCleanup"] = "passed"
        guard("after_cleanup", cleanup=True, post_root=True)
        _, live, unknown = observe_processes()
        need(not live and not unknown and all(child["process"].returncode is not None and absent(child["process"].pid) for child in children),
             "final_process_closure_unverified")
        report["processCleanup"].update({"observedOwnedProcesses": list(attributed.values()), "remaining": [],
                                         "unknownRootReferences": [], "finalZeroObserved": True})
    except Exception as error:
        report["scratchCleanup"] = "unverified"
        report["errors"].append(finite(error))


def main():
    completed = False
    def interrupt(_number, _frame):
        global interrupted
        interrupted = True
    for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(number, interrupt)
    try:
        preflight()
        compile_harness()
        install_runtime()
        verify_compiled("after_runtime_setup")
        guard("after_setup")
        first = phase("index")
        independent_index_audit(first)
        verify_export("after_index")
        verify_runtime("after_index")
        verify_compiled("after_index")
        guard("after_index")
        phase("lifecycle")
        independent_empty_audit()
        verify_export("after_lifecycle")
        verify_runtime("after_lifecycle")
        verify_compiled("after_lifecycle")
        guard("after_lifecycle")
        completed = True
    except Exception as error:
        report["errors"].append(finite(error))
        report["errorType"] = type(error).__name__
        tb = error.__traceback__
        while tb is not None and tb.tb_next is not None:
            tb = tb.tb_next
        report["errorLocation"] = None if tb is None else {"file": Path(tb.tb_frame.f_code.co_filename).name, "line": tb.tb_lineno}
    finally:
        cleanup()
    report["accepted"] = bool(completed and not report["errors"] and not interrupted
                              and len(report["phases"]) == 2 and len(report["guards"]) == 6
                              and all(g["passed"] for g in report["guards"])
                              and all(c.get("normallyClosed") and c.get("exitCode") == 0 for c in report["commands"])
                              and not any(child["signals"] for child in children) and report.get("scratchCleanup") == "passed")
    report["status"] = "passed" if report["accepted"] else "failed"
    output = json.dumps(report, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()
    need(len(output) <= REPORT_LIMIT, "report_bound")
    signal.signal(signal.SIGALRM, lambda *_: os._exit(1))
    signal.setitimer(signal.ITIMER_REAL, 2)
    sys.stdout.buffer.write(b"FINDLET_QMD_KEYWORD_INTEGRATION_RESULT=" + output + b"\n")
    sys.stdout.buffer.flush()
    signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
