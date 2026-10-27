import Darwin
import Foundation
import FindletCore

// Direct Node execution avoids bin/qmd's unforwarded child-runtime signals.
// A session owns its PID until waitUntilExit completes; no name-based process killing.
final class QMDProcessRunner: @unchecked Sendable {
    private let lock = NSLock()
    private var active: Session?

    func run(executable: URL, arguments: [String], directory: URL, environment: [String: String]) async throws -> Data {
        let session = Session(executable: executable, arguments: arguments, directory: directory, environment: environment)
        lock.lock(); let occupied = active != nil
        if !occupied { active = session }
        lock.unlock()
        guard !occupied else { throw FindletError.message("A QMD operation is still finishing.") }
        defer { lock.lock(); active = nil; lock.unlock() }
        return try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                DispatchQueue.global(qos: .userInitiated).async {
                    do { continuation.resume(returning: try session.run()) }
                    catch { continuation.resume(throwing: error) }
                }
            }
        } onCancel: { session.cancel() }
    }

    func cancel() async {
        lock.lock(); let session = active; lock.unlock()
        guard let session else { return }
        session.cancel()
        await session.waitForExit()
    }

    private final class Session: @unchecked Sendable {
        private let process = Process()
        private let output = Pipe()
        private let errors = Pipe()
        private let lock = NSLock()
        private var cancelled = false
        private var finished = false
        private var started = false
        private var exceededLimit = false
        private var readFailed = false
        private var stdout = Data()
        private var waiters: [CheckedContinuation<Void, Never>] = []

        init(executable: URL, arguments: [String], directory: URL, environment: [String: String]) {
            process.executableURL = executable; process.arguments = arguments
            process.currentDirectoryURL = directory; process.environment = environment
            process.standardInput = FileHandle.nullDevice
            process.standardOutput = output; process.standardError = errors
        }

        func run() throws -> Data {
            defer { finish() }
            lock.lock()
            if cancelled { lock.unlock(); throw CancellationError() }
            do { try process.run(); started = true; lock.unlock() }
            catch { lock.unlock(); throw FindletError.message("A required local search process could not be started. Check the selected runtime and macOS tools.") }
            let readers = DispatchGroup()
            for (pipe, retainOutput, limit) in [(output, true, 2 * 1_024 * 1_024), (errors, false, 512 * 1_024)] {
                readers.enter()
                DispatchQueue.global(qos: .utility).async { [self] in
                    defer { try? pipe.fileHandleForReading.close(); readers.leave() }
                    var count = 0
                    do {
                        while let chunk = try pipe.fileHandleForReading.read(upToCount: 32_768), !chunk.isEmpty {
                            count += chunk.count
                            lock.lock()
                            if count > limit { exceededLimit = true }
                            if retainOutput && count <= limit { stdout.append(chunk) }
                            lock.unlock()
                            if count > limit { cancel() }
                        }
                    } catch {
                        lock.lock(); readFailed = true; lock.unlock(); cancel()
                    }
                }
            }
            process.waitUntilExit()
            readers.wait()
            lock.lock()
            let wasCancelled = cancelled, tooLarge = exceededLimit, failedRead = readFailed, result = stdout
            lock.unlock()
            if tooLarge { throw FindletError.message("QMD exceeded its output limit and was stopped.") }
            if failedRead { throw FindletError.message("QMD output could not be read.") }
            if wasCancelled { throw CancellationError() }
            guard process.terminationReason == .exit, process.terminationStatus == 0 else {
                throw FindletError.message("QMD did not complete (status \(process.terminationStatus)). Check the configured 2.8.3 installation and prepared CPU runtime. The previous complete index is retained.")
            }
            return result
        }

        func cancel() {
            lock.lock(); cancelled = true
            let shouldSignal = started && !finished && process.isRunning
            if shouldSignal { process.terminate() }
            lock.unlock()
            guard shouldSignal else { return }
            DispatchQueue.global(qos: .utility).asyncAfter(deadline: .now() + 2) { [self] in
                lock.lock(); defer { lock.unlock() }
                if started && !finished && process.isRunning {
                    _ = Darwin.kill(process.processIdentifier, SIGKILL)
                }
            }
        }

        func waitForExit() async {
            await withCheckedContinuation { continuation in
                lock.lock()
                if finished { lock.unlock(); continuation.resume() }
                else { waiters.append(continuation); lock.unlock() }
            }
        }

        private func finish() {
            lock.lock(); finished = true; let pending = waiters; waiters.removeAll(); lock.unlock()
            for continuation in pending { continuation.resume() }
        }
    }
}

actor OperationGate {
    private var held = false
    private var waiters: [CheckedContinuation<Void, Error>] = []
    func enter() async throws {
        if !held { held = true; return }
        guard waiters.count < 32 else { throw FindletError.message("Too many pending operations. Wait for cancellation to finish.") }
        try await withCheckedThrowingContinuation { waiters.append($0) }
    }
    func leave() {
        if waiters.isEmpty { held = false }
        else { waiters.removeFirst().resume() }
    }
}
