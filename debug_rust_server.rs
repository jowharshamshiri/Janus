use std::os::unix::net::UnixDatagram;
use std::fs;

fn main() {
    println!("Starting debug Rust server...");
    
    let socket_path = "/tmp/rust_server_debug.sock";
    
    // Clean up existing socket
    let _ = fs::remove_file(socket_path);
    
    // Bind socket
    let socket = match UnixDatagram::bind(socket_path) {
        Ok(socket) => {
            println!("Successfully bound socket to: {}", socket_path);
            
            // Verify the socket file was actually created
            if std::path::Path::new(socket_path).exists() {
                println!("Socket file confirmed to exist at: {}", socket_path);
            } else {
                eprintln!("WARNING: Socket file does not exist despite successful bind!");
            }
            
            socket
        }
        Err(e) => {
            eprintln!("Failed to bind socket to {}: {}", socket_path, e);
            return;
        }
    };
    
    // Set socket to blocking mode for easier debugging
    if let Err(e) = socket.set_nonblocking(false) {
        eprintln!("Failed to set blocking mode: {}", e);
        return;
    }
    
    println!("Socket is now listening for datagrams...");
    println!("Waiting for data...");
    
    loop {
        let mut buffer = vec![0u8; 64 * 1024];
        
        match socket.recv_from(&mut buffer) {
            Ok((size, sender_addr)) => {
                let data = &buffer[..size];
                let data_str = String::from_utf8_lossy(data);
                let sender_path = sender_addr.as_pathname()
                    .and_then(|p| p.to_str())
                    .unwrap_or("<unknown>");
                
                println!("===== RECEIVED DATA =====");
                println!("Size: {} bytes", size);
                println!("Sender: {}", sender_path);
                println!("Raw data: {:?}", data);
                println!("Data as string: {}", data_str);
                println!("========================");
                
                break; // Exit after first message for debugging
            }
            Err(e) => {
                eprintln!("Error receiving: {}", e);
                break;
            }
        }
    }
    
    // Clean up
    let _ = fs::remove_file(socket_path);
    println!("Debug server exiting");
}