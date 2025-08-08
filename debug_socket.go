package main

import (
	"fmt"
	"log"
	"net"
	"os"
	"time"
)

func main() {
	// Create a response socket path
	socketPath := fmt.Sprintf("/tmp/debug_socket_%d.sock", time.Now().UnixNano())
	
	fmt.Printf("Creating socket at: %s\n", socketPath)
	
	// Create and bind the socket
	responseConn, err := net.ListenUnixgram("unixgram", &net.UnixAddr{Name: socketPath, Net: "unixgram"})
	if err != nil {
		log.Fatalf("Failed to bind response socket: %v", err)
	}
	
	fmt.Printf("Socket bound successfully\n")
	
	// Check if file exists
	if _, err := os.Stat(socketPath); err == nil {
		fmt.Printf("✅ Socket file exists: %s\n", socketPath)
	} else {
		fmt.Printf("❌ Socket file does NOT exist: %s\n", socketPath)
	}
	
	// Keep socket alive for testing
	fmt.Printf("Keeping socket alive for 10 seconds...\n")
	
	go func() {
		for i := 0; i < 10; i++ {
			time.Sleep(1 * time.Second)
			if _, err := os.Stat(socketPath); err == nil {
				fmt.Printf("[%ds] Socket file still exists\n", i+1)
			} else {
				fmt.Printf("[%ds] ❌ Socket file disappeared!\n", i+1)
			}
		}
	}()
	
	// Sleep for 10 seconds
	time.Sleep(10 * time.Second)
	
	// Clean up
	responseConn.Close()
	os.Remove(socketPath)
	fmt.Printf("Socket cleaned up\n")
}