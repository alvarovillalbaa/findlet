#!/usr/bin/env python3
"""Real, app-less local inference in owned public macOS CI. Never run locally.

Reuse the hash-pinned keyword supervisor's generic file/process/archive helpers.
Its preflight, main, installer and keyword/diagnostic journeys are never called.
This profile supplies its own source, native-model, phase and cleanup contracts.
"""
import base64
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import stat
import struct
import sys
import tempfile
import time
import uuid

BASE = "ce70e75c0b5a55195049565ca9e6a13ebacc5614"
BRANCH = "refs/heads/qa/findlet-qmd-semantic-20261111-5"
HELPER = "Tests/scripts/run-keyword-integration.py"
HELPER_SHA = "6e860f582ded76240c03dd188448571b433b06722a29708093e2db5d95bd9981"
HARNESS = "Tests/integration/SemanticPipelineHarness.swift"
LOCK = "Tests/fixtures/qmd-darwin-arm64-semantic-package-lock.json"
LOCK_SHA = "9561987453ecc5c41a5fa41935980c109016121c37103a592f4f7ffb3e1dfa35"
MODELS = "Tests/fixtures/qmd-semantic-models.json"
ADDED = {HARNESS, LOCK, MODELS, "Tests/scripts/run-semantic-integration.py",
         "docs/proposals/qmd-semantic-integration.md",
         "docs/proposals/qmd-semantic-integration.workflow.yml.example"}
APPENDED = {"AGENTS.md", "Tests/README.md"}
DOCUMENTS = {
    "doc-a.md": b"# Orbital mechanics\nGravity attracts a spacecraft toward Earth. Its sideways velocity continually carries it forward as it falls, producing a stable orbit around the planet. A satellite remains in orbit through the balance of gravitational acceleration and tangential motion.\n",
    "doc-b.md": b"# Bread fermentation\nYeast consumes sugars in bread dough and releases carbon dioxide gas. Gluten traps the bubbles so the dough expands during proofing. Warmth and time support fermentation before the loaf is baked in an oven.\n",
    "doc-c.md": b"# Computer networking\nComputers exchange messages as packets across a network. Routers forward traffic using destination addresses, and transport protocols coordinate delivery between devices. Ethernet and wireless links carry these digital communications.\n",
}
PRIVATE = tuple(DOCUMENTS.values()) + tuple(
    piece for body in DOCUMENTS.values() for line in body.splitlines()
    for piece in line.split(b". ") if len(piece) >= 24
) + (
    b"What keeps a satellite circling the planet?", b"Why does dough rise before baking?",
    b"How can two computers exchange messages over a network?",
)
SOURCE = sys.argv[2] if len(sys.argv) == 3 and sys.argv[1] == "--source-commit" else None
REPO = Path.cwd().resolve()
raw_helper = (REPO / HELPER).read_bytes()
if hashlib.sha256(raw_helper).hexdigest() != HELPER_SHA:
    raise SystemExit("semantic_supervisor_support_changed")
spec = importlib.util.spec_from_file_location("findlet_owned_support", REPO / HELPER)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
g.HARNESS, g.ROOT_LIMIT = HARNESS, 6 * 1024**3
g.repo, g.source = REPO, SOURCE
g.report = {"schemaVersion": "findlet.qmd-semantic-integration.v1", "sourceCommit": SOURCE,
            "canonicalBaseCommit": BASE, "status": "failed", "accepted": False, "productAccepted": False,
            "commands": [], "guards": [], "sourceFiles": [], "phases": [], "errors": [],
            "scope": {"cases": ["S01", "S02"], "actualLocalInference": True, "appUI": False,
                      "privateFolders": False, "oldCasesRepeated": False, "modelRedistribution": False,
                      "providerAPI": False, "paidService": False},
            "proofLimits": [
                "Two authored app-less journeys; no general retrieval-quality, UI, permission, private-folder or trusted-distribution acceptance.",
                "Production QMD discards its inner stderr. Only bounded outer harness and independent-observer streams are retained here.",
                "QMD force-CPU may load the packaged Metal backend with model GPU layers zero. This is not CPU-only binary or strict offline proof.",
                "Owned PID/start/UID and file/hash observations are boundary checks, not continuous host-wide or external-runner teardown attestation.",
            ]}
need, sha, read = g.need, g.sha, g.read
source_vector = None
fixtures_vector = models_vector = None
known = {}
base_clean = g.clean
g.clean = lambda value: base_clean(value).replace(g.nonce, "[owner-nonce]") if g.nonce else base_clean(value)


def privacy_scan():
    bad = False
    for row in g.report["commands"]:
        for key in ("stdout", "stderr"):
            stream = row.get(key, {})
            if stream.get("encoding") == "gzip-base64" and "data" in stream:
                body = gzip.decompress(base64.b64decode(stream["data"], validate=True))
                if any(token in body for token in PRIVATE):
                    stream.pop("data", None)
                    stream.update({"encoding": "withheld", "retained": False, "privacyScanPassed": False})
                    bad = True
                else:
                    stream["privacyScanPassed"] = True
    return not bad


def command(*args, **kwargs):
    try:
        result = g.command(*args, **kwargs)
        if g.root is not None and g.root.exists():
            g.owner()
            total, entries = 0, 0
            for folder, dirs, files in os.walk(g.root, followlinks=False):
                for name in dirs + files:
                    info = (Path(folder) / name).lstat()
                    total += info.st_size if stat.S_ISREG(info.st_mode) else 0
                    entries += 1
                    need(total <= g.ROOT_LIMIT and entries <= 100000, "owned_storage_bound")
            need(shutil.disk_usage(g.root).free >= 2 * 1024**3, "remote_disk_reserve_exhausted")
            g.report.setdefault("storageObservations", []).append({"label": args[0], "regularBytes": total, "entries": entries})
        return result
    finally:
        need(privacy_scan(), "authored_text_detected_in_output")


def guard(label, cleanup=False, post_root=False):
    global source_vector
    options = {"cleanup": cleanup, "post_root": post_root}
    out, _, _ = command(label + "_head", ["/usr/bin/git", "rev-parse", "HEAD"], **options)
    need(out.decode().strip() == SOURCE, "source_head_changed")
    out, _, _ = command(label + "_tree", ["/usr/bin/git", "ls-tree", "-r", "-z", "HEAD"], **options)
    tree = g.parse_tree(out)
    out, _, _ = command(label + "_index", ["/usr/bin/git", "ls-files", "--stage", "-z"], **options)
    need(g.parse_tree(out, index=True) == tree, "source_index_changed")
    out, _, _ = command(label + "_base", ["/usr/bin/git", "ls-tree", "-r", "-z", BASE], **options)
    baseline = g.parse_tree(out)
    need(set(tree) == set(baseline) | ADDED and not set(baseline) & ADDED, "source_scope_paths")
    vector = []
    for name, expected in sorted(tree.items()):
        current = g.source_file(name)
        need({k: current[k] for k in ("mode", "gitBlob")} == expected, "source_native_bytes_changed")
        if name in baseline and name not in APPENDED:
            need(expected == baseline[name], "prior_source_changed")
        vector.append(current)
    for name in APPENDED:
        out, _, _ = command(label + "_original_" + name.replace("/", "_"), ["/usr/bin/git", "show", BASE + ":" + name], **options)
        need(read(REPO / name).startswith(out), "prior_instruction_or_test_docs_overwritten")
    for suffix, extra in (("status", []), ("ignored", ["--ignored=matching"])):
        out, _, _ = command(label + "_" + suffix, ["/usr/bin/git", "status", "--porcelain=v1", "-z", "--untracked-files=all", *extra], **options)
        need(out == b"", "source_dirty_or_generated")
    if source_vector is None:
        source_vector = vector
        g.source_vector = vector
        g.report["sourceFiles"] = vector
    need(source_vector == vector, "source_vector_changed")
    g.report["guards"].append({"label": label, "passed": True, "files": len(vector),
                               "bytes": sum(x["bytes"] for x in vector), "vectorSha256": sha(json.dumps(vector, sort_keys=True).encode())})


def directory(name):
    value = g.make_directory(name)
    known[name] = (value.lstat().st_dev, value.lstat().st_ino)
    return value


def preflight():
    need(platform.system() == "Darwin" and platform.machine() == "arm64" and platform.mac_ver()[0].split(".")[0] == "15"
         and sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
         "isolated_macos15_arm64_required")
    need(re.fullmatch(r"[0-9a-f]{40}", SOURCE or "") and os.environ.get("CI") == "true"
         and os.environ.get("GITHUB_ACTIONS") == "true" and os.environ.get("GITHUB_REPOSITORY") == g.REPOSITORY
         and os.environ.get("GITHUB_REF") == BRANCH and os.environ.get("GITHUB_EVENT_NAME") == "push"
         and os.environ.get("SOURCE_COMMIT") == SOURCE and os.environ.get("FINDLET_PUBLIC_REPOSITORY") == "true",
         "approved_public_ci_required")
    event = g.strict_json(read(os.environ["GITHUB_EVENT_PATH"], 262144))
    need(event.get("repository", {}).get("private") is False and event.get("repository", {}).get("full_name") == g.REPOSITORY
         and event.get("ref") == BRANCH and re.fullmatch(r"[0-9a-f]{40}", event.get("after", ""))
         and event.get("deleted") is False, "public_owned_push_required")
    g.report["activationCommit"] = event["after"]
    started = os.environ.get("FINDLET_SEMANTIC_JOB_STARTED_MS", "")
    need(re.fullmatch(r"[0-9]{13}", started), "earliest_job_clock_required")
    now, mono = time.time(), time.monotonic()
    started = int(started) / 1000
    remaining = started + 1200 - now
    need(0 <= now - started < 1200 and remaining >= 450, "job_window_exhausted")
    g.work_end = mono + min(900, remaining - 150)
    g.job_end = mono + remaining
    g.report["timing"] = {"earliestStepEpochMs": int(started * 1000), "setupElapsedMs": round((now - started) * 1000),
                           "admittedWorkMs": round((g.work_end - mono) * 1000), "cleanupReservedMs": 120000, "marginReservedMs": 30000}
    parent = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    need(parent.is_dir() and REPO != parent and REPO not in parent.parents and Path(g.DEVELOPER).is_dir(), "runner_profile_invalid")
    free = shutil.disk_usage(parent).free
    memory = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    # Free public M1 runners have 7 GB RAM/14 GB SSD. The three weights total
    # 2.56 GB; admit 6 GiB physical RAM and 8 GiB free storage, with 6 GiB
    # maximum task scratch and 2 GiB remote disk reserve. No larger/paid runner.
    need(free >= 8 * 1024**3 and memory >= 6 * 1024**3,
         "remote_resource_reserve_unavailable")
    g.root = Path(tempfile.mkdtemp(prefix="fs uri %-", dir=parent)); g.root.chmod(0o700)
    info = g.root.lstat(); g.root_identity = (info.st_dev, info.st_ino)
    g.nonce = os.urandom(16).hex()
    fd = os.open(g.root / ".owner", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as target:
        target.write(g.nonce.encode()); target.flush(); os.fsync(target.fileno())
    info = (g.root / ".owner").lstat(); g.marker_identity = (info.st_dev, info.st_ino)
    for name in ("source", "build", "runtime", "runtime/node", "runtime/tools", "tmp", "cache", "config", "models", "input", "negative",
                 "cache/swift", "cache/clang", "cache/npm", "cache/xdg", "cache/data", "cache/state"):
        directory(name)
    for name in ("npmrc", "global-npmrc"):
        g.owned_write("config/" + name, b"")
    home = os.environ.get("HOME", "")
    need(Path(home).is_absolute() and Path(home).is_dir(), "home_unavailable")
    g.env = {"HOME": home, "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "en_US.UTF-8", "LC_ALL": "C", "TZ": "UTC",
             "CI": "true", "DEVELOPER_DIR": g.DEVELOPER, "TMPDIR": str(g.root / "tmp") + "/", "TMP": str(g.root / "tmp"),
             "TEMP": str(g.root / "tmp"), "XDG_CONFIG_HOME": str(g.root / "config"), "XDG_CACHE_HOME": str(g.root / "cache/xdg"),
             "XDG_DATA_HOME": str(g.root / "cache/data"), "XDG_STATE_HOME": str(g.root / "cache/state"),
             "SWIFTPM_MODULECACHE_OVERRIDE": str(g.root / "cache/swift"), "CLANG_MODULE_CACHE_PATH": str(g.root / "cache/clang"),
             "NPM_CONFIG_CACHE": str(g.root / "cache/npm"), "NPM_CONFIG_USERCONFIG": str(g.root / "config/npmrc"),
             "NPM_CONFIG_GLOBALCONFIG": str(g.root / "config/global-npmrc"), "NPM_CONFIG_REGISTRY": "https://registry.npmjs.org/",
             "NPM_CONFIG_IGNORE_SCRIPTS": "true", "NPM_CONFIG_AUDIT": "false", "NPM_CONFIG_FUND": "false",
             "NPM_CONFIG_UPDATE_NOTIFIER": "false", "NODE_LLAMA_CPP_SKIP_DOWNLOAD": "true", "NO_COLOR": "1",
             "QMD_FORCE_CPU": "1", "GGML_METAL_NO_RESIDENCY": "1", "GIT_CONFIG_NOSYSTEM": "1",
             "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"}
    g.baseline_processes = {pid: row["start"] for pid, row in g.process_snapshot().items()}
    g.report["runtime"] = {"macOS": platform.mac_ver()[0], "architecture": platform.machine(), "python": platform.python_version(),
                           "remoteFreeBytesBefore": free, "physicalMemoryBytes": memory,
                           "scratchLimitBytes": g.ROOT_LIMIT, "homePreserved": True,
                           "environmentKeys": sorted(g.env), "genericSupervisorSha256": HELPER_SHA}
    guard("before_setup")
    g.export_source()


def compile_harness():
    xcode, _, _ = command("xcode_version", ["/usr/bin/xcodebuild", "-version"])
    swift, _, _ = command("swift_version", ["/usr/bin/xcrun", "swiftc", "--version"])
    sdk, _, _ = command("sdk_version", ["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-version"])
    path, _, _ = command("sdk_path", ["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-path"])
    need(xcode.strip() == b"Xcode 16.4\nBuild version 16F6" and b"Swift version 6.1.2" in swift and sdk.strip() == b"15.5",
         "toolchain_profile_changed")
    sdk_path = Path(path.decode().strip())
    need(sdk_path.is_dir() and sdk_path.resolve().is_relative_to(Path(g.DEVELOPER)), "sdk_path_invalid")
    shared = ["/usr/bin/xcrun", "swiftc", "-swift-version", "5", "-target", "arm64-apple-macosx15.0", "-sdk", str(sdk_path),
              "-module-cache-path", str(g.root / "cache/swift"), "-Xcc", "-fmodules-cache-path=" + str(g.root / "cache/clang"), "-parse-as-library"]
    build = g.root / "build"
    command("compile_core", [*shared, "-emit-module", "-emit-library", "-module-name", "FindletCore",
                             "-emit-module-path", str(build / "FindletCore.swiftmodule"),
                             *[str(g.root / "source" / n) for n in g.CORE], "-o", str(build / "libFindletCore.dylib")], 120)
    g.harness_binary = build / "SemanticPipelineHarness"
    command("compile_semantic_harness", [*shared, "-I", str(build), "-L", str(build), "-lFindletCore", "-Xlinker", "-rpath", "-Xlinker",
                                         "@executable_path", *[str(g.root / "source" / n) for n in g.SERVICES + [HARNESS]], "-o", str(g.harness_binary)], 180)
    g.report["compiledFiles"] = [{"relativePath": str(p.relative_to(g.root)), **g.fingerprint(p)}
                                 for p in (g.harness_binary, build / "libFindletCore.dylib", build / "FindletCore.swiftmodule")]
    g.report["toolchain"] = {"xcode": xcode.decode().strip(), "swift": swift.decode().strip(), "sdk": "15.5", "language": "5"}
    g.verify_export("after_compile")


def download(label, url, target, maximum, digest=None, exact=None):
    need(not target.exists(), "download_target_exists")
    command(label, ["/usr/bin/curl", "--disable", "--fail", "--show-error", "--silent", "--location", "--max-redirs", "5",
                    "--proto", "=https", "--proto-redir", "=https", "--connect-timeout", "10", "--max-time", "160",
                    "--max-filesize", str(maximum), "--output", str(target), url], 170)
    os.chmod(target, 0o600)
    proof = g.fingerprint(target)
    need(proof["bytes"] <= maximum and (exact is None or proof["bytes"] == exact)
         and (digest is None or proof["sha256"] == digest), "download_pin_mismatch")
    return proof


NATIVE = r"""
const fs=require('node:fs'),path=require('node:path');
const {createRequire}=require('node:module'); const {pathToFileURL}=require('node:url');
(async()=>{
const tools=process.argv[1],r=createRequire(path.join(tools,'package.json'));
const Database=r('better-sqlite3'),vec=r('sqlite-vec'); const db=new Database(':memory:');
let llm;try {vec.load(db);const versions=db.prepare('SELECT sqlite_version() AS sqliteVersion,vec_version() AS vecVersion').get();
db.close(); const {LlamaCpp}=await import(pathToFileURL(path.join(tools,'node_modules/@tobilu/qmd/dist/llm.js')));
llm=new LlamaCpp();const backend=await llm.getDeviceInfo({allowBuild:false});await llm.dispose();
const addons=Object.keys(require.cache).filter(x=>x.endsWith('.node'));
process.stdout.write(JSON.stringify({platform:process.platform,arch:process.arch,node:process.version,versions,
  gpu:backend.gpu,gpuOffloading:backend.gpuOffloading,gpuDevices:backend.gpuDevices,cpuCores:backend.cpuCores,
  addons,vector:fs.realpathSync(vec.getLoadablePath()),databaseClosed:!db.open,backendDisposed:true}));
}finally{if(db.open)db.close();if(llm)await llm.dispose();}
})().catch(()=>{process.stderr.write('native_admission_failed');process.exitCode=1});
"""

PY_VECTOR_PROBE = r"""
import json,sqlite3,sys
connection=sqlite3.connect(':memory:')
try:
    connection.enable_load_extension(True)
    connection.load_extension(sys.argv[1])
    connection.enable_load_extension(False)
    version=connection.execute('SELECT vec_version()').fetchone()[0]
    json_ok=connection.execute("SELECT json_extract(json_object('ok',1),'$.ok')").fetchone()[0]==1
finally:
    connection.close()
print(json.dumps({'sqliteVersion':sqlite3.sqlite_version,'vecVersion':version,'jsonAvailable':json_ok,'connectionClosed':True}))
"""

PY_VECTOR_AUDIT = r"""
import sqlite3,sys
connection=sqlite3.connect(sys.argv[1],uri=True)
try:
    connection.enable_load_extension(True)
    connection.load_extension(sys.argv[2])
    connection.enable_load_extension(False)
    connection.execute('PRAGMA query_only=ON')
    value=connection.execute(sys.argv[3]).fetchone()[0]
finally:
    connection.close()
print(value)
"""


def install_runtime():
    archive = g.root / "runtime/node.tar.gz"
    proof = download("download_node", g.NODE_URL, archive, 64 * 1024**2, g.NODE_SHA256)
    g.report["nodeArchive"] = {"url": g.NODE_URL, "expectedSha256": g.NODE_SHA256, "file": proof}
    g.extract_node(archive)
    g.node = g.root / "runtime/node/bin/node"
    npm = g.root / "runtime/node/lib/node_modules/npm/bin/npm-cli.js"
    g.report["nodeBinary"] = g.macho(g.node)
    g.env["PATH"] = str(g.node.parent) + ":/usr/bin:/bin:/usr/sbin:/sbin"
    out, err, _ = command("node_version", [str(g.node), "--version"])
    need(out == b"v26.13.0\n" and not err, "node_version_changed")
    out, err, _ = command("npm_version", [str(g.node), str(npm), "--version"])
    need(out == b"11.20.0\n" and not err, "npm_version_changed")
    raw = read(REPO / LOCK, 262144); need(sha(raw) == LOCK_SHA, "semantic_lock_changed")
    lock = g.strict_json(raw)
    original = g.strict_json(read(REPO / g.LOCK, 262144))
    need(sha(read(REPO / g.LOCK)) == g.LOCK_SHA256 and set(lock["packages"]) == set(original["packages"])
         and len(lock["packages"]) == 179, "original_lock_changed")
    for name, value in lock["packages"].items():
        if name:
            need(all(value.get(k) == original["packages"][name].get(k) for k in ("version", "resolved", "integrity")), "locked_package_changed")
    deps = {"@tobilu/qmd": "2.8.3", "better-sqlite3": "13.0.3", "sqlite-vec": "0.1.9", "sqlite-vec-darwin-arm64": "0.1.9",
            "@node-llama-cpp/mac-arm64-metal": "3.20.0"}
    need(lock["packages"][""]["dependencies"] == deps and lock["lockfileVersion"] == 3, "semantic_lock_roots_changed")
    tools = g.root / "runtime/tools"
    g.owned_write("runtime/tools/package.json", (json.dumps({"name": lock["name"], "version": "0.0.0", "private": True, "dependencies": deps}) + "\n").encode())
    g.owned_write("runtime/tools/package-lock.json", raw)
    command("frozen_runtime_install", [str(g.node), str(npm), "ci", "--ignore-scripts", "--omit=optional", "--no-audit", "--no-fund", "--progress=false"], 240, cwd=tools)
    need(read(tools / "package-lock.json") == raw, "installed_lock_rewritten")
    scope = tools / "node_modules/@node-llama-cpp"
    need({p.name for p in scope.iterdir()} == {"mac-arm64-metal"}, "unexpected_optional_backend")
    installed = []
    for name, value in lock["packages"].items():
        if not name or value.get("optional") is True:
            continue
        pkg = g.strict_json(read(tools / name / "package.json", 1048576))
        need(pkg["version"] == value["version"], "installed_locked_version_changed")
        installed.append({"path": name, "version": pkg["version"], "integrity": value["integrity"]})
    g.report["runtimeLock"] = {"path": LOCK, "sha256": LOCK_SHA, "bytes": len(raw), "packages": len(lock["packages"]), "installed": installed}
    out, _, _ = command("actual_native_cpu_admission", [str(g.node), "-e", NATIVE, str(tools)], 60)
    native = g.strict_json(out)
    need(native["platform"] == "darwin" and native["arch"] == "arm64" and native["node"] == "v26.13.0"
         and native["versions"]["vecVersion"] == "v0.1.9" and native["databaseClosed"] and native["backendDisposed"]
         and native["gpu"] is False and native["gpuOffloading"] is False and native["gpuDevices"] == [], "native_cpu_admission_failed")
    need(all(Path(p).resolve(strict=True).is_relative_to(tools.resolve()) for p in native["addons"] + [native["vector"]]), "native_binding_outside_runtime")
    g.report["nativeAdmission"] = native
    out, _, _ = command("python_vec_observer_admission", [sys.executable, "-I", "-B", "-S", "-c", PY_VECTOR_PROBE, native["vector"]], 30)
    observer = g.strict_json(out)
    need(observer["vecVersion"] == "v0.1.9" and observer["jsonAvailable"] is True and observer["connectionClosed"] is True,
         "python_vec_observer_admission_failed")
    g.report["observerNativeAdmission"] = {**observer, "python": platform.python_version(),
                                           "pythonExecutable": sys.executable, "beforeModelDownloads": True}
    g.package = tools / "node_modules/@tobilu/qmd"
    g.runtime_vector = g.tree_vector(g.root / "runtime")
    g.verify_runtime("after_admission")


def install_models_and_fixtures():
    global fixtures_vector, models_vector
    metadata = g.strict_json(read(REPO / MODELS, 16384))
    need(len(metadata["models"]) == 3 and metadata["totalBytes"] == 2560742688 and metadata["semanticLockSha256"] == LOCK_SHA,
         "model_manifest_shape")
    records = []
    for model in metadata["models"]:
        need(model["gated"] is False and re.fullmatch(r"[0-9a-f]{40}", model["revision"])
             and re.fullmatch(r"[0-9a-f]{64}", model["sha256"]) and Path(model["file"]).name == model["file"]
             and model["url"] == f"https://huggingface.co/{model['repo']}/resolve/{model['revision']}/{model['file']}", "model_url_pin")
        target = g.root / "models" / model["file"]
        proof = download("download_" + model["role"], model["url"], target, model["bytes"], model["sha256"], model["bytes"])
        fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            need(os.read(fd, 4) == b"GGUF", "model_magic")
        finally:
            os.close(fd)
        records.append({**model, "actual": proof})
    g.report["modelFiles"] = records
    models_vector = g.tree_vector(g.root / "models")
    for name, value in DOCUMENTS.items():
        g.owned_write("input/" + name, value)
    g.owned_write("negative/invalid.gguf", b"GGUF" + struct.pack("<IQQ", 3, 0, 0))
    fixtures_vector = g.tree_vector(g.root / "input") + g.tree_vector(g.root / "negative")
    g.report["fixtureFiles"] = fixtures_vector


AUDIT = r"""
const fs=require('node:fs'),path=require('node:path');const {createRequire}=require('node:module');
const r=createRequire(path.join(process.argv[1],'package.json'));const Database=r('better-sqlite3'),vec=r('sqlite-vec');
const db=new Database(process.argv[2],{readonly:true,fileMustExist:true});
try{vec.load(db);db.pragma('query_only=ON');
const docs=db.prepare('SELECT path,collection,hash FROM documents WHERE active=1 ORDER BY path').all();
const cv=db.prepare('SELECT hash,seq,pos,total_chunks,embed_fingerprint FROM content_vectors ORDER BY hash,seq').all();
const rows=db.prepare('SELECT hash_seq,embedding FROM vectors_vec ORDER BY hash_seq').all();
if(docs.length!==3||cv.length!==3||rows.length!==3)throw Error('count');
for(const row of rows){if(!cv.some(c=>row.hash_seq===c.hash+'_'+c.seq&&c.total_chunks===1&&c.pos===0&&c.embed_fingerprint.length>0&&
 docs.some(d=>d.hash===c.hash&&d.collection==='findlet_documents')))throw Error('join');
const bytes=row.embedding;if(!Buffer.isBuffer(bytes)||bytes.length!==4096)throw Error('dimensions');let norm=0;
for(let i=0;i<bytes.length;i+=4){const v=bytes.readFloatLE(i);if(!Number.isFinite(v))throw Error('finite');norm+=v*v;}if(!(norm>0))throw Error('zero');}
const cached=db.prepare('SELECT result FROM llm_cache').all();let expansionEntries=0;const rerankScores=[];
for(const row of cached){const value=JSON.parse(row.result);if(Array.isArray(value)){
 if(value.length&&value.every(v=>v&&['lex','vec','hyde'].includes(v.type)&&typeof(v.query??v.text)==='string'))expansionEntries++;
}else if(typeof value==='number'&&Number.isFinite(value)&&value>=0&&value<=1){rerankScores.push(value);}}
if(expansionEntries<1||rerankScores.length<3||new Set(rerankScores).size<2||rerankScores.every(s=>s===0.5))throw Error('local_inference_cache');
process.stdout.write(JSON.stringify({activeDocuments:3,contentChunks:3,joinedVectors:3,dimensions:1024,allFiniteNonzero:true,
  snapshotPaths:docs.map(d=>d.path),queryOnly:true,vectorLayout:'qmd2.8.3_vectors_vec',
  expansionCacheEntries:expansionEntries,rerankCacheEntries:rerankScores.length,rerankScoresNonconstant:true,noUniformFallback:true}));
}finally{db.close();}
"""


def audit_index(first):
    generation = first["pointer"]["generation"]
    need(str(uuid.UUID(generation)) == generation, "audit_generation")
    folder = g.root / "library/generations" / generation
    database = folder / "index.sqlite"
    state = g.strict_json(read(folder / "state.json", 4 * 1024**2))
    manifest = state.get("manifest", state)
    documents = manifest["documents"]
    expected = sorted(str(uuid.UUID(d["id"])) + ".md" for d in documents)
    need(len(expected) == 3 and sorted(d["relativePath"] for d in documents) == sorted(DOCUMENTS), "audit_manifest_mapping")
    before = g.fingerprint(database)
    sidecars = [Path(str(database) + suffix) for suffix in ("-journal", "-wal", "-shm")]
    def sidecar_state():
        return [{"suffix": p.name.removeprefix("index.sqlite"), "absent": not os.path.lexists(p),
                 "file": None if not os.path.lexists(p) else g.fingerprint(p)} for p in sidecars]
    before_sidecars = sidecar_state()
    need(all(v["absent"] or v["file"]["bytes"] == 0 for v in before_sidecars), "audit_pending_sidecars")
    _, live, unknown = g.observe_processes()
    need(not live and not unknown, "audit_live_process")
    # Closed immutable URI through the admitted isolated Python binding. Apple's
    # system sqlite3 shell does not expose .load. No dependency installation.
    fd = os.open(database, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        need(os.read(fd, 16) == b"SQLite format 3\x00", "audit_sqlite_header")
    finally:
        os.close(fd)
    need(before == g.fingerprint(database), "audit_unstable_admission")
    extension = Path(g.report["nativeAdmission"]["vector"])
    need(extension.resolve(strict=True).is_relative_to((g.root / "runtime").resolve()), "audit_extension_outside_runtime")
    sql = r"""
WITH good_vectors AS (
 SELECT v.hash_seq, CASE WHEN json_valid(vec_to_json(v.embedding)) THEN
   vec_length(v.embedding)=1024
   AND NOT EXISTS(SELECT 1 FROM json_each(vec_to_json(v.embedding)) j
                  WHERE j.type NOT IN ('integer','real') OR abs(j.value)>3.4028234663852886e38)
   AND (SELECT total(j.value*j.value) FROM json_each(vec_to_json(v.embedding)) j)>0
   AND (SELECT total(j.value*j.value) FROM json_each(vec_to_json(v.embedding)) j)<1.0e100
 ELSE 0 END AS valid FROM vectors_vec v
), numbers AS (
 SELECT CAST(result AS REAL) AS score FROM llm_cache
 WHERE json_valid(result) AND json_type(result) IN ('integer','real')
), expansions AS (
 SELECT result FROM llm_cache WHERE json_valid(result) AND json_type(result)='array'
 AND json_array_length(result)>0
 AND NOT EXISTS(SELECT 1 FROM json_each(result) e WHERE json_extract(e.value,'$.type') NOT IN ('lex','vec','hyde')
                OR coalesce(json_type(e.value,'$.query'),json_type(e.value,'$.text'),'missing')!='text')
)
SELECT json_object(
 'activeDocuments',(SELECT count(*) FROM documents WHERE active=1 AND collection='findlet_documents'),
 'allActiveDocuments',(SELECT count(*) FROM documents WHERE active=1),
 'contentChunks',(SELECT count(*) FROM content_vectors),
 'vectorRows',(SELECT count(*) FROM good_vectors),
 'validVectors',(SELECT count(*) FROM good_vectors WHERE valid=1),
 'joinedVectors',(SELECT count(*) FROM good_vectors v WHERE valid=1 AND EXISTS(
   SELECT 1 FROM content_vectors c JOIN documents d ON d.hash=c.hash
   WHERE v.hash_seq=c.hash||'_'||c.seq AND c.seq=0 AND c.pos=0 AND c.total_chunks=1
     AND length(c.embed_fingerprint)>0 AND d.active=1 AND d.collection='findlet_documents')),
 'snapshotPaths',json((SELECT json_group_array(path) FROM (SELECT path FROM documents WHERE active=1 ORDER BY path))),
 'expansionCacheEntries',(SELECT count(*) FROM expansions),
 'rerankCacheEntries',(SELECT count(*) FROM numbers WHERE score>=0 AND score<=1),
 'distinctRerankScores',(SELECT count(DISTINCT score) FROM numbers WHERE score>=0 AND score<=1),
 'nonFallbackRerankScores',(SELECT count(*) FROM numbers WHERE score>=0 AND score<=1 AND score!=0.5));
"""
    uri = database.as_uri() + "?mode=ro&immutable=1"
    out, _, _ = command("independent_closed_vector_audit", [sys.executable, "-I", "-B", "-S", "-c", PY_VECTOR_AUDIT,
                         uri, str(extension), sql], 30)
    value = g.strict_json(out)
    after = g.fingerprint(database); after_sidecars = sidecar_state()
    flags = {"snapshotPathsExact": value["snapshotPaths"] == expected,
             "databaseIdentityAndHashUnchanged": before == after,
             "sidecarsUnchanged": before_sidecars == after_sidecars,
             "exactDocumentsChunksAndVectors": all(value[k] == 3 for k in
                 ("activeDocuments", "allActiveDocuments", "contentChunks", "vectorRows", "validVectors", "joinedVectors")),
             "expansionCachePresent": value["expansionCacheEntries"] >= 1,
             "nonconstantRerankerCachePresent": value["rerankCacheEntries"] >= 3 and value["distinctRerankScores"] >= 2
                 and value["nonFallbackRerankScores"] >= 1}
    g.report["independentVectorAudit"] = {**value, "flags": flags, "before": before, "after": after,
        "sidecarsBefore": before_sidecars, "sidecarsAfter": after_sidecars, "expectedPaths": expected,
        "dimensions": 1024, "immutableReadOnly": True, "metadataOnlyOutput": True}
    need(all(flags.values()), "audit_integrity_or_metadata_failed")


def verify_external(label):
    if g.runtime_vector is not None:
        g.verify_runtime(label)
    if models_vector is not None:
        need(g.tree_vector(g.root / "models") == models_vector, "external_models_changed")
    if fixtures_vector is not None:
        need(g.tree_vector(g.root / "input") + g.tree_vector(g.root / "negative") == fixtures_vector, "authored_originals_changed")
    if g.export_vector:
        g.verify_export(label)
    if g.report.get("compiledFiles"):
        g.verify_compiled(label)
    g.report.setdefault("externalChecks", []).append({"label": label, "passed": True})


def phase(name, case, queries, checks):
    out, _, row = command(case + "_production_journey", [str(g.harness_binary), name, str(g.root), g.nonce, SOURCE],
                           seconds=420 if name == "prepare" else 200, allowed=(0, 1, 2))
    value = g.strict_json(out)
    g.report["phases"].append(value)
    need(row["exitCode"] == 0 and value["completed"] is True and value["phase"] == name and value["sourceCommit"] == SOURCE
         and len(value["queries"]) == queries and set(value["checks"]) == checks and len(value["checks"]) == len(checks), "semantic_journey_failed")
    return value


PREPARE_CHECKS = {"keywordBaseBuiltWithoutModels", "explicitPreparationConsentRequired", "actualEmbeddingPreparationCompleted",
                  "semanticGenerationPublished", "queriesPreservePublishedPointerAndState", "noNativeChildRemainsAfterQueries"}
REOPEN_CHECKS = {"newProcessPreservesPublishedState", "newEngineReadsSemanticReadiness", "failedNativePreparationPreservesState",
                 "failedStagedGenerationRemoved", "ownedNativeQueryCancelled", "cancelledNativeChildExited", "cancellationPreservesSemanticState",
                 "forgetClearsSemanticSummary", "forgetRemovesPointer", "forgetEmpties_generations", "forgetEmpties_cache", "noNativeChildRemainsAfterForget"}


def cleanup():
    if g.root is None:
        g.report["scratchCleanup"] = "not_created"
        return
    g.cleanup_end = min(time.monotonic() + 120, g.job_end - 30)
    try:
        # Reuse the supervisor's attribution fences; stop only individually
        # observed descendants when Foundation gave them a separate group.
        for _ in range(160):
            rows, live, unknown = g.observe_processes()
            need(not unknown, "unattributed_root_reference_preserved")
            if not live and all(c["process"].poll() is not None and g.absent(c["process"].pid) for c in g.children):
                break
            for p in live:
                own = g.attributed[p["pid"]]
                need(p["uid"] == os.getuid() and p["start"] == own["start"] and p["pgid"] == own["pgid"], "cleanup_signal_identity")
                try:
                    os.kill(p["pid"], signal.SIGTERM if _ < 100 else signal.SIGKILL)
                except ProcessLookupError:
                    pass
            time.sleep(0.05)
        for child in g.children:
            child["process"].wait(timeout=1)
        _, live, unknown = g.observe_processes()
        need(not live and not unknown and all(g.absent(c["process"].pid) for c in g.children), "owned_processes_remaining")
        g.owner(); verify_external("before_cleanup"); guard("before_cleanup", cleanup=True)
        allowed = {".owner", "source", "build", "runtime", "tmp", "cache", "config", "models", "input", "negative", "library", "semantic-handoff.json"}
        need({p.name for p in g.root.iterdir()} <= allowed, "unclassified_scratch_preserved")
        inventory = g.tree_vector(g.root)
        for name, identity in known.items():
            value = (g.root / name).lstat()
            need(stat.S_ISDIR(value.st_mode) and value.st_uid == os.getuid() and (value.st_dev, value.st_ino) == identity,
                 "known_directory_changed")
        g.report["scratchInventory"] = {"entries": len(inventory), "regularBytes": sum(v["bytes"] for v in inventory if "sha256" in v),
                                        "vectorSha256": sha(json.dumps(inventory, sort_keys=True).encode()), "knownDirectories": len(known)}
        _, live, unknown = g.observe_processes(); need(not live and not unknown, "predelete_processes_remaining")
        g.owner(); shutil.rmtree(g.root); need(not os.path.lexists(g.root), "scratch_remaining")
        g.report["scratchCleanup"] = "passed"
        guard("after_cleanup", cleanup=True, post_root=True)
        _, live, unknown = g.observe_processes(); need(not live and not unknown, "postdelete_processes_remaining")
        g.report["processCleanup"] = {"observedOwnedProcesses": list(g.attributed.values()), "predeleteZeroObserved": True,
                                      "finalZeroObserved": True, "remaining": [], "unknownRootReferences": []}
    except Exception as error:
        g.report["scratchCleanup"] = "unverified"; g.report["errors"].append(g.finite(error))


def main():
    completed = False
    def interrupt(_signal, _frame):
        g.interrupted = True
    for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(number, interrupt)
    try:
        preflight(); compile_harness(); install_runtime(); install_models_and_fixtures()
        verify_external("after_setup"); guard("after_setup")
        first = phase("prepare", "S01", 6, PREPARE_CHECKS)
        audit_index(first); verify_external("after_prepare"); guard("after_prepare")
        phase("reopen", "S02", 2, REOPEN_CHECKS)
        need(not (g.root / "library/current.json").exists()
             and not list((g.root / "library/generations").iterdir()) and not list((g.root / "library/cache").iterdir()), "independent_forget_failed")
        verify_external("after_reopen"); guard("after_reopen")
        completed = True
    except Exception as error:
        g.report["errors"].append(g.finite(error))
        tb = error.__traceback__
        while tb and tb.tb_next:
            tb = tb.tb_next
        g.report["errorLocation"] = None if tb is None else {"file": Path(tb.tb_frame.f_code.co_filename).name, "line": tb.tb_lineno}
    finally:
        cleanup()
    private_ok = privacy_scan()
    need(private_ok, "withheld_private_stream")
    g.report["accepted"] = bool(completed and not g.report["errors"] and not g.interrupted
                                 and g.report.get("scratchCleanup") == "passed" and len(g.report["guards"]) == 6
                                 and len(g.report["phases"]) == 2)
    g.report["status"] = "passed" if g.report["accepted"] else "failed"
    raw = json.dumps(g.report, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    need(len(raw) <= 8 * 1024**2, "receipt_bound")
    print("FINDLET_SEMANTIC_RECEIPT_BEGIN")
    print(raw.decode())
    print("FINDLET_SEMANTIC_RECEIPT_END")
    return 0 if g.report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
