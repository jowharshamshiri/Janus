
use std::env;
use tokio::runtime::Runtime;
use rust_janus::{JanusServer, ServerConfig, JSONRPCError};
use serde_json;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <socket_path>", args[0]);
        std::process::exit(1);
    }
    
    let socket_path = &args[1];
    println!("🔧 Starting Rust server with socket: {}", socket_path);
    
    // Remove existing socket
    let _ = std::fs::remove_file(socket_path);
    
    let rt = Runtime::new().unwrap();
    rt.block_on(async {
        println!("🔧 Creating server config...");
        let config = ServerConfig {
            socket_path: socket_path.to_string(),
            max_connections: 10,
            default_timeout: 30,
            max_message_size: 65536,
            cleanup_on_start: true,
            cleanup_on_shutdown: true,
        };
        
        println!("🔧 Creating JanusServer instance...");
        let mut server = JanusServer::new(config);
        
        println!("🔧 Registering custom_test handler...");
        server.register_handler("custom_test", |request| {
            println!("🎯 custom_test handler called with request: {:?}", request);
            let test_param = request.args
                .as_ref()
                .and_then(|args| args.get("test_param"))
                .and_then(|v| v.as_str())
                .unwrap_or("unknown");
            
            let response = serde_json::json!({
                "result": "custom_test_success", 
                "received_param": test_param,
                "handler_called": true
            });
            
            println!("🎯 custom_test returning: {:?}", response);
            Ok(response)
        }).await;
        
        println!("🔧 Handler registered successfully");
        
        println!("🔧 Starting server listening...");
        if let Err(e) = server.start_listening().await {
            eprintln!("❌ Failed to start server: {}", e);
            std::process::exit(1);
        }
        
        println!("SERVER_READY");
        println!("🔧 Server ready and listening...");
        
        // Enhanced wait with periodic status
        tokio::select! {
            result = server.wait_for_completion() => {
                match result {
                    Ok(_) => println!("🔧 Server completed successfully"),
                    Err(e) => eprintln!("❌ Server error: {}", e)
                }
            }
            _ = tokio::signal::ctrl_c() => {
                println!("🔧 Received interrupt signal, shutting down...");
            }
        }
    });
}
