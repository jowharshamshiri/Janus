#!/usr/bin/env node

/**
 * Unix Socket API Documentation CLI Tool
 * Generate and serve documentation with live reload
 */

import { Command } from 'commander';
import * as fs from 'fs/promises';
import * as path from 'path';
import { DocumentationGenerator } from './generator';
import { DocumentationServer } from './server';
import { FileWatcher } from './watcher';

const program = new Command();

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
  .description('Generate and serve Unix Socket API documentation')
  .version('1.0.0');

program
  .command('generate')
  .description('Generate static documentation from API specification')
  .argument('<spec-file>', 'Path to API specification JSON file')
  .option('-o, --output <dir>', 'Output directory', './docs')
  .option('-t, --title <title>', 'Documentation title')
  .option('-d, --description <desc>', 'Documentation description')
  .option('-v, --version <version>', 'API version')
  .option('-l, --logo <url>', 'Logo URL')
  .option('-s, --styles <file>', 'Custom CSS file')
  .option('--no-examples', 'Exclude examples')
  .option('--no-types', 'Exclude TypeScript types')
  .action(async (specFile: string, options: GenerateOptions) => {
    try {
      console.log('🚀 Generating Unix Socket API documentation...');
      
      // Validate spec file
      const specPath = path.resolve(specFile);
      const specContent = await fs.readFile(specPath, 'utf8');
      const apiSpec = JSON.parse(specContent);
      
      console.log(`📋 Loaded API specification: ${apiSpec.name} v${apiSpec.version}`);
      
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
      const generator = new DocumentationGenerator(apiSpec, {
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
      console.log('   • openapi.json   - OpenAPI specification');
      console.log('   • README.md      - Documentation guide');
      console.log('');
      console.log(`🌐 Open ${path.join(outputDir, 'index.html')} in your browser`);
      
    } catch (error) {
      console.error('❌ Error generating documentation:', error);
      process.exit(1);
    }
  });

program
  .command('serve')
  .description('Serve documentation with live reload')
  .argument('<spec-file>', 'Path to API specification JSON file')
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
  .action(async (specFile: string, options: ServeOptions & GenerateOptions) => {
    try {
      console.log('🚀 Starting Unix Socket API documentation server...');
      
      const specPath = path.resolve(specFile);
      const outputDir = path.resolve(options.output);
      const port = parseInt(options.port.toString());
      
      // Initial generation
      await generateDocumentation(specPath, outputDir, {
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
        
        const watcher = new FileWatcher([specPath], async (changedFile) => {
          console.log(`📝 File changed: ${changedFile}`);
          console.log('🔄 Regenerating documentation...');
          
          try {
            await generateDocumentation(specPath, outputDir, {
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
  .command('validate')
  .description('Validate API specification file')
  .argument('<spec-file>', 'Path to API specification JSON file')
  .action(async (specFile: string) => {
    try {
      console.log('🔍 Validating API specification...');
      
      const specPath = path.resolve(specFile);
      const specContent = await fs.readFile(specPath, 'utf8');
      const apiSpec = JSON.parse(specContent);
      
      // Basic validation
      if (!apiSpec.version) {
        throw new Error('Missing required field: version');
      }
      
      if (!apiSpec.name) {
        throw new Error('Missing required field: name');
      }
      
      if (!apiSpec.channels || Object.keys(apiSpec.channels).length === 0) {
        throw new Error('Missing or empty channels');
      }
      
      // Validate channels
      for (const [channelId, channel] of Object.entries(apiSpec.channels)) {
        if (!channel || typeof channel !== 'object') {
          throw new Error(`Invalid channel: ${channelId}`);
        }
        
        const channelObj = channel as any;
        if (!channelObj.name) {
          throw new Error(`Channel ${channelId} missing name`);
        }
        
        if (!channelObj.commands || Object.keys(channelObj.commands).length === 0) {
          throw new Error(`Channel ${channelId} has no commands`);
        }
        
        // Validate commands
        for (const [commandName, command] of Object.entries(channelObj.commands)) {
          const commandObj = command as any;
          if (!commandObj.name || !commandObj.description) {
            throw new Error(`Command ${channelId}.${commandName} missing name or description`);
          }
        }
      }
      
      console.log('✅ API specification is valid');
      console.log(`📋 API: ${apiSpec.name} v${apiSpec.version}`);
      console.log(`📁 Channels: ${Object.keys(apiSpec.channels).length}`);
      
      const totalCommands = Object.values(apiSpec.channels).reduce((total: number, channel: any) => {
        return total + Object.keys(channel.commands).length;
      }, 0);
      
      console.log(`⚡ Commands: ${totalCommands}`);
      
      if (apiSpec.models) {
        console.log(`🏗️  Models: ${Object.keys(apiSpec.models).length}`);
      }
      
    } catch (error) {
      console.error('❌ Validation failed:', error);
      process.exit(1);
    }
  });

program
  .command('init')
  .description('Initialize a new API specification file')
  .argument('[name]', 'API name', 'My API')
  .option('-o, --output <file>', 'Output file', 'api-spec.json')
  .action(async (name: string, options: { output: string }) => {
    try {
      console.log('🎉 Initializing new API specification...');
      
      const template = {
        version: '1.0.0',
        name,
        description: `${name} - Unix Socket API`,
        channels: {
          'example-service': {
            name: 'Example Service',
            description: 'Example service demonstrating the API',
            commands: {
              'ping': {
                name: 'Ping',
                description: 'Simple ping command',
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
      
      console.log('✅ API specification created');
      console.log(`📄 File: ${outputPath}`);
      console.log('');
      console.log('🚀 Next steps:');
      console.log(`   1. Edit: ${options.output}`);
      console.log(`   2. Validate: janus-docs validate ${options.output}`);
      console.log(`   3. Generate docs: janus-docs generate ${options.output}`);
      console.log(`   4. Serve with live reload: janus-docs serve ${options.output}`);
      
    } catch (error) {
      console.error('❌ Error creating specification:', error);
      process.exit(1);
    }
  });

// Helper function
async function generateDocumentation(
  specPath: string,
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
  const specContent = await fs.readFile(specPath, 'utf8');
  const apiSpec = JSON.parse(specContent);
  
  let customStyles = '';
  if (options.styles) {
    try {
      customStyles = await fs.readFile(path.resolve(options.styles), 'utf8');
    } catch (error) {
      // Ignore if styles file doesn't exist
    }
  }
  
  const generator = new DocumentationGenerator(apiSpec, {
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

// Parse command line arguments
if (require.main === module) {
  program.parse();
}