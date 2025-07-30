
// Professional Unix Socket API Development Environment
class JanusDevelopmentEnvironment {
  constructor() {
    this.apiSpec = null;
    this.connections = new Map();
    this.editors = new Map();
    this.currentPanel = 'documentation';
    this.init();
  }

  async init() {
    try {
      const response = await fetch('./api-spec.json');
      this.apiSpec = await response.json();
    } catch (error) {
      console.error('Failed to load API specification:', error);
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

    // Panel interactions
    this.setupDocumentationListeners();
    this.setupExplorerListeners();
    this.setupMonitorListeners();
    this.setupToolsListeners();
  }

  switchPanel(panelName) {
    // Update tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.panel === panelName);
    });

    // Update nav panels
    document.querySelectorAll('.nav-panel').forEach(panel => {
      panel.classList.toggle('active', panel.id === panelName + '-panel');
    });

    // Update content panels
    document.querySelectorAll('.content-panel').forEach(panel => {
      panel.classList.toggle('active', panel.id === panelName.replace('-', '-') + '-content');
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
      if (e.target.matches('[data-action="try-command"]')) {
        this.tryCommand(e.target.dataset.channel, e.target.dataset.command);
      } else if (e.target.matches('[data-action="copy-example"]')) {
        this.copyExample(e.target.dataset.channel, e.target.dataset.command);
      }
    });
  }

  tryCommand(channelId, commandName) {
    // Switch to explorer and populate
    this.switchPanel('explorer');
    const channelSelect = document.getElementById('explorer-channel');
    const commandSelect = document.getElementById('explorer-command');
    
    if (channelSelect) channelSelect.value = channelId;
    this.populateCommands(channelId);
    if (commandSelect) commandSelect.value = commandName;
    this.updateRequestEditor(channelId, commandName);
  }

  copyExample(channelId, commandName) {
    const command = this.apiSpec?.channels[channelId]?.commands[commandName];
    if (command) {
      const example = this.generateCommandExample(channelId, commandName, command);
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
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new JanusDevelopmentEnvironment();
});
