// ArticleInput component — Stitch investigation_desk intake form
// Logic (useState, handleSubmit, handleContentChange) is UNCHANGED from Phase 3.
// Markup uses Stitch design system; accessibility labels added for test compatibility.

import React, { useState, ChangeEvent, FormEvent } from 'react';
import { ArticleInputProps } from '../types';

const ArticleInput: React.FC<ArticleInputProps> = ({ onSubmit, isLoading }) => {
  // ── UNCHANGED STATE & HANDLERS ─────────────────────────────────────────
  const [content, setContent] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [title, setTitle] = useState('');
  const [contentType, setContentType] = useState<'text' | 'url'>('text');

  const handleContentChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const value = event.target.value;
    if (value.length <= 50000) {
      setContent(value);
    }
  };

  const handleSourceUrlChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSourceUrl(event.target.value);
  };

  const handleTitleChange = (event: ChangeEvent<HTMLInputElement>) => {
    setTitle(event.target.value);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();

    if (!content.trim()) {
      return;
    }

    try {
      await onSubmit(content.trim());
    } catch (error) {
      console.error('Submission failed:', error);
    }
  };

  const isValidUrl = (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const isSubmitDisabled = !content.trim() || isLoading || (sourceUrl && !isValidUrl(sourceUrl));
  const characterCount = content.length;
  const isNearLimit = characterCount > 45000;
  const urlError = sourceUrl && !isValidUrl(sourceUrl);
  // ── END UNCHANGED LOGIC ────────────────────────────────────────────────

  const today = new Date().toISOString().split('T')[0];

  return (
    /* The "Physical" Investigation Paper */
    <div className="paper-texture text-typewriter-ribbon rounded-sm overflow-hidden flex flex-col" style={{ boxShadow: '0px 24px 60px rgba(0,0,0,0.5)' }}>
      <form onSubmit={handleSubmit}>

        {/* Document Header */}
        <div className="flex justify-between items-start p-6 border-b border-typewriter-ribbon/20 bg-paper-aged/50">
          <div>
            <span className="block font-metadata-xs text-metadata-xs text-typewriter-ribbon/70 mb-1">FILE REFERENCE</span>
            <div className="font-technical-sm text-technical-sm">DSCN-INTAKE-001</div>
          </div>
          <div className="text-right">
            <span className="block font-metadata-xs text-metadata-xs text-typewriter-ribbon/70 mb-1">DATE OPENED</span>
            <div className="font-technical-sm text-technical-sm">{today}</div>
          </div>
        </div>

        {/* Content Type Toggle (kept for test compat — visually subtle) */}
        <div className="flex border-b border-typewriter-ribbon/20 bg-paper-aged/30">
          <button
            type="button"
            className={`px-4 py-2 font-label-caps text-label-caps text-[10px] transition-colors ${contentType === 'text' ? 'active text-ink-red border-b-2 border-ink-red' : 'text-typewriter-ribbon/50 hover:text-typewriter-ribbon'}`}
            onClick={() => setContentType('text')}
            disabled={isLoading}
            aria-pressed={contentType === 'text'}
          >
            Text Input
          </button>
          <button
            type="button"
            className={`px-4 py-2 font-label-caps text-label-caps text-[10px] transition-colors ${contentType === 'url' ? 'active text-ink-red border-b-2 border-ink-red' : 'text-typewriter-ribbon/50 hover:text-typewriter-ribbon'}`}
            onClick={() => setContentType('url')}
            disabled={isLoading}
            aria-pressed={contentType === 'url'}
          >
            URL Analysis
          </button>
        </div>

        {/* Hidden fields required by tests (visually suppressed) */}
        <div className="px-6 pt-4 space-y-2">
          <div>
            <label htmlFor="article-title" className="sr-only">Article Title</label>
            <input
              id="article-title"
              type="text"
              value={title}
              onChange={handleTitleChange}
              disabled={isLoading}
              placeholder="Article title (optional)"
              className="w-full bg-transparent border-0 border-b border-typewriter-ribbon/20 focus:ring-0 focus:border-ink-red font-technical-sm text-technical-sm text-typewriter-ribbon px-0 py-1 rounded-none placeholder-typewriter-ribbon/30 outline-none text-[11px]"
            />
          </div>
          <div>
            <label htmlFor="source-url" className="sr-only">Source URL</label>
            <input
              id="source-url"
              type="url"
              value={sourceUrl}
              onChange={handleSourceUrlChange}
              disabled={isLoading}
              placeholder="Source URL (optional — https://...)"
              className="w-full bg-transparent border-0 border-b border-typewriter-ribbon/20 focus:ring-0 focus:border-ink-red font-technical-sm text-technical-sm text-typewriter-ribbon px-0 py-1 rounded-none placeholder-typewriter-ribbon/30 outline-none text-[11px]"
            />
            {urlError && (
              <p className="font-metadata-xs text-metadata-xs text-ink-red mt-1">Please enter a valid URL (e.g. https://...)</p>
            )}
          </div>
        </div>

        {/* Textarea / Intake Area */}
        <div className="relative flex-grow flex min-h-[400px]" id="investigation-area">
          <div className="scanline-overlay"></div>
          {/* Line Numbers Gutter */}
          <div className="w-12 border-r border-typewriter-ribbon/20 bg-paper-aged/30 flex flex-col items-center py-6 select-none opacity-50 pt-[28px]">
            {['01','02','03','04','05','06','07','08','09','10'].map((n) => (
              <span key={n} className="font-technical-sm text-technical-sm text-typewriter-ribbon/60 leading-[32px]">{n}</span>
            ))}
          </div>
          {/* Input Area */}
          <div className="flex-grow relative p-6">
            {/* Status Stamp */}
            <div className={`absolute top-4 right-8 -rotate-6 pointer-events-none opacity-80 mix-blend-multiply z-10 ${content.length > 5 ? '' : 'hidden'}`}>
              <div className="border-4 border-ink-red p-2 stamp-texture inline-block">
                <span className="font-stamp-lg text-stamp-lg text-ink-red block text-center uppercase leading-none">UNVERIFIED<br />UNTIL ANALYZED</span>
              </div>
            </div>
            <label htmlFor="case-input" className="sr-only">Article Content</label>
            <textarea
              id="case-input"
              className={`w-full h-full bg-transparent border-none resize-none focus:ring-0 font-body-md text-body-md text-typewriter-ribbon lined-paper leading-[32px] placeholder:text-typewriter-ribbon/30 outline-none min-h-[360px] ${contentType === 'url' ? 'opacity-50 pointer-events-none' : ''}`}
              placeholder={contentType === 'url' ? 'URL analysis coming soon — switch to Text Input mode to paste content.' : 'Enter subject testimony, paste forensic logs, or describe the evidence...'}
              spellCheck={false}
              value={content}
              onChange={handleContentChange}
              disabled={isLoading}
              required
            />
          </div>
        </div>

        {/* Character Counter + Help Text */}
        <div className="px-6 py-2 border-t border-typewriter-ribbon/10 bg-paper-aged/20 flex justify-between items-center">
          <span className="font-metadata-xs text-metadata-xs text-typewriter-ribbon/50">
            Our AI will analyze your content for misinformation signals.
          </span>
          <div className="character-counter">
            <span className={`font-metadata-xs text-metadata-xs ${isNearLimit ? 'text-ink-red' : 'text-typewriter-ribbon/50'}`}>
              {characterCount.toLocaleString()}/50,000 characters{isNearLimit ? ' (approaching limit)' : ''}
            </span>
          </div>
        </div>

        {/* Workspace Footer Actions */}
        <div className="bg-carbon-gray border-t border-typewriter-ribbon p-4 flex justify-between items-center text-on-surface">
          <div className="flex gap-4">
            <button
              type="button"
              className="font-label-caps text-label-caps text-on-surface-variant hover:text-primary transition-colors flex items-center gap-2"
              onClick={() => {
                setContent('');
                setTitle('');
                setSourceUrl('');
              }}
            >
              <span className="material-symbols-outlined text-[16px]">backspace</span> CLEAR
            </button>
          </div>
          <button
            type="submit"
            className={`bg-ink-red text-white font-label-caps text-label-caps px-6 py-3 rounded-none transition-colors flex items-center gap-2 border border-ink-red ${isSubmitDisabled ? 'opacity-60 pointer-events-none' : 'hover:bg-secondary-container'}`}
            disabled={!!isSubmitDisabled}
          >
            {isLoading ? (
              <>
                Analyzing...{' '}
                <span className="spinner" style={{
                  display: 'inline-block',
                  width: '14px',
                  height: '14px',
                  border: '2px solid rgba(255,255,255,0.3)',
                  borderTop: '2px solid white',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                }}></span>
              </>
            ) : (
              <>Analyze Content <span className="material-symbols-outlined text-[18px]">arrow_forward</span></>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ArticleInput;