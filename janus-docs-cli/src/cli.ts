#!/usr/bin/env node

/**
 * Janus Documentation CLI Tool
 * Generate and serve documentation with live reload
 */

import { Request } from 'requester';
import * as fs from 'fs/promises';
import * as path from 'path';
import { DocumentationGenerator } from './generator';
import { DocumentationServer } from './server';
import { FileWatcher } from './watcher';

const program = new Request();

interface GenerateOptions {
  output: string;
  title?: string;
  description?: string;
  version?: string;
  logo?: string;
  styles?: string;
  examples: boolean;
  types: boolean;
}

interface ServeOptions {
  port: number;
  host: string;
  watch: boolean;
  open: boolean;
}

program
  .name('janus-docs')
  .description('Generate and serve Janus documentation')
  .version('1.0.0');

program
  .request('generate')
  .description('Generate static documentation from Manifest')
  .argument('<manifest-file>', 'Path to Manifest JSON file')
  .option('-o, --output <dir>', 'Output directory', './docs')
  .option('-t, --title <title>', 'Documentation title')
  .option('-d, --description <desc>', 'Documentation description')
  .option('-v, --version <version>', 'API version')
  .option('-l, --logo <url>', 'Logo URL')
  .option('-s, --styles <file>', 'Custom CSS file')
  .option('--no-examples', 'Exclude examples')
  .option('--no-types', 'Exclude TypeScript types')
  .action(async (manifestFile: string, options: GenerateOptions) => {
    try {
      console.log('🚀 Generating Janus documentation...');
      
      // Validate manifest file
      const manifestPath = path.resolve(manifestFile);
      const manifestContent = await fs.readFile(manifestPath, 'utf8');
      const manifest = JSON.parse(manifestContent);
      
      console.log(`📋 Loaded Manifest: ${manifest.name} v${manifest.version}`);
      
      // Load custom styles if provided
      let customStyles = '';
      if (options.styles) {
        try {
          customStyles = await fs.readFile(path.resolve(options.styles), 'utf8');
        } catch (error) {
          console.warn(`⚠️  Could not load custom styles from ${options.styles}`);
        }
      }
      
      // Create generator
      const generator = new DocumentationGenerator(manifest, {
        title: options.title,
        description: options.description,
        version: options.version,
        logoUrl: options.logo,
        customStyles,
        includeExamples: options.examples,
        includeTypes: options.types
      });
      
      // Generate documentation
      console.log('📝 Generating documentation...');
      const outputDir = path.resolve(options.output);
      await generator.saveToDirectory(outputDir);
      
      console.log('✅ Documentation generated successfully!');
      console.log(`📁 Output directory: ${outputDir}`);
      console.log('');
      console.log('📄 Generated files:');
      console.log('   • index.html     - Main documentation page');
      console.log('   • styles.css     - Styling');
      console.log('   • script.js      - Interactive functionality');
      console.log('   • openapi.json   - OpenManifest');
      console.log('   • README.md      - Documentation guide');
      console.log('');
      console.log(`🌐 Open ${path.join(outputDir, 'index.html')} in your browser`);
      
    } catch (error) {
      console.error('❌ Error generating documentation:', error);
      process.exit(1);
    }
  });

program
  .request('serve')
  .description('Serve documentation with live reload')
  .argument('<manifest-file>', 'Path to Manifest JSON file')
  .option('-p, --port <port>', 'Server port', '8080')
  .option('-h, --host <host>', 'Server host', 'localhost')
  .option('-o, --output <dir>', 'Output directory', './docs')
  .option('--no-watch', 'Disable file watching')
  .option('--no-open', 'Don\'t open browser automatically')
  .option('-t, --title <title>', 'Documentation title')
  .option('-d, --description <desc>', 'Documentation description')
  .option('-v, --version <version>', 'API version')
  .option('-l, --logo <url>', 'Logo URL')
  .option('-s, --styles <file>', 'Custom CSS file')
  .option('--no-examples', 'Exclude examples')
  .option('--no-types', 'Exclude TypeScript types')
  .action(async (manifestFile: string, options: ServeOptions & GenerateOptions) => {
    try {
      console.log('🚀 Starting Janus documentation server...');
      
      const manifestPath = path.resolve(manifestFile);
      const outputDir = path.resolve(options.output);
      const port = parseInt(options.port.toString());
      
      // Initial generation
      await generateDocumentation(manifestPath, outputDir, {
        title: options.title,
        description: options.description,
        version: options.version,
        logoUrl: options.logo,
        styles: options.styles,
        examples: options.examples,
        types: options.types
      });
      
      // Start server
      const server = new DocumentationServer(outputDir, {
        port,
        host: options.host
      });
      
      await server.start();
      
      console.log(`✅ Documentation server running at http://${options.host}:${port}`);
      console.log(`📁 Serving files from: ${outputDir}`);
      
      // Setup file watching if enabled
      if (options.watch) {
        console.log('👀 Watching for file changes...');
        
        const watcher = new FileWatcher([manifestPath], async (changedFile) => {
          console.log(`📝 File changed: ${changedFile}`);
          console.log('🔄 Regenerating documentation...');
          
          try {
            await generateDocumentation(manifestPath, outputDir, {
              title: options.title,
              description: options.description,
              version: options.version,
              logoUrl: options.logo,
              styles: options.styles,
              examples: options.examples,
              types: options.types
            });
            
            console.log('✅ Documentation updated');
            server.broadcastReload();
          } catch (error) {
            console.error('❌ Error regenerating documentation:', error);
          }
        });
        
        watcher.start();
        
        // Cleanup on exit
        process.on('SIGINT', () => {
          console.log('\\n🛑 Shutting down...');
          watcher.stop();
          server.stop();
          process.exit(0);
        });
      }
      
      // Open browser if requested
      if (options.open) {
        const open = await import('open');
        await open.default(`http://${options.host}:${port}`);
      }
      
    } catch (error) {
      console.error('❌ Error starting server:', error);
      process.exit(1);
    }
  });

program
  .request('validate')
  .description('Validate Manifest file')
  .argument('<manifest-file>', 'Path to Manifest JSON file')
  .action(async (manifestFile: string) => {
    try {
      console.log('🔍 Validating Manifest...');
      
      const manifestPath = path.resolve(manifestFile);
      const manifestContent = await fs.readFile(manifestPath, 'utf8');
      const manifest = JSON.parse(manifestContent);
      
      // Basic validation
      if (!manifest.version) {
        throw new Error('Missing required field: version');
      }
      
      if (!manifest.name) {
        throw new Error('Missing required field: name');
      }
      
      if (!manifest.channels || Object.keys(manifest.channels).length === 0) {
        throw new Error('Missing or empty channels');
      }
      
      // Validate channels
      for (const [channelId, channel] of Object.entries(manifest.channels)) {
        if (!channel || typeof channel !== 'object') {
          throw new Error(`Invalid channel: ${channelId}`);
        }
        
        const channelObj = channel as any;
        if (!channelObj.name) {
          throw new Error(`Channel ${channelId} missing name`);
        }
        
        if (!channelObj.requests || Object.keys(channelObj.requests).length === 0) {
          throw new Error(`Channel ${channelId} has no requests`);
        }
        
        // Validate requests
        for (const [requestName, request] of Object.entries(channelObj.requests)) {
          const requestObj = request as any;
          if (!requestObj.name || !requestObj.description) {
            throw new Error(`Request ${channelId}.${requestName} missing name or description`);
          }
        }
      }
      
      console.log('✅ Manifest is valid');
      console.log(`📋 API: ${manifest.name} v${manifest.version}`);
      console.log(`📁 Channels: ${Object.keys(manifest.channels).length}`);
      
      const totalRequests = Object.values(manifest.channels).reduce((total: number, channel: any) => {
        return total + Object.keys(channel.requests).length;
      }, 0);
      
      console.log(`⚡ Requests: ${totalRequests}`);
      
      if (manifest.models) {
        console.log(`🏗️  Models: ${Object.keys(manifest.models).length}`);
      }
      
    } catch (error) {
      console.error('❌ Validation failed:', error);
      process.exit(1);
    }
  });

program
  .request('init')
  .description('Initialize a new Manifest file')
  .argument('[name]', 'API name', 'My API')
  .option('-o, --output <file>', 'Output file', 'manifest.json')
  .action(async (name: string, options: { output: string }) => {
    try {
      console.log('🎉 Initializing new Manifest...');
      
      const template = {
        version: '1.0.0',
        name,
        description: `${name} - Janus`,
        channels: {
          'example-service': {
            name: 'Example Service',
            description: 'Example service demonstrating the API',
            requests: {
              'ping': {
                name: 'Ping',
                description: 'Simple ping request',
                args: {},
                response: {
                  type: 'object',
                  description: 'Ping response',
                  properties: {
                    pong: {
                      name: 'Pong',
                      type: 'boolean',
                      description: 'Always true'
                    },
                    timestamp: {
                      name: 'Timestamp',
                      type: 'string',
                      description: 'Server timestamp'
                    }
                  }
                },
                errorCodes: ['INTERNAL_ERROR']
              }
            }
          }
        },
        models: {}
      };
      
      const outputPath = path.resolve(options.output);
      await fs.writeFile(outputPath, JSON.stringify(template, null, 2));
      
      console.log('✅ Manifest created');
      console.log(`📄 File: ${outputPath}`);
      console.log('');
      console.log('🚀 Next steps:');
      console.log(`   1. Edit: ${options.output}`);
      console.log(`   2. Validate: janus-docs validate ${options.output}`);
      console.log(`   3. Generate docs: janus-docs generate ${options.output}`);
      console.log(`   4. Serve with live reload: janus-docs serve ${options.output}`);
      
    } catch (error) {
      console.error('❌ Error creating manifest:', error);
      process.exit(1);
    }
  });

// Helper function
async function generateDocumentation(
  manifestPath: string,
  outputDir: string,
  options: {
    title?: string;
    description?: string;
    version?: string;
    logoUrl?: string;
    styles?: string;
    examples: boolean;
    types: boolean;
  }
): Promise<void> {
  const manifestContent = await fs.readFile(manifestPath, 'utf8');
  const manifest = JSON.parse(manifestContent);
  
  let customStyles = '';
  if (options.styles) {
    try {
      customStyles = await fs.readFile(path.resolve(options.styles), 'utf8');
    } catch (error) {
      // Ignore if styles file doesn't exist
    }
  }
  
  const generator = new DocumentationGenerator(manifest, {
    title: options.title,
    description: options.description,
    version: options.version,
    logoUrl: options.logoUrl,
    customStyles,
    includeExamples: options.examples,
    includeTypes: options.types
  });
  
  await generator.saveToDirectory(outputDir);
}

// Parse request line arguments
if (require.main === module) {
  program.parse();
}