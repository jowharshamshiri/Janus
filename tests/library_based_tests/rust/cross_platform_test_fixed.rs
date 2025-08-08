use std::process::{Command, Stdio};
use std::io::Read;
use tokio::time::{sleep, Duration};
use uuid::Uuid;

/// Test Go client with Rust server using binary-to-binary approach
/// This tests the actual deployed binaries that users will use
#[tokio::test]
async fn test_go_client_to_rust_server_binary() {
    let socket_path = format!("/tmp/cross-platform-test-{}.sock", Uuid::new_v4());
    
    println!("Testing Go client → Rust server cross-platform communication (binary-to-binary)");
    
    // Start Rust server using binary
    let mut rust_server = Command::new("../../../RustJanus/target/release/janus")
        .args(&["--socket", &socket_path, "--listen"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("Failed to start Rust server");
    
    // Give server time to start
    sleep(Duration::from_millis(1000)).await;
    
    // Verify socket exists
    if !std::path::Path::new(&socket_path).exists() {
        let _ = rust_server.kill();
        panic!("Rust server failed to create socket file: {}", socket_path);
    }
    
    println!("Socket file verified: {}", socket_path);
    
    // Execute Go client
    let go_client_output = Command::new("../../../GoJanus/janus")
        .args(&[
            "--send-to", &socket_path,
            "--request", "manifest",
            "--channel", "test"
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .expect("Failed to execute Go client");
    
    let stdout = String::from_utf8_lossy(&go_client_output.stdout);
    let stderr = String::from_utf8_lossy(&go_client_output.stderr);
    
    println!("Go client stdout: {}", stdout);
    println!("Go client stderr: {}", stderr);
    println!("Go client exit code: {}", go_client_output.status.code().unwrap_or(-1));
    
    // Kill server
    let _ = rust_server.kill();
    let _ = rust_server.wait();
    
    // Check if communication succeeded - look for successful response reception
    let communication_successful = stderr.contains("SUCCESS: Received response") 
        && stderr.contains("bytes from");
    
    if communication_successful {
        println!("✓ Go client → Rust server binary communication successful");
    } else {
        assert!(communication_successful, "Go client → Rust server communication failed: {}", stderr);
    }
    
    // Cleanup
    std::fs::remove_file(&socket_path).ok();
}