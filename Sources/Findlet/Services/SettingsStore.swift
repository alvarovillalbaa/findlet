import Foundation
import Darwin
import FindletCore

struct StoredFindletSetup: Codable {
    var version = 1
    var settings = FindletSettings()
    var indexedFolders: [FolderSelection]?
    var indexedRuntime: RuntimeConfiguration?
    var preparedRuntime: RuntimeConfiguration?
}

func runtimeIdentity(_ runtime: RuntimeConfiguration) -> RuntimeConfiguration {
    var result = runtime
    result.modelPreparationAccepted = false
    return result
}

/// An unreadable or concurrently changed settings file is never replaced by
/// defaults. The user can repair the original and explicitly retry loading it.
@MainActor
final class SettingsStore {
    let url: URL
    private var loadedBytes: Data?
    private var mayWrite = false
    private let maximumBytes = 8 * 1024 * 1024

    init(applicationSupport: URL) { url = applicationSupport.appendingPathComponent("settings.json") }

    func load() throws -> StoredFindletSetup {
        mayWrite = false
        if !FileManager.default.fileExists(atPath: url.path) {
            // A dangling symlink also needs preserving.
            if (try? FileManager.default.destinationOfSymbolicLink(atPath: url.path)) != nil {
                throw FindletError.message("The settings file is a symbolic link. It was left unchanged.")
            }
            loadedBytes = nil
            mayWrite = true
            return StoredFindletSetup()
        }
        let data = try boundedData()
        let result: StoredFindletSetup
        do { result = try JSONDecoder().decode(StoredFindletSetup.self, from: data) }
        catch { throw FindletError.message("Findlet's saved settings could not be read. The original file was left unchanged.") }
        try validate(result)
        loadedBytes = data
        mayWrite = true
        return result
    }

    func save(_ setup: StoredFindletSetup) throws {
        guard mayWrite else { throw FindletError.message("Repair or reload the existing settings before saving changes. The original file has not been replaced.") }
        try validate(setup)
        let folder = url.deletingLastPathComponent()
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        let parent = try folder.resourceValues(forKeys: [.isSymbolicLinkKey, .isDirectoryKey])
        guard parent.isDirectory == true, parent.isSymbolicLink != true else {
            throw FindletError.message("The settings folder is not a regular local directory.")
        }
        try verifyExpectedContents()
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(setup)
        guard data.count <= maximumBytes else { throw FindletError.message("These settings exceed the supported size. The existing file was preserved.") }
        let temporary = folder.appendingPathComponent(".\(UUID().uuidString).settings.tmp")
        let descriptor = open(temporary.path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, mode_t(0o600))
        guard descriptor >= 0 else { throw FindletError.message("A private settings update could not be created. Existing settings were preserved.") }
        var published = false
        defer { if !published { try? FileManager.default.removeItem(at: temporary) } }
        let handle = FileHandle(fileDescriptor: descriptor, closeOnDealloc: true)
        do {
            try handle.write(contentsOf: data)
            try handle.synchronize()
            try handle.close()
        } catch {
            try? handle.close()
            throw error
        }
        try verifyExpectedContents()
        guard rename(temporary.path, url.path) == 0 else {
            throw FindletError.message("The settings update could not be completed. Existing settings were preserved.")
        }
        published = true
        loadedBytes = data
    }

    private func verifyExpectedContents() throws {
        if let loadedBytes {
            guard try boundedData() == loadedBytes else {
                mayWrite = false
                throw FindletError.message("Settings changed outside this window. Reload settings before saving; the existing file was preserved.")
            }
        } else if FileManager.default.fileExists(atPath: url.path)
                    || (try? FileManager.default.destinationOfSymbolicLink(atPath: url.path)) != nil {
            mayWrite = false
            throw FindletError.message("A settings file appeared since setup began. Reload it before saving.")
        }
    }

    private func boundedData() throws -> Data {
        try validateRegularFile(url)
        let descriptor = open(url.path, O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC)
        guard descriptor >= 0 else { throw FindletError.message("The settings file could not be read safely. It was left unchanged.") }
        let handle = FileHandle(fileDescriptor: descriptor, closeOnDealloc: true)
        defer { try? handle.close() }
        var before = stat()
        guard fstat(descriptor, &before) == 0, before.st_mode & mode_t(S_IFMT) == mode_t(S_IFREG),
              before.st_size >= 0, before.st_size <= Int64(maximumBytes) else {
            throw FindletError.message("The settings file is invalid or too large. It was left unchanged.")
        }
        var data = Data()
        while data.count <= maximumBytes {
            let count = min(64 * 1024, maximumBytes + 1 - data.count)
            guard count > 0 else { break }
            guard let chunk = try handle.read(upToCount: count), !chunk.isEmpty else { break }
            data.append(chunk)
        }
        var after = stat()
        guard data.count <= maximumBytes, fstat(descriptor, &after) == 0, Int64(data.count) == after.st_size,
              before.st_dev == after.st_dev, before.st_ino == after.st_ino, before.st_size == after.st_size,
              before.st_mtimespec.tv_sec == after.st_mtimespec.tv_sec,
              before.st_mtimespec.tv_nsec == after.st_mtimespec.tv_nsec,
              before.st_ctimespec.tv_sec == after.st_ctimespec.tv_sec,
              before.st_ctimespec.tv_nsec == after.st_ctimespec.tv_nsec else {
            throw FindletError.message("The settings file changed while it was read. Reload it; the original was not replaced.")
        }
        return data
    }

    private func validateRegularFile(_ url: URL) throws {
        let values = try url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
        guard values.isRegularFile == true, values.isSymbolicLink != true else {
            throw FindletError.message("The settings path is not a regular file. It was left unchanged.")
        }
    }

    private func validate(_ setup: StoredFindletSetup) throws {
        guard setup.version == 1 else { throw FindletError.message("These settings use an unsupported version. The original file was preserved.") }
        try validateFolders(setup.settings.folders)
        if let folders = setup.indexedFolders { try validateFolders(folders) }
        for runtime in [setup.settings.runtime, setup.indexedRuntime, setup.preparedRuntime].compactMap({ $0 }) {
            let paths = [runtime.nodePath, runtime.qmdPackagePath, runtime.embeddingModelPath,
                         runtime.expansionModelPath, runtime.rerankerModelPath]
            guard paths.allSatisfy({ $0.utf8.count <= 16_384 && !$0.contains("\0") && ($0.isEmpty || $0.hasPrefix("/")) }) else {
                throw FindletError.message("Saved runtime paths are invalid. The settings file was left unchanged.")
            }
        }
    }

    private func validateFolders(_ folders: [FolderSelection]) throws {
        guard folders.count <= 32, Set(folders.map(\.id)).count == folders.count,
              folders.allSatisfy({ !$0.name.isEmpty && $0.name.count <= 200 && !$0.bookmark.isEmpty && $0.bookmark.count <= 1_048_576 }) else {
            throw FindletError.message("Saved folder selections are invalid or exceed their limits. The original settings were preserved.")
        }
    }
}
