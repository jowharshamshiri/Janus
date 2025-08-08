# JANUS PRIME DIRECTIVE - MESSAGE FORMAT STANDARDIZATION

## CRITICAL PROTOCOL MANIFEST

**ALL** Janus implementations across Go, Rust, Swift, and TypeScript MUST use these exact message formats for 100% cross-platform compatibility.

**NO BACKWARD COMPATIBILITY**: This project does not maintain legacy code or support backward compatibility. All implementations must implement the current standardized message formats without exception.

### Message Format Requirements

Every JanusRequest MUST contain exactly these fields:

```json
{
  "id": <unique_uuid_for_this_request>,
  "method": <method_name_being_invoked>,
  "channelId": <channel_routing_identifier>,
  "request": <request_name_legacy_field>,
  "reply_to": <response_socket_path>,
  "args": <request_arguments_object>,
  "timeout": <timeout_in_seconds>,
  "timestamp": "2025-08-06T12:34:56.789Z"
}
```

Every JanusResponse MUST contain exactly these fields:

```json
{
  "result": <unwrapped_actual_response_data>,
  "error": <json_rpc_error_object_or_null>,
  "success": <boolean_indicator>,
  "request_id": <id_of_original_request>,
  "id": <unique_id_for_this_response>,
  "timestamp": "2025-08-06T12:34:56.789Z"
}
```

### Request Field Manifests

- **`id`**: UUID v4 string for unique request identification
- **`method`**: Method name being invoked (1-256 chars, alphanumeric + `-_`)
- **`channelId`**: Channel routing identifier (1-256 chars, alphanumeric + `-_`)
- **`request`**: Request name (1-256 chars, alphanumeric + `-_`)
- **`reply_to`**: Response socket path for reply correlation
- **`args`**: Request arguments object (optional, max 5MB)
- **`timeout`**: Timeout in seconds (optional, 0.1-300.0, default: 30.0)
- **`timestamp`**: RFC 3339 timestamp with milliseconds (YYYY-MM-DDTHH:MM:SS.sssZ)

### Response Field Manifests

- **`result`**: The actual unwrapped response data (not wrapped in additional objects)
- **`error`**: JSONRPCError object if error occurred, `null` if success
- **`success`**: Boolean indicator - `true` for success, `false` for error
- **`request_id`**: The exact ID from the original request being responded to
- **`id`**: Unique identifier for this manifestific response message
- **`timestamp`**: RFC 3339 timestamp with milliseconds (YYYY-MM-DDTHH:MM:SS.sssZ)

### Timestamp Format Requirements

**RFC 3339 with milliseconds**: `2025-08-06T12:34:56.789Z`
- **Format**: YYYY-MM-DDTHH:MM:SS.sssZ (ISO 8601 subset)
- **Timezone**: UTC (Z) timezone only
- **Precision**: Exactly 3 millisecond digits

**Language Implementation Guidelines**:
- **Rust**: `chrono::DateTime::parse_from_rfc3339()` / `to_rfc3339()`
- **Go**: `time.RFC3339Nano` truncated to milliseconds
- **TypeScript**: `new Date().toISOString()` / `Date.parse()`
- **Swift**: `ISO8601DateFormatter` with `.withFractionalSeconds`

### Cross-Platform Compatibility Requirements

1. **100% Field Consistency**: Every implementation must use identical field names
2. **100% Type Consistency**: Field types must match exactly across implementations  
3. **100% Response Tracking**: Each response must be individually trackable
4. **100% Error Handling**: Error format must be identical across implementations
5. **100% Message Framing**: Response structure must be byte-for-byte compatible

### Implementation Priority

**ALL FUTURE SESSIONS** are dedicated to achieving this until complete:
- Fix Go implementation request/response formats
- Fix Rust implementation request/response formats  
- Fix Swift implementation request/response formats
- Fix TypeScript implementation request/response formats
- Verify 100% cross-platform communication in 16-combination matrix (4x4)

### Success Criteria

Cross-platform communication is considered complete when:
1. Go client → Rust/Swift/TypeScript servers work seamlessly
2. Rust client → Go/Swift/TypeScript servers work seamlessly
3. Swift client → Go/Rust/TypeScript servers work seamlessly
4. TypeScript client → Go/Rust/Swift servers work seamlessly
5. All 16 combinations pass library-based testing with 100% success rate

### Verification Request

```bash
cd /Users/bahram/ws/prj/Janus/tests/library_based_tests
python3 orchestrator/test_orchestrator.py
```

**Target**: All tests pass with 100% success rate across all 16 client-server combinations.

---

**This manifest overrides all previous response format decisions and is mandatory for all implementations.**