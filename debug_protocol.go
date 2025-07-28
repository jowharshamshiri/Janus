package main

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	"net"
	"time"
)

func main() {
	// Connect to socket
	conn, err := net.Dial("unix", "/tmp/test_manual.sock")
	if err != nil {
		panic(err)
	}
	defer conn.Close()

	// Create a simple ping command
	command := map[string]interface{}{
		"id":         "test-123",
		"channelId":  "test",
		"command":    "ping",
		"args":       map[string]interface{}{},
		"timeout":    5.0,
		"timestamp":  time.Now().UTC().Format(time.RFC3339),
	}

	// Serialize to JSON
	cmdBytes, _ := json.Marshal(command)
	fmt.Printf("Sending command: %s\n", string(cmdBytes))

	// Send with 4-byte length prefix
	length := uint32(len(cmdBytes))
	binary.Write(conn, binary.BigEndian, length)
	conn.Write(cmdBytes)

	// Read response
	var respLength uint32
	binary.Read(conn, binary.BigEndian, &respLength)
	fmt.Printf("Response length: %d\n", respLength)

	respBytes := make([]byte, respLength)
	conn.Read(respBytes)
	fmt.Printf("Response: %s\n", string(respBytes))
}