/**
 * File Watcher
 * Watches for changes in Manifest files
 */

import * as chokidar from 'chokidar';
import * as path from 'path';

export type FileChangeCallback = (filePath: string) => void;

export class FileWatcher {
  private watcher: chokidar.FSWatcher | null = null;
  private watchPaths: string[];
  private callback: FileChangeCallback;
  private isWatching = false;

  constructor(watchPaths: string[], callback: FileChangeCallback) {
    this.watchPaths = watchPaths.map(p => path.resolve(p));
    this.callback = callback;
  }

  /**
   * Start watching files
   */
  start(): void {
    if (this.isWatching) {
      return;
    }

    this.watcher = chokidar.watch(this.watchPaths, {
      ignored: /(^|[\/\\])\../, // ignore dotfiles
      persistent: true,
      ignoreInitial: true
    });

    this.watcher
      .on('change', (filePath) => {
        console.log(`📝 File changed: ${path.relative(process.cwd(), filePath)}`);
        this.callback(filePath);
      })
      .on('add', (filePath) => {
        console.log(`📝 File added: ${path.relative(process.cwd(), filePath)}`);
        this.callback(filePath);
      })
      .on('unlink', (filePath) => {
        console.log(`📝 File removed: ${path.relative(process.cwd(), filePath)}`);
        this.callback(filePath);
      })
      .on('error', (error) => {
        console.error('🚨 File watcher error:', error);
      });

    this.isWatching = true;
    console.log(`👀 Watching ${this.watchPaths.length} file(s) for changes`);
  }

  /**
   * Stop watching files
   */
  stop(): void {
    if (this.watcher) {
      this.watcher.close();
      this.watcher = null;
    }
    this.isWatching = false;
    console.log('👀 File watching stopped');
  }

  /**
   * Check if currently watching
   */
  isActive(): boolean {
    return this.isWatching;
  }

  /**
   * Get watched paths
   */
  getWatchedPaths(): string[] {
    return [...this.watchPaths];
  }
}