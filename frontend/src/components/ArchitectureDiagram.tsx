import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { ZoomIn, ZoomOut, RotateCcw, AlertTriangle, Code } from 'lucide-react';

interface ArchitectureDiagramProps {
  mermaidCode: string;
}

export const ArchitectureDiagram: React.FC<ArchitectureDiagramProps> = ({ mermaidCode }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [renderError, setRenderError] = useState<boolean>(false);
  const [zoom, setZoom] = useState<number>(1);
  const [showRaw, setShowRaw] = useState<boolean>(false);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'strict',
      fontFamily: 'Inter, sans-serif',
      themeVariables: {
        darkMode: true,
        background: '#121826',
        primaryColor: '#1A2234',
        primaryTextColor: '#E6EAF2',
        primaryBorderColor: '#6C8CFF',
        lineColor: '#6C8CFF',
        secondaryColor: '#1A2234',
        tertiaryColor: '#121826',
      },
    });

    const renderChart = async () => {
      if (!mermaidCode) return;
      try {
        setRenderError(false);
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(id, mermaidCode);
        setSvgContent(svg);
      } catch (err) {
        console.warn('Mermaid render error caught:', err);
        setRenderError(true);
      }
    };

    renderChart();
  }, [mermaidCode]);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.2, 2.0));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.2, 0.6));
  const handleReset = () => setZoom(1);

  return (
    <div className="relative w-full rounded-xl bg-surface border border-border overflow-hidden">
      {/* Controls Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-surface-2/50 border-b border-border text-xs text-text-muted">
        <span className="font-semibold text-text uppercase tracking-wider text-[11px]">
          Architecture Flowchart
        </span>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setShowRaw(!showRaw)}
            className="p-1.5 rounded hover:bg-surface-2 text-text-muted hover:text-text cursor-pointer"
            title="Toggle Raw Mermaid Code"
          >
            <Code className="w-3.5 h-3.5" />
          </button>
          <div className="w-[1px] h-3 bg-border mx-1" />
          <button
            type="button"
            onClick={handleZoomOut}
            className="p-1.5 rounded hover:bg-surface-2 text-text-muted hover:text-text cursor-pointer"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="font-mono text-[11px] px-1">{Math.round(zoom * 100)}%</span>
          <button
            type="button"
            onClick={handleZoomIn}
            className="p-1.5 rounded hover:bg-surface-2 text-text-muted hover:text-text cursor-pointer"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="p-1.5 rounded hover:bg-surface-2 text-text-muted hover:text-text cursor-pointer"
            title="Reset Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Diagram Area */}
      <div className="p-6 overflow-auto min-h-[300px] flex items-center justify-center">
        {showRaw || renderError ? (
          <div className="w-full">
            {renderError && (
              <div className="flex items-center gap-2 p-3 mb-4 rounded-lg bg-warning/10 border border-warning/30 text-warning text-xs">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>Could not render diagram visually. Showing raw Mermaid definition:</span>
              </div>
            )}
            <pre className="p-4 rounded-lg bg-surface-2 border border-border text-xs font-mono text-text overflow-x-auto">
              {mermaidCode}
            </pre>
          </div>
        ) : (
          <div
            ref={containerRef}
            style={{ transform: `scale(${zoom})`, transformOrigin: 'center center', transition: 'transform 0.15s ease' }}
            dangerouslySetInnerHTML={{ __html: svgContent }}
            className="w-full flex items-center justify-center"
          />
        )}
      </div>
    </div>
  );
};
