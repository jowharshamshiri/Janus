/**
 * Documentation Server with Live Reload
 * Serves static documentation files with WebSocket live reload
 */

import * as express from 'express';
import * as path from 'path';
import * as http from 'http';
import * as WebSocket from 'ws';

export interface ServerOptions {
  port: number;
  host?: string;
}

export class DocumentationServer {
  private app: express.Application;
  private server: http.Server | null = null;
  private wss: WebSocket.Server | null = null;
  private docsDir: string;
  private options: Required<ServerOptions>;

  constructor(docsDir: string, options: ServerOptions) {
    this.docsDir = docsDir;
    this.options = {
      port: options.port,
      host: options.host ?? 'localhost'
    };

    this.app = express();
    this.setupRoutes();
  }

  /**
   * Setup Express routes
   */
  private setupRoutes(): void {
    // Serve static files
    this.app.use(express.static(this.docsDir));

    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({ status: 'ok', timestamp: new Date().toISOString() });
    });

    // API info endpoint
    this.app.get('/api/info', (req, res) => {
      res.json({
        name: 'Unix Socket API Documentation Server',
        version: '1.0.0',
        docsDir: this.docsDir,
        timestamp: new Date().toISOString()
      });
    });

    // Default route to index.html
    this.app.get('/', (req, res) => {
      res.sendFile(path.join(this.docsDir, 'index.html'));
    });

    // Catch-all route for SPA behavior
    this.app.get('*', (req, res) => {
      res.sendFile(path.join(this.docsDir, 'index.html'));
    });
  }

  /**
   * Start the server
   */
  async start(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.server = http.createServer(this.app);

      // Setup WebSocket server for live reload
      this.wss = new WebSocket.Server({ server: this.server });

      this.wss.on('connection', (ws) => {
        console.log('🔌 Live reload client connected');
        
        ws.on('close', () => {
          console.log('🔌 Live reload client disconnected');
        });

        ws.on('error', (error) => {
          console.error('🚨 WebSocket error:', error);
        });

        // Send welcome message
        ws.send(JSON.stringify({
          type: 'connected',
          message: 'Live reload connected'
        }));
      });

      this.server.listen(this.options.port, this.options.host, () => {
        resolve();
      });

      this.server.on('error', (error) => {
        reject(error);
      });
    });
  }

  /**
   * Stop the server
   */
  stop(): void {
    if (this.wss) {
      this.wss.close();
      this.wss = null;
    }

    if (this.server) {
      this.server.close();
      this.server = null;
    }
  }

  /**
   * Broadcast reload message to all connected clients
   */
  broadcastReload(): void {
    if (this.wss) {
      this.wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(JSON.stringify({
            type: 'reload',
            timestamp: new Date().toISOString()
          }));
        }
      });
    }
  }

  /**
   * Get server info
   */
  getInfo(): { port: number; host: string; isRunning: boolean } {
    return {
      port: this.options.port,
      host: this.options.host,
      isRunning: this.server !== null
    };
  }
}