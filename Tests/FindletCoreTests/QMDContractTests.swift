import Foundation
import XCTest
@testable import FindletCore

final class QMDContractTests: XCTestCase {
    private let directory = URL(fileURLWithPath: "/tmp/findlet-authored-generation", isDirectory: true)
    private let folder = FolderSelection(name: "Authored", bookmark: Data())

    private func fixture() -> (IndexManifest, IndexedDocument) {
        let document = IndexedDocument(folderID: folder.id, relativePath: "notes/plan.md", title: "plan.md")
        return (IndexManifest(generation: UUID(), documents: [document], folders: [folder]), document)
    }
    private func data(_ rows: [[String: Any]]) throws -> Data { try JSONSerialization.data(withJSONObject: rows) }
    private func row(_ document: IndexedDocument, score: Double = 0.8) -> [String: Any] {
        ["file": directory.appendingPathComponent("corpus/" + document.snapshotName).path,
         "score": score, "line": 2, "title": "Untrusted title", "snippet": "Authored excerpt"]
    }

    func testOptionLikeQueryRemainsOnePositionalArgumentInEveryMode() throws {
        for mode in SearchMode.allCases {
            let query = "--help; $(not-a-command)\nsecond line"
            let arguments = try QMDContract.searchArguments(query: query, mode: mode)
            XCTAssertEqual(Array(arguments.suffix(2)), ["--", query])
            XCTAssertEqual(arguments.filter { $0 == query }.count, 1)
            XCTAssertEqual(arguments[2], mode.command)
            XCTAssertEqual(arguments[arguments.firstIndex(of: "-c")! + 1], QMDContract.collection)
        }
    }

    func testEmptyNullAndOversizedUTF8QueriesAreRejected() {
        for query in [" \n", "bad\0query", String(repeating: "🟠", count: 1_025)] {
            XCTAssertThrowsError(try QMDContract.searchArguments(query: query, mode: .keyword))
        }
    }

    func testResultsUseManifestIdentityAndOriginalLabels() throws {
        let (manifest, document) = fixture()
        let hits = try QMDContract.decodeResults(data([row(document)]), manifest: manifest, generationURL: directory)
        XCTAssertEqual(hits.count, 1)
        XCTAssertEqual(hits[0].documentID, document.id)
        XCTAssertEqual(hits[0].title, "plan.md")
        XCTAssertEqual(hits[0].path, "notes/plan.md")
        XCTAssertEqual(hits[0].line, 2)
    }

    func testMultipleChunksReturnHighestScoringHitOnce() throws {
        let (manifest, document) = fixture()
        let hits = try QMDContract.decodeResults(data([row(document, score: 0.2), row(document, score: 0.9)]), manifest: manifest, generationURL: directory)
        XCTAssertEqual(hits.count, 1)
        XCTAssertEqual(hits.first?.score, 0.9)
    }

    func testOutsideUnregisteredAndVirtualPathsFailClosed() throws {
        let (manifest, document) = fixture()
        for file in ["/tmp/outside.md", "./corpus/../outside.md", "qmd://findlet_documents/" + document.snapshotName,
                     directory.appendingPathComponent("corpus/unknown.md").path,
                     directory.appendingPathComponent("corpus-sibling/" + document.snapshotName).path] {
            var result = row(document); result["file"] = file
            XCTAssertThrowsError(try QMDContract.decodeResults(data([result]), manifest: manifest, generationURL: directory))
        }
    }

    func testKnownRelativeSnapshotIsAccepted() throws {
        let (manifest, document) = fixture()
        var result = row(document); result["file"] = "./corpus/" + document.snapshotName
        XCTAssertEqual(try QMDContract.decodeResults(data([result]), manifest: manifest, generationURL: directory).count, 1)
    }

    func testInvalidLinesMalformedJSONAndExcessRowsAreRejected() throws {
        let (manifest, document) = fixture()
        var result = row(document); result["line"] = 0
        for value in [try data([result]), Data("{\"results\":[]}".utf8), try data(Array(repeating: row(document), count: 201))] {
            XCTAssertThrowsError(try QMDContract.decodeResults(value, manifest: manifest, generationURL: directory))
        }
    }

    func testEmptyOutputArrayIsARealEmptyResult() throws {
        let (manifest, _) = fixture()
        XCTAssertEqual(try QMDContract.decodeResults(Data("[]".utf8), manifest: manifest, generationURL: directory), [])
    }

    func testDuplicateManifestCannotCrashDictionaryConstruction() throws {
        var (manifest, document) = fixture()
        manifest.documents.append(document)
        XCTAssertThrowsError(try QMDContract.decodeResults(data([row(document)]), manifest: manifest, generationURL: directory))
    }

    func testOversizedProcessOutputIsRejectedBeforeJSONDecoding() {
        let (manifest, _) = fixture()
        XCTAssertThrowsError(try QMDContract.decodeResults(Data(repeating: 32, count: 2 * 1_024 * 1_024 + 1), manifest: manifest, generationURL: directory))
    }
}
