/**
 * Lab Components Index
 *
 * Central export point for all lab-related components
 *
 * @module features/labs/components
 */

export { FileExplorer } from './FileExplorer';
export type { FileExplorerProps } from './FileExplorer';

export { CodeEditor } from './CodeEditor';
export type { CodeEditorProps, CodeEditorRef } from './CodeEditor';

export { TerminalEmulator } from './TerminalEmulator';
export type { TerminalEmulatorProps, TerminalCommand } from './TerminalEmulator';

export { IDESelector } from './IDESelector';
export type { IDESelectorProps } from './IDESelector';

export { LabControls } from './LabControls';
export type { LabControlsProps } from './LabControls';

export { ResourceMonitor } from './ResourceMonitor';
export type { ResourceMonitorProps, ResourceUsage } from './ResourceMonitor';

export { AIAssistant } from './AIAssistant';
export type { AIAssistantProps, AIMessage } from './AIAssistant';
