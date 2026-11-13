#!/usr/bin/env python3
"""Fixed public macOS packaging control; never launch Findlet or run tests."""

import base64
import ctypes
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import resource
import secrets
import select
import selectors
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

REPOSITORY = "alvarovillalbaa/findlet"
BRANCH = "refs/heads/qa/findlet-panel-preview-20261113-1"
WORKFLOW = ".github/workflows/panel-preview-package.yml"
CONTROLLER = "Tests/ci/run-panel-preview-package.py"
BASE = "66cb4806061fe0b4e5407b740185fd0ff2f87087"
ARCHIVE = "Findlet-0.1.1-macos-universal.zip"
PREFIX = b"FINDLET_PANEL_PREVIEW_PACKAGE_RESULT="
MIB = 1024 ** 2
MAX_STORAGE, MAX_STREAM, MAX_REPORT = 4096 * MIB, MIB, 16 * MIB


def need(value, reason):
    if not value:
        raise RuntimeError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def safe(name):
    need(name and not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts
         and str(PurePosixPath(name)) == name.rstrip("/") and "\\" not in name
         and all(32 <= ord(c) != 127 for c in name), "unsafe_path")
    return name


def identity(path):
    row = path.lstat()
    return [row.st_dev, row.st_ino, row.st_uid, stat.S_IMODE(row.st_mode)]


def file_sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(MIB), b""):
            digest.update(part)
    return digest.hexdigest()


class NativeXAttrs:
    """Darwin listxattr/getxattr ABI; every read is bounded and leaf-nofollow."""
    def __init__(self):
        library = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
        self.list = library.listxattr
        self.list.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
        self.list.restype = ctypes.c_ssize_t
        self.get = library.getxattr
        self.get.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_int]
        self.get.restype = ctypes.c_ssize_t

    def two_pass(self, function, prefix, suffix, maximum, label):
        ctypes.set_errno(0)
        required = function(*prefix, None, 0, *suffix)
        if required < 0:
            raise RuntimeError("native_xattr_" + label + ":errno=" + str(ctypes.get_errno()))
        need(required <= maximum, "native_xattr_" + label + "_bound")
        buffer = ctypes.create_string_buffer(max(1, required))
        ctypes.set_errno(0)
        actual = function(*prefix, buffer, required, *suffix)
        if actual < 0:
            raise RuntimeError("native_xattr_" + label + ":errno=" + str(ctypes.get_errno()))
        need(actual == required, "native_xattr_" + label + "_changed")
        return buffer.raw[:actual]

    def names(self, path):
        raw = self.two_pass(self.list, (path,), (1,), 65536, "names")
        need(not raw or raw.endswith(b"\0"), "native_xattr_names_termination")
        names = raw[:-1].split(b"\0") if raw else []
        need(len(names) <= 256 and len(set(names)) == len(names) and all(names), "native_xattr_names_structure")
        return sorted(names)

    def read(self, path):
        before = path.lstat(); encoded = os.fsencode(path); names = self.names(encoded); result = {}; total = sum(map(len, names))
        for name in names:
            value = self.two_pass(self.get, (encoded, name), (0, 1), 256 * 1024, "value")
            total += len(value); need(total <= 512 * 1024, "native_xattr_cumulative_bound")
            result[name.decode("utf-8", errors="strict")] = value
        final_names = self.names(encoded); after = path.lstat()
        stamp = lambda row: (row.st_dev, row.st_ino, row.st_mode, row.st_uid, row.st_size, row.st_mtime_ns, row.st_ctime_ns)
        need(final_names == names and stamp(before) == stamp(after), "native_xattr_path_or_names_changed")
        return result


class Check:
    def __init__(self):
        self.checkout = Path.cwd().resolve()
        self.root, self.known, self.source = None, None, None
        self.groups, self.processes, self.direct, self.frozen = set(), {}, {}, {}
        self.interrupted, self.signals = None, []
        self.max_storage = self.max_rss = self.max_processes = 0
        self.compressed = 0
        self.started = time.monotonic()
        self.work_end, self.cleanup_end = self.started + 900, self.started + 1050
        self.report = {"schemaVersion": 1, "repository": REPOSITORY, "status": "failed", "commands": [],
                       "testsExecuted": False, "applicationLaunched": False, "capturePerformed": False,
                       "externalRuntimeBundled": False, "runtimeInstalledOrInvoked": False, "engineAcceptancePerformed": False,
                       "cleanup": {"verified": False}, "ownedSignals": self.signals}
        self.env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL", "DEVELOPER_DIR") if key in os.environ}
        self.env.update(CI="true", GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1", DO_NOT_TRACK="1",
                        PYTHONDONTWRITEBYTECODE="1")
        for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(number, self.cancel)

    def cancel(self, number, _frame):
        self.interrupted = number

    def git(self, *args):
        row = subprocess.run(["git", *args], cwd=self.checkout, env=self.env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        need(row.returncode == 0 and len(row.stdout) < 8 * MIB and len(row.stderr) < MAX_STREAM, "git_guard")
        return row.stdout

    def guard(self, first=False):
        need(self.git("rev-parse", "HEAD").decode().strip() == self.commit, "source_head_changed")
        need(not self.git("status", "--porcelain=v1", "--untracked-files=all", "--ignored"), "source_not_clean")
        vector, index = {}, []
        for entry in filter(None, self.git("ls-tree", "-rz", "--full-tree", "HEAD").split(b"\0")):
            metadata, raw_name = entry.split(b"\t", 1)
            mode, kind, oid = metadata.split()
            name = safe(raw_name.decode()); path = self.checkout / name
            need(kind == b"blob" and mode in (b"100644", b"100755") and path.is_file() and not path.is_symlink(), "source_entry")
            need(identity(path)[2:] == [os.getuid(), 0o755 if mode == b"100755" else 0o644], "source_mode")
            data = path.read_bytes()
            need(len(data) <= 4 * MIB and hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest().encode() == oid, "source_blob")
            vector[name] = {"bytes": len(data), "sha256": sha(data), "blob": oid.decode(), "mode": mode.decode()}
            index.append(mode + b" " + oid + b" 0\t" + raw_name)
        need(sorted(filter(None, self.git("ls-files", "--stage", "-z").split(b"\0"))) == sorted(index), "index_tree")
        index_sha = file_sha(self.checkout / ".git/index")
        if first:
            need(self.git("rev-list", "--parents", "-n", "1", self.commit).decode().split() == [self.commit, BASE], "source_parent")
            need(WORKFLOW not in vector and sum(row["bytes"] for row in vector.values()) < 16 * MIB, "inert_source_scope")
            need(set(self.git("diff", "--name-only", BASE, self.commit, "--", "Package.swift", "Sources", "Resources", "Tests", "script", ".codex/environments/environment.toml").decode().splitlines())
                 == {"Resources/Info.plist", "script/build_and_run.sh", CONTROLLER}, "accepted_app_inputs_changed")
            self.source, self.index_sha = vector, index_sha
            self.report.update(sourceCommit=self.commit, canonicalBaseCommit=BASE, sourceVector=vector, indexSha256=index_sha)
        else:
            need(vector == self.source and index_sha == self.index_sha, "source_or_index_changed")

    def admit(self):
        need(sys.platform == "darwin" and os.environ.get("CI") == "true" and os.environ.get("GITHUB_ACTIONS") == "true", "public_macos_ci_only")
        need(os.environ.get("GITHUB_REPOSITORY") == REPOSITORY and os.environ.get("GITHUB_REF") == BRANCH
             and os.environ.get("GITHUB_EVENT_NAME") == "create" and os.environ.get("GITHUB_WORKFLOW_REF") == REPOSITORY + "/" + WORKFLOW + "@" + BRANCH, "workflow_scope")
        event_path = Path(os.environ["GITHUB_EVENT_PATH"])
        need(event_path.stat().st_size < MIB, "event_bound")
        event = json.loads(event_path.read_bytes())
        need(event["repository"]["private"] is False and event["repository"]["full_name"] == REPOSITORY, "public_repository")
        need(len(sys.argv) == 3 and sys.argv[1] == "--source-commit" and re.fullmatch(r"[0-9a-f]{40}", sys.argv[2]), "fixed_source_argument")
        self.commit = sys.argv[2]
        need(os.environ.get("SOURCE_COMMIT") == self.commit, "source_env")
        elapsed = time.time() - int(os.environ["FINDLET_JOB_STARTED_MS"]) / 1000
        need(0 <= elapsed < 120 and 1200 - elapsed - 30 >= 1050, "job_budget")
        self.guard(first=True)
        self.xattrs = NativeXAttrs()
        self.xattrs.read(self.checkout)  # Refuse unsupported native reads before creating disposable output.
        self.report["nativeXattrs"] = {"library": "/usr/lib/libSystem.B.dylib", "options": 1, "position": 0, "sourceDirectoryProbePassed": True}
        runner = Path(os.environ["RUNNER_TEMP"]).resolve()
        need(runner.is_dir() and not runner.is_relative_to(self.checkout), "runner_temp_scope")
        need(shutil.disk_usage(runner).free >= 6 * 1024**3, "remote_free_reserve")
        os.umask(0o077)
        self.root = Path(tempfile.mkdtemp(prefix="findlet-preview-", dir=runner)); self.root_id = identity(self.root)
        self.nonce = secrets.token_hex(24)
        (self.root / "owner").write_text(self.nonce); self.owner_id = identity(self.root / "owner")
        self.report["ownedRoot"] = {"path": str(self.root), "rootIdentity": self.root_id, "ownerIdentity": self.owner_id}
        for name in ("export", "cache", "cache/swiftpm", "tmp", "extract"):
            (self.root / name).mkdir(mode=0o700)
        self.env.update(FINDLET_PREVIEW_OWNER=self.nonce, TMPDIR=str(self.root / "tmp") + "/",
                        XDG_CACHE_HOME=str(self.root / "cache"), CLANG_MODULE_CACHE_PATH=str(self.root / "cache/clang"),
                        SWIFTPM_MODULECACHE_OVERRIDE=str(self.root / "cache/swift"), FINDLET_SWIFTPM_CACHE=str(self.root / "cache/swiftpm"))
        self.report["github"] = {key: os.environ.get(key) for key in ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA", "GITHUB_WORKFLOW_SHA", "GITHUB_WORKFLOW_REF")}
        self.known = self.snapshot()

    def snapshot(self):
        need(identity(self.root) == self.root_id and identity(self.root / "owner") == self.owner_id
             and (self.root / "owner").read_text() == self.nonce, "owned_root_changed")
        rows, total, attribute_bytes = {}, 0, 0
        for parent, dirs, files in os.walk(self.root, followlinks=False):
            for name in dirs + files:
                path = Path(parent) / name; rel = path.relative_to(self.root).as_posix(); value = path.lstat()
                need(value.st_uid == os.getuid() and (stat.S_ISLNK(value.st_mode) or not stat.S_IMODE(value.st_mode) & 0o022), "owned_mode:" + rel)
                attrs = self.xattrs.read(path); attribute_bytes += sum(len(key.encode()) + len(value) for key, value in attrs.items())
                need(attribute_bytes <= 8 * MIB, "snapshot_xattr_cumulative_bound")
                row = {"identity": identity(path), "xattrs": {key: sha(value) for key, value in attrs.items()}}
                if stat.S_ISLNK(value.st_mode):
                    need(path.resolve().is_relative_to(self.root), "owned_symlink_escape:" + rel)
                    row.update(type="symlink", target=os.readlink(path))
                elif stat.S_ISDIR(value.st_mode):
                    row["type"] = "directory"
                else:
                    need(stat.S_ISREG(value.st_mode) and value.st_size <= 512 * MIB, "owned_file_type_or_size")
                    total += value.st_size; row.update(type="file", bytes=value.st_size, sha256=file_sha(path))
                rows[rel] = row
                need(total <= MAX_STORAGE and len(rows) <= 60000, "owned_storage_or_entries")
        need(shutil.disk_usage(self.root).free >= 2 * 1024**3, "remote_free_reserve")
        self.max_storage = max(self.max_storage, total)
        for prefix, expected in self.frozen.items():
            need({key: row for key, row in rows.items() if key == prefix or key.startswith(prefix + "/")} == expected, "frozen_changed:" + prefix)
        return rows

    def freeze(self, prefix):
        rows = self.snapshot()
        selected = {key: row for key, row in rows.items() if key == prefix or key.startswith(prefix + "/")}
        need(selected, "empty_freeze")
        self.frozen[prefix] = selected; self.known = rows

    def sample(self, enforce=True):
        result = subprocess.run(["/bin/ps", "eww", "-axo", "pid=,ppid=,pgid=,lstart=,rss=,command="], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
        need(result.returncode == 0 and len(result.stdout) < 16 * MIB, "process_inventory")
        rows = {}
        for line in result.stdout.decode().splitlines():
            fields = line.split(None, 9)
            if len(fields) == 10:
                pid, parent, group = map(int, fields[:3]); rows[pid] = [parent, group, " ".join(fields[3:8]), int(fields[8]), fields[9]]
        live_direct = {pid for pid, child in self.direct.items() if child.poll() is None}
        owned = {pid for pid, row in rows.items() if pid in live_direct or self.processes.get(pid) == row[2]
                 or "FINDLET_PREVIEW_OWNER=" + self.nonce in row[4].split()}
        changed = True
        while changed:
            changed = False
            groups = {rows[pid][1] for pid in owned}
            for pid, row in rows.items():
                if pid not in owned and (row[1] in groups or row[0] in owned):
                    owned.add(pid); changed = True
        live = {pid: rows[pid] for pid in owned}
        for pid, row in live.items():
            self.processes[pid] = row[2]; self.groups.add(row[1])
        rss = sum(row[3] * 1024 for row in live.values())
        self.max_rss, self.max_processes = max(self.max_rss, rss), max(self.max_processes, len(live))
        if enforce:
            need(rss <= 4096 * MIB and len(live) <= 64, "owned_process_resource_bound")
        return live

    def stop(self):
        for number in (signal.SIGTERM, signal.SIGKILL):
            for pid, row in self.sample(False).items():
                try:
                    need(len(self.signals) < 256, "owned_signal_bound")
                    os.kill(pid, number); self.signals.append({"pid": pid, "start": row[2], "signal": int(number)})
                except ProcessLookupError:
                    pass
            until = min(self.cleanup_end, time.monotonic() + 3)
            while time.monotonic() < until:
                for child in self.direct.values():
                    child.poll()
                if not self.sample(False):
                    return
                time.sleep(0.05)
        need(not self.sample(False), "owned_process_survived")

    def run(self, label, args, timeout=60):
        need(not self.interrupted and time.monotonic() < self.work_end, "interrupted_or_work_deadline")
        self.guard(); self.known = self.snapshot()
        record = {"id": label, "argv": [str(x).replace(str(self.root), "$OWNED") for x in args]}; self.report["commands"].append(record)
        def limits():
            for key, maximum in ((resource.RLIMIT_CPU, 900), (resource.RLIMIT_FSIZE, 512 * MIB), (resource.RLIMIT_NOFILE, 512), (resource.RLIMIT_CORE, 0)):
                resource.setrlimit(key, (maximum, maximum))
        child = subprocess.Popen([str(x) for x in args], cwd=self.root / "export", env=self.env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, preexec_fn=limits)
        self.direct[child.pid] = child; self.groups.add(child.pid)
        selector = selectors.DefaultSelector(); streams = {"stdout": bytearray(), "stderr": bytearray()}; eof = set(); failure = None
        observed = {name: [0, hashlib.sha256()] for name in streams}
        for name in streams:
            stream = getattr(child, name); os.set_blocking(stream.fileno(), False); selector.register(stream, selectors.EVENT_READ, name)
        end = min(self.work_end, time.monotonic() + timeout); sampled = time.monotonic()
        def drain(wait, enforce=True):
            for key, _ in selector.select(wait):
                try:
                    data = os.read(key.fd, 65536)
                except BlockingIOError:
                    continue
                if not data:
                    eof.add(key.data); selector.unregister(key.fileobj); key.fileobj.close()
                else:
                    observed[key.data][0] += len(data); observed[key.data][1].update(data)
                    room = MAX_STREAM - len(streams[key.data]); streams[key.data].extend(data[:room])
                    if enforce:
                        need(len(data) <= room, "command_stream_bound")
        try:
            while selector.get_map() or child.poll() is None:
                need(not self.interrupted and time.monotonic() < end, "command_timeout_or_interruption:" + label)
                self.sample(); drain(0.1)
                if time.monotonic() - sampled >= 5:
                    total = sum(path.stat().st_size for path in self.root.rglob("*") if path.is_file() and not path.is_symlink())
                    need(total <= MAX_STORAGE, "storage_sample_bound"); self.max_storage = max(self.max_storage, total); sampled = time.monotonic()
            record["exitCode"] = child.wait(timeout=1)
            need(record["exitCode"] == 0 and not self.sample(), "command_failed_or_left_processes:" + label)
        except BaseException as error:
            failure = error; record["error"] = str(error)[:512]
            try:
                self.stop(); child.wait(timeout=3)
                until = min(self.cleanup_end, time.monotonic() + 3)
                while selector.get_map() and time.monotonic() < until:
                    drain(0.05, False)
            except Exception as error:
                record["terminationError"] = str(error)[:512]
            record["exitCode"] = child.returncode
        finally:
            for key in list(selector.get_map().values()):
                selector.unregister(key.fileobj); key.fileobj.close()
            selector.close()
            for name, data in streams.items():
                record[name] = self.original(bytes(data), complete=name in eof and observed[name][0] == len(data), eof=name in eof,
                                             descriptorClosed=getattr(child, name).closed, observedBytes=observed[name][0], observedSha256=observed[name][1].hexdigest())
            self.guard()
            if not self.sample(False):
                self.known = self.snapshot()
        if failure:
            raise failure
        return bytes(streams["stdout"]), bytes(streams["stderr"])

    def original(self, data, **extra):
        packed = gzip.compress(data, mtime=0); self.compressed += len(packed)
        need(self.compressed <= 9 * MIB, "compressed_originals_bound")
        return dict(bytes=len(data), sha256=sha(data), gzipBase64=base64.b64encode(packed).decode(), **extra)

    def package(self):
        for name, row in self.source.items():
            if name in ("Package.swift", "LICENSE", "THIRD_PARTY.md", "docs/runtime-setup.md", "script/build_and_run.sh") or name.startswith(("Sources/", "Resources/", "Tests/FindletCoreTests/")):
                target = self.root / "export" / name; target.parent.mkdir(parents=True, exist_ok=True)
                data = (self.checkout / name).read_bytes(); need(sha(data) == row["sha256"], "export_source")
                with target.open("xb") as output:
                    output.write(data)
                target.chmod(int(row["mode"], 8) & 0o777)
                need(target.stat().st_size == row["bytes"] and file_sha(target) == row["sha256"], "export_written_bytes")
        rows = self.snapshot()
        for prefix in ("export/Package.swift", "export/LICENSE", "export/THIRD_PARTY.md", "export/docs/runtime-setup.md",
                       "export/Sources", "export/Resources", "export/script", "export/Tests"):
            self.frozen[prefix] = {key: row for key, row in rows.items() if key == prefix or key.startswith(prefix + "/")}
        toolchain = {}
        for name, args in (("host", ["/usr/bin/uname", "-m"]), ("macos", ["/usr/bin/sw_vers", "-productVersion"]),
                           ("xcode", ["/usr/bin/xcodebuild", "-version"]), ("swift", ["/usr/bin/xcrun", "swift", "--version"]),
                           ("sdk", ["/usr/bin/xcrun", "--sdk", "macosx", "--show-sdk-version"])):
            toolchain[name] = self.run(name, args)[0].decode().strip()
        need(toolchain["host"] == "arm64" and toolchain["macos"].split(".")[0] == "15" and int(toolchain["sdk"].split(".")[0]) >= 15
             and toolchain["xcode"] == "Xcode 16.4\nBuild version 16F6", "reviewed_macos_host_sdk")
        self.run("preview-build", ["./script/build_and_run.sh", "--build-preview"], timeout=720)
        dist = self.root / "export/dist"; app = dist / "Findlet.app"; archive = dist / ARCHIVE
        need({p.name for p in dist.iterdir()} == {"Findlet.app", ARCHIVE, ARCHIVE + ".sha256"}, "dist_output_set")
        self.freeze("export/dist")
        expected_files = {"Contents/Info.plist", "Contents/MacOS/Findlet", "Contents/Resources/AppIcon.icns",
                          "Contents/Resources/LICENSE.txt", "Contents/Resources/THIRD_PARTY.md", "Contents/Resources/SETUP.md",
                          "Contents/_CodeSignature/CodeResources"}
        def manifest(bundle):
            rows = {}; attribute_bytes = 0
            for path in [bundle, *bundle.rglob("*")]:
                need(not path.is_symlink() and (path.is_file() or path.is_dir()), "bundle_entry")
                attrs = {}
                for key, value in self.xattrs.read(path).items():
                    attribute_bytes += len(value)
                    need(attribute_bytes <= 256 * 1024, "bundle_xattr_bound")
                    attrs[key] = {"bytes": len(value), "sha256": sha(value), "base64": base64.b64encode(value).decode()}
                row = {"type": "file" if path.is_file() else "directory", "mode": stat.S_IMODE(path.stat().st_mode), "xattrs": attrs}
                if path.is_file():
                    row.update(bytes=path.stat().st_size, sha256=file_sha(path))
                rows[path.relative_to(bundle).as_posix()] = row
            need({p for p, row in rows.items() if row["type"] == "file"} == expected_files
                 and {p for p, row in rows.items() if row["type"] == "directory"} == {".", "Contents", "Contents/MacOS", "Contents/Resources", "Contents/_CodeSignature"}
                 and sum(row.get("bytes", 0) for row in rows.values()) <= 32 * MIB, "bundle_file_set_or_size")
            return rows
        before = manifest(app); binary = app / "Contents/MacOS/Findlet"
        need(before["Contents/Info.plist"]["sha256"] == self.source["Resources/Info.plist"]["sha256"]
             and before["Contents/Resources/AppIcon.icns"]["sha256"] == self.source["Resources/AppIcon.icns"]["sha256"], "bundle_source_metadata_icon")
        for leaf, source in (("LICENSE.txt", "LICENSE"), ("THIRD_PARTY.md", "THIRD_PARTY.md"), ("SETUP.md", "docs/runtime-setup.md")):
            need(before["Contents/Resources/" + leaf]["bytes"] == self.source[source]["bytes"]
                 and before["Contents/Resources/" + leaf]["sha256"] == self.source[source]["sha256"], "bundle_notice_source:" + leaf)
        plist = plistlib.loads((app / "Contents/Info.plist").read_bytes())
        need(plist["CFBundleIdentifier"] == "com.alvarovillalbaa.Findlet" and plist["CFBundleShortVersionString"] == "0.1.1"
             and plist["CFBundleVersion"] == "2" and plist["LSMinimumSystemVersion"] == "15.0" and before["Contents/MacOS/Findlet"]["mode"] & 0o111, "bundle_contract")
        self.run("plist", ["/usr/bin/plutil", "-lint", app / "Contents/Info.plist"])
        need(set(self.run("architectures", ["/usr/bin/lipo", "-archs", binary])[0].decode().split()) == {"arm64", "x86_64"}, "universal_architectures")
        for arch in ("arm64", "x86_64"):
            output = self.run("minimum-os-" + arch, ["/usr/bin/xcrun", "vtool", "-arch", arch, "-show-build", binary])[0].decode()
            need(re.findall(r"^\s*platform\s+(\S+)\s*$", output, re.M) == ["MACOS"] and re.findall(r"^\s*minos\s+(\S+)\s*$", output, re.M) == ["15.0"], "mach_o_minimum_os")
        for arch in ("arm64", "x86_64"):
            linked = self.run("linked-libraries-" + arch, ["/usr/bin/otool", "-arch", arch, "-L", binary])[0].decode()
            dependencies = re.findall(r"^\s+(\S+)\s+\(compatibility version", linked, re.M)
            need(dependencies and all(p.startswith(("/System/Library/", "/usr/lib/", "@rpath/libswift")) for p in dependencies), "external_dynamic_dependency")
            load_commands = self.run("load-commands-" + arch, ["/usr/bin/otool", "-arch", arch, "-l", binary])[0].decode()
            rpaths = re.findall(r"^\s*cmd LC_RPATH\s*\n\s*cmdsize \d+\s*\n\s*path (\S+) \(offset \d+\)\s*$", load_commands, re.M)
            need(len(rpaths) == len(re.findall(r"^\s*cmd LC_RPATH\s*$", load_commands, re.M))
                 and set(rpaths) <= {"/usr/lib/swift", "@executable_path/../Frameworks"}
                 and (not any(p.startswith("@rpath/libswift") for p in dependencies) or "/usr/lib/swift" in rpaths), "unexpected_runtime_search_path:" + arch)
        self.run("signature", ["/usr/bin/codesign", "--verify", "--strict", "--all-architectures", app])
        signature = self.run("signature-details", ["/usr/bin/codesign", "-dv", "--verbose=4", app])[1].decode()
        need("Signature=adhoc" in signature and "Identifier=com.alvarovillalbaa.Findlet" in signature and "TeamIdentifier=not set" in signature, "ad_hoc_signature")
        need(archive.is_file() and not archive.is_symlink() and archive.stat().st_size <= 8 * MIB, "archive_size_or_type")
        data = archive.read_bytes(); need(sha(data) == self.frozen["export/dist"]["export/dist/" + ARCHIVE]["sha256"], "frozen_archive_bytes")
        checksum = (dist / (ARCHIVE + ".sha256")).read_bytes(); need(checksum == (sha(data) + "  " + ARCHIVE + "\n").encode(), "archive_checksum")
        with zipfile.ZipFile(archive) as package:
            entries = package.infolist(); need(len(entries) <= 512 and len({e.filename for e in entries}) == len(entries)
                                              and sum(e.file_size for e in entries) <= 32 * MIB, "zip_expansion")
            for entry in entries:
                safe(entry.filename); need(not entry.flag_bits & 1 and not stat.S_ISLNK(entry.external_attr >> 16), "zip_entry")
                if entry.filename.startswith("__MACOSX/"):
                    if entry.filename == "__MACOSX/":
                        need(entry.is_dir(), "appledouble_container"); continue
                    owner = PurePosixPath(entry.filename.removeprefix("__MACOSX/"))
                    if entry.is_dir():
                        mapped = owner.as_posix()
                    else:
                        need(owner.name.startswith("._") and package.read(entry)[:8] == b"\x00\x05\x16\x07\x00\x02\x00\x00", "appledouble_metadata")
                        mapped = str(owner.with_name(owner.name[2:]))
                    need((mapped == "Findlet.app" or mapped.startswith("Findlet.app/")) and (dist / mapped).exists(), "appledouble_owner")
                else:
                    need(entry.filename.startswith("Findlet.app/") and (dist / entry.filename).exists(), "zip_bundle_entry")
        self.run("fresh-extraction", ["/usr/bin/ditto", "-x", "-k", archive, self.root / "extract"])
        self.freeze("extract")
        need({p.name for p in (self.root / "extract").iterdir()} == {"Findlet.app"} and manifest(self.root / "extract/Findlet.app") == before, "extracted_bundle_byte_mode_manifest")
        self.run("extracted-signature", ["/usr/bin/codesign", "--verify", "--strict", "--all-architectures", self.root / "extract/Findlet.app"])
        distribution = canonical({"schemaVersion": 1, "kind": "findlet.ad-hoc-preview", "sourceCommit": self.commit,
                                  "sourceVectorSha256": sha(canonical(self.source)), "toolchain": toolchain, "architectures": ["arm64", "x86_64"],
                                  "minimumMacOS": "15.0", "signature": "ad-hoc", "bundleManifest": before,
                                  "archive": {"name": ARCHIVE, "bytes": len(data), "sha256": sha(data)},
                                  "testsExecuted": False, "applicationLaunched": False, "capturePerformed": False,
                                  "externalRuntimeBundled": False, "runtimeInstalledOrInvoked": False,
                                  "engineAcceptancePerformed": False, "intelEngineAcceptanceVerified": False,
                                  "trustedDistributionVerified": False, "cleanMachineLaunchVerified": False}) + b"\n"
        self.report.update(retainedOriginals={ARCHIVE: self.original(data), ARCHIVE + ".sha256": self.original(checksum),
                                             "Findlet-preview-manifest.json": self.original(distribution)}, bundleManifest=before, toolchain=toolchain)

    def cleanup(self):
        if self.root is None:
            self.report["cleanup"] = {"verified": True, "created": False}; return
        self.stop(); need(not self.sample(False), "cleanup_processes_remain"); self.guard()
        rows = self.snapshot(); need(rows == self.known, "unregistered_owned_changes")
        self.report["ownedSnapshot"] = {"entries": len(rows), "sha256": sha(canonical(rows))}
        for name in sorted(rows, key=lambda x: (x.count("/"), x), reverse=True):
            need(time.monotonic() < self.cleanup_end, "cleanup_deadline")
            path = self.root / name; row = rows[name]; need(identity(path) == row["identity"], "cleanup_identity")
            if row["type"] == "file":
                need(file_sha(path) == row["sha256"], "cleanup_bytes")
            elif row["type"] == "symlink":
                need(os.readlink(path) == row["target"], "cleanup_symlink")
            path.rmdir() if row["type"] == "directory" else path.unlink()
        need(identity(self.root) == self.root_id and not list(self.root.iterdir()), "cleanup_root")
        self.root.rmdir(); self.guard()
        self.report["cleanup"] = {"verified": True, "created": True, "removedEntries": len(rows), "rootAbsent": not self.root.exists(),
                                  "ownedProcessesRemaining": 0, "attributedProcessGroups": sorted(self.groups), "attributedProcessIdentities": len(self.processes)}

    def execute(self):
        try:
            self.admit(); self.package(); self.guard(); self.known = self.snapshot()
            need(not self.interrupted, "signal_interruption"); self.report["status"] = "passed"
        except BaseException as error:
            self.report["error"] = str(error)[:1024]
        finally:
            try:
                self.cleanup()
            except BaseException as error:
                self.report["cleanup"]["error"] = str(error)[:1024]; self.report["status"] = "failed"
            if self.interrupted or self.signals:
                self.report.update(status="failed", interruptedBySignal=self.interrupted)
            self.report["resources"] = {"maxOwnedBytes": self.max_storage, "maxOwnedRSSBytes": self.max_rss, "maxOwnedProcesses": self.max_processes,
                                        "elapsedSeconds": round(time.monotonic() - self.started, 3), "storageBound": MAX_STORAGE,
                                        "sampledRSSBound": 4096 * MIB, "workBudgetSeconds": 900, "cleanupBudgetSeconds": 150,
                                        "compressedOriginalBytes": self.compressed, "processScope": "Attributed children, inherited owner markers and process groups; excludes unrelated Apple/Xcode services."}
            data = PREFIX + canonical(self.report) + b"\n"; need(len(data) <= MAX_REPORT, "receipt_size")
            descriptor = sys.stdout.fileno(); os.set_blocking(descriptor, False); output = memoryview(data)
            end = min(self.cleanup_end + 5, time.monotonic() + 5)
            try:
                while output:
                    need(time.monotonic() < end, "receipt_write_deadline")
                    if select.select([], [descriptor], [], 0.05)[1]:
                        try:
                            output = output[os.write(descriptor, output):]
                        except BlockingIOError:
                            pass
            except (OSError, RuntimeError):
                return 1
        return 0 if self.report["status"] == "passed" and self.report["cleanup"]["verified"] else 1


if __name__ == "__main__":
    sys.exit(Check().execute())
