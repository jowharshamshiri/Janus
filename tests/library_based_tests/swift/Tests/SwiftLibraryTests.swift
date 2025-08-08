import XCTest
import SwiftJanus
import Foundation

final class SwiftLibraryTests: XCTestCase {
    
    /// Test Swift library manifest request directly
    /// This test would catch the "manifest" wrapper bug
    func testSwiftLibraryManifestRequest() async throws {
        let socketPath = "/tmp/swift-lib-test-\(UUID().uuidString).sock"
        defer { try? FileManager.default.removeItem(atPath: socketPath) }
        
        // Start Swift server using library (not binary)
        let server = JanusServer()
        
        // Start server in background task
        let serverTask = Task {
            try await server.startListening(socketPath)
        }
        
        // Give server time to start
        try await Task.sleep(nanoseconds: 100_000_000) // 100ms
        
        // Create Swift client using library (not binary)
        let client = try await JanusClient(socketPath: socketPath)
        
        // Test manifest request using library
        let result = try await client.sendRequest("manifest")
        
        // CRITICAL: Validate actual response structure - this would catch the bug
        XCTAssertTrue(result.success, "Response should be successful")
        XCTAssertNotNil(result.result, "Response should contain result data")
        
        if let manifestData = result.result {
            if let manifestDict = manifestData.value as? [String: Any] {
                XCTAssertTrue(manifestDict.keys.contains("version"), 
                             "Manifest response should contain version")
                XCTAssertTrue(manifestDict.keys.contains("models"), 
                             "Manifest response should contain models")
                
                // CRITICAL: This assertion catches the "manifest" wrapper bug
                XCTAssertFalse(manifestDict.keys.contains("manifest"), 
                              "Manifest response should NOT be wrapped in manifest field")
                
                print("✅ Swift library manifest request test PASSED")
                print("Version: \(manifestDict["version"] ?? "nil")")
                print("Models: \(manifestDict["models"] ?? "nil")")
            } else {
                XCTFail("Response result should be a dictionary")
            }
        } else {
            XCTFail("Response should contain result data")
        }
        
        print("Swift manifest response structure: \(result)")
        
        // Cancel server task
        serverTask.cancel()
    }
    
    /// Test Swift library message format validation
    func testSwiftLibraryMessageFormat() throws {
        // Test JanusRequest structure
        let request = JanusRequest(
            id: "test-id-123",
            request: "ping",
            replyTo: nil,
            args: ["message": AnyCodable("test")]
        )
        
        // Serialize to JSON and validate structure
        let encoder = JSONEncoder()
        let data = try encoder.encode(request)
        let json = try JSONSerialization.jsonObject(with: data) as! [String: Any]
        
        // Validate required fields
        XCTAssertNotNil(json["id"], "Request should have id field")
        XCTAssertNotNil(json["request"], "Request should have request field")
        XCTAssertNotNil(json["args"], "Request should have args field")
        
        print("Swift JanusRequest JSON: \(String(data: data, encoding: .utf8) ?? "invalid")")
        
        // Test JanusResponse structure per PRIME DIRECTIVE format
        let response = JanusResponse(
            requestId: "test-id-123",
            success: true,
            result: AnyCodable(["data": "test"]),
            error: nil
        )
        
        let responseData = try encoder.encode(response)
        let responseJson = try JSONSerialization.jsonObject(with: responseData) as! [String: Any]
        
        // Validate required fields (PRIME DIRECTIVE format)
        XCTAssertNotNil(responseJson["request_id"], "Response should have request_id field")
        XCTAssertNotNil(responseJson["success"], "Response should have success field")
        XCTAssertNotNil(responseJson["result"], "Response should have result field")
        XCTAssertNotNil(responseJson["id"], "Response should have id field")
        XCTAssertNotNil(responseJson["timestamp"], "Response should have timestamp field")
        
        // CRITICAL: Error field should be omitted when null
        if response.error == nil {
            // When error is nil, field should be omitted or null
            if let errorField = responseJson["error"] {
                XCTAssertTrue(errorField is NSNull, "Error field should be null when error is nil")
            }
        }
        
        print("Swift JanusResponse JSON: \(String(data: responseData, encoding: .utf8) ?? "invalid")")
    }
    
    /// Test all built-in requests for format consistency
    func testSwiftBuiltinRequests() async throws {
        let socketPath = "/tmp/swift-builtin-test-\(UUID().uuidString).sock"
        defer { try? FileManager.default.removeItem(atPath: socketPath) }
        
        // Start server
        let server = JanusServer()
        let serverTask = Task {
            try await server.startListening(socketPath)
        }
        
        try await Task.sleep(nanoseconds: 100_000_000) // 100ms
        
        // Create client
        let client = try await JanusClient(socketPath: socketPath)
        
        let requests = ["ping", "echo", "get_info", "validate", "slow_process", "manifest"]
        
        for cmd in requests {
            let args: [String: AnyCodable]? = cmd == "manifest" ? nil : ["message": AnyCodable("test")]
            
            do {
                let result = try await client.sendRequest(cmd, args: args)
                XCTAssertTrue(result.success, "\(cmd) should be successful")
                XCTAssertNotNil(result.result, "\(cmd) result should not be nil")
                
                // For manifest request, validate it's not wrapped
                if cmd == "manifest" {
                    if let manifestData = result.result,
                       let manifestDict = manifestData.value as? [String: Any] {
                        XCTAssertFalse(manifestDict.keys.contains("manifest"), 
                                      "Manifest should not be wrapped in manifest field")
                        XCTAssertTrue(manifestDict.keys.contains("version"), "Manifest should have version")
                        XCTAssertTrue(manifestDict.keys.contains("models"), "Manifest should have models")
                    } else {
                        XCTFail("Response result should be a dictionary")
                    }
                }
                
                print("\(cmd) response structure: \(result)")
            } catch {
                XCTFail("\(cmd) request failed: \(error)")
            }
        }
        
        serverTask.cancel()
    }
    
    /// Test Swift server startup and basic functionality
    func testSwiftServerStartup() async throws {
        let socketPath = "/tmp/swift-startup-test-\(UUID().uuidString).sock"
        defer { try? FileManager.default.removeItem(atPath: socketPath) }
        
        // Test server creation
        let server = JanusServer()
        
        // Start server with timeout
        let serverTask = Task {
            try await server.startListening(socketPath)
        }
        
        // Give server brief time to start
        try await Task.sleep(nanoseconds: 50_000_000) // 50ms
        
        // Server should start successfully (task is running)
        XCTAssertFalse(serverTask.isCancelled, "Server task should be running")
        
        // Validate socket file exists (should be created during startup)
        let socketExists = FileManager.default.fileExists(atPath: socketPath)
        if socketExists {
            print("Socket file created successfully")
        }
        
        serverTask.cancel()
    }
}

/// Test cross-platform communication between Swift and other implementations
final class SwiftCrossPlatformTests: XCTestCase {
    
    /// Test Swift client → Go server communication
    func testSwiftClientToGoServer() async throws {
        let socketPath = "/tmp/swift-to-go-test-\(UUID().uuidString).sock"
        defer { try? FileManager.default.removeItem(atPath: socketPath) }
        
        // Start Go server using binary (need the Go server for cross-platform test)
        let goServerProcess = Process()
        goServerProcess.executableURL = URL(fileURLWithPath: "/Users/bahram/ws/prj/Janus/GoJanus/janus")
        goServerProcess.arguments = ["--listen", "--socket", socketPath]
        
        try goServerProcess.run()
        
        // Give server time to start
        try await Task.sleep(nanoseconds: 200_000_000) // 200ms
        
        // Test Swift client → Go server using library
        do {
            let client = try await JanusClient(socketPath: socketPath)
            
            let result = try await client.sendRequest("manifest")
            
            print("✅ Swift client → Go server communication successful")
            print("Response: \(result)")
            
            // Validate response structure
            XCTAssertTrue(result.success, "Response should be successful")
            if let manifestData = result.result,
               let manifestDict = manifestData.value as? [String: Any] {
                XCTAssertTrue(manifestDict.keys.contains("version"), "Response should contain version")
                XCTAssertTrue(manifestDict.keys.contains("models"), "Response should contain models")
                // Should not be wrapped in manifest field
                XCTAssertFalse(manifestDict.keys.contains("manifest"), 
                              "Should not have manifest wrapper")
            } else {
                XCTFail("Response result should be a dictionary")
            }
        } catch {
            XCTFail("Swift client → Go server failed: \(error)")
        }
        
        // Cleanup
        goServerProcess.terminate()
    }
    
    /// Test Go client → Swift server communication
    func testGoClientToSwiftServer() async throws {
        let socketPath = "/tmp/go-to-swift-test-\(UUID().uuidString).sock"
        defer { try? FileManager.default.removeItem(atPath: socketPath) }
        
        // Start Swift server using library
        let server = JanusServer()
        let serverTask = Task {
            try await server.startListening(socketPath)
        }
        
        // Give server time to start and bind socket
        try await Task.sleep(nanoseconds: 200_000_000) // 200ms
        
        // Test Go client → Swift server manifest request
        let goClientProcess = Process()
        goClientProcess.executableURL = URL(fileURLWithPath: "/Users/bahram/ws/prj/Janus/GoJanus/janus")
        goClientProcess.arguments = [
            "--send-to", socketPath,
            "--request", "manifest"
        ]
        
        let pipe = Pipe()
        goClientProcess.standardOutput = pipe
        let errorPipe = Pipe()
        goClientProcess.standardError = errorPipe
        
        try goClientProcess.run()
        goClientProcess.waitUntilExit()
        
        let outputData = pipe.fileHandleForReading.readDataToEndOfFile()
        let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()
        let stdout = String(data: outputData, encoding: .utf8) ?? ""
        let stderr = String(data: errorData, encoding: .utf8) ?? ""
        
        print("Go client stdout: \(stdout)")
        print("Go client stderr: \(stderr)")
        print("Go client exit code: \(goClientProcess.terminationStatus)")
        
        // CRITICAL: This should now succeed after fixing the Swift server
        XCTAssertEqual(goClientProcess.terminationStatus, 0, "Go client → Swift server should succeed")
        
        // Parse the output to validate response structure
        if stdout.contains("Success=true") {
            print("✅ Go client → Swift server communication successful")
            
            // Validate the response contains proper manifest structure
            XCTAssertTrue(stdout.contains("version"), "Response should contain version")
            XCTAssertTrue(stdout.contains("models"), "Response should contain models")
            
            // CRITICAL: Should NOT contain "manifest" wrapper
            XCTAssertFalse(stdout.contains("manifest:"), "Should not have manifest wrapper")
        } else {
            XCTFail("Go client → Swift server failed: \(stderr)")
        }
        
        serverTask.cancel()
    }
}