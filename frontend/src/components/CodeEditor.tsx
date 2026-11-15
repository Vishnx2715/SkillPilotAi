import React, { useRef, useCallback } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: 'javascript' | 'python';
  height?: string;
  readOnly?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language = 'javascript',
  height = '400px',
  readOnly = false,
}) => {
  const editorRef = useRef<any>(null);

  const handleMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;
    // Configure basic theme
    monaco.editor.defineTheme('skillpilot-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#0f172a',
      },
    });
    monaco.editor.setTheme('skillpilot-dark');
  }, []);

  const monacoLang = language === 'python' ? 'python' : 'javascript';

  return (
    <div className="rounded-xl overflow-hidden border border-slate-700 bg-slate-950">
      <Editor
        height={height}
        language={monacoLang}
        value={value}
        onChange={(val) => onChange(val || '')}
        onMount={handleMount}
        theme="vs-dark"
        options={{
          fontSize: 14,
          fontFamily: 'JetBrains Mono, monospace',
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          lineNumbers: 'on',
          roundedSelection: true,
          padding: { top: 12 },
          readOnly,
          automaticLayout: true,
          tabSize: 2,
          wordWrap: 'on',
        }}
      />
    </div>
  );
};
