import Darwin
import Foundation
import FindletCore

enum SourceFileAccess {
    struct Root {
        let url: URL
        let descriptor: Int32
        let identity: stat
    }

    static func withRoot<T>(_ selection: FolderSelection, body: (Root) throws -> T) throws -> T {
        try Task.checkCancellation()
        var stale = false
        let url: URL
        do {
            url = try URL(resolvingBookmarkData: selection.bookmark,
                          options: [.withoutUI, .withoutMounting],
                          relativeTo: nil, bookmarkDataIsStale: &stale)
        } catch {
            throw FindletError.message("A selected folder could not be resolved. Select it again in Settings.")
        }
        guard !stale, url.isFileURL else {
            throw FindletError.message("A selected folder bookmark is stale. Select that folder again in Settings.")
        }
        let scoped = url.startAccessingSecurityScopedResource()
        defer { if scoped { url.stopAccessingSecurityScopedResource() } }
        let descriptor = try openAbsoluteDirectory(url)
        defer { Darwin.close(descriptor) }
        let info = try information(descriptor)
        guard try isEligible(url: url, info: info, directory: true) else {
            throw FindletError.message("Choose a visible, local folder outside a package. Cloud-only folders are not indexed.")
        }
        return try body(Root(url: url, descriptor: descriptor, identity: info))
    }

    static func openAbsoluteDirectory(_ url: URL) throws -> Int32 {
        guard url.isFileURL, url.path.hasPrefix("/"), !url.path.utf8.contains(0) else {
            throw FindletError.message("The folder location is not a safe local path.")
        }
        let components = url.path.split(separator: "/", omittingEmptySubsequences: true).map(String.init)
        try validate(components: components, allowEmpty: true)
        var current = Darwin.open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC)
        guard current >= 0 else { throw readFailure() }
        do {
            for component in components {
                try Task.checkCancellation()
                let next = component.withCString {
                    Darwin.openat(current, $0, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
                }
                guard next >= 0 else { throw readFailure() }
                Darwin.close(current)
                current = next
            }
            return current
        } catch {
            Darwin.close(current)
            throw error
        }
    }

    static func validate(components: [String], allowEmpty: Bool = false) throws {
        guard (allowEmpty || !components.isEmpty),
              components.allSatisfy({ !$0.isEmpty && $0 != "." && $0 != ".." &&
                  !$0.contains("/") && !$0.utf8.contains(0) }) else {
            throw FindletError.message("A document has an unsafe relative path.")
        }
    }

    static func information(_ descriptor: Int32) throws -> stat {
        var result = stat()
        guard Darwin.fstat(descriptor, &result) == 0 else { throw readFailure() }
        return result
    }

    private static func duplicate(_ descriptor: Int32) throws -> Int32 {
        let copy = Darwin.fcntl(descriptor, F_DUPFD_CLOEXEC, 0)
        guard copy >= 0 else { throw readFailure() }
        return copy
    }

    static func entryInformation(in descriptor: Int32, name: String) throws -> stat {
        var result = stat()
        let status = name.withCString { Darwin.fstatat(descriptor, $0, &result, AT_SYMLINK_NOFOLLOW) }
        guard status == 0 else { throw readFailure() }
        return result
    }

    static func isDirectory(_ info: stat) -> Bool {
        info.st_mode & mode_t(S_IFMT) == mode_t(S_IFDIR)
    }

    static func isRegular(_ info: stat) -> Bool {
        info.st_mode & mode_t(S_IFMT) == mode_t(S_IFREG)
    }

    static func isExcludedByFlags(_ info: stat) -> Bool {
        info.st_flags & UInt32(UF_HIDDEN | SF_DATALESS) != 0
    }

    static func sameObject(_ lhs: stat, _ rhs: stat) -> Bool {
        lhs.st_dev == rhs.st_dev && lhs.st_ino == rhs.st_ino &&
            lhs.st_mode & mode_t(S_IFMT) == rhs.st_mode & mode_t(S_IFMT)
    }

    static func unchanged(_ lhs: stat, _ rhs: stat) -> Bool {
        sameObject(lhs, rhs) && lhs.st_size == rhs.st_size && lhs.st_flags == rhs.st_flags &&
            lhs.st_mtimespec.tv_sec == rhs.st_mtimespec.tv_sec &&
            lhs.st_mtimespec.tv_nsec == rhs.st_mtimespec.tv_nsec &&
            lhs.st_ctimespec.tv_sec == rhs.st_ctimespec.tv_sec &&
            lhs.st_ctimespec.tv_nsec == rhs.st_ctimespec.tv_nsec
    }

    static func isEligible(url: URL, info: stat, directory: Bool) throws -> Bool {
        guard !isExcludedByFlags(info) else { return false }
        let values: URLResourceValues
        do {
            values = try url.resourceValues(forKeys: [
                .isHiddenKey, .isPackageKey, .volumeIsLocalKey,
                .isUbiquitousItemKey, .ubiquitousItemDownloadingStatusKey,
            ])
        } catch { throw readFailure() }
        guard values.isHidden != true, values.volumeIsLocal == true else { return false }
        if directory && values.isPackage == true { return false }
        if values.isUbiquitousItem == true {
            guard values.ubiquitousItemDownloadingStatus == .current ||
                    values.ubiquitousItemDownloadingStatus == .downloaded else { return false }
        }
        return true
    }

    static func openDirectory(in parent: Int32, name: String, expected: stat) throws -> Int32 {
        let descriptor = name.withCString {
            Darwin.openat(parent, $0, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
        }
        guard descriptor >= 0 else { throw readFailure() }
        do {
            let actual = try information(descriptor)
            guard isDirectory(actual), sameObject(expected, actual), !isExcludedByFlags(actual) else {
                throw changedFailure()
            }
            return descriptor
        } catch {
            Darwin.close(descriptor)
            throw error
        }
    }

    static func withRegularFile<T>(root: Root, components: [String], expected: stat? = nil,
                                   body: (Int32, stat, URL) throws -> T) throws -> T {
        try validate(components: components)
        try assertRootUnchanged(root)
        var parent = try duplicate(root.descriptor)
        defer { Darwin.close(parent) }
        var url = root.url
        for component in components.dropLast() {
            try Task.checkCancellation()
            let info = try entryInformation(in: parent, name: component)
            url.appendPathComponent(component, isDirectory: true)
            guard isDirectory(info), !component.hasPrefix("."),
                  try isEligible(url: url, info: info, directory: true) else { throw changedFailure() }
            let next = try openDirectory(in: parent, name: component, expected: info)
            Darwin.close(parent)
            parent = next
        }
        let name = components.last!
        let info = try entryInformation(in: parent, name: name)
        url.appendPathComponent(name, isDirectory: false)
        guard isRegular(info), !name.hasPrefix("."),
              try isEligible(url: url, info: info, directory: false),
              expected.map({ unchanged($0, info) }) ?? true else { throw changedFailure() }
        // O_NONBLOCK prevents a regular-file-to-FIFO swap from blocking open.
        let descriptor = name.withCString {
            Darwin.openat(parent, $0, O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC)
        }
        guard descriptor >= 0 else { throw readFailure() }
        defer { Darwin.close(descriptor) }
        let opened = try information(descriptor)
        guard isRegular(opened), unchanged(info, opened), !isExcludedByFlags(opened) else { throw changedFailure() }
        let result = try body(descriptor, opened, url)
        let after = try entryInformation(in: parent, name: name)
        guard unchanged(opened, after) else { throw changedFailure() }
        try assertCurrentFile(root: root, components: components, expected: opened)
        try assertRootUnchanged(root)
        return result
    }

    static func forEachEntry(in descriptor: Int32, body: (String) throws -> Void) throws {
        let copy = try duplicate(descriptor)
        guard let stream = Darwin.fdopendir(copy) else {
            Darwin.close(copy)
            throw readFailure()
        }
        defer { Darwin.closedir(stream) }
        while true {
            try Task.checkCancellation()
            errno = 0
            guard let pointer = Darwin.readdir(stream) else {
                guard errno == 0 else { throw readFailure() }
                break
            }
            var entry = pointer.pointee
            let count = Int(entry.d_namlen)
            let name = withUnsafePointer(to: &entry.d_name) { pointer -> String? in
                let bytes = UnsafeRawPointer(pointer).assumingMemoryBound(to: UInt8.self)
                return String(bytes: UnsafeBufferPointer(start: bytes, count: count), encoding: .utf8)
            }
            guard let name else {
                throw FindletError.message("A selected folder contains a filename that is not valid UTF-8. Rename it before rebuilding.")
            }
            if name == "." || name == ".." { continue }
            try validate(components: [name])
            try body(name)
        }
    }

    static func assertRootUnchanged(_ root: Root) throws {
        let current = try openAbsoluteDirectory(root.url)
        defer { Darwin.close(current) }
        guard sameObject(root.identity, try information(current)) else { throw changedFailure() }
    }

    static func overlaps(_ root: Root, with other: URL) throws -> Bool {
        let otherFD = try openAbsoluteDirectory(other)
        defer { Darwin.close(otherFD) }
        let otherInfo = try information(otherFD)
        return try hasAncestor(root.identity, of: other) || hasAncestor(otherInfo, of: root.url)
    }

    private static func hasAncestor(_ ancestor: stat, of url: URL) throws -> Bool {
        let components = url.path.split(separator: "/", omittingEmptySubsequences: true).map(String.init)
        try validate(components: components, allowEmpty: true)
        var current = Darwin.open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC)
        guard current >= 0 else { throw readFailure() }
        defer { Darwin.close(current) }
        if sameObject(ancestor, try information(current)) { return true }
        for component in components {
            try Task.checkCancellation()
            let next = component.withCString {
                Darwin.openat(current, $0, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
            }
            guard next >= 0 else { throw readFailure() }
            Darwin.close(current)
            current = next
            if sameObject(ancestor, try information(current)) { return true }
        }
        return false
    }

    private static func assertCurrentFile(root: Root, components: [String], expected: stat) throws {
        var parent = try duplicate(root.descriptor)
        defer { Darwin.close(parent) }
        for component in components.dropLast() {
            try Task.checkCancellation()
            let info = try entryInformation(in: parent, name: component)
            guard isDirectory(info), !isExcludedByFlags(info) else { throw changedFailure() }
            let next = try openDirectory(in: parent, name: component, expected: info)
            Darwin.close(parent)
            parent = next
        }
        let name = components.last!
        let descriptor = name.withCString {
            Darwin.openat(parent, $0, O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC)
        }
        guard descriptor >= 0 else { throw changedFailure() }
        defer { Darwin.close(descriptor) }
        let current = try information(descriptor)
        guard isRegular(current), unchanged(expected, current), !isExcludedByFlags(current) else {
            throw changedFailure()
        }
    }

    static func readFailure() -> FindletError {
        .message("A selected folder or file could not be read safely. Check access and select the folder again if it moved.")
    }

    static func changedFailure() -> FindletError {
        .message("A selected file or folder changed during access. Originals were not modified; rebuild the index again.")
    }
}
