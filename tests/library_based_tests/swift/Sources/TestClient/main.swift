
import Foundation
import SwiftJanus

@main
struct ClientApp {
    static func main() async {
        let serverSocket = CommandLine.arguments[1]
        
        do {
            let client = try await JanusClient(socketPath: serverSocket)
            
            // Test 1: Manifest request
            let manifestResponse = try await client.sendRequest("manifest")
            
            if manifestResponse.success,
               let result = manifestResponse.result?.value as? [String: Any],
               let version = result["version"] as? String {
                print("MANIFEST_VERSION:\(version)")
            }
            
            // Test 2: Echo request
            let echoResponse = try await client.sendRequest("echo", 
                args: ["message": AnyCodable("Hello from Swift"),
                       "timestamp": AnyCodable(ISO8601DateFormatter().string(from: Date()))])
            
            if echoResponse.success,
               let result = echoResponse.result?.value {
                if let jsonData = try? JSONSerialization.data(withJSONObject: result),
                   let jsonString = String(data: jsonData, encoding: .utf8) {
                    print("ECHO_RESULT:\(jsonString)")
                }
            }
            
            // Test 3: Custom request (if available)
            let customResponse = try await client.sendRequest("custom_test",
                args: ["test_param": AnyCodable("swift_value")])
            
            if customResponse.success,
               let result = customResponse.result?.value {
                if let jsonData = try? JSONSerialization.data(withJSONObject: result),
                   let jsonString = String(data: jsonData, encoding: .utf8) {
                    print("CUSTOM_RESULT:\(jsonString)")
                }
            }
            
            print("TEST_COMPLETE")
            
        } catch {
            print("Test failed: \(error)")
            exit(1)
        }
    }
}
