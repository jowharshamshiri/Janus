/**
 * Documentation Generator
 * Simplified version of the TypeScript implementation
 */

import * as fs from 'fs/promises';
import * as path from 'path';

export interface DocumentationOptions {
  title?: string;
  description?: string;
  version?: string;
  includeExamples?: boolean;
  includeTypes?: boolean;
  customStyles?: string;
  logoUrl?: string;
}

export class DocumentationGenerator {
  private apiSpec: any;
  private options: Required<DocumentationOptions>;

  constructor(apiSpec: any, options: DocumentationOptions = {}) {
    this.apiSpec = apiSpec;
    this.options = {
      title: options.title ?? apiSpec.name,
      description: options.description ?? apiSpec.description ?? 'Unix Socket API Documentation',
      version: options.version ?? apiSpec.version,
      includeExamples: options.includeExamples ?? true,
      includeTypes: options.includeTypes ?? true,
      customStyles: options.customStyles ?? '',
      logoUrl: options.logoUrl ?? ''
    };
  }

  /**
   * Save documentation to directory
   */
  async saveToDirectory(outputDir: string): Promise<void> {
    // Ensure output directory exists
    await fs.mkdir(outputDir, { recursive: true });
    
    // Generate documentation components
    const html = this.generateHTML();
    const css = this.generateCSS();
    const javascript = this.generateJavaScript();
    const openApiSpec = this.generateOpenAPISpec();
    
    // Write files
    await fs.writeFile(path.join(outputDir, 'index.html'), html);
    await fs.writeFile(path.join(outputDir, 'styles.css'), css);
    await fs.writeFile(path.join(outputDir, 'script.js'), javascript);
    await fs.writeFile(path.join(outputDir, 'openapi.json'), JSON.stringify(openApiSpec, null, 2));
    
    // Create README
    const readme = this.generateReadme(outputDir);
    await fs.writeFile(path.join(outputDir, 'README.md'), readme);
  }

  /**
   * Generate HTML documentation
   */
  private generateHTML(): string {
    const channelCount = Object.keys(this.apiSpec.channels).length;
    const commandCount = Object.values(this.apiSpec.channels).reduce((total: number, channel: any) => {
      return total + Object.keys(channel.commands).length;
    }, 0);

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${this.options.title} - API Documentation</title>
    <link rel="stylesheet" href="styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css" rel="stylesheet">
</head>
<body>
    <nav class="sidebar">
        <div class="sidebar-header">
            ${this.options.logoUrl ? `<img src="${this.options.logoUrl}" alt="Logo" class="logo">` : ''}
            <h1>${this.options.title}</h1>
            <p class="version">v${this.options.version}</p>
        </div>
        
        <div class="search-container">
            <input type="text" id="search" placeholder="Search commands..." class="search-input">
        </div>
        
        <div class="sidebar-content">
            <div class="nav-section">
                <h3>Overview</h3>
                <ul>
                    <li><a href="#introduction">Introduction</a></li>
                    <li><a href="#protocol">Protocol</a></li>
                    <li><a href="#errors">Error Handling</a></li>
                </ul>
            </div>
            
            <div class="nav-section">
                <h3>Channels</h3>
                <ul>
                    ${Object.entries(this.apiSpec.channels).map(([channelId, channel]: [string, any]) => `
                        <li>
                            <a href="#channel-${channelId}" class="channel-link">${channel.name}</a>
                            <ul class="command-list">
                                ${Object.keys(channel.commands).map(commandName => 
                                    `<li><a href="#command-${channelId}-${commandName}" class="command-link">${commandName}</a></li>`
                                ).join('')}
                            </ul>
                        </li>
                    `).join('')}
                </ul>
            </div>
            
            ${this.apiSpec.models ? `
            <div class="nav-section">
                <h3>Models</h3>
                <ul>
                    ${Object.keys(this.apiSpec.models).map(modelName => 
                        `<li><a href="#model-${modelName}" class="model-link">${modelName}</a></li>`
                    ).join('')}
                </ul>
            </div>
            ` : ''}
        </div>
    </nav>

    <main class="main-content">
        <section id="introduction" class="section">
            <h1>${this.options.title}</h1>
            <p class="lead">${this.options.description}</p>
            
            <div class="info-cards">
                <div class="info-card">
                    <h3>Protocol</h3>
                    <p>Unix Domain Sockets</p>
                </div>
                <div class="info-card">
                    <h3>Version</h3>
                    <p>${this.options.version}</p>
                </div>
                <div class="info-card">
                    <h3>Channels</h3>
                    <p>${channelCount} available</p>
                </div>
                <div class="info-card">
                    <h3>Commands</h3>
                    <p>${commandCount} total</p>
                </div>
            </div>
        </section>

        <section id="protocol" class="section">
            <h2>Protocol Overview</h2>
            <p>This API uses Unix Domain Sockets for inter-process communication with JSON-based messaging and 4-byte length prefixes.</p>
            
            <h3>Message Format</h3>
            <div class="code-block">
                <pre><code class="language-json">{
  "id": "uuid-v4-string",
  "channelId": "channel-identifier", 
  "command": "command-name",
  "args": {
    "key": "value"
  },
  "timeout": 30.0,
  "timestamp": "2025-07-29T10:50:00.000Z"
}</code></pre>
            </div>
            
            <h3>Response Format</h3>
            <div class="code-block">
                <pre><code class="language-json">{
  "commandId": "uuid-from-request",
  "channelId": "channel-identifier",
  "success": true,
  "result": {
    "data": "response-data"
  },
  "timestamp": "2025-07-29T10:50:01.000Z"
}</code></pre>
            </div>
        </section>

        <section id="errors" class="section">
            <h2>Error Handling</h2>
            <p>All errors follow a standardized format with specific error codes and detailed messages.</p>
            
            <div class="code-block">
                <pre><code class="language-json">{
  "commandId": "uuid-from-request",
  "channelId": "channel-identifier", 
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": "Additional context"
  },
  "timestamp": "2025-07-29T10:50:01.000Z"
}</code></pre>
            </div>
        </section>

        ${this.generateChannelDocumentation()}
        
        ${this.apiSpec.models ? this.generateModelDocumentation() : ''}
    </main>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/plugins/autoloader/prism-autoloader.min.js"></script>
    <script src="script.js"></script>
</body>
</html>`;
  }

  /**
   * Generate channel documentation
   */
  private generateChannelDocumentation(): string {
    return Object.entries(this.apiSpec.channels).map(([channelId, channel]: [string, any]) => `
        <section id="channel-${channelId}" class="section">
            <h2>${channel.name}</h2>
            <p>${channel.description || ''}</p>
            
            ${Object.entries(channel.commands).map(([commandName, command]: [string, any]) => 
                this.generateCommandDocumentation(channelId, commandName, command)
            ).join('')}
        </section>
    `).join('');
  }

  /**
   * Generate command documentation
   */
  private generateCommandDocumentation(channelId: string, commandName: string, command: any): string {
    return `
        <div id="command-${channelId}-${commandName}" class="command">
            <h3>${command.name}</h3>
            <p>${command.description}</p>
            
            <div class="command-details">
                <div class="command-info">
                    <span class="badge">Channel: ${channelId}</span>
                    <span class="badge">Command: ${commandName}</span>
                    ${command.timeout ? `<span class="badge">Timeout: ${command.timeout}s</span>` : ''}
                </div>
                
                ${command.args && Object.keys(command.args).length > 0 ? `
                <h4>Arguments</h4>
                <div class="arguments">
                    ${Object.entries(command.args).map(([argName, arg]: [string, any]) => 
                        this.generateArgumentDocumentation(argName, arg)
                    ).join('')}
                </div>
                ` : ''}
                
                ${command.response ? `
                <h4>Response</h4>
                <div class="response">
                    <p><strong>Type:</strong> ${command.response.type}</p>
                    <p>${command.response.description}</p>
                </div>
                ` : ''}
                
                ${command.errorCodes ? `
                <h4>Error Codes</h4>
                <div class="error-codes">
                    ${command.errorCodes.map((code: string) => `<code class="error-code">${code}</code>`).join(' ')}
                </div>
                ` : ''}
                
                ${this.options.includeExamples ? this.generateCommandExample(channelId, commandName, command) : ''}
            </div>
        </div>
    `;
  }

  /**
   * Generate argument documentation
   */
  private generateArgumentDocumentation(argName: string, arg: any): string {
    return `
        <div class="argument">
            <div class="argument-header">
                <h5>${arg.name || argName}</h5>
                <span class="type">${arg.type}</span>
                ${arg.required ? '<span class="required">required</span>' : '<span class="optional">optional</span>'}
            </div>
            <p>${arg.description}</p>
            ${arg.default !== undefined ? `<p><strong>Default:</strong> <code>${JSON.stringify(arg.default)}</code></p>` : ''}
            ${arg.enum ? `<p><strong>Allowed values:</strong> ${arg.enum.map((v: any) => `<code>${JSON.stringify(v)}</code>`).join(', ')}</p>` : ''}
        </div>
    `;
  }

  /**
   * Generate command example
   */
  private generateCommandExample(channelId: string, commandName: string, command: any): string {
    const exampleCommand = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      channelId,
      command: commandName,
      args: command.args ? this.generateExampleArgs(command.args) : undefined,
      timeout: command.timeout || 30.0,
      timestamp: new Date().toISOString()
    };

    const exampleResponse = {
      commandId: '550e8400-e29b-41d4-a716-446655440000',
      channelId,
      success: true,
      result: { message: 'Command executed successfully' },
      timestamp: new Date().toISOString()
    };

    return `
        <h4>Example</h4>
        <div class="example">
            <h5>Request</h5>
            <div class="code-block">
                <pre><code class="language-json">${JSON.stringify(exampleCommand, null, 2)}</code></pre>
            </div>
            
            <h5>Response</h5>
            <div class="code-block">
                <pre><code class="language-json">${JSON.stringify(exampleResponse, null, 2)}</code></pre>
            </div>
        </div>
    `;
  }

  /**
   * Generate example arguments
   */
  private generateExampleArgs(args: any): any {
    const example: any = {};
    for (const [argName, arg] of Object.entries(args)) {
      const argObj = arg as any;
      if (argObj.default !== undefined) {
        example[argName] = argObj.default;
      } else if (argObj.enum) {
        example[argName] = argObj.enum[0];
      } else {
        switch (argObj.type) {
          case 'string':
            example[argName] = `example-${argName}`;
            break;
          case 'number':
          case 'integer':
            example[argName] = 42;
            break;
          case 'boolean':
            example[argName] = true;
            break;
          case 'array':
            example[argName] = ['item1', 'item2'];
            break;
          case 'object':
            example[argName] = { key: 'value' };
            break;
        }
      }
    }
    return Object.keys(example).length > 0 ? example : undefined;
  }

  /**
   * Generate model documentation
   */
  private generateModelDocumentation(): string {
    if (!this.apiSpec.models) return '';

    return `
        <section id="models" class="section">
            <h2>Data Models</h2>
            
            ${Object.entries(this.apiSpec.models).map(([modelName, model]: [string, any]) => `
                <div id="model-${modelName}" class="model">
                    <h3>${model.name}</h3>
                    <p>${model.description}</p>
                    
                    ${model.properties ? `
                    <h4>Properties</h4>
                    <div class="model-properties">
                        ${Object.entries(model.properties).map(([propName, prop]: [string, any]) => 
                            this.generateArgumentDocumentation(propName, prop)
                        ).join('')}
                    </div>
                    ` : ''}
                </div>
            `).join('')}
        </section>
    `;
  }

  /**
   * Generate CSS styles
   */
  private generateCSS(): string {
    return `
/* Unix Socket API Documentation Styles */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    background: #f8f9fa;
}

.sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 280px;
    height: 100vh;
    background: #2c3e50;
    color: white;
    overflow-y: auto;
    z-index: 1000;
}

.sidebar-header {
    padding: 2rem 1.5rem;
    border-bottom: 1px solid #34495e;
}

.logo {
    max-width: 60px;
    margin-bottom: 1rem;
}

.sidebar-header h1 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.version {
    color: #bdc3c7;
    font-size: 0.9rem;
}

.search-container {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #34495e;
}

.search-input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #34495e;
    border-radius: 4px;
    background: #34495e;
    color: white;
    font-size: 0.9rem;
}

.search-input::placeholder {
    color: #bdc3c7;
}

.sidebar-content {
    padding: 1rem 0;
}

.nav-section {
    margin-bottom: 2rem;
}

.nav-section h3 {
    padding: 0 1.5rem;
    color: #ecf0f1;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 1rem;
}

.nav-section ul {
    list-style: none;
}

.nav-section > ul > li > a {
    display: block;
    padding: 0.75rem 1.5rem;
    color: #bdc3c7;
    text-decoration: none;
    transition: all 0.2s;
}

.nav-section > ul > li > a:hover,
.nav-section > ul > li > a.active {
    background: #34495e;
    color: white;
}

.command-list {
    background: #34495e;
}

.command-list li a {
    display: block;
    padding: 0.5rem 2.5rem;
    color: #95a5a6;
    text-decoration: none;
    font-size: 0.9rem;
    transition: all 0.2s;
}

.command-list li a:hover,
.command-list li a.active {
    background: #3498db;
    color: white;
}

.main-content {
    margin-left: 280px;
    padding: 2rem;
    max-width: 1200px;
}

.section {
    background: white;
    margin-bottom: 2rem;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section h1 {
    color: #2c3e50;
    margin-bottom: 1rem;
    font-size: 2.5rem;
}

.section h2 {
    color: #2c3e50;
    margin-bottom: 1.5rem;
    font-size: 2rem;
    border-bottom: 2px solid #ecf0f1;
    padding-bottom: 0.5rem;
}

.section h3 {
    color: #34495e;
    margin: 2rem 0 1rem 0;
    font-size: 1.5rem;
}

.section h4 {
    color: #7f8c8d;
    margin: 1.5rem 0 1rem 0;
    font-size: 1.2rem;
}

.section h5 {
    color: #95a5a6;
    margin: 1rem 0 0.5rem 0;
    font-size: 1rem;
}

.lead {
    font-size: 1.2rem;
    color: #7f8c8d;
    margin-bottom: 2rem;
}

.info-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 2rem 0;
}

.info-card {
    background: #ecf0f1;
    padding: 1.5rem;
    border-radius: 6px;
    text-align: center;
}

.info-card h3 {
    color: #2c3e50;
    margin-bottom: 0.5rem;
    font-size: 1rem;
}

.info-card p {
    color: #7f8c8d;
    font-weight: 600;
}

.code-block {
    background: #2c3e50;
    border-radius: 6px;
    margin: 1rem 0;
    overflow-x: auto;
    position: relative;
}

.code-block pre {
    padding: 1.5rem;
    margin: 0;
    color: #ecf0f1;
}

.copy-button {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: #3498db;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
}

.command {
    border: 1px solid #ecf0f1;
    border-radius: 6px;
    margin: 1.5rem 0;
    padding: 1.5rem;
    background: #fdfdfd;
}

.command-details {
    margin-top: 1rem;
}

.command-info {
    margin-bottom: 1rem;
}

.badge {
    background: #3498db;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.8rem;
    margin-right: 0.5rem;
    display: inline-block;
}

.arguments, .model-properties {
    border-left: 3px solid #3498db;
    padding-left: 1rem;
    margin: 1rem 0;
}

.argument, .model {
    border: 1px solid #ecf0f1;
    border-radius: 4px;
    padding: 1rem;
    margin: 0.5rem 0;
    background: white;
}

.argument-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.5rem;
}

.argument-header h5 {
    margin: 0;
    color: #2c3e50;
}

.type {
    background: #95a5a6;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 3px;
    font-size: 0.8rem;
    font-family: monospace;
}

.required {
    background: #e74c3c;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 3px;
    font-size: 0.8rem;
}

.optional {
    background: #f39c12;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 3px;
    font-size: 0.8rem;
}

.error-codes {
    margin: 1rem 0;
}

.error-code {
    background: #e74c3c;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 3px;
    font-size: 0.9rem;
    margin-right: 0.5rem;
    display: inline-block;
    margin-bottom: 0.5rem;
}

.example {
    background: #f8f9fa;
    border: 1px solid #ecf0f1;
    border-radius: 6px;
    padding: 1rem;
    margin: 1rem 0;
}

/* Live reload indicator */
.reload-indicator {
    position: fixed;
    top: 1rem;
    right: 1rem;
    background: #2ecc71;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.8rem;
    z-index: 1001;
    transition: all 0.3s;
}

.reload-indicator.hidden {
    opacity: 0;
    transform: translateX(100%);
}

/* Responsive design */
@media (max-width: 768px) {
    .sidebar {
        transform: translateX(-100%);
        transition: transform 0.3s;
    }
    
    .sidebar.open {
        transform: translateX(0);
    }
    
    .main-content {
        margin-left: 0;
        padding: 1rem;
    }
    
    .mobile-toggle {
        display: block !important;
    }
}

/* Custom styles */
${this.options.customStyles}
    `.trim();
  }

  /**
   * Generate JavaScript functionality
   */
  private generateJavaScript(): string {
    return `
// Unix Socket API Documentation JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Highlight current section in navigation
    const observerOptions = {
        rootMargin: '-20% 0px -70% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Remove active class from all nav links
                document.querySelectorAll('.sidebar a').forEach(link => {
                    link.classList.remove('active');
                });
                
                // Add active class to corresponding nav link
                const id = entry.target.id;
                const navLink = document.querySelector(\`a[href="#\${id}"]\`);
                if (navLink) {
                    navLink.classList.add('active');
                }
            }
        });
    }, observerOptions);

    // Observe all sections and commands
    document.querySelectorAll('.section, .command').forEach(section => {
        if (section.id) {
            observer.observe(section);
        }
    });

    // Search functionality
    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const navLinks = document.querySelectorAll('.sidebar a');
            
            navLinks.forEach(link => {
                const text = link.textContent.toLowerCase();
                const listItem = link.closest('li');
                
                if (text.includes(query) || query === '') {
                    listItem.style.display = 'block';
                } else {
                    listItem.style.display = 'none';
                }
            });
        });
    }

    // Copy code blocks to clipboard
    document.querySelectorAll('.code-block').forEach(block => {
        const button = document.createElement('button');
        button.className = 'copy-button';
        button.textContent = 'Copy';
        
        block.appendChild(button);
        
        button.addEventListener('click', async () => {
            const code = block.querySelector('code').textContent;
            try {
                await navigator.clipboard.writeText(code);
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = 'Copy';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy code:', err);
            }
        });
    });

    // Mobile menu toggle
    const createMobileToggle = () => {
        const toggle = document.createElement('button');
        toggle.className = 'mobile-toggle';
        toggle.innerHTML = '☰';
        toggle.style.cssText = \`
            position: fixed;
            top: 1rem;
            left: 1rem;
            z-index: 1001;
            background: #2c3e50;
            color: white;
            border: none;
            padding: 0.75rem;
            border-radius: 6px;
            font-size: 1.2rem;
            cursor: pointer;
            display: none;
        \`;
        
        document.body.appendChild(toggle);
        
        toggle.addEventListener('click', () => {
            document.querySelector('.sidebar').classList.toggle('open');
        });
        
        // Show/hide mobile toggle based on screen size
        const checkMobile = () => {
            if (window.innerWidth <= 768) {
                toggle.style.display = 'block';
            } else {
                toggle.style.display = 'none';
                document.querySelector('.sidebar').classList.remove('open');
            }
        };
        
        window.addEventListener('resize', checkMobile);
        checkMobile();
    };
    
    createMobileToggle();

    // Live reload support (WebSocket connection)
    if (window.location.protocol === 'http:') {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = \`\${wsProtocol}//\${window.location.host}/ws\`;
        
        try {
            const ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log('📡 Connected to live reload server');
                showReloadIndicator('Connected', 'green');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'reload') {
                    console.log('🔄 Reloading page...');
                    showReloadIndicator('Reloading...', 'orange');
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                }
            };
            
            ws.onclose = () => {
                console.log('📡 Disconnected from live reload server');
                showReloadIndicator('Disconnected', 'red');
            };
            
            ws.onerror = () => {
                console.log('📡 Live reload not available');
            };
        } catch (error) {
            // Live reload not available, ignore
        }
    }
    
    function showReloadIndicator(text, color) {
        let indicator = document.querySelector('.reload-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'reload-indicator';
            document.body.appendChild(indicator);
        }
        
        indicator.textContent = text;
        indicator.style.backgroundColor = color;
        indicator.classList.remove('hidden');
        
        if (color === 'green') {
            setTimeout(() => {
                indicator.classList.add('hidden');
            }, 2000);
        }
    }
});
    `.trim();
  }

  /**
   * Generate OpenAPI specification
   */
  private generateOpenAPISpec(): any {
    return {
      openapi: '3.0.3',
      info: {
        title: this.options.title,
        description: this.options.description,
        version: this.options.version,
        'x-protocol': 'unix-socket',
        'x-message-format': 'json-with-length-prefix'
      },
      servers: [
        {
          url: 'unix:/tmp/api.sock',
          description: 'Unix Domain Socket Server'
        }
      ],
      paths: this.generateOpenAPIPaths(),
      components: {
        schemas: this.generateOpenAPISchemas()
      }
    };
  }

  /**
   * Generate OpenAPI paths
   */
  private generateOpenAPIPaths(): any {
    const paths: any = {};
    
    for (const [channelId, channel] of Object.entries(this.apiSpec.channels)) {
      const channelObj = channel as any;
      for (const [commandName, command] of Object.entries(channelObj.commands)) {
        const pathKey = \`/\${channelId}/\${commandName}\`;
        const commandObj = command as any;
        
        paths[pathKey] = {
          post: {
            summary: commandObj.name,
            description: commandObj.description,
            'x-channel': channelId,
            'x-command': commandName,
            requestBody: {
              required: true,
              content: {
                'application/json': {
                  schema: { type: 'object' }
                }
              }
            },
            responses: {
              '200': {
                description: 'Successful response',
                content: {
                  'application/json': {
                    schema: { type: 'object' }
                  }
                }
              },
              'default': {
                description: 'Error response',
                content: {
                  'application/json': {
                    schema: { type: 'object' }
                  }
                }
              }
            }
          }
        };
      }
    }
    
    return paths;
  }

  /**
   * Generate OpenAPI schemas
   */
  private generateOpenAPISchemas(): any {
    const schemas: any = {};
    
    if (this.apiSpec.models) {
      for (const [modelName, model] of Object.entries(this.apiSpec.models)) {
        const modelObj = model as any;
        schemas[modelName] = {
          type: modelObj.type,
          description: modelObj.description,
          properties: modelObj.properties || {},
          required: modelObj.required || []
        };
      }
    }
    
    return schemas;
  }

  /**
   * Generate README
   */
  private generateReadme(outputDir: string): string {
    return \`# \${this.options.title} Documentation

This directory contains automatically generated documentation for the Unix Socket API.

## Files

- \\\`index.html\\\` - Main documentation page (open in browser)
- \\\`styles.css\\\` - Styling for the documentation
- \\\`script.js\\\` - Interactive functionality
- \\\`openapi.json\\\` - OpenAPI/Swagger specification

## Usage

1. **View Documentation**: Open \\\`index.html\\\` in a web browser
2. **API Integration**: Use \\\`openapi.json\\\` with API tools like Postman or Insomnia
3. **Development**: Import the OpenAPI spec into your development environment

## Features

- 📱 **Responsive Design**: Works on desktop and mobile
- 🔍 **Search Functionality**: Find commands and models quickly
- 📋 **Copy Examples**: Click to copy code examples
- 🎨 **Professional Styling**: Clean, modern interface
- 🔗 **Deep Linking**: Direct links to sections and commands
- 🔄 **Live Reload**: Automatic updates during development

Generated on: \${new Date().toISOString()}
Generated with: unixsocket-docs-cli v1.0.0
\`;
  }
}\`;
  }
}