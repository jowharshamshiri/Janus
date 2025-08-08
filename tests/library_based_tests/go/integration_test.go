package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"GoJanus/pkg/protocol"
	"GoJanus/pkg/server"
	"GoJanus/pkg/models"
)

// TestGoLibraryManifestRequest tests the manifest request using Go libraries directly
// This catches bugs that binary-based tests miss
func TestGoLibraryManifestRequest(t *testing.T) {
	// Setup test socket path
	socketPath := fmt.Sprintf("/tmp/go-lib-test-%d.sock", time.Now().UnixNano())
	defer os.Remove(socketPath)

	// Start Go server using library (not binary)
	config := &server.ServerConfig{
		SocketPath: socketPath,
	}
	srv := server.NewJanusServer(config)
	require.NotNil(t, srv, "Failed to create server")

	// Use server event system to detect when ready
	serverReady := make(chan bool, 1)
	serverError := make(chan error, 1)

	// Register listening event handler
	srv.On("listening", func(data interface{}) {
		select {
		case serverReady <- true:
		default:
		}
	})

	// Register error event handler
	srv.On("error", func(data interface{}) {
		if err, ok := data.(error); ok {
			select {
			case serverError <- err:
			default:
			}
		}
	})

	// Start server in background
	go func() {
		err := srv.StartListening()
		if err != nil {
			select {
			case serverError <- err:
			default:
			}
		}
	}()

	// Wait for server to be ready
	select {
	case <-serverReady:
		// Server started successfully
	case err := <-serverError:
		t.Fatalf("Server failed to start: %v", err)
	case <-time.After(5 * time.Second):
		t.Fatal("Server startup timeout")
	}

	// Give server time to bind socket
	time.Sleep(100 * time.Millisecond)

	// Create Go client using library (not binary)
	client, err := protocol.New(socketPath)
	require.NoError(t, err, "Failed to create client")
	require.NotNil(t, client, "Client should not be nil")

	// Test manifest request using library
	t.Run("ManifestRequest", func(t *testing.T) {
		ctx := context.Background()
		response, err := client.SendRequest(ctx, "manifest", nil)
		require.NoError(t, err, "Manifest request should succeed")
		require.NotNil(t, response, "Manifest response should not be nil")
		require.True(t, response.Success, "Manifest request should be successful")

		// The result should be unwrapped direct value (not map[string]interface{})
		result := response.Result
		require.NotNil(t, result, "Result should not be nil")

		// Result should be a manifest object (map containing version, channels)
		resultMap, ok := result.(map[string]interface{})
		require.True(t, ok, "Result should be map[string]interface{} for manifest")
		
		// Validate manifest response structure
		assert.Contains(t, resultMap, "version", "Manifest response should contain version")
		assert.Contains(t, resultMap, "models", "Manifest response should contain models")
		
		// Validate response is proper manifest format (not wrapped)
		version, ok := resultMap["version"].(string)
		assert.True(t, ok, "Version should be string")
		assert.NotEmpty(t, version, "Version should not be empty")

		_, ok = resultMap["models"].(map[string]interface{})
		assert.True(t, ok, "Models should be map")

		// CRITICAL: Ensure response is NOT wrapped in "manifest" field
		_, hasManifestWrapper := resultMap["manifest"]
		assert.False(t, hasManifestWrapper, "CRITICAL: Manifest response should NOT be wrapped in 'manifest' field")

		// Log actual response structure for debugging
		t.Logf("Manifest response structure: %+v", resultMap)
	})

	// Test other built-in requests for format consistency
	t.Run("BuiltInRequests", func(t *testing.T) {
		// Test ping without args (it doesn't take parameters)
		t.Run("ping", func(t *testing.T) {
			ctx := context.Background()
			response, err := client.SendRequest(ctx, "ping", nil)
			require.NoError(t, err, "ping request should succeed")
			require.NotNil(t, response, "ping response should not be nil")
			require.True(t, response.Success, "ping should be successful")
			require.NotNil(t, response.Result, "ping result should not be nil")
			t.Logf("ping response structure: %+v", response.Result)
		})

		// Test requests that require message argument
		requestsWithMessage := []string{"echo", "validate"}
		for _, cmd := range requestsWithMessage {
			t.Run(cmd, func(t *testing.T) {
				ctx := context.Background()
				args := map[string]interface{}{"message": "test"}
				response, err := client.SendRequest(ctx, cmd, args)
				require.NoError(t, err, fmt.Sprintf("%s request should succeed", cmd))
				require.NotNil(t, response, fmt.Sprintf("%s response should not be nil", cmd))
				require.True(t, response.Success, fmt.Sprintf("%s should be successful", cmd))
				require.NotNil(t, response.Result, fmt.Sprintf("%s result should not be nil", cmd))
				t.Logf("%s response structure: %+v", cmd, response.Result)
			})
		}

		// Test requests without arguments
		requestsWithoutArgs := []string{"get_info", "slow_process"}
		for _, cmd := range requestsWithoutArgs {
			t.Run(cmd, func(t *testing.T) {
				ctx := context.Background()
				response, err := client.SendRequest(ctx, cmd, nil)
				require.NoError(t, err, fmt.Sprintf("%s request should succeed", cmd))
				require.NotNil(t, response, fmt.Sprintf("%s response should not be nil", cmd))
				require.True(t, response.Success, fmt.Sprintf("%s should be successful", cmd))
				require.NotNil(t, response.Result, fmt.Sprintf("%s result should not be nil", cmd))
				t.Logf("%s response structure: %+v", cmd, response.Result)
			})
		}
	})
}

// TestGoLibraryMessageFormat validates actual message structures
func TestGoLibraryMessageFormat(t *testing.T) {
	socketPath := fmt.Sprintf("/tmp/go-format-test-%d.sock", time.Now().UnixNano())
	defer os.Remove(socketPath)

	// Create client
	client, err := protocol.New(socketPath)
	require.NoError(t, err, "Failed to create client")
	require.NotNil(t, client)

	t.Run("JanusRequestStructure", func(t *testing.T) {
		// Create a request and validate its JSON structure
		cmd := models.JanusRequest{
			ID:        "test-id-123",
			Request:   "ping",
			Args:      map[string]interface{}{"message": "test"},
			ReplyTo:   nil,
		}

		// Serialize to JSON
		data, err := json.Marshal(cmd)
		require.NoError(t, err, "Request should serialize to JSON")

		// Parse back and validate structure
		var parsed map[string]interface{}
		err = json.Unmarshal(data, &parsed)
		require.NoError(t, err, "JSON should parse back to map")

		// Validate required fields
		assert.Contains(t, parsed, "id", "Request should have id field")
		assert.Contains(t, parsed, "request", "Request should have request field")
		assert.Contains(t, parsed, "args", "Request should have args field")

		// Log actual JSON structure
		t.Logf("JanusRequest JSON: %s", string(data))
	})

	t.Run("JanusResponseStructure", func(t *testing.T) {
		// Create a response and validate structure
		response := models.JanusResponse{
			RequestID: "test-id-123",
			ID:        "response-id-456",
			Success:   true,
			Result:    map[string]interface{}{"data": "test"},
			Error:     nil,
			Timestamp: "2025-08-06T12:34:56.789Z",
		}

		// Serialize to JSON
		data, err := json.Marshal(response)
		require.NoError(t, err, "Response should serialize to JSON")

		// Parse back and validate structure
		var parsed map[string]interface{}
		err = json.Unmarshal(data, &parsed)
		require.NoError(t, err, "JSON should parse back to map")

		// Validate required fields per PRIME DIRECTIVE format
		assert.Contains(t, parsed, "request_id", "Response should have request_id field")
		assert.Contains(t, parsed, "id", "Response should have id field")
		assert.Contains(t, parsed, "success", "Response should have success field")
		assert.Contains(t, parsed, "result", "Response should have result field")
		assert.Contains(t, parsed, "timestamp", "Response should have timestamp field")

		// CRITICAL: Validate error field handling
		if response.Error == nil {
			// When error is nil, field should be omitted or null
			if errorField, exists := parsed["error"]; exists {
				assert.Nil(t, errorField, "Error field should be null when error is nil")
			}
		}

		// Log actual JSON structure  
		t.Logf("JanusResponse JSON: %s", string(data))
	})
}

// TestGoLibraryServerStartup validates server can start and respond
func TestGoLibraryServerStartup(t *testing.T) {
	socketPath := fmt.Sprintf("/tmp/go-startup-test-%d.sock", time.Now().UnixNano())
	defer os.Remove(socketPath)

	// Test server startup
	config := &server.ServerConfig{
		SocketPath: socketPath,
	}
	srv := server.NewJanusServer(config)
	require.NotNil(t, srv, "Should create server")

	// Use event system to detect server ready
	ready := make(chan bool, 1)
	
	// Register listening event handler
	srv.On("listening", func(data interface{}) {
		select {
		case ready <- true:
		default:
		}
	})
	
	// Start server
	go func() {
		srv.StartListening()
	}()

	// Wait for server ready
	select {
	case <-ready:
		t.Log("Server started successfully")
	case <-time.After(5 * time.Second):
		t.Fatal("Server startup timeout")
	}

	// Validate socket file exists
	_, err := os.Stat(socketPath)
	assert.NoError(t, err, "Socket file should exist")
}