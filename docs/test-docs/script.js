
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
        this.switchPanel(e.target.dataset.panel);
      });
    });

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
    const connectBtn = document.getElementById('monitor-connect-btn');
    const disconnectBtn = document.getElementById('monitor-disconnect-btn');
    const clearBtn = document.getElementById('monitor-clear-btn');
    
    if (connectBtn) {
      connectBtn.addEventListener('click', () => this.connectMonitor());
    }
    if (disconnectBtn) {
      disconnectBtn.addEventListener('click', () => this.disconnectMonitor());
    }
    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.clearMonitorLog());
    }
  }

  setupToolsListeners() {
    // Handle Development Tools interactions
    const generateBtn = document.getElementById('generate-client-btn');
    const exportBtn = document.getElementById('export-openapi-btn');
    
    if (generateBtn) {
      generateBtn.addEventListener('click', () => this.generateClientCode());
    }
    if (exportBtn) {
      exportBtn.addEventListener('click', () => this.exportOpenAPI());
    }
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

  updateConnectionStatus() {
    const status = document.getElementById('global-connection-status');
    // Update based on actual connection state
  }

  updateContextPanel() {
    // Update context panel based on current panel
  }

  showToast(message) {
    // Show temporary notification
    console.log(message);
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #2563eb; color: white; padding: 12px 20px; border-radius: 6px; z-index: 10000; font-size: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); animation: slideIn 0.3s ease;';
    
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    }, 3000);
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new JanusDevelopmentEnvironment();
});
