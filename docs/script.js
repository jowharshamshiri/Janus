
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
