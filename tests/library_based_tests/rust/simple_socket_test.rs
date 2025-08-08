use std::os::unix::net::UnixDatagram;
use tokio::time::{timeout, Duration};

/// Simple test to verify Rust server can receive datagram from basic Unix socket
#[tokio::test]
async fn test_basic_datagram_communication() {
    let server_socket = "/tmp/simple-test-server.sock";
    let client_socket = "/tmp/simple-test-client.sock";
    
    // Remove any existing sockets
    std::fs::remove_file(server_socket).ok();
    std::fs::remove_file(client_socket).ok();
    
    // Create server socket
    let server = UnixDatagram::bind(server_socket).expect("Failed to bind server socket");
    server.set_nonblocking(true).expect("Failed to set non-blocking");
    
    println!("Server bound to: {}", server_socket);
    
    // Create client and send message
    let client = UnixDatagram::bind(client_socket).expect("Failed to bind client socket");
    let test_message = b"Hello from client";
    client.send_to(test_message, server_socket).expect("Failed to send message");
    
    println!("Client sent message: {:?}", std::str::from_utf8(test_message));
    
    // Try to receive on server
    let mut buffer = [0u8; 1024];
    let receive_result = timeout(Duration::from_secs(2), async {
        loop {
            match server.recv_from(&mut buffer) {
                Ok((size, addr)) => {
                    let received = &buffer[..size];
                    println!("Server received {} bytes: {:?}", size, std::str::from_utf8(received));
                    return (size, addr);
                }
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                    tokio::time::sleep(Duration::from_millis(10)).await;
                    continue;
                }
                Err(e) => panic!("Receive error: {}", e),
            }
        }
    }).await;
    
    match receive_result {
        Ok((size, _addr)) => {
            let received = &buffer[..size];
            assert_eq!(received, test_message);
            println!("✓ Basic datagram communication successful");
        }
        Err(_) => {
            panic!("Timeout waiting for message");
        }
    }
    
    // Cleanup
    std::fs::remove_file(server_socket).ok();
    std::fs::remove_file(client_socket).ok();
}