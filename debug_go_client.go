package main

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"time"
)

type JanusRequest struct {
	ID        string                 `json:"id"`
	Method    string                 `json:"method"`
	ChannelID string                 `json:"channelId"`
	Request   string                 `json:"request"`
	ReplyTo   string                 `json:"reply_to"`
	Args      map[string]interface{} `json:"args"`
	Timeout   float64                `json:"timeout"`
	Timestamp string                 `json:"timestamp"`
}

func main() {
	fmt.Println("Starting debug Go client...")

	// Create a manifest request
	request := JanusRequest{
		ID:        "debug-test-123",
		Method:    "manifest",
		ChannelID: "system",
		Request:   "manifest",
		ReplyTo:   "/tmp/go_client_debug.sock",
		Args:      make(map[string]interface{}),
		Timeout:   5.0,
		Timestamp: time.Now().UTC().Format("2006-01-02T15:04:05.000Z"),
	}

	// Marshal to JSON
	requestData, err := json.Marshal(request)
	if err != nil {
		fmt.Printf("Error marshaling request: %v\n", err)
		return
	}

	fmt.Printf("Sending request: %s\n", string(requestData))

	// Create Unix datagram socket with temporary client socket
	clientAddr, err := net.ResolveUnixAddr("unixgram", "/tmp/go_debug_client.sock")
	if err != nil {
		fmt.Printf("Error resolving client address: %v\n", err)
		return
	}

	// Clean up any existing client socket
	os.Remove("/tmp/go_debug_client.sock")

	conn, err := net.ListenUnixgram("unixgram", clientAddr)
	if err != nil {
		fmt.Printf("Error creating client socket: %v\n", err)
		return
	}
	defer conn.Close()
	defer os.Remove("/tmp/go_debug_client.sock")

	// Resolve server address
	serverAddr, err := net.ResolveUnixAddr("unixgram", "/tmp/rust_janus_test.sock")
	if err != nil {
		fmt.Printf("Error resolving server address: %v\n", err)
		return
	}

	// Send the request using WriteTo
	n, err := conn.WriteTo(requestData, serverAddr)
	if err != nil {
		fmt.Printf("Error sending request: %v\n", err)
		return
	}

	fmt.Printf("Successfully sent %d bytes to Rust server\n", n)
	fmt.Println("Request sent successfully!")
}