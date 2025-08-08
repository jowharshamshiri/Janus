#!/bin/bash

# Kill any existing processes
pkill -f "janus --socket"
rm -f /tmp/go-rust-test.sock*

# Start Rust server
echo "Starting Rust server..."
cd /Users/bahram/ws/prj/Janus
RustJanus/target/debug/janus --socket /tmp/go-rust-test.sock --listen &
RUST_PID=$!

# Give server time to start
sleep 2

# Send request from Go client
echo -e "\nSending ping from Go client..."
cd GoJanus
go run cmd/janus/main.go --send-to /tmp/go-rust-test.sock --request ping

echo -e "\nSending manifest request from Go client..."
go run cmd/janus/main.go --send-to /tmp/go-rust-test.sock --request manifest

# Kill server
kill $RUST_PID

echo -e "\n✅ Test complete!"