package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"time"

	"github.com/bahram/janus/GoJanus/pkg/models"
	"github.com/bahram/janus/GoJanus/pkg/protocol"
)

func main() {
	socketPath := "/tmp/go-rust-simple-test.sock"
	
	// Start Rust server
	fmt.Println("Starting Rust server...")
	serverCmd := exec.Command(
		"/Users/bahram/ws/prj/Janus/RustJanus/target/debug/janus",
		"--socket", socketPath,
		"--listen",
	)
	
	if err := serverCmd.Start(); err != nil {
		fmt.Printf("Failed to start Rust server: %v\n", err)
		os.Exit(1)
	}
	defer serverCmd.Process.Kill()
	
	// Give server time to start
	time.Sleep(2 * time.Second)
	
	// Create Go client
	fmt.Println("Creating Go client...")
	client, err := protocol.New(socketPath)
	if err != nil {
		fmt.Printf("Failed to create Go client: %v\n", err)
		os.Exit(1)
	}
	
	// Test ping request
	fmt.Println("Sending ping request...")
	response, err := client.SendRequest("ping", nil, nil)
	if err != nil {
		fmt.Printf("Ping request failed: %v\n", err)
		os.Exit(1)
	}
	
	fmt.Printf("Ping response: %+v\n", response)
	
	// Test manifest request
	fmt.Println("\nSending manifest request...")
	response, err = client.SendRequest("manifest", nil, nil)
	if err != nil {
		fmt.Printf("Manifest request failed: %v\n", err)
		os.Exit(1)
	}
	
	// Print full response
	responseJSON, _ := json.MarshalIndent(response, "", "  ")
	fmt.Printf("Manifest response:\n%s\n", responseJSON)
	
	// Parse manifest from result
	if response.Success && response.Result != nil {
		resultBytes, _ := json.Marshal(response.Result)
		var manifest models.Manifest
		if err := json.Unmarshal(resultBytes, &manifest); err != nil {
			fmt.Printf("Failed to parse manifest: %v\n", err)
		} else {
			fmt.Printf("\nParsed manifest version: %s\n", manifest.Version)
		}
	}
	
	fmt.Println("\n✅ Go client to Rust server communication successful!")
}