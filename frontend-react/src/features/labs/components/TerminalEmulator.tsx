/**
 * Terminal Emulator Component
 *
 * xterm.js-based terminal emulator for lab environment
 * Supports:
 * - Command execution
 * - Command history (up/down arrows)
 * - Output streaming
 * - Clear screen
 * - Copy/paste
 * - Multi-line input
 *
 * @module features/labs/components/TerminalEmulator
 */

import React, { useEffect, useRef, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import '@xterm/xterm/css/xterm.css';
import styles from './TerminalEmulator.module.css';

export interface TerminalCommand {
  command: string;
  output: string;
  exitCode: number;
  timestamp: Date;
}

export interface TerminalEmulatorProps {
  history: TerminalCommand[];
  onExecuteCommand: (command: string) => Promise<void>;
  onClear?: () => void;
  isExecuting?: boolean;
  readOnly?: boolean;
}

export const TerminalEmulator: React.FC<TerminalEmulatorProps> = ({
  history,
  onExecuteCommand,
  onClear,
  isExecuting = false,
  readOnly = false
}) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<Terminal | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const [currentCommand, setCurrentCommand] = useState('');
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const promptRef = useRef('$ ');

  // Initialize terminal
  useEffect(() => {
    if (!terminalRef.current || xtermRef.current) return;

    const terminal = new Terminal({
      cursorBlink: true,
      cursorStyle: 'block',
      fontFamily: "'Fira Code', 'Courier New', monospace",
      fontSize: 14,
      lineHeight: 1.5,
      theme: {
        background: '#1e1e1e',
        foreground: '#cccccc',
        cursor: '#007acc',
        cursorAccent: '#1e1e1e',
        // @ts-expect-error - selection property exists in xterm but not in type definition
        selection: 'rgba(0, 122, 204, 0.3)',
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#ffffff'
      },
      allowTransparency: false,
      scrollback: 1000,
      tabStopWidth: 4,
      convertEol: true
    });

    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();

    terminal.loadAddon(fitAddon);
    terminal.loadAddon(webLinksAddon);

    terminal.open(terminalRef.current);
    fitAddon.fit();

    xtermRef.current = terminal;
    fitAddonRef.current = fitAddon;

    // Write welcome message
    terminal.writeln('\x1b[1;32mLab Terminal Environment\x1b[0m');
    terminal.writeln('\x1b[90mType commands and press Enter to execute\x1b[0m');
    terminal.writeln('');
    terminal.write(promptRef.current);

    // Handle terminal input
    let currentLine = '';
    terminal.onData((data) => {
      if (readOnly || isExecuting) return;

      const code = data.charCodeAt(0);

      // Enter key
      if (code === 13) {
        terminal.write('\r\n');
        if (currentLine.trim()) {
          handleCommand(currentLine.trim());
          setCommandHistory(prev => [...prev, currentLine.trim()]);
          setHistoryIndex(-1);
        } else {
          terminal.write(promptRef.current);
        }
        currentLine = '';
        setCurrentCommand('');
        return;
      }

      // Backspace
      if (code === 127) {
        if (currentLine.length > 0) {
          currentLine = currentLine.slice(0, -1);
          terminal.write('\b \b');
          setCurrentCommand(currentLine);
        }
        return;
      }

      // Arrow Up (history previous)
      if (data === '\x1b[A') {
        if (commandHistory.length > 0 && historyIndex < commandHistory.length - 1) {
          const newIndex = historyIndex + 1;
          const historicCommand = commandHistory[commandHistory.length - 1 - newIndex];

          // Clear current line
          terminal.write('\r\x1b[K');
          terminal.write(promptRef.current);
          terminal.write(historicCommand);

          currentLine = historicCommand;
          setCurrentCommand(currentLine);
          setHistoryIndex(newIndex);
        }
        return;
      }

      // Arrow Down (history next)
      if (data === '\x1b[B') {
        if (historyIndex > 0) {
          const newIndex = historyIndex - 1;
          const historicCommand = commandHistory[commandHistory.length - 1 - newIndex];

          // Clear current line
          terminal.write('\r\x1b[K');
          terminal.write(promptRef.current);
          terminal.write(historicCommand);

          currentLine = historicCommand;
          setCurrentCommand(currentLine);
          setHistoryIndex(newIndex);
        } else if (historyIndex === 0) {
          // Clear line
          terminal.write('\r\x1b[K');
          terminal.write(promptRef.current);
          currentLine = '';
          setCurrentCommand('');
          setHistoryIndex(-1);
        }
        return;
      }

      // Ctrl+C (cancel)
      if (code === 3) {
        terminal.write('^C\r\n');
        terminal.write(promptRef.current);
        currentLine = '';
        setCurrentCommand('');
        return;
      }

      // Ctrl+L (clear)
      if (code === 12) {
        terminal.clear();
        terminal.write(promptRef.current);
        return;
      }

      // Regular character
      if (code >= 32 && code < 127) {
        currentLine += data;
        terminal.write(data);
        setCurrentCommand(currentLine);
      }
    });

    // Handle resize
    const handleResize = () => {
      fitAddon.fit();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      terminal.dispose();
      xtermRef.current = null;
    };
  }, [readOnly]);

  // Handle command execution
  const handleCommand = async (command: string) => {
    const terminal = xtermRef.current;
    if (!terminal) return;

    try {
      await onExecuteCommand(command);
    } catch (error) {
      terminal.writeln(`\x1b[1;31mError: ${error}\x1b[0m`);
      terminal.write(promptRef.current);
    }
  };

  // Display command history
  useEffect(() => {
    const terminal = xtermRef.current;
    if (!terminal || history.length === 0) return;

    const lastCommand = history[history.length - 1];

    // Display output
    if (lastCommand.output) {
      const lines = lastCommand.output.split('\n');
      lines.forEach(line => {
        terminal.writeln(line);
      });
    }

    // Display exit code if non-zero
    if (lastCommand.exitCode !== 0) {
      terminal.writeln(`\x1b[1;31m[Exit code: ${lastCommand.exitCode}]\x1b[0m`);
    }

    // Show prompt again
    terminal.write(promptRef.current);
  }, [history]);

  // Handle clear
  const handleClear = () => {
    if (xtermRef.current) {
      xtermRef.current.clear();
      xtermRef.current.write(promptRef.current);
    }
    if (onClear) {
      onClear();
    }
  };

  return (
    <div className={styles.terminalContainer}>
      <div className={styles.terminalHeader}>
        <span className={styles.terminalTitle}>Terminal</span>
        <div className={styles.terminalActions}>
          <button
            id="clear-terminal-btn"
            className={styles.terminalActionBtn}
            onClick={handleClear}
            title="Clear Terminal (Ctrl+L)"
            disabled={readOnly}
          >
            🗑️
          </button>
        </div>
      </div>
      <div
        ref={terminalRef}
        className={styles.terminal}
        id="terminal-emulator"
      />
      {isExecuting && (
        <div className={styles.executingIndicator}>
          <span className={styles.executingSpinner}></span>
          <span>Executing...</span>
        </div>
      )}
      {readOnly && (
        <div className={styles.readOnlyOverlay}>
          <span className={styles.readOnlyMessage}>Terminal is read-only. Start lab to execute commands.</span>
        </div>
      )}
    </div>
  );
};

export default TerminalEmulator;
