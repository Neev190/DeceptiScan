// SystemErrorReport.tsx — Stitch system_error_report screen
// This is a DISPLAY-ONLY page — it renders a stylized error/fault report card.
// It is NOT a bug submission form; there are no form inputs or API calls.
// Used as both a navigable page (/system-error) and the app's 404 catch-all route.
//
// Mock content notes:
// - Timestamp: replaced with real Date.now() so at least this is accurate.
// - Ref ID: generated from current timestamp (non-static, non-fake).
// - Fault diagnosis messages ("SOURCE DOCUMENT IS EMPTY", "RECEIVED: NULL"):
//   retained as illustrative placeholder copy showing the error card template.
//   This page does not assert a real backend error — it demonstrates the UI state.
//   A future task could wire this to a React error boundary or router error state.

import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

const SystemErrorReport: React.FC = () => {
  const navigate = useNavigate();

  const timestamp = useMemo(() => {
    const d = new Date();
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }, []);

  const refId = useMemo(() => {
    return 'DS-' + Date.now().toString(36).slice(-4).toUpperCase();
  }, []);

  return (
    <main className="flex-grow flex items-center justify-center px-margin-mobile md:px-margin-desktop py-12 relative overflow-hidden bg-lead-charcoal min-h-[calc(100vh-160px)]">
      {/* Scanline sweep */}
      <div
        className="absolute pointer-events-none z-20"
        style={{
          width: '100%',
          height: '100px',
          background: 'linear-gradient(0deg, rgba(0,0,0,0) 0%, rgba(143,48,42,0.1) 50%, rgba(0,0,0,0) 100%)',
          opacity: 0.1,
          animation: 'sys-scanline 8s linear infinite',
        }}
      />
      {/* Vignette cracked overlay */}
      <div
        className="absolute inset-0 pointer-events-none z-0"
        style={{ background: 'radial-gradient(circle, transparent 20%, #101010 120%)' }}
      />
      {/* Grid texture */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none z-0"
        style={{
          backgroundImage: "url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGcgb3BhY2l0eT0iMC4wMyIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjEiPjxwYXRoIGQ9Ik0wIDYwaDYwTTAgMGg2MCIvPjwvZz48L3N2Zz4=')",
        }}
      />

      {/* Error Card */}
      <div className="max-w-3xl w-full bg-carbon-gray border border-outline-variant shadow-[0px_24px_60px_rgba(0,0,0,0.5)] relative overflow-hidden z-10">
        {/* Red Warning Header */}
        <div className="bg-error-container text-on-error-container p-4 border-b border-outline-variant/30 flex items-center gap-3">
          <span className="material-symbols-outlined text-error">warning</span>
          <h1 className="font-headline-lg text-headline-lg text-error uppercase m-0 leading-none">ERRor!!!</h1>
        </div>

        <div className="p-8 md:p-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Metadata Column */}
            <div className="md:col-span-1 md:border-r border-outline-variant md:pr-8 space-y-6">
              <div>
                <div className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase mb-1">Status</div>
                <div className="font-technical-sm text-technical-sm text-error">INVESTIGATION INTERRUPTED</div>
              </div>
              <div>
                <div className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase mb-1">Timestamp</div>
                <div className="font-technical-sm text-technical-sm text-on-surface">{timestamp}</div>
              </div>
              <div>
                <div className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase mb-1">Ref ID</div>
                <div className="font-technical-sm text-technical-sm text-on-surface">{refId}</div>
              </div>
            </div>

            {/* Details Column */}
            <div className="md:col-span-2 space-y-8">
              <div>
                <h2 className="font-label-caps text-label-caps text-on-surface-variant uppercase mb-2 border-b border-outline-variant pb-2">
                  Fault Diagnosis
                </h2>
                <p className="font-technical-sm text-technical-sm text-on-surface mt-4">UNEXPECTED FAULT DETECTED.</p>
                <div className="mt-4 bg-surface-container-low p-4 border border-outline-variant font-technical-sm text-technical-sm text-on-surface-variant">
                  &gt; REASON: UNEXPECTED FAULT — NO DIAGNOSTIC DATA AVAILABLE.<br />
                  &gt; ACTION: ABORT SEQUENCE.
                </div>
              </div>
              <div className="pt-4">
                <button
                  onClick={() => navigate('/')}
                  className="bg-ink-red hover:bg-secondary-container text-primary font-label-caps text-label-caps py-3 px-6 flex items-center gap-2 transition-colors duration-200"
                >
                  <span className="material-symbols-outlined text-sm">arrow_back</span>
                  RETURN TO INVESTIGATION
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Corner tape accents */}
        <div className="absolute top-0 right-0 w-16 h-16 bg-surface-container-low border-b border-l border-outline-variant transform translate-x-8 -translate-y-8 rotate-45 opacity-50" />
        <div className="absolute bottom-0 left-0 w-16 h-16 bg-surface-container-low border-t border-r border-outline-variant transform -translate-x-8 translate-y-8 rotate-45 opacity-50" />
      </div>

      <style>{`
        @keyframes sys-scanline {
          0% { top: -100px; }
          100% { top: 100%; }
        }
      `}</style>
    </main>
  );
};

export default SystemErrorReport;
