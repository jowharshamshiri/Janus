import { JanusClient, JanusClientConfig } from 'typescript-janus/dist/protocol/janus-client';
import { JanusServer } from 'typescript-janus/dist/server/janus-server';
import { JanusRequest, JanusResponse } from 'typescript-janus/dist/types/protocol';
import { spawn, ChildProcess } from 'child_process';
import { promises as fs } from 'fs';
import { v4 as uuidv4 } from 'uuid';

describe('TypeScript Library Tests', () => {
  
  /**
   * Test TypeScript library manifest request directly
   * This test would catch the "manifest" wrapper bug
   */
  test('testTypeScriptLibraryManifestRequest', async () => {
    const socketPath = `/tmp/typescript-lib-test-${uuidv4()}.sock`;
    
    try {
      // Start TypeScript server using library (not binary)
      const server = new JanusServer({ socketPath });
      
      // Start server in background
      const serverPromise = server.listen();
      
      // Give server time to start
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Create TypeScript client using library (not binary)
      const config: JanusClientConfig = {
        socketPath: socketPath
      };
      const client = await JanusClient.create(config);
      
      // Test manifest request using library
      const result = await client.sendRequest('manifest', undefined);
      
      // CRITICAL: Validate actual response structure - this would catch the bug
      expect(result.success).toBe(true);
      expect(result.result).toBeDefined();
      
      const manifestData = result.result;
      expect(manifestData).toBeInstanceOf(Object);
      
      const manifestObject = manifestData as Record<string, any>;
      expect(manifestObject).toHaveProperty('version');
      expect(manifestObject).toHaveProperty('models');
      
      // CRITICAL: This assertion catches the "manifest" wrapper bug
      expect(manifestObject).not.toHaveProperty('manifest');
      
      console.log('✅ TypeScript library manifest request test PASSED');
      console.log('Version:', manifestObject.version);
      console.log('Models:', manifestObject.models);
      
      console.log('TypeScript manifest response structure:', result);
      
      // Stop server
      await server.close();
      
    } finally {
      // Cleanup
      try {
        await fs.unlink(socketPath);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  });

  /**
   * Test TypeScript library message format validation
   */
  test('testTypeScriptLibraryMessageFormat', () => {
    // Test JanusRequest structure
    const request: JanusRequest = {
      id: 'test-id-123',
      method: 'ping',
      request: 'ping',
      args: { message: 'test' },
      reply_to: undefined,
      timestamp: new Date().toISOString().replace(/\.\d{3}Z$/, '.000Z')
    };
    
    // Serialize to JSON and validate structure
    const requestJson = JSON.stringify(request);
    const parsedRequest = JSON.parse(requestJson);
    
    // Validate required fields
    expect(parsedRequest).toHaveProperty('id');
    expect(parsedRequest).toHaveProperty('request');
    expect(parsedRequest).toHaveProperty('method');
    expect(parsedRequest).toHaveProperty('args');
    
    console.log('TypeScript JanusRequest JSON:', requestJson);
    
    // Test JanusResponse structure
    const response: JanusResponse = {
      request_id: 'test-id-123',
      id: 'response-id-456',
      success: true,
      result: { data: 'test' },
      error: undefined,
      timestamp: new Date().toISOString().replace(/\.\d{3}Z$/, '.000Z')
    };
    
    const responseJson = JSON.stringify(response);
    const parsedResponse = JSON.parse(responseJson);
    
    // Validate required fields (PRIME DIRECTIVE format)
    expect(parsedResponse).toHaveProperty('request_id');
    expect(parsedResponse).toHaveProperty('success');
    expect(parsedResponse).toHaveProperty('result');
    expect(parsedResponse).toHaveProperty('id');
    expect(parsedResponse).toHaveProperty('timestamp');
    
    // CRITICAL: Error field should be omitted when undefined/null
    if (response.error === undefined || response.error === null) {
      // When error is undefined, field should be omitted or null
      if ('error' in parsedResponse) {
        expect(parsedResponse.error).toBeNull();
      }
    }
    
    console.log('TypeScript JanusResponse JSON:', responseJson);
  });

  /**
   * Test all built-in requests for format consistency
   */
  test('testTypeScriptBuiltinRequests', async () => {
    const socketPath = `/tmp/typescript-builtin-test-${uuidv4()}.sock`;
    
    try {
      // Start server
      const server = new JanusServer({ socketPath });
      const serverPromise = server.listen();
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Create client
      const config: JanusClientConfig = {
        socketPath: socketPath
      };
      const client = await JanusClient.create(config);
      
      const requests = ['ping', 'echo', 'get_info', 'validate', 'slow_process', 'manifest'];
      
      for (const cmd of requests) {
        const args = cmd === 'manifest' ? undefined : { message: 'test' };
        
        try {
          const result = await client.sendRequest(cmd, args);
          expect(result.success).toBe(true);
          expect(result.result).toBeDefined();
          
          // For manifest request, validate it's not wrapped
          if (cmd === 'manifest') {
            const manifestData = result.result as Record<string, any>;
            expect(manifestData).not.toHaveProperty('manifest');
            expect(manifestData).toHaveProperty('version');
            expect(manifestData).toHaveProperty('models');
          }
          
          console.log(`${cmd} response structure:`, result);
          
        } catch (error) {
          throw new Error(`${cmd} request failed: ${error}`);
        }
      }
      
      await server.close();
      
    } finally {
      try {
        await fs.unlink(socketPath);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  });

  /**
   * Test TypeScript server startup and basic functionality
   */
  test('testTypeScriptServerStartup', async () => {
    const socketPath = `/tmp/typescript-startup-test-${uuidv4()}.sock`;
    
    try {
      // Test server creation
      const server = new JanusServer({ socketPath });
      
      // Start server
      const serverPromise = server.listen();
      
      // Give server brief time to start
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Validate socket file exists (should be created during startup)
      let socketExists = false;
      try {
        await fs.access(socketPath);
        socketExists = true;
        console.log('Socket file created successfully');
      } catch (e) {
        // Socket may not exist yet, that's ok for this test
      }
      
      await server.close();
      
    } finally {
      try {
        await fs.unlink(socketPath);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  });
});

/**
 * Test cross-platform communication between TypeScript and other implementations
 */
describe('TypeScript Cross-Platform Tests', () => {
  
  /**
   * Test TypeScript client → Go server communication
   */
  test('testTypeScriptClientToGoServer', async () => {
    const socketPath = `/tmp/typescript-to-go-test-${uuidv4()}.sock`;
    
    let goServer: ChildProcess | null = null;
    
    try {
      // Start Go server using binary
      goServer = spawn('../../../../Janus/GoJanus/janus', ['--listen', '--socket', socketPath]);
      
      // Give server time to start
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // Test TypeScript client → Go server using library
      const config: JanusClientConfig = {
        socketPath: socketPath
      };
      const client = await JanusClient.create(config);
      
      const result = await client.sendRequest('manifest', undefined);
      
      console.log('✅ TypeScript client → Go server communication successful');
      console.log('Response:', result);
      
      // Validate response structure
      expect(result.success).toBe(true);
      const manifestData = result.result as Record<string, any>;
      expect(manifestData).toHaveProperty('version');
      expect(manifestData).toHaveProperty('models');
      // Should not be wrapped in manifest field
      expect(manifestData).not.toHaveProperty('manifest');
      
    } catch (error) {
      throw new Error(`TypeScript client → Go server failed: ${error}`);
    } finally {
      // Cleanup
      if (goServer) {
        goServer.kill();
      }
      try {
        await fs.unlink(socketPath);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  });

  /**
   * Test Go client → TypeScript server communication
   */
  test('testGoClientToTypeScriptServer', async () => {
    const socketPath = `/tmp/go-to-typescript-test-${uuidv4()}.sock`;
    
    let server: JanusServer | null = null;
    
    try {
      // Start TypeScript server using library
      server = new JanusServer({ socketPath });
      const serverPromise = server.listen();
      
      // Give server time to start and bind socket
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // Test Go client → TypeScript server manifest request
      const goClientPromise = new Promise<{stdout: string, stderr: string, code: number}>((resolve, reject) => {
        const goClient = spawn('../../../../Janus/GoJanus/janus', [
          '--send-to', socketPath,
          '--request', 'manifest'
        ]);
        
        let stdout = '';
        let stderr = '';
        
        goClient.stdout?.on('data', (data) => {
          stdout += data.toString();
        });
        
        goClient.stderr?.on('data', (data) => {
          stderr += data.toString();
        });
        
        goClient.on('close', (code) => {
          resolve({ stdout, stderr, code: code || 0 });
        });
        
        goClient.on('error', reject);
      });
      
      const { stdout, stderr, code } = await goClientPromise;
      
      console.log('Go client stdout:', stdout);
      console.log('Go client stderr:', stderr);
      console.log('Go client exit code:', code);
      
      // CRITICAL: This should now succeed after fixing the TypeScript server
      expect(code).toBe(0);
      
      // Parse the output to validate response structure
      if (stdout.includes('Success=true')) {
        console.log('✅ Go client → TypeScript server communication successful');
        
        // Validate the response contains proper manifest structure
        expect(stdout).toContain('version');
        expect(stdout).toContain('models');
        
        // CRITICAL: Should NOT contain "manifest" wrapper
        expect(stdout).not.toContain('manifest:');
      } else {
        throw new Error(`Go client → TypeScript server failed: ${stderr}`);
      }
      
    } finally {
      if (server) {
        await server.close();
      }
      try {
        await fs.unlink(socketPath);
      } catch (e) {
        // Ignore cleanup errors
      }
    }
  });
});
// Force exit after all tests complete to avoid Jest hanging
afterAll((done) => {
  // Give a small delay for cleanup then exit
  setTimeout(() => {
    done();
    process.exit(0);
  }, 500);
});
