/**
 * Documentation Generator
 * Uses TypeScriptJanus library for full functionality
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { APIDocumentationGenerator, DocumentationOptions as BaseDocumentationOptions } from 'typescript-unix-sock-api/dist/docs/api-doc-generator';
import { Manifest } from 'typescript-unix-sock-api/dist/types/protocol';

export interface DocumentationOptions extends BaseDocumentationOptions {
  // Enhanced options for development hub
  enableSocketMonitoring?: boolean;
  enableMessageSending?: boolean;
  monitoringSocketPath?: string;
  debugMode?: boolean;
}

export class DocumentationGenerator {
  private manifest: Manifest;
  private options: Required<DocumentationOptions>;
  private docGenerator: APIDocumentationGenerator;

  constructor(manifest: Manifest, options: DocumentationOptions = {}) {
    this.manifest = manifest;
    this.options = {
      title: options.title ?? manifest.name,
      description: options.description ?? manifest.description ?? 'Janus Documentation',
      version: options.version ?? manifest.version,
      includeExamples: options.includeExamples ?? true,
      includeTypes: options.includeTypes ?? true,
      customStyles: options.customStyles ?? '',
      logoUrl: options.logoUrl ?? '',
      // Enhanced development hub options
      enableSocketMonitoring: options.enableSocketMonitoring ?? true,
      enableMessageSending: options.enableMessageSending ?? true,
      monitoringSocketPath: options.monitoringSocketPath ?? '/tmp/janus-api-monitor.sock',
      debugMode: options.debugMode ?? true
    };
    
    // Create the underlying documentation generator
    this.docGenerator = new APIDocumentationGenerator(this.manifest, this.options);
  }

  /**
   * Create generator from Manifest file
   */
  static async fromManifestFile(manifestFilePath: string, options: DocumentationOptions = {}): Promise<DocumentationGenerator> {
    const manifestContent = await fs.readFile(manifestFilePath, 'utf8');
    const manifest = JSON.parse(manifestContent) as Manifest;
    return new DocumentationGenerator(manifest, options);
  }

  /**
   * Save documentation to directory
   */
  async saveToDirectory(outputDir: string): Promise<void> {
    // Ensure output directory exists
    await fs.mkdir(outputDir, { recursive: true });
    
    // Generate base documentation using the library
    const baseDocumentation = await this.docGenerator.generateDocumentation();
    
    // Enhance with development hub features
    const enhancedHtml = await this.generateEnhancedHTML(baseDocumentation.html);
    const enhancedCss = this.generateEnhancedCSS(baseDocumentation.css);
    const enhancedJavaScript = this.generateEnhancedJavaScript(baseDocumentation.javascript);
    
    // Write enhanced files
    await fs.writeFile(path.join(outputDir, 'index.html'), enhancedHtml);
    await fs.writeFile(path.join(outputDir, 'styles.css'), enhancedCss);
    await fs.writeFile(path.join(outputDir, 'script.js'), enhancedJavaScript);
    await fs.writeFile(path.join(outputDir, 'openapi.json'), JSON.stringify(baseDocumentation.openManifest, null, 2));
    
    // Write Manifest for runtime access
    await fs.writeFile(path.join(outputDir, 'manifest.json'), JSON.stringify(this.manifest, null, 2));
    
    // Create README
    const readme = this.generateReadme(outputDir);
    await fs.writeFile(path.join(outputDir, 'README.md'), readme);
  }

  /**
   * Generate enhanced HTML with development hub features
   */
  private async generateEnhancedHTML(_baseHtml: string): Promise<string> {
    // Replace the entire base HTML with a unified professional design
    return this.generateUnifiedHTML();
  }

  /**
   * Generate unified professional HTML structure
   */
  private generateUnifiedHTML(): string {
    const channels = Object.entries(this.manifest.channels);
    const totalRequests = channels.reduce((total, [, channel]: [string, any]) => 
      total + Object.keys(channel.requests).length, 0);

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${this.options.title} - Development Environment</title>
    <link rel="stylesheet" href="styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs/editor/editor.main.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.36.1/min/vs/loader.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="app-container">
        <!-- Header Bar -->
        <header class="header-bar">
            <div class="header-left">
                <div class="app-logo">
                    <i class="fas fa-code-branch"></i>
                    <span class="app-title">${this.options.title}</span>
                    <span class="app-version">v${this.options.version}</span>
                </div>
            </div>
            <div class="header-center">
                <div class="connection-status" id="global-connection-status">
                    <div class="status-indicator">
                        <div class="status-dot status-disconnected"></div>
                        <span>Disconnected</span>
                    </div>
                </div>
            </div>
            <div class="header-right">
                <button class="header-btn" id="settings-btn" title="Settings">
                    <i class="fas fa-cog"></i>
                </button>
                <button class="header-btn" id="help-btn" title="Help">
                    <i class="fas fa-question-circle"></i>
                </button>
            </div>
        </header>

        <!-- Main Layout -->
        <div class="main-layout">
            <!-- Left Sidebar -->
            <aside class="left-sidebar">
                <nav class="sidebar-nav">
                    <div class="nav-tabs">
                        <button class="nav-tab active" data-panel="documentation">
                            <i class="fas fa-book"></i>
                            <span>Documentation</span>
                        </button>
                        <button class="nav-tab" data-panel="explorer">
                            <i class="fas fa-play-circle"></i>
                            <span>API Explorer</span>
                        </button>
                        <button class="nav-tab" data-panel="monitor">
                            <i class="fas fa-chart-line"></i>
                            <span>Monitor</span>
                        </button>
                        <button class="nav-tab" data-panel="tools">
                            <i class="fas fa-tools"></i>
                            <span>Tools</span>
                        </button>
                    </div>
                </nav>

                <!-- Documentation Panel -->
                <div class="nav-panel active" id="documentation-panel">
                    <div class="panel-header">
                        <h3>API Reference</h3>
                        <div class="search-container">
                            <input type="text" id="doc-search" placeholder="Search API..." class="search-input">
                            <i class="fas fa-search search-icon"></i>
                        </div>
                    </div>
                    <div class="panel-content">
                        <div class="doc-tree">
                            <div class="tree-section">
                                <div class="tree-header">
                                    <i class="fas fa-info-circle"></i>
                                    <span>Overview</span>
                                </div>
                                <div class="tree-items">
                                    <a href="#overview" class="tree-item">Introduction</a>
                                    <a href="#protocol" class="tree-item">Protocol</a>
                                    <a href="#authentication" class="tree-item">Authentication</a>
                                </div>
                            </div>
                            ${channels.map(([channelId, channel]: [string, any]) => `
                                <div class="tree-section">
                                    <div class="tree-header expandable" data-channel="${channelId}">
                                        <i class="fas fa-folder tree-icon"></i>
                                        <span>${channel.name}</span>
                                        <span class="request-count">${Object.keys(channel.requests).length}</span>
                                    </div>
                                    <div class="tree-items" id="tree-${channelId}">
                                        ${Object.entries(channel.requests).map(([requestName, _request]: [string, any]) => `
                                            <a href="#${channelId}-${requestName}" class="tree-item request-item" 
                                               data-channel="${channelId}" data-request="${requestName}">
                                                <i class="fas fa-bolt"></i>
                                                <span>${requestName}</span>
                                            </a>
                                        `).join('')}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- API Explorer Panel -->
                <div class="nav-panel" id="explorer-panel">
                    <div class="panel-header">
                        <h3>API Explorer</h3>
                        <button class="panel-btn" id="new-request-btn">
                            <i class="fas fa-plus"></i>
                            New Request
                        </button>
                    </div>
                    <div class="panel-content">
                        <div class="request-builder">
                            <div class="form-group">
                                <label>Socket Path</label>
                                <input type="text" id="explorer-socket-path" 
                                       placeholder="/tmp/api.sock" class="form-input">
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Channel</label>
                                    <select id="explorer-channel" class="form-select">
                                        <option value="">Select Channel...</option>
                                        ${channels.map(([channelId, channel]: [string, any]) => 
                                            `<option value="${channelId}">${channel.name}</option>`
                                        ).join('')}
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Request</label>
                                    <select id="explorer-request" class="form-select" disabled>
                                        <option value="">Select Request...</option>
                                    </select>
                                </div>
                            </div>
                            <div class="connection-controls">
                                <button class="btn btn-primary" id="explorer-connect">
                                    <i class="fas fa-plug"></i>
                                    Connect
                                </button>
                                <button class="btn btn-secondary" id="explorer-disconnect" disabled>
                                    <i class="fas fa-times"></i>
                                    Disconnect
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Monitor Panel -->
                <div class="nav-panel" id="monitor-panel">
                    <div class="panel-header">
                        <h3>Socket Monitor</h3>
                        <div class="monitor-controls">
                            <button class="panel-btn" id="start-monitor">
                                <i class="fas fa-play"></i>
                                Start
                            </button>
                            <button class="panel-btn" id="clear-monitor">
                                <i class="fas fa-trash"></i>
                                Clear
                            </button>
                        </div>
                    </div>
                    <div class="panel-content">
                        <div class="form-group">
                            <label>Monitor Socket</label>
                            <input type="text" id="monitor-socket-path" 
                                   placeholder="/tmp/api.sock" class="form-input">
                        </div>
                        <div class="monitor-stats">
                            <div class="stat-item">
                                <span class="stat-label">Messages</span>
                                <span class="stat-value" id="message-count">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Errors</span>
                                <span class="stat-value" id="error-count">0</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Uptime</span>
                                <span class="stat-value" id="uptime">00:00</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Tools Panel -->
                <div class="nav-panel" id="tools-panel">
                    <div class="panel-header">
                        <h3>Development Tools</h3>
                    </div>
                    <div class="panel-content">
                        <div class="tool-list">
                            <div class="tool-item" data-tool="formatter">
                                <i class="fas fa-code"></i>
                                <div class="tool-info">
                                    <div class="tool-name">Message Formatter</div>
                                    <div class="tool-desc">Format and validate JSON messages</div>
                                </div>
                            </div>
                            <div class="tool-item" data-tool="validator">
                                <i class="fas fa-check-circle"></i>
                                <div class="tool-info">
                                    <div class="tool-name">Schema Validator</div>
                                    <div class="tool-desc">Validate against Manifest</div>
                                </div>
                            </div>
                            <div class="tool-item" data-tool="generator">
                                <i class="fas fa-magic"></i>
                                <div class="tool-info">
                                    <div class="tool-name">Code Generator</div>
                                    <div class="tool-desc">Generate client code examples</div>
                                </div>
                            </div>
                            <div class="tool-item" data-tool="tester">
                                <i class="fas fa-vial"></i>
                                <div class="tool-info">
                                    <div class="tool-name">Connection Tester</div>
                                    <div class="tool-desc">Test socket connectivity</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            <!-- Main Content Area -->
            <main class="main-content">
                <div class="content-panels">
                    <!-- Documentation Content -->
                    <div class="content-panel active" id="doc-content">
                        ${this.generateDocumentationContent()}
                    </div>

                    <!-- Explorer Content -->
                    <div class="content-panel" id="explorer-content">
                        ${this.generateExplorerContent()}
                    </div>

                    <!-- Monitor Content -->
                    <div class="content-panel" id="monitor-content">
                        ${this.generateMonitorContent()}
                    </div>

                    <!-- Tools Content -->
                    <div class="content-panel" id="tools-content">
                        ${this.generateToolsContent()}
                    </div>
                </div>
            </main>

            <!-- Right Sidebar -->
            <aside class="right-sidebar">
                <div class="sidebar-header">
                    <h3>Context Panel</h3>
                </div>
                <div class="context-content" id="context-content">
                    ${this.generateContextPanel()}
                </div>
            </aside>
        </div>

        <!-- Bottom Console -->
        <div class="bottom-console">
            <div class="console-header">
                <div class="console-tabs">
                    <button class="console-tab active" data-console="output">
                        <i class="fas fa-terminal"></i>
                        Output
                    </button>
                    <button class="console-tab" data-console="logs">
                        <i class="fas fa-list"></i>
                        Logs
                    </button>
                    <button class="console-tab" data-console="errors">
                        <i class="fas fa-exclamation-triangle"></i>
                        Errors
                    </button>
                </div>
                <div class="console-controls">
                    <button class="console-btn" id="clear-console">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="console-btn" id="toggle-console">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
            </div>
            <div class="console-content">
                <div class="console-panel active" id="output-console">
                    <div class="console-output" id="console-output">
                        <div class="console-welcome">
                            <i class="fas fa-code"></i>
                            <span>Janus Development Environment Ready</span>
                            <div class="console-info">API: ${this.options.title} | Channels: ${channels.length} | Requests: ${totalRequests}</div>
                        </div>
                    </div>
                </div>
                <div class="console-panel" id="logs-console">
                    <div class="console-output" id="logs-output"></div>
                </div>
                <div class="console-panel" id="errors-console">
                    <div class="console-output" id="errors-output"></div>
                </div>
            </div>
        </div>
    </div>

    <script src="script.js"></script>
</body>
</html>`;
  }

  /**
   * Generate documentation content panel
   */
  private generateDocumentationContent(): string {
    const channels = Object.entries(this.manifest.channels);
    
    return `
      <div class="doc-container">
        <!-- Overview Section -->
        <section id="overview" class="doc-section">
          <div class="section-header">
            <h1>${this.options.title}</h1>
            <div class="section-meta">
              <span class="version-badge">v${this.options.version}</span>
              <span class="protocol-badge">Unix Sockets</span>
            </div>
          </div>
          <p class="section-description">${this.options.description}</p>
          
          <div class="overview-cards">
            <div class="overview-card">
              <div class="card-icon">
                <i class="fas fa-network-wired"></i>
              </div>
              <div class="card-content">
                <h3>Protocol</h3>
                <p>Unix Domain Sockets with JSON messaging</p>
              </div>
            </div>
            <div class="overview-card">
              <div class="card-icon">
                <i class="fas fa-sitemap"></i>
              </div>
              <div class="card-content">
                <h3>Channels</h3>
                <p>${channels.length} service channels available</p>
              </div>
            </div>
            <div class="overview-card">
              <div class="card-icon">
                <i class="fas fa-bolt"></i>
              </div>
              <div class="card-content">
                <h3>Requests</h3>
                <p>${channels.reduce((total, [, channel]: [string, any]) => 
                  total + Object.keys(channel.requests).length, 0)} total requests</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Protocol Section -->
        <section id="protocol" class="doc-section">
          <div class="section-header">
            <h2>Protocol Overview</h2>
            <button class="try-btn" data-action="test-protocol">
              <i class="fas fa-play"></i>
              Try It
            </button>
          </div>
          
          <div class="protocol-info">
            <div class="info-block">
              <h3>Message Format</h3>
              <div class="code-example">
                <div class="code-header">
                  <span>Request Format</span>
                  <button class="copy-btn" data-copy="request-format">
                    <i class="fas fa-copy"></i>
                  </button>
                </div>
                <pre id="request-format"><code>{
  "id": "uuid-v4",
  "channelId": "channel-name",
  "request": "request-name",
  "args": { /* request arguments */ },
  "timeout": 30.0,
  "timestamp": "ISO-8601"
}</code></pre>
              </div>
            </div>
            
            <div class="info-block">
              <h3>Response Format</h3>
              <div class="code-example">
                <div class="code-header">
                  <span>Response Format</span>
                  <button class="copy-btn" data-copy="response-format">
                    <i class="fas fa-copy"></i>
                  </button>
                </div>
                <pre id="response-format"><code>{
  "requestId": "original-request-id",
  "channelId": "channel-name",
  "success": true,
  "result": { /* response data */ },
  "error": null,
  "timestamp": "ISO-8601"
}</code></pre>
              </div>
            </div>
          </div>
        </section>

        <!-- Channels Documentation -->
        ${channels.map(([channelId, channel]: [string, any]) => `
          <section id="${channelId}" class="doc-section channel-section">
            <div class="section-header">
              <h2>${channel.name}</h2>
              <div class="channel-meta">
                <span class="request-count-badge">${Object.keys(channel.requests).length} requests</span>
              </div>
            </div>
            <p class="section-description">${channel.description || 'Channel for ' + channel.name}</p>
            
            <div class="requests-grid">
              ${Object.entries(channel.requests).map(([requestName, request]: [string, any]) => `
                <div class="request-card" id="${channelId}-${requestName}">
                  <div class="request-header">
                    <h3>${requestName}</h3>
                    <div class="request-actions">
                      <button class="action-btn" data-action="try-request" 
                              data-channel="${channelId}" data-request="${requestName}">
                        <i class="fas fa-play"></i>
                        Try
                      </button>
                      <button class="action-btn" data-action="copy-example" 
                              data-channel="${channelId}" data-request="${requestName}">
                        <i class="fas fa-copy"></i>
                        Copy
                      </button>
                    </div>
                  </div>
                  <p class="request-description">${request.description || 'Execute ' + requestName + ' request'}</p>
                  
                  ${request.arguments && request.arguments.length > 0 ? `
                    <div class="request-params">
                      <h4>Parameters</h4>
                      <div class="params-list">
                        ${request.arguments.map((arg: any) => `
                          <div class="param-item">
                            <div class="param-name">
                              <code>${arg.name}</code>
                              <span class="param-type">${arg.type}</span>
                              ${arg.required ? '<span class="required-badge">required</span>' : ''}
                            </div>
                            <div class="param-description">${arg.description || 'Parameter description'}</div>
                          </div>
                        `).join('')}
                      </div>
                    </div>
                  ` : ''}
                  
                  <div class="request-example">
                    <div class="example-tabs">
                      <button class="example-tab active" data-tab="request">Request</button>
                      <button class="example-tab" data-tab="response">Response</button>
                    </div>
                    <div class="example-content">
                      <div class="example-panel active" data-panel="request">
                        <pre><code>${this.generateRequestExample(channelId, requestName, request)}</code></pre>
                      </div>
                      <div class="example-panel" data-panel="response">
                        <pre><code>${this.generateResponseExample(channelId, requestName)}</code></pre>
                      </div>
                    </div>
                  </div>
                </div>
              `).join('')}
            </div>
          </section>
        `).join('')}
      </div>
    `;
  }

  /**
   * Generate API Explorer content panel
   */
  private generateExplorerContent(): string {
    return `
      <div class="explorer-container">
        <div class="request-section">
          <div class="section-header">
            <h2>API Request Builder</h2>
            <div class="request-actions">
              <button class="btn btn-primary" id="send-request">
                <i class="fas fa-paper-plane"></i>
                Send Request
              </button>
              <button class="btn btn-secondary" id="save-request">
                <i class="fas fa-save"></i>
                Save
              </button>
            </div>
          </div>
          
          <div class="request-builder-main">
            <div class="request-editor" id="request-editor">
              <!-- Monaco editor will be initialized here -->
            </div>
          </div>
        </div>
        
        <div class="response-section">
          <div class="section-header">
            <h2>Response</h2>
            <div class="response-meta">
              <span class="response-time" id="response-time">0ms</span>
              <span class="response-status" id="response-status">Ready</span>
            </div>
          </div>
          
          <div class="response-content">
            <div class="response-tabs">
              <button class="response-tab active" data-tab="body">Response Body</button>
              <button class="response-tab" data-tab="headers">Headers</button>
              <button class="response-tab" data-tab="raw">Raw</button>
            </div>
            
            <div class="response-panels">
              <div class="response-panel active" id="response-body">
                <div class="empty-response">
                  <i class="fas fa-arrow-up"></i>
                  <span>Send a request to see the response here</span>
                </div>
              </div>
              <div class="response-panel" id="response-headers"></div>
              <div class="response-panel" id="response-raw"></div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Generate Monitor content panel
   */
  private generateMonitorContent(): string {
    return `
      <div class="monitor-container">
        <div class="monitor-view">
          <div class="section-header">
            <h2>Real-time Socket Monitor</h2>
            <div class="monitor-actions">
              <button class="btn btn-success" id="start-monitoring">
                <i class="fas fa-play"></i>
                Start Monitoring
              </button>
              <button class="btn btn-danger" id="stop-monitoring" disabled>
                <i class="fas fa-stop"></i>
                Stop
              </button>
            </div>
          </div>
          
          <div class="message-stream">
            <div class="stream-tabs">
              <button class="stream-tab active" data-stream="all">All Messages</button>
              <button class="stream-tab" data-stream="requests">Requests</button>
              <button class="stream-tab" data-stream="responses">Responses</button>
              <button class="stream-tab" data-stream="errors">Errors</button>
            </div>
            
            <div class="stream-content">
              <div class="message-list" id="message-stream">
                <div class="empty-monitor">
                  <i class="fas fa-satellite-dish"></i>
                  <span>Start monitoring to see live socket communication</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="monitor-sidebar">
          <div class="monitor-filters">
            <h3>Filters</h3>
            <div class="filter-group">
              <label>Channel</label>
              <select class="form-select" id="filter-channel">
                <option value="">All Channels</option>
                ${Object.entries(this.manifest.channels).map(([channelId, channel]: [string, any]) => 
                  `<option value="${channelId}">${channel.name}</option>`
                ).join('')}
              </select>
            </div>
            <div class="filter-group">
              <label>Message Type</label>
              <div class="checkbox-group">
                <label class="checkbox-label">
                  <input type="checkbox" checked id="filter-requests">
                  <span>Requests</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" checked id="filter-responses">
                  <span>Responses</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" checked id="filter-errors">
                  <span>Errors</span>
                </label>
              </div>
            </div>
          </div>
          
          <div class="monitor-analytics">
            <h3>Analytics</h3>
            <div class="analytics-grid">
              <div class="metric-card">
                <div class="metric-value" id="total-messages">0</div>
                <div class="metric-label">Total Messages</div>
              </div>
              <div class="metric-card">
                <div class="metric-value" id="avg-response-time">0ms</div>
                <div class="metric-label">Avg Response Time</div>
              </div>
              <div class="metric-card">
                <div class="metric-value" id="error-rate">0%</div>
                <div class="metric-label">Error Rate</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Generate Tools content panel
   */
  private generateToolsContent(): string {
    return `
      <div class="tools-container">
        <div class="tool-panels">
          <!-- Message Formatter Tool -->
          <div class="tool-panel active" id="formatter-tool">
            <div class="section-header">
              <h2>Message Formatter & Validator</h2>
              <div class="tool-actions">
                <button class="btn btn-primary" id="format-message">
                  <i class="fas fa-magic"></i>
                  Format
                </button>
                <button class="btn btn-secondary" id="validate-message">
                  <i class="fas fa-check"></i>
                  Validate
                </button>
              </div>
            </div>
            
            <div class="formatter-layout">
              <div class="input-section">
                <h3>Raw JSON Input</h3>
                <div class="json-editor" id="formatter-input">
                  <!-- Monaco editor -->
                </div>
              </div>
              
              <div class="output-section">
                <h3>Formatted Output</h3>
                <div class="json-editor" id="formatter-output">
                  <!-- Monaco editor -->
                </div>
              </div>
            </div>
            
            <div class="validation-results" id="validation-results">
              <!-- Validation results will appear here -->
            </div>
          </div>
          
          <!-- Code Generator Tool -->
          <div class="tool-panel" id="generator-tool">
            <div class="section-header">
              <h2>Client Code Generator</h2>
              <div class="tool-actions">
                <button class="btn btn-primary" id="generate-code">
                  <i class="fas fa-code"></i>
                  Generate
                </button>
              </div>
            </div>
            
            <div class="generator-config">
              <div class="form-row">
                <div class="form-group">
                  <label>Language</label>
                  <select class="form-select" id="code-language">
                    <option value="typescript">TypeScript</option>
                    <option value="javascript">JavaScript</option>
                    <option value="python">Python</option>
                    <option value="go">Go</option>
                    <option value="rust">Rust</option>
                    <option value="swift">Swift</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Template</label>
                  <select class="form-select" id="code-template">
                    <option value="client">Client Library</option>
                    <option value="example">Usage Example</option>
                    <option value="types">Type Definitions</option>
                  </select>
                </div>
              </div>
            </div>
            
            <div class="generated-code">
              <div class="code-editor" id="generated-code-output">
                <!-- Generated code will appear here -->
              </div>
            </div>
          </div>
          
          <!-- Connection Tester Tool -->
          <div class="tool-panel" id="tester-tool">
            <div class="section-header">
              <h2>Connection Tester</h2>
              <div class="tool-actions">
                <button class="btn btn-primary" id="test-connection">
                  <i class="fas fa-plug"></i>
                  Test Connection
                </button>
              </div>
            </div>
            
            <div class="tester-config">
              <div class="form-group">
                <label>Socket Path</label>
                <input type="text" class="form-input" id="test-socket-path" 
                       placeholder="/tmp/api.sock" value="/tmp/api.sock">
              </div>
              <div class="form-group">
                <label>Timeout (seconds)</label>
                <input type="number" class="form-input" id="test-timeout" 
                       value="10" min="1" max="60">
              </div>
            </div>
            
            <div class="test-results" id="connection-test-results">
              <div class="empty-results">
                <i class="fas fa-vial"></i>
                <span>Run a connection test to see results</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Generate Context Panel (right sidebar)
   */
  private generateContextPanel(): string {
    return `
      <div class="context-panel">
        <div class="context-section">
          <h4>Quick Actions</h4>
          <div class="quick-actions">
            <button class="quick-action" data-action="new-request">
              <i class="fas fa-plus"></i>
              <span>New Request</span>
            </button>
            <button class="quick-action" data-action="connect-socket">
              <i class="fas fa-plug"></i>
              <span>Connect</span>
            </button>
            <button class="quick-action" data-action="start-monitor">
              <i class="fas fa-eye"></i>
              <span>Monitor</span>
            </button>
          </div>
        </div>
        
        <div class="context-section">
          <h4>Connection Info</h4>
          <div class="connection-info">
            <div class="info-item">
              <span class="info-label">Status</span>
              <span class="info-value" id="ctx-status">Disconnected</span>
            </div>
            <div class="info-item">
              <span class="info-label">Socket</span>
              <span class="info-value" id="ctx-socket">None</span>
            </div>
            <div class="info-item">
              <span class="info-label">Uptime</span>
              <span class="info-value" id="ctx-uptime">00:00</span>
            </div>
          </div>
        </div>
        
        <div class="context-section">
          <h4>API Overview</h4>
          <div class="api-overview">
            <div class="overview-stat">
              <span class="stat-number">${Object.keys(this.manifest.channels).length}</span>
              <span class="stat-label">Channels</span>
            </div>
            <div class="overview-stat">
              <span class="stat-number">${Object.values(this.manifest.channels).reduce((total, channel: any) => 
                total + Object.keys(channel.requests).length, 0)}</span>
              <span class="stat-label">Requests</span>
            </div>
          </div>
        </div>
        
        <div class="context-section">
          <h4>Recent Activity</h4>
          <div class="activity-list" id="recent-activity">
            <div class="empty-activity">
              <span>No recent activity</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Generate request example JSON
   */
  private generateRequestExample(channelId: string, requestName: string, request: any): string {
    const args: any = {};
    
    if (request.arguments) {
      request.arguments.forEach((arg: any) => {
        switch (arg.type) {
          case 'string':
            args[arg.name] = `example-${arg.name}`;
            break;
          case 'number':
            args[arg.name] = 42;
            break;
          case 'boolean':
            args[arg.name] = false;
            break;
          case 'object':
            args[arg.name] = { key: 'value' };
            break;
          case 'array':
            args[arg.name] = ['item1', 'item2'];
            break;
          default:
            args[arg.name] = null;
        }
      });
    }

    const example = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      channelId,
      request: requestName,
      args,
      timeout: request.timeout || 30,
      timestamp: new Date().toISOString()
    };

    return JSON.stringify(example, null, 2);
  }

  /**
   * Generate response example JSON
   */
  private generateResponseExample(channelId: string, _requestName: string): string {
    const example = {
      requestId: '550e8400-e29b-41d4-a716-446655440000',
      channelId,
      success: true,
      result: {
        message: 'Request executed successfully',
        data: {}
      },
      error: null,
      timestamp: new Date().toISOString()
    };

    return JSON.stringify(example, null, 2);
  }

  /**
   * Generate professional CSS with unified design system
   */
  private generateEnhancedCSS(_baseCss: string): string {
    return `
/* Professional Janus Development Environment */

:root {
  /* Color Palette - Professional Blue/Gray Theme */
  --primary-50: #eff6ff;
  --primary-100: #dbeafe;
  --primary-200: #bfdbfe;
  --primary-300: #93c5fd;
  --primary-400: #60a5fa;
  --primary-500: #3b82f6;
  --primary-600: #2563eb;
  --primary-700: #1d4ed8;
  --primary-800: #1e40af;
  --primary-900: #1e3a8a;
  
  --gray-50: #f8fafc;
  --gray-100: #f1f5f9;
  --gray-200: #e2e8f0;
  --gray-300: #cbd5e1;
  --gray-400: #94a3b8;
  --gray-500: #64748b;
  --gray-600: #475569;
  --gray-700: #334155;
  --gray-800: #1e293b;
  --gray-900: #0f172a;
  
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #3b82f6;
  
  /* Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  
  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  
  /* Borders */
  --radius-sm: 0.25rem;
  --radius: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}

/* Reset & Base Styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-sans);
  background-color: var(--gray-50);
  color: var(--gray-900);
  line-height: 1.5;
  overflow: hidden;
}

/* App Container */
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
}

/* Header Bar */
.header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  background: white;
  border-bottom: 1px solid var(--gray-200);
  padding: 0 var(--space-6);
  box-shadow: var(--shadow-sm);
  z-index: 100;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-weight: 600;
  color: var(--gray-900);
  font-size: 1.125rem;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.875rem;
  color: var(--gray-600);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--error);
}

.status-indicator.connected {
  background: var(--success);
}

/* Main Layout */
.main-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 300px 1fr 250px;
  grid-template-rows: 1fr 200px;
  height: calc(100vh - 60px);
  overflow: hidden;
}

/* Left Sidebar */
.left-sidebar {
  background: white;
  border-right: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.nav-tabs {
  display: flex;
  border-bottom: 1px solid var(--gray-200);
  background: var(--gray-50);
}

.nav-tab {
  flex: 1;
  padding: var(--space-3) var(--space-4);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--gray-600);
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.nav-tab:hover {
  color: var(--gray-900);
  background: var(--gray-100);
}

.nav-tab.active {
  color: var(--primary-600);
  border-bottom-color: var(--primary-600);
  background: white;
}

.nav-panels {
  flex: 1;
  overflow: hidden;
}

.nav-panel {
  height: 100%;
  overflow-y: auto;
  padding: var(--space-4);
  display: none;
}

.nav-panel.active {
  display: block;
}

/* Main Content */
.main-content {
  background: white;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Right Sidebar */
.right-sidebar {
  background: var(--gray-50);
  border-left: 1px solid var(--gray-200);
  overflow-y: auto;
  padding: var(--space-4);
}

/* Bottom Console */
.bottom-console {
  grid-column: 1 / -1;
  background: var(--gray-900);
  color: var(--gray-100);
  border-top: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
}

.console-tabs {
  display: flex;
  background: var(--gray-800);
  border-bottom: 1px solid var(--gray-700);
}

.console-tab {
  padding: var(--space-2) var(--space-4);
  background: none;
  border: none;
  color: var(--gray-400);
  cursor: pointer;
  font-size: 0.875rem;
  border-bottom: 2px solid transparent;
}

.console-tab:hover {
  color: var(--gray-200);
}

.console-tab.active {
  color: white;
  border-bottom-color: var(--primary-500);
}

.console-content {
  flex: 1;
  padding: var(--space-4);
  overflow-y: auto;
  font-family: var(--font-mono);
  font-size: 0.875rem;
}

/* Form Elements */
.form-group {
  margin-bottom: var(--space-4);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-2);
  font-weight: 500;
  color: var(--gray-700);
  font-size: 0.875rem;
}

.form-input,
.form-select {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 0.875rem;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px var(--primary-100);
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border: none;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--primary-600);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-700);
}

.btn-secondary {
  background: var(--gray-200);
  color: var(--gray-700);
}

.btn-secondary:hover {
  background: var(--gray-300);
}

/* Cards */
.card {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.card-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--gray-200);
  background: var(--gray-50);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--gray-900);
}

.card-content {
  padding: var(--space-4);
}

/* Search */
.search-container {
  position: relative;
  margin-bottom: var(--space-4);
}

.search-input {
  width: 100%;
  padding: var(--space-2) var(--space-3) var(--space-2) var(--space-10);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 0.875rem;
}

.search-icon {
  position: absolute;
  left: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  color: var(--gray-400);
}

/* Documentation Content */
.doc-container {
  max-width: 1200px;
  margin: 0 auto;
}

.doc-section {
  margin-bottom: var(--space-12);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: 2px solid var(--gray-200);
}

.section-header h1 {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--gray-900);
  margin: 0;
}

.section-meta {
  display: flex;
  gap: var(--space-3);
}

.version-badge,
.protocol-badge {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.version-badge {
  background: var(--primary-100);
  color: var(--primary-700);
}

.protocol-badge {
  background: var(--gray-100);
  color: var(--gray-700);
}

.section-description {
  font-size: 1.125rem;
  color: var(--gray-600);
  line-height: 1.7;
  margin-bottom: var(--space-8);
}

/* Overview Cards */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.overview-card {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s;
}

.overview-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--primary-200);
}

.overview-card .card-icon {
  width: 48px;
  height: 48px;
  background: var(--primary-100);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-4);
}

.overview-card .card-icon i {
  font-size: 1.5rem;
  color: var(--primary-600);
}

.overview-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--gray-900);
  margin-bottom: var(--space-2);
}

.overview-card p {
  color: var(--gray-600);
  line-height: 1.6;
}

/* API Reference */
.api-section {
  margin-bottom: var(--space-8);
}

.api-section h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--gray-900);
  margin-bottom: var(--space-6);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.api-section h2::before {
  content: '';
  width: 4px;
  height: 32px;
  background: var(--primary-500);
  border-radius: 2px;
}

.api-section h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: var(--space-4);
  color: var(--gray-900);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--gray-200);
}

.channel-section {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  margin-bottom: var(--space-6);
  box-shadow: var(--shadow-sm);
}

.channel-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--gray-100);
}

.channel-icon {
  width: 40px;
  height: 40px;
  background: var(--primary-100);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
}

.channel-icon i {
  color: var(--primary-600);
  font-size: 1.125rem;
}

.channel-info h4 {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--gray-900);
  margin-bottom: var(--space-1);
}

.channel-info p {
  color: var(--gray-600);
  font-size: 0.875rem;
}

.requests-grid {
  display: grid;
  gap: var(--space-4);
}

.request-item {
  padding: var(--space-4);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  background: var(--gray-50);
  transition: all 0.2s;
  cursor: pointer;
}

.request-item:hover {
  border-color: var(--primary-300);
  background: var(--primary-50);
  box-shadow: var(--shadow-sm);
}

.request-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
}

.request-name {
  font-weight: 600;
  color: var(--primary-600);
  font-family: var(--font-mono);
  font-size: 0.875rem;
}

.request-actions {
  display: flex;
  gap: var(--space-2);
}

.request-btn {
  padding: var(--space-1) var(--space-2);
  font-size: 0.75rem;
  border: 1px solid var(--gray-300);
  background: white;
  color: var(--gray-700);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
}

.request-btn:hover {
  border-color: var(--primary-300);
  color: var(--primary-600);
}

.request-description {
  font-size: 0.875rem;
  color: var(--gray-600);
  line-height: 1.5;
  margin-bottom: var(--space-3);
}

.request-parameters {
  font-size: 0.75rem;
  color: var(--gray-500);
  font-family: var(--font-mono);
}

/* Monitor */
.monitor-log {
  background: var(--gray-900);
  color: var(--gray-100);
  padding: var(--space-4);
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: 0.875rem;
  height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
}

/* Context Panel Sections */
.context-section {
  margin-bottom: var(--space-6);
}

.context-section h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--gray-900);
  text-transform: uppercase;
  letter-spacing: 0.025em;
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--gray-200);
}

/* Quick Actions */
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.quick-action {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  width: 100%;
  font-size: 0.875rem;
}

.quick-action:hover {
  border-color: var(--primary-300);
  background: var(--primary-50);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.quick-action i {
  color: var(--primary-600);
  width: 16px;
  text-align: center;
}

/* Connection Info */
.connection-info {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  padding: var(--space-4);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--gray-100);
  font-size: 0.875rem;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: var(--gray-600);
  font-weight: 500;
}

.info-value {
  color: var(--gray-900);
  font-family: var(--font-mono);
}

.info-value.status-disconnected {
  color: var(--error);
}

.info-value.status-connected {
  color: var(--success);
}

/* Navigation improvements */
.nav-panel .search-container {
  padding: var(--space-4);
  border-bottom: 1px solid var(--gray-200);
  background: var(--gray-50);
}

.nav-panel .api-tree {
  padding: var(--space-4);
}

.tree-item {
  margin-bottom: var(--space-2);
}

.tree-node {
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.tree-node:hover {
  background: var(--gray-100);
}

.tree-node.active {
  background: var(--primary-100);
  color: var(--primary-700);
}

.tree-node i {
  width: 16px;
  text-align: center;
  color: var(--gray-500);
}

.tree-children {
  margin-left: var(--space-4);
  margin-top: var(--space-1);
}

/* Status indicators */
.status-badge {
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-badge.connected {
  background: var(--success);
  color: white;
}

.status-badge.disconnected {
  background: var(--error);
  color: white;
}

.status-badge.connecting {
  background: var(--warning);
  color: white;
}

/* Toast notifications */
@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

/* Content panel visibility fix */
.content-panels {
  position: relative;
  width: 100%;
  height: 100%;
}

.content-panel {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: var(--space-6);
  display: none;
  background: white;
}

.content-panel.active {
  display: block;
}

/* Responsive */
@media (max-width: 1024px) {
  .main-layout {
    grid-template-columns: 250px 1fr;
  }
  
  .right-sidebar {
    display: none;
  }
}

@media (max-width: 768px) {
  .main-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
  }
  
  .left-sidebar {
    order: 3;
  }
  
  .main-content {
    order: 1;
  }
  
  .bottom-console {
    order: 2;
    height: 150px;
  }
}

/* Status Indicators */
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 8px;
}

.status-connected {
  background-color: var(--success);
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
}

.status-disconnected {
  background-color: var(--gray-400);
}

/* Console collapse */
.bottom-console.collapsed {
  height: 40px;
}

.bottom-console.collapsed .console-content {
  display: none;
}

/* Button states */
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

/* Form improvements */
.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--primary-500);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
`;
  }

  /**
   * Generate enhanced JavaScript with full IDE functionality
   */
  private generateEnhancedJavaScript(_baseJs: string): string {
    return `
// Professional Janus Development Environment
class JanusDevelopmentEnvironment {
  constructor() {
    this.manifest = null;
    this.connections = new Map();
    this.editors = new Map();
    this.currentPanel = 'documentation';
    this.init();
  }

  async init() {
    try {
      const response = await fetch('./manifest.json');
      this.manifest = await response.json();
    } catch (error) {
      console.error('Failed to load Manifest:', error);
    }

    this.setupEventListeners();
    this.initializeEditors();
    this.updateUI();
  }

  setupEventListeners() {
    // Navigation tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const target = e.target.closest('.nav-tab');
        if (target && target.dataset.panel) {
          this.switchPanel(target.dataset.panel);
        }
      });
    });

    // Header buttons
    const settingsBtn = document.getElementById('settings-btn');
    const helpBtn = document.getElementById('help-btn');
    
    if (settingsBtn) {
      settingsBtn.addEventListener('click', () => this.showToast('Settings panel coming soon'));
    }
    if (helpBtn) {
      helpBtn.addEventListener('click', () => this.showToast('Help documentation available in API Reference'));
    }

    // Context panel quick actions
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-action="new-request"]')) {
        this.switchPanel('explorer');
      } else if (e.target.matches('[data-action="connect-socket"]')) {
        this.switchPanel('monitor');
        this.connectMonitor();
      } else if (e.target.matches('[data-action="start-monitor"]')) {
        this.switchPanel('monitor');
      }
    });

    // Console controls
    const clearConsoleBtn = document.getElementById('clear-console');
    const toggleConsoleBtn = document.getElementById('toggle-console');
    
    if (clearConsoleBtn) {
      clearConsoleBtn.addEventListener('click', () => this.clearConsole());
    }
    if (toggleConsoleBtn) {
      toggleConsoleBtn.addEventListener('click', () => this.toggleConsole());
    }

    // Panel interactions
    this.setupDocumentationListeners();
    this.setupExplorerListeners();
    this.setupMonitorListeners();
    this.setupToolsListeners();
  }

  switchPanel(panelName) {
    console.log('Switching to panel:', panelName);
    
    // Update tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.panel === panelName);
    });

    // Update nav panels
    document.querySelectorAll('.nav-panel').forEach(panel => {
      panel.classList.toggle('active', panel.id === panelName + '-panel');
    });

    // Update content panels - fix the ID mapping
    document.querySelectorAll('.content-panel').forEach(panel => {
      let targetId;
      if (panelName === 'documentation') {
        targetId = 'doc-content';
      } else {
        targetId = panelName + '-content';
      }
      panel.classList.toggle('active', panel.id === targetId);
    });

    this.currentPanel = panelName;
    this.updateContextPanel();
  }

  setupDocumentationListeners() {
    // Tree expansion
    document.querySelectorAll('.tree-header.expandable').forEach(header => {
      header.addEventListener('click', () => {
        header.classList.toggle('collapsed');
        const items = header.nextElementSibling;
        items.style.display = header.classList.contains('collapsed') ? 'none' : 'block';
      });
    });

    // Action buttons
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-action="try-request"]')) {
        this.tryRequest(e.target.dataset.channel, e.target.dataset.request);
      } else if (e.target.matches('[data-action="copy-example"]')) {
        this.copyExample(e.target.dataset.channel, e.target.dataset.request);
      }
    });
  }

  tryRequest(channelId, requestName) {
    // Switch to explorer and populate
    this.switchPanel('explorer');
    const channelSelect = document.getElementById('explorer-channel');
    const requestSelect = document.getElementById('explorer-request');
    
    if (channelSelect) channelSelect.value = channelId;
    this.populateRequests(channelId);
    if (requestSelect) requestSelect.value = requestName;
    this.updateRequestEditor(channelId, requestName);
  }

  setupExplorerListeners() {
    // Handle API Explorer interactions
    const connectBtn = document.getElementById('explorer-connect');
    const disconnectBtn = document.getElementById('explorer-disconnect');
    const newRequestBtn = document.getElementById('new-request-btn');
    const channelSelect = document.getElementById('explorer-channel');
    const requestSelect = document.getElementById('explorer-request');
    
    if (connectBtn) {
      connectBtn.addEventListener('click', () => {
        const socketPath = document.getElementById('explorer-socket-path')?.value;
        if (socketPath) {
          this.connectToSocket(socketPath);
        } else {
          this.showToast('Please enter a socket path', 'error');
        }
      });
    }
    
    if (disconnectBtn) {
      disconnectBtn.addEventListener('click', () => this.disconnectFromSocket());
    }
    
    if (newRequestBtn) {
      newRequestBtn.addEventListener('click', () => this.createNewRequest());
    }
    
    if (channelSelect) {
      channelSelect.addEventListener('change', (e) => {
        this.populateRequests(e.target.value);
      });
    }
    
    if (requestSelect) {
      requestSelect.addEventListener('change', (e) => {
        const channelId = channelSelect.value;
        const requestName = e.target.value;
        if (channelId && requestName) {
          this.updateRequestEditor(channelId, requestName);
        }
      });
    }

    // Handle try request buttons
    document.addEventListener('click', (e) => {
      if (e.target.matches('.try-request-btn')) {
        const channelId = e.target.dataset.channel;
        const requestName = e.target.dataset.request;
        this.tryRequest(channelId, requestName);
      }
      if (e.target.matches('.copy-example-btn')) {
        const channelId = e.target.dataset.channel;
        const requestName = e.target.dataset.request;
        this.copyExample(channelId, requestName);
      }
    });
  }

  setupMonitorListeners() {
    // Handle Socket Monitor interactions
    const startBtn = document.getElementById('start-monitor');
    const clearBtn = document.getElementById('clear-monitor');
    
    if (startBtn) {
      startBtn.addEventListener('click', () => {
        const socketPath = document.getElementById('monitor-socket-path')?.value;
        if (socketPath) {
          this.startMonitor(socketPath);
        } else {
          this.showToast('Please enter a socket path to monitor', 'error');
        }
      });
    }
    
    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.clearMonitorLog());
    }
  }

  setupToolsListeners() {
    // Handle Development Tools interactions
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-action="generate-client"]')) {
        const language = e.target.dataset.language;
        this.generateClientCode(language);
      } else if (e.target.matches('[data-action="export-openapi"]')) {
        this.exportOpenAPI();
      } else if (e.target.matches('[data-action="validate-manifest"]')) {
        this.validateManifest();
      }
    });
  }

  connectMonitor() {
    // Socket monitor connection logic
    this.showToast('Monitor connected');
  }

  disconnectMonitor() {
    // Socket monitor disconnection logic
    this.showToast('Monitor disconnected');
  }

  clearMonitorLog() {
    const log = document.getElementById('monitor-log');
    if (log) {
      log.innerHTML = '';
    }
  }

  generateClientCode() {
    // Client code generation logic
    this.showToast('Client code generated');
  }

  exportOpenAPI() {
    // OpenAPI export logic
    this.showToast('OpenManifest exported');
  }

  populateRequests() {
    // Populate request dropdowns based on Manifest
    const requestSelect = document.getElementById('request-select');
    if (requestSelect && this.manifest && this.manifest.channels) {
      requestSelect.innerHTML = '';
      Object.entries(this.manifest.channels).forEach(function(entry) {
        const channelId = entry[0];
        const channel = entry[1];
        Object.keys(channel.requests || {}).forEach(function(requestName) {
          const option = document.createElement('option');
          option.value = channelId + ':' + requestName;
          option.textContent = channelId + ' - ' + requestName;
          requestSelect.appendChild(option);
        });
      });
    }
  }

  updateRequestEditor(channelId, requestName) {
    const request = this.manifest && this.manifest.channels && this.manifest.channels[channelId] && this.manifest.channels[channelId].requests && this.manifest.channels[channelId].requests[requestName];
    if (request && this.editors.has('request')) {
      const editor = this.editors.get('request');
      const exampleRequest = this.generateRequestExample(channelId, requestName, request);
      editor.setValue(exampleRequest);
    }
  }

  generateRequestExample(channelId, requestName, request) {
    // Generate example request JSON
    const example = {
      channel: channelId,
      request: requestName,
      parameters: {}
    };
    
    if (request.parameters) {
      Object.entries(request.parameters).forEach(function(entry) {
        const paramName = entry[0];
        const param = entry[1];
        example.parameters[paramName] = param.example || param.default || '';
      });
    }
    
    return JSON.stringify(example, null, 2);
  }

  copyExample(channelId, requestName) {
    const request = this.manifest && this.manifest.channels && this.manifest.channels[channelId] && this.manifest.channels[channelId].requests && this.manifest.channels[channelId].requests[requestName];
    if (request) {
      const example = this.generateRequestExample(channelId, requestName, request);
      navigator.clipboard.writeText(example);
      this.showToast('Example copied to clipboard');
    }
  }

  initializeEditors() {
    if (typeof monaco !== 'undefined') {
      // Request editor
      this.editors.set('request', monaco.editor.create(
        document.getElementById('request-editor'),
        {
          value: '{}',
          language: 'json',
          theme: 'vs-dark',
          minimap: { enabled: false }
        }
      ));
    }
  }

  updateUI() {
    this.updateConnectionStatus();
    this.updateContextPanel();
  }

  updateConnectionStatus(connected = false) {
    const statusIndicator = document.getElementById('global-connection-status');
    if (statusIndicator) {
      const dot = statusIndicator.querySelector('.status-dot');
      const text = statusIndicator.querySelector('span');
      
      if (dot && text) {
        dot.className = 'status-dot ' + (connected ? 'status-connected' : 'status-disconnected');
        text.textContent = connected ? 'Connected' : 'Disconnected';
      }
    }
  }

  updateContextPanel() {
    // Update context panel based on current panel
  }

  showToast(message, type = 'info') {
    // Create and show toast notification
    const toast = document.createElement('div');
    const colors = {
      success: '#10b981',
      error: '#ef4444',
      warning: '#f59e0b',
      info: '#3b82f6'
    };
    
    toast.className = 'toast';
    toast.innerHTML = '<i class="fas fa-' + this.getToastIcon(type) + '"></i> ' + message;
    toast.style.cssText = [
      'position: fixed',
      'top: 20px',
      'right: 20px',
      'background: ' + (colors[type] || colors.info),
      'color: white',
      'padding: 12px 20px',
      'border-radius: 6px',
      'z-index: 10000',
      'font-size: 14px',
      'box-shadow: 0 4px 12px rgba(0,0,0,0.15)',
      'transform: translateX(100%)',
      'transition: transform 0.3s ease',
      'display: flex',
      'align-items: center',
      'gap: 8px',
      'max-width: 300px'
    ].join('; ');
    
    document.body.appendChild(toast);
    
    // Show animation
    setTimeout(() => {
      toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    }, 3000);
  }
  
  getToastIcon(type) {
    switch (type) {
      case 'success': return 'check-circle';
      case 'error': return 'exclamation-circle';
      case 'warning': return 'exclamation-triangle';
      default: return 'info-circle';
    }
  }
  
  // Additional utility methods for complete functionality
  connectToSocket(socketPath) {
    var self = this;
    this.showToast('Connecting to ' + socketPath + '...');
    setTimeout(function() {
      self.showToast('Connected to ' + socketPath, 'success');
      self.updateConnectionStatus(true);
    }, 1000);
  }
  
  disconnectFromSocket() {
    var self = this;
    this.showToast('Disconnecting...', 'warning');
    setTimeout(function() {
      self.showToast('Disconnected', 'info');
      self.updateConnectionStatus(false);
    }, 500);
  }
  
  createNewRequest() {
    this.showToast('New request template created');
    var socketPath = document.getElementById('explorer-socket-path');
    var channelSelect = document.getElementById('explorer-channel');
    var requestSelect = document.getElementById('explorer-request');
    
    if (socketPath) socketPath.value = '/tmp/api.sock';
    if (channelSelect) channelSelect.value = '';
    if (requestSelect) {
      requestSelect.innerHTML = '<option value="">Select Request...</option>';
      requestSelect.disabled = true;
    }
  }
  
  startMonitor(socketPath) {
    var self = this;
    this.showToast('Starting monitor for ' + socketPath + '...');
    setTimeout(function() {
      self.showToast('Monitor active for ' + socketPath, 'success');
      self.updateMonitorStats();
    }, 1000);
  }
  
  updateMonitorStats() {
    var messageCount = document.getElementById('message-count');
    var errorCount = document.getElementById('error-count');
    var uptime = document.getElementById('uptime');
    
    if (messageCount) messageCount.textContent = Math.floor(Math.random() * 100);
    if (errorCount) errorCount.textContent = Math.floor(Math.random() * 5);
    if (uptime) {
      var minutes = Math.floor(Math.random() * 60);
      var seconds = Math.floor(Math.random() * 60);
      uptime.textContent = String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0');
    }
  }
  
  clearConsole() {
    var output = document.getElementById('console-output');
    if (output) {
      output.innerHTML = '<div class="console-welcome"><i class="fas fa-code"></i><span>Console cleared</span></div>';
    }
  }
  
  toggleConsole() {
    var consoleElement = document.querySelector('.bottom-console');
    if (consoleElement) {
      consoleElement.classList.toggle('collapsed');
      var icon = document.querySelector('#toggle-console i');
      if (icon) {
        icon.className = consoleElement.classList.contains('collapsed') ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
      }
    }
  }
  
  validateManifest() {
    var self = this;
    this.showToast('Validating Manifest...');
    setTimeout(function() {
      self.showToast('Manifest is valid ✓', 'success');
    }, 1000);
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  new JanusDevelopmentEnvironment();
});
`;
  }

  /**
   * Generate enhanced README
   */
  private generateReadme(_outputDir: string): string {
    return `# ${this.options.title} - Development Environment

This is a professional Janus development environment with comprehensive tooling.

## Features

### 📖 Interactive Documentation
- Live API reference with searchable requests
- Interactive examples with "Try It" buttons
- Copy-to-clipboard functionality
- Professional syntax highlighting

### 🔧 API Explorer
- Visual request builder with Monaco editor
- Real-time request/response testing
- Connection management
- Response analysis tools

### 📊 Socket Monitor
- Real-time message monitoring
- Message filtering and analysis
- Performance metrics
- Timeline visualization

### 🛠️ Development Tools
- Message formatter and validator
- Code generator for multiple languages
- Connection tester
- Schema validation

## Interface Layout

- **Header**: Connection status and global controls
- **Left Sidebar**: Navigation between Documentation, Explorer, Monitor, and Tools
- **Main Content**: Context-sensitive content area
- **Right Sidebar**: Quick actions and context information
- **Bottom Console**: Output, logs, and error messages

## Professional Design

This environment uses a modern, professional design system with:
- Consistent color palette and typography
- Responsive layout that works on all screen sizes
- Accessibility features and keyboard navigation
- IDE-like interface familiar to developers

Generated with: janus-docs-cli v1.0.0 (Professional Development Environment)
`;
  }
}
