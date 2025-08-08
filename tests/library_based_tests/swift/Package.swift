// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "JanusLibraryTestsSwift",
    platforms: [
        .macOS(.v13)
    ],
    dependencies: [
        .package(path: "../../../SwiftJanus")
    ],
    targets: [
        .executableTarget(
            name: "TestClient",
            dependencies: ["SwiftJanus"]
        ),
        .executableTarget(
            name: "TestServer",
            dependencies: ["SwiftJanus"]
        ),
        .testTarget(
            name: "LibraryTestsSwift",
            dependencies: ["SwiftJanus"],
            path: "Tests"
        )
    ]
)