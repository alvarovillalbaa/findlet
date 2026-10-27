// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "Findlet",
    platforms: [.macOS("15.0")],
    products: [
        .executable(name: "Findlet", targets: ["Findlet"]),
        .library(name: "FindletCore", targets: ["FindletCore"]),
    ],
    targets: [
        .target(name: "FindletCore"),
        .executableTarget(name: "Findlet", dependencies: ["FindletCore"]),
        .testTarget(name: "FindletCoreTests", dependencies: ["FindletCore"]),
    ]
)
