# Janus Documentation CLI

A powerful CLI tool for generating and serving professional documentation from Janus manifests.

## Features

🚀 **Static Generation**: Generate beautiful, responsive documentation  
🔄 **Live Reload**: Serve with automatic updates when manifests change  
📱 **Responsive**: Works perfectly on desktop and mobile  
🎨 **Professional**: Swagger/OpenAPI-style documentation  
🔍 **Interactive**: Search, copy examples, deep linking  
⚡ **Fast**: Built with TypeScript and modern tools  

## Installation

```bash
# Install globally
npm install -g janus-docs-cli

# Or use with npx (no installation needed)
npx janus-docs-cli --help
```

## Quick Start

```bash
# Generate static documentation
janus-docs generate manifest.json

# Serve with live reload
janus-docs serve manifest.json --port 8080

# Initialize new Manifest
janus-docs init "My API"

# Validate manifest
janus-docs validate manifest.json
```

## Requests

### `generate`

Generate static documentation from an Manifest.

```bash
janus-docs generate <manifest-file> [options]

Options:
  -o, --output <dir>        Output directory (default: "./docs")
  -t, --title <title>       Documentation title
  -d, --description <desc>  Documentation description
  -v, --version <version>   API version
  -l, --logo <url>          Logo URL
  -s, --styles <file>       Custom CSS file
  --no-examples             Exclude examples
  --no-types                Exclude TypeScript types
```

**Example:**
```bash
janus-docs generate manifest.json \\
  --output ./docs \\
  --title "My API" \\
  --description "Comprehensive API documentation" \\
  --logo "https://example.com/logo.png"
```

### `serve`

Serve documentation with live reload during development.

```bash
janus-docs serve <manifest-file> [options]

Options:
  -p, --port <port>         Server port (default: 8080)
  -h, --host <host>         Server host (default: localhost)
  -o, --output <dir>        Output directory (default: "./docs")
  --no-watch                Disable file watching
  --no-open                 Don't open browser automatically
  [generation options...]   All generate options are supported
```

**Example:**
```bash
janus-docs serve manifest.json \\
  --port 3000 \\
  --watch \\
  --open
```

### `validate`

Validate an Manifest file for correctness.

```bash
janus-docs validate <manifest-file>
```

### `init`

Initialize a new Manifest file with example content.

```bash
janus-docs init [name] [options]

Options:
  -o, --output <file>       Output file (default: "manifest.json")
```

## Manifest Format

The CLI expects JSON files following the Janus manifest format:

```json
{
  "version": "1.0.0",
  "name": "My API",
  "description": "API description",
  "channels": {
    "user-service": {
      "name": "User Service",
      "description": "User management operations",
      "requests": {
        "create-user": {
          "name": "Create User",
          "description": "Create a new user account",
          "args": {
            "username": {
              "name": "Username",
              "type": "string",
              "description": "Unique username",
              "required": true,
              "minLength": 3,
              "maxLength": 50
            }
          },
          "response": {
            "type": "object",
            "description": "User creation result"
          },
          "errorCodes": ["VALIDATION_FAILED", "USERNAME_EXISTS"]
        }
      }
    }
  },
  "models": {
    "User": {
      "name": "User",
      "type": "object",
      "description": "User model",
      "properties": {
        "id": {
          "name": "ID",
          "type": "string",
          "description": "User ID"
        }
      },
      "required": ["id"]
    }
  }
}
```

## Customization

### Custom Styles

Create a custom CSS file and use it with the `--styles` option:

```css
/* custom-styles.css */
.sidebar-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

```bash
janus-docs generate manifest.json --styles custom-styles.css
```

### Custom Logo

Add your logo with the `--logo` option:

```bash
janus-docs generate manifest.json --logo "https://example.com/logo.png"
```

## Generated Documentation Features

### 📱 Responsive Design
- Mobile-friendly interface
- Collapsible navigation
- Touch-friendly interactions

### 🔍 Search Functionality
- Real-time request search
- Keyboard shortcuts
- Filter by channels and models

### 📋 Interactive Examples
- Copy code examples with one click
- Working request/response examples
- Protocol-manifestific formatting

### 🔗 Deep Linking
- Direct links to requests and models
- Bookmarkable URLs
- Navigation highlighting

### 🔄 Live Reload (Serve Mode)
- Automatic browser refresh
- WebSocket-based updates
- File watching with debouncing

## Development Workflow

1. **Create Manifest**:
   ```bash
   janus-docs init "My API"
   ```

2. **Develop with Live Reload**:
   ```bash
   janus-docs serve manifest.json --watch --open
   ```

3. **Validate Manifest**:
   ```bash
   janus-docs validate manifest.json
   ```

4. **Generate Production Docs**:
   ```bash
   janus-docs generate manifest.json --output ./public/docs
   ```

## Integration Examples

### CI/CD Pipeline

```yaml
# .github/workflows/docs.yml
name: Generate API Documentation

on:
  push:
    paths:
      - 'manifest.json'

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Generate Documentation
        run: |
          npx janus-docs-cli generate manifest.json --output ./docs
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

### NPM Scripts

```json
{
  "scripts": {
    "docs:generate": "janus-docs generate manifest.json",
    "docs:serve": "janus-docs serve manifest.json --watch",
    "docs:validate": "janus-docs validate manifest.json",
    "docs:build": "npm run docs:validate && npm run docs:generate"
  }
}
```

### Docker

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY manifest.json .

RUN npx janus-docs-cli generate manifest.json --output ./docs

FROM nginx:alpine
COPY --from=0 /app/docs /usr/share/nginx/html

EXPOSE 80
```

## Output Structure

The generated documentation includes:

```
docs/
├── index.html          # Main documentation page
├── styles.css          # Compiled styles
├── script.js           # Interactive functionality
├── openapi.json        # OpenManifest
└── README.md           # Documentation guide
```

## Requirements

- Node.js 16.0.0 or higher
- Modern web browser for viewing docs

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

- 📖 Documentation: See examples and API reference
- 🐛 Issues: Report bugs and feature requests
- 💬 Discussions: Ask questions and share feedback