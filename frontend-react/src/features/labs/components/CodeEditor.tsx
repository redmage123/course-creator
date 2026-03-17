/**
 * Code Editor Component
 *
 * Monaco Editor integration for VSCode-like code editing experience
 * Supports:
 * - Syntax highlighting for multiple languages
 * - IntelliSense and autocomplete
 * - Keyboard shortcuts (Ctrl+S save, Ctrl+Enter run)
 * - Theme customization
 * - Read-only mode
 *
 * @module features/labs/components/CodeEditor
 */

import { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import Editor, { Monaco } from '@monaco-editor/react';
// @ts-expect-error - monaco-editor types not installed yet
import type * as monacoEditor from 'monaco-editor';
import styles from './CodeEditor.module.css';

export interface CodeEditorProps {
  value: string;
  language: string;
  onChange: (value: string) => void;
  onSave?: () => void;
  onRun?: () => void;
  readOnly?: boolean;
  height?: string;
  theme?: 'vs-dark' | 'light' | 'hc-black';
}

export interface CodeEditorRef {
  focus: () => void;
  getValue: () => string;
  setValue: (value: string) => void;
  getSelection: () => string;
  insertText: (text: string) => void;
}

export const CodeEditor = forwardRef<CodeEditorRef, CodeEditorProps>(({
  value,
  language,
  onChange,
  onSave,
  onRun,
  readOnly = false,
  height = '100%',
  theme = 'vs-dark'
}, ref) => {
  const editorRef = useRef<monacoEditor.editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);

  // Handle editor mount
  const handleEditorDidMount = (
    editor: monacoEditor.editor.IStandaloneCodeEditor,
    monaco: Monaco
  ) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Configure editor options
    editor.updateOptions({
      fontSize: 14,
      lineHeight: 21,
      fontFamily: "'Fira Code', 'Courier New', monospace",
      fontLigatures: true,
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      automaticLayout: true,
      formatOnPaste: true,
      formatOnType: true,
      readOnly: readOnly,
      tabSize: 2,
      insertSpaces: true,
      wordWrap: 'on',
      lineNumbers: 'on',
      renderWhitespace: 'selection',
      cursorBlinking: 'smooth',
      cursorSmoothCaretAnimation: 'on',
      smoothScrolling: true,
      padding: { top: 16, bottom: 16 }
    });

    // Add keyboard shortcuts
    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,
      () => {
        if (onSave) {
          onSave();
        }
      }
    );

    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
      () => {
        if (onRun && !readOnly) {
          onRun();
        }
      }
    );

    // Focus editor
    editor.focus();
  };

  // Handle editor value change
  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      onChange(value);
    }
  };

  // Expose editor methods through ref
  useImperativeHandle(ref, () => ({
    focus: () => {
      editorRef.current?.focus();
    },
    getValue: () => {
      return editorRef.current?.getValue() || '';
    },
    setValue: (newValue: string) => {
      editorRef.current?.setValue(newValue);
    },
    getSelection: () => {
      const selection = editorRef.current?.getSelection();
      if (selection) {
        return editorRef.current?.getModel()?.getValueInRange(selection) || '';
      }
      return '';
    },
    insertText: (text: string) => {
      const selection = editorRef.current?.getSelection();
      if (selection) {
        editorRef.current?.executeEdits('', [{
          range: selection,
          text: text
        }]);
      }
    }
  }));

  // Update read-only state when prop changes
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({ readOnly });
    }
  }, [readOnly]);

  return (
    <div className={styles.codeEditor} id="code-editor">
      <Editor
        height={height}
        language={language}
        value={value}
        theme={theme}
        onChange={handleEditorChange}
        onMount={handleEditorDidMount}
        options={{
          selectOnLineNumbers: true,
          roundedSelection: false,
          readOnly: readOnly,
          cursorStyle: 'line',
          automaticLayout: true
        }}
        loading={
          <div className={styles.editorLoading}>
            <div className={styles.spinner}></div>
            <span>Loading editor...</span>
          </div>
        }
      />
      {readOnly && (
        <div className={styles.readOnlyOverlay}>
          <span className={styles.readOnlyBadge}>Read Only - Start lab to edit</span>
        </div>
      )}
    </div>
  );
});

CodeEditor.displayName = 'CodeEditor';

export default CodeEditor;
