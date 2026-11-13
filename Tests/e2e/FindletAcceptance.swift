import AppKit
import CoreGraphics
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
        var windowFrames: [[String: Any]] = []
        var clickIndex = 0
        func phase(_ name: String) { phases.append(name) }
        func wait(_ condition: @escaping () -> Bool, seconds: TimeInterval = 20) {
            XCTAssertEqual(XCTWaiter.wait(for: [XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in condition() }, object: nil)], timeout: seconds), .completed)
        }
        func click(_ element: XCUIElement) {
            XCTAssertTrue(element.waitForExistence(timeout: 20))
            clickIndex += 1
            let ready = XCTNSPredicateExpectation(predicate: NSPredicate { _, _ in element.isHittable && element.isEnabled }, object: nil)
            let result = XCTWaiter.wait(for: [ready], timeout: 15)
            if result != .completed {
                let frame = element.frame
                let value: [String: Any] = ["kind": "findlet.ui-control-readiness", "index": clickIndex,
                    "hittable": element.isHittable, "enabled": element.isEnabled,
                    "x": Double(frame.minX), "y": Double(frame.minY), "width": Double(frame.width), "height": Double(frame.height)]
                if let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]) {
                    let attachment = XCTAttachment(data: data, uniformTypeIdentifier: "public.json")
                    attachment.name = "control-readiness"; attachment.lifetime = .keepAlways; add(attachment)
                }
            }
            XCTAssertEqual(result, .completed)
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
            guard let display = NSScreen.main else { XCTFail("Native display is unavailable"); return }
            XCTAssertEqual(NSScreen.screens.count, 1)
            let visible = display.visibleFrame
            let bounds = CGRect(x: visible.minX, y: display.frame.maxY - visible.maxY, width: visible.width, height: visible.height)
            let owners = NSRunningApplication.runningApplications(withBundleIdentifier: "com.alvarovillalbaa.Findlet").filter { !$0.isTerminated }
            guard owners.count == 1,
                  let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] else {
                XCTFail("One owned native application is required"); return
            }
            let panels = windows.filter {
                ($0[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == owners[0].processIdentifier &&
                ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == NSWindow.Level.floating.rawValue
            }
            guard panels.count == 1, let raw = panels[0][kCGWindowBounds as String] as? [String: Any],
                  let panel = CGRect(dictionaryRepresentation: raw as CFDictionary) else {
                XCTFail("One owned floating search panel is required"); return
            }
            let contained = bounds.insetBy(dx: -1, dy: -1).contains(panel)
            let field = searchField().frame
            let fieldContained = field.width > 0 && field.height > 0 && panel.contains(field)
            let geometry: [String: Any] = ["kind": "findlet.ui-window-frame", "phase": name,
                "x": Double(panel.minX), "y": Double(panel.minY), "width": Double(panel.width), "height": Double(panel.height),
                "withinVisibleDisplay": contained, "searchFieldWithinPanel": fieldContained,
                "source": "ownedWindowServerAndAXSearchField"]
            windowFrames.append(geometry)
            if let data = try? JSONSerialization.data(withJSONObject: geometry, options: [.sortedKeys]) {
                let attachment = XCTAttachment(data: data, uniformTypeIdentifier: "public.json")
                attachment.name = "window-frame"; attachment.lifetime = .keepAlways; add(attachment)
            }
            XCTAssertGreaterThan(panel.width, 0); XCTAssertGreaterThan(panel.height, 0)
            XCTAssertTrue(fieldContained); XCTAssertTrue(searchField().isHittable)
            XCTAssertTrue(contained, "Search panel must stay within the visible display")
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
        // The search panel is nonactivating. Use Findlet's own status menu
        // instead of assuming Command-Q is routed away from the active app.
        let status = app.statusItems["Findlet"].firstMatch
        let menuItem = app.menuBars.menuBarItems["Findlet"].firstMatch
        wait { status.exists || menuItem.exists }
        click(status.exists ? status : menuItem)
        click(app.menuItems["Quit Findlet"].firstMatch)
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
            "windowFrames": windowFrames,
            "nativePickerSelections": 3, "actualKeywordQueries": 3, "expectedTopHits": 2,
            "finderRevealObserved": true, "normalQuitObserved": true, "quitRoute": "ownedStatusMenu", "reopenedDocumentCount": 2,
            "forgottenDocumentCount": 0, "queryOrDocumentValuesRetained": false]
        let attachment = XCTAttachment(data: try JSONSerialization.data(withJSONObject: observation, options: [.sortedKeys, .prettyPrinted]), uniformTypeIdentifier: "public.json")
        attachment.name = "ui-observations"; attachment.lifetime = .keepAlways; add(attachment)
    }
}
