import Foundation
import XCTest

// T3: actual native app, QMD and owned local SQLite; authored files only.
final class FindletAcceptance: XCTestCase {
    @MainActor
    func testNUI01ConfigureSearchReopenAndForget() throws {
        continueAfterFailure = false
        let configURL = try XCTUnwrap(Bundle(for: Self.self).url(forResource: "FixtureConfig", withExtension: "json"))
        let config = try XCTUnwrap(JSONSerialization.jsonObject(with: Data(contentsOf: configURL)) as? [String: String])
        let folder = try XCTUnwrap(config["folder"])
        let node = try XCTUnwrap(config["node"])
        let package = try XCTUnwrap(config["package"])
        let app = XCUIApplication(bundleIdentifier: "com.alvarovillalbaa.Findlet")
        var phases: [String] = []
        func phase(_ name: String) { phases.append(name) }
        func wait(_ condition: @escaping () -> Bool, seconds: TimeInterval = 20) {
            XCTAssertEqual(XCTWaiter.wait(for: [XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in condition() }, object: nil)], timeout: seconds), .completed)
        }
        func click(_ element: XCUIElement) {
            XCTAssertTrue(element.waitForExistence(timeout: 20))
            XCTAssertTrue(element.isHittable); element.click()
        }
        func choose(_ path: String) {
            app.typeKey("g", modifierFlags: [.command, .shift])
            app.typeText(path); app.typeKey(.return, modifierFlags: [])
            click(app.dialogs.buttons["Open"].firstMatch)
        }
        func searchField() -> XCUIElement { app.searchFields["Search selected documents"].firstMatch }
        func replaceQuery(_ value: String) {
            click(searchField()); app.typeKey("a", modifierFlags: .command)
            app.typeKey(.delete, modifierFlags: []); if !value.isEmpty { app.typeText(value) }
        }
        func showSearch() {
            app.typeKey(" ", modifierFlags: [.control, .option])
            XCTAssertTrue(searchField().waitForExistence(timeout: 15))
        }
        func picture(_ name: String) {
            // Query/results, setup paths and automatic diagnostics are withheld.
            XCTAssertEqual(searchField().value as? String, "")
            let image = XCTAttachment(screenshot: app.screenshot()); image.name = name
            image.lifetime = .keepAlways; add(image)
        }
        defer { app.terminate() }
        app.launch()
        XCTAssertTrue(app.staticTexts["Choose what to search"].waitForExistence(timeout: 20))
        picture("01-empty-setup"); phase("firstLaunchSetup")
        click(app.buttons["Set Up Findlet…"])
        click(app.buttons["Add Folders…"]); choose(folder)
        click(app.buttons["Choose node executable"]); choose(node)
        click(app.buttons["Choose qmd 2.8.3 package"]); choose(package)
        let rebuild = app.buttons["Rebuild Local Index"].firstMatch
        wait { rebuild.exists && rebuild.isEnabled }; rebuild.click()
        XCTAssertTrue(app.staticTexts["Indexed 2 local documents. Type a query to search."].firstMatch.waitForExistence(timeout: 90))
        phase("nativePickersAndActualRebuild")
        app.typeKey("w", modifierFlags: .command); showSearch()
        XCTAssertTrue(app.staticTexts["Local · QMD 2.8.3 · 2 indexed documents"].exists)
        picture("02-ready-empty"); phase("shortcutOpensSearch")
        replaceQuery("quartzvelvetnative")
        let alpha = app.buttons["orchard.txt. orchard.txt"].firstMatch
        XCTAssertTrue(alpha.waitForExistence(timeout: 45)); XCTAssertTrue(app.staticTexts["1 results"].exists)
        app.typeKey(.downArrow, modifierFlags: [])
        XCTAssertTrue(alpha.isSelected)
        click(app.buttons["Reveal in Finder"])
        let finder = XCUIApplication(bundleIdentifier: "com.apple.finder")
        let authoredWindow = finder.windows["authored-findlet"]
        XCTAssertTrue(authoredWindow.waitForExistence(timeout: 15))
        XCTAssertTrue(finder.staticTexts["orchard.txt"].firstMatch.waitForExistence(timeout: 15))
        phase("actualKeywordHitAndFinderReveal")
        authoredWindow.click(); finder.typeKey("w", modifierFlags: .command)
        app.activate(); showSearch(); replaceQuery("")
        app.typeKey(.escape, modifierFlags: [])
        wait { !searchField().exists || !searchField().isHittable }
        showSearch(); phase("escapeAndShortcutReopen")
        replaceQuery("noauthoredmatchnative")
        XCTAssertTrue(app.staticTexts["No matching documents"].waitForExistence(timeout: 45))
        replaceQuery("")
        click(app.radioButtons["Semantic"].firstMatch)
        XCTAssertTrue(app.staticTexts["Prepare semantic search explicitly"].waitForExistence(timeout: 15))
        click(app.radioButtons["Keyword"].firstMatch); phase("emptyAndUnpreparedStates")
        app.typeKey("q", modifierFlags: .command)
        wait { app.state == .notRunning }; phase("normalQuit")
        app.launch(); showSearch()
        XCTAssertTrue(app.staticTexts["Local · QMD 2.8.3 · 2 indexed documents"].waitForExistence(timeout: 20))
        picture("03-reopened-empty")
        replaceQuery("cobaltlilacnative")
        XCTAssertTrue(app.buttons["harbor.md. harbor.md"].firstMatch.waitForExistence(timeout: 45))
        replaceQuery(""); phase("persistentReopenAndSecondSearch")
        click(app.buttons["Open Settings"])
        click(app.buttons["Forget Findlet Index…"])
        click(app.buttons["Forget Index"].firstMatch)
        XCTAssertTrue(app.staticTexts["0 documents in Findlet's current index."].firstMatch.waitForExistence(timeout: 30))
        app.typeKey("w", modifierFlags: .command); showSearch()
        XCTAssertTrue(app.staticTexts["Rebuild to use this setup"].waitForExistence(timeout: 15))
        picture("04-forgotten-empty"); phase("nativeForgetConfirmation")
        let observation: [String: Any] = ["caseId": "NUI01", "status": "passed", "phases": phases,
            "nativePickerSelections": 3, "actualKeywordQueries": 3, "expectedTopHits": 2,
            "finderRevealObserved": true, "normalQuitObserved": true, "reopenedDocumentCount": 2,
            "forgottenDocumentCount": 0, "queryOrDocumentValuesRetained": false]
        let attachment = XCTAttachment(data: try JSONSerialization.data(withJSONObject: observation, options: [.sortedKeys, .prettyPrinted]), uniformTypeIdentifier: "public.json")
        attachment.name = "ui-observations"; attachment.lifetime = .keepAlways; add(attachment)
    }
}
