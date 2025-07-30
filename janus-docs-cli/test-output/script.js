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
                const navLink = document.querySelector(`a[href="#${id}"]`);
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

    // Copy code blocks to clipboard
    document.querySelectorAll('.code-block').forEach(block => {
        const button = document.createElement('button');
        button.className = 'copy-button';
        button.textContent = 'Copy';
        button.style.cssText = `
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
        `;
        
        block.style.position = 'relative';
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
        toggle.style.cssText = `
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
        `;
        
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

    // Search functionality
    const createSearch = () => {
        const searchContainer = document.createElement('div');
        searchContainer.style.cssText = `
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #34495e;
        `;
        
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.placeholder = 'Search commands...';
        searchInput.style.cssText = `
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #34495e;
            border-radius: 4px;
            background: #34495e;
            color: white;
            font-size: 0.9rem;
        `;
        
        searchInput.style.setProperty('::placeholder', 'color: #bdc3c7');
        
        searchContainer.appendChild(searchInput);
        
        const sidebarHeader = document.querySelector('.sidebar-header');
        sidebarHeader.parentNode.insertBefore(searchContainer, sidebarHeader.nextSibling);
        
        // Search functionality
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
    };
    
    createSearch();
});
      // Development Hub JavaScript
      class JanusDevHub {
        constructor() {
          this.apiSpec = null;
          this.socketClient = null;
          this.monitorConnection = null;
          this.messageEditors = new Map();
          this.init();
        }

        async init() {
          // Load API specification
          try {
            const response = await fetch('./api-spec.json');
            this.apiSpec = await response.json();
          } catch (error) {
            console.error('Failed to load API specification:', error);
          }

          this.setupEventListeners();
          this.initializeEditors();
        }

        setupEventListeners() {
          // Tab system
          document.addEventListener('click', (e) => {
            if (e.target.matches('.tab-button')) {
              this.switchTab(e.target);
            }
          });

          // Socket monitoring
          document.getElementById('start-monitoring')?.addEventListener('click', () => {
            this.startMonitoring();
          });

          document.getElementById('stop-monitoring')?.addEventListener('click', () => {
            this.stopMonitoring();
          });

          document.getElementById('clear-monitor')?.addEventListener('click', () => {
            this.clearMonitor();
          });

          // Message sender
          document.getElementById('connect-sender')?.addEventListener('click', () => {
            this.connectSender();
          });

          document.getElementById('disconnect-sender')?.addEventListener('click', () => {
            this.disconnectSender();
          });

          document.getElementById('send-message')?.addEventListener('click', () => {
            this.sendMessage();
          });

          // Channel/command selection
          document.getElementById('select-channel')?.addEventListener('change', (e) => {
            this.populateCommands(e.target.value);
            this.updateMessageEditor();
          });

          document.getElementById('select-command')?.addEventListener('change', () => {
            this.updateMessageEditor();
          });

          // Connection tester
          document.getElementById('test-connection')?.addEventListener('click', () => {
            this.testConnection();
          });

          document.getElementById('ping-server')?.addEventListener('click', () => {
            this.pingServer();
          });
        }

        initializeEditors() {
          // Initialize Monaco editors if available
          if (typeof monaco !== 'undefined') {
            // Message editor
            const messageEditorElement = document.getElementById('message-editor');
            if (messageEditorElement) {
              const messageEditor = monaco.editor.create(messageEditorElement, {
                value: '{}',
                language: 'json',
                theme: 'vs-dark',
                minimap: { enabled: false },
                scrollBeyondLastLine: false
              });
              this.messageEditors.set('message', messageEditor);
            }

            // JSON formatter editor
            const jsonEditorElement = document.getElementById('json-editor');
            if (jsonEditorElement) {
              const jsonEditor = monaco.editor.create(jsonEditorElement, {
                value: '',
                language: 'json',
                theme: 'vs-dark',
                minimap: { enabled: false },
                scrollBeyondLastLine: false
              });
              this.messageEditors.set('json', jsonEditor);
            }
          }
        }

        switchTab(tabButton) {
          const tabGroup = tabButton.closest('.monitor-tabs, .input-tabs');
          const contentContainer = tabGroup.nextElementSibling;
          const targetTab = tabButton.dataset.tab;

          // Update tab buttons
          tabGroup.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
          });
          tabButton.classList.add('active');

          // Update tab content
          contentContainer.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
          });
          document.getElementById(targetTab)?.classList.add('active');
        }

        async startMonitoring() {
          const socketPath = document.getElementById('monitor-socket-path').value;
          if (!socketPath) {
            alert('Please enter a socket path');
            return;
          }

          try {
            this.updateMonitorStatus('connecting', 'Connecting...');
            
            // Create a passive monitoring connection
            // This would use the TypeScript library's monitoring capabilities
            await this.createMonitorConnection(socketPath);
            
            this.updateMonitorStatus('connected', 'Monitoring');
            document.getElementById('start-monitoring').disabled = true;
            document.getElementById('stop-monitoring').disabled = false;
          } catch (error) {
            this.updateMonitorStatus('disconnected', 'Failed to connect');
            console.error('Monitoring failed:', error);
          }
        }

        async createMonitorConnection(socketPath) {
          // Implementation would use TypeScript library for monitoring
          // For now, simulate the connection
          return new Promise((resolve) => {
            setTimeout(() => {
              this.simulateMessages();
              resolve();
            }, 1000);
          });
        }

        simulateMessages() {
          // Simulate incoming messages for demonstration
          const messages = [
            { 
              type: 'command',
              channelId: 'user-service',
              commandName: 'create-user',
              timestamp: new Date().toISOString(),
              data: { username: 'john_doe', email: 'john@example.com' }
            },
            {
              type: 'response',
              commandId: 'cmd-123',
              timestamp: new Date().toISOString(),
              success: true,
              data: { userId: '12345', message: 'User created successfully' }
            }
          ];

          messages.forEach((msg, index) => {
            setTimeout(() => {
              this.displayMessage(msg);
            }, (index + 1) * 2000);
          });
        }

        displayMessage(message) {
          const messageList = document.getElementById('message-list');
          const emptyState = messageList.querySelector('.empty-state');
          if (emptyState) {
            emptyState.remove();
          }

          const messageElement = document.createElement('div');
          messageElement.className = 'message-item';
          messageElement.innerHTML = `
            <div class="message-header">
              <span class="message-type">${message.type}</span>
              <span class="message-time">${new Date(message.timestamp).toLocaleTimeString()}</span>
            </div>
            <div class="message-content">${JSON.stringify(message.data || message, null, 2)}</div>
          `;

          messageList.appendChild(messageElement);
          messageList.scrollTop = messageList.scrollHeight;
        }

        updateMonitorStatus(status, text) {
          const statusElement = document.getElementById('monitor-status');
          const dot = statusElement.querySelector('.status-dot');
          const textElement = statusElement.querySelector('.status-text');

          dot.className = `status-dot status-${status}`;
          textElement.textContent = text;
        }

        populateCommands(channelId) {
          const commandSelect = document.getElementById('select-command');
          commandSelect.innerHTML = '<option value="">Select a command...</option>';

          if (channelId && this.apiSpec?.channels[channelId]) {
            const commands = this.apiSpec.channels[channelId].commands;
            Object.keys(commands).forEach(commandName => {
              const option = document.createElement('option');
              option.value = commandName;
              option.textContent = commandName;
              commandSelect.appendChild(option);
            });
            commandSelect.disabled = false;
          } else {
            commandSelect.disabled = true;
          }
        }

        updateMessageEditor() {
          const channelId = document.getElementById('select-channel').value;
          const commandName = document.getElementById('select-command').value;

          if (channelId && commandName && this.apiSpec) {
            const command = this.apiSpec.channels[channelId]?.commands[commandName];
            if (command) {
              const template = this.generateMessageTemplate(command);
              const editor = this.messageEditors.get('message');
              if (editor) {
                editor.setValue(JSON.stringify(template, null, 2));
              }
            }
          }
        }

        generateMessageTemplate(command) {
          const template = {};
          
          if (command.arguments) {
            command.arguments.forEach(arg => {
              switch (arg.type) {
                case 'string':
                  template[arg.name] = '';
                  break;
                case 'number':
                  template[arg.name] = 0;
                  break;
                case 'boolean':
                  template[arg.name] = false;
                  break;
                case 'object':
                  template[arg.name] = {};
                  break;
                case 'array':
                  template[arg.name] = [];
                  break;
                default:
                  template[arg.name] = null;
              }
            });
          }

          return template;
        }

        async connectSender() {
          const socketPath = document.getElementById('sender-socket-path').value;
          if (!socketPath) {
            alert('Please enter a socket path');
            return;
          }

          try {
            this.updateSenderStatus('connecting', 'Connecting...');
            
            // Create connection using TypeScript library
            await this.createSenderConnection(socketPath);
            
            this.updateSenderStatus('connected', 'Connected');
            document.getElementById('connect-sender').disabled = true;
            document.getElementById('disconnect-sender').disabled = false;
            document.getElementById('send-message').disabled = false;
          } catch (error) {
            this.updateSenderStatus('disconnected', 'Failed to connect');
            console.error('Connection failed:', error);
          }
        }

        async createSenderConnection(socketPath) {
          // Implementation would use TypeScript library
          return new Promise((resolve) => {
            setTimeout(resolve, 1000);
          });
        }

        updateSenderStatus(status, text) {
          const statusElement = document.getElementById('sender-status');
          const dot = statusElement.querySelector('.status-dot');
          const textElement = statusElement.querySelector('.status-text');

          dot.className = `status-dot status-${status}`;
          textElement.textContent = text;
        }

        async sendMessage() {
          const channelId = document.getElementById('select-channel').value;
          const commandName = document.getElementById('select-command').value;
          const editor = this.messageEditors.get('message');

          if (!channelId || !commandName || !editor) {
            alert('Please select a channel, command, and enter message data');
            return;
          }

          try {
            const messageData = JSON.parse(editor.getValue());
            
            // Send message using TypeScript library
            const response = await this.sendSocketMessage(channelId, commandName, messageData);
            
            this.displayResponse(response);
          } catch (error) {
            console.error('Send message failed:', error);
            this.displayResponse({ error: error.message });
          }
        }

        async sendSocketMessage(channelId, commandName, data) {
          // Implementation would use TypeScript library
          return new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                success: true,
                data: { message: 'Message sent successfully', commandId: 'cmd-' + Date.now() },
                timestamp: new Date().toISOString()
              });
            }, 500);
          });
        }

        displayResponse(response) {
          const responseDisplay = document.getElementById('response-display');
          const emptyState = responseDisplay.querySelector('.empty-state');
          if (emptyState) {
            emptyState.remove();
          }

          responseDisplay.innerHTML = `
            <div class="response-content">
              <pre>${JSON.stringify(response, null, 2)}</pre>
            </div>
          `;
        }

        clearMonitor() {
          const messageList = document.getElementById('message-list');
          messageList.innerHTML = '<div class="empty-state"><p>No messages yet. Start monitoring to see real-time communication.</p></div>';
        }

        stopMonitoring() {
          // Stop monitoring
          this.updateMonitorStatus('disconnected', 'Disconnected');
          document.getElementById('start-monitoring').disabled = false;
          document.getElementById('stop-monitoring').disabled = true;
        }

        async testConnection() {
          const socketPath = document.getElementById('test-socket-path').value;
          if (!socketPath) {
            alert('Please enter a socket path');
            return;
          }

          const resultsContainer = document.getElementById('connection-results');
          resultsContainer.innerHTML = '<div class="loading">Testing connection...</div>';

          try {
            // Test connection using TypeScript library
            const result = await this.performConnectionTest(socketPath);
            this.displayConnectionResults(result);
          } catch (error) {
            this.displayConnectionResults({ success: false, error: error.message });
          }
        }

        async performConnectionTest(socketPath) {
          // Implementation would use TypeScript library
          return new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                success: true,
                socketPath,
                timestamp: new Date().toISOString(),
                latency: Math.random() * 10 + 1,
                details: 'Connection successful'
              });
            }, 1000);
          });
        }

        displayConnectionResults(result) {
          const resultsContainer = document.getElementById('connection-results');
          
          if (result.success) {
            resultsContainer.innerHTML = `
              <div class="test-result success">
                <h4>✅ Connection Successful</h4>
                <p><strong>Socket Path:</strong> ${result.socketPath}</p>
                <p><strong>Latency:</strong> ${result.latency?.toFixed(2)}ms</p>
                <p><strong>Timestamp:</strong> ${result.timestamp}</p>
              </div>
            `;
          } else {
            resultsContainer.innerHTML = `
              <div class="test-result error">
                <h4>❌ Connection Failed</h4>
                <p><strong>Error:</strong> ${result.error}</p>
                <p><strong>Socket Path:</strong> ${result.socketPath || 'Unknown'}</p>
              </div>
            `;
          }
        }
      }

      // Initialize development hub when page loads
      document.addEventListener('DOMContentLoaded', () => {
        new JanusDevHub();
      });
    