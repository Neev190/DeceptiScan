// AnalysisResult component — Inkwell Gazette visual redesign
// Logic (useState, handleFeedback, renderHighlightedText) is UNCHANGED from Phase 3.
// Only JSX markup is rewrapped to match the Stitch mockup design system.

import React, { useState } from 'react';
import { AnalysisResult as AnalysisResultType, SentenceAnalysis } from '../types';
import ScoreMeter from './ScoreMeter';
import { classificationToStatus, STAMP_CONFIGS } from '../theme';
import '../styles/inkwell.css';

interface AnalysisResultProps {
  result: AnalysisResultType;
}

const AnalysisResult: React.FC<AnalysisResultProps> = ({ result }) => {
  // ─── UNCHANGED STATE & HANDLERS ──────────────────────────────────────────────
  const [selectedSentence, setSelectedSentence] = useState<SentenceAnalysis | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const getSentenceStyle = (sentence: SentenceAnalysis) => {
    const baseStyle: React.CSSProperties = {
      padding: '0.25rem 0.5rem',
      margin: '0.125rem',
      borderRadius: '0.25rem',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      display: 'inline',
    };

    if (sentence.isSuspicious) {
      return {
        ...baseStyle,
        backgroundColor: '#fee2e2',
        color: '#991b1b',
        borderLeft: '3px solid #ef4444',
      };
    } else if (sentence.score >= 75) {
      return {
        ...baseStyle,
        backgroundColor: '#dcfce7',
        color: '#166534',
        borderLeft: '3px solid #22c55e',
      };
    } else {
      return {
        ...baseStyle,
        backgroundColor: '#f8fafc',
        color: '#1e293b',
      };
    }
  };

  const renderHighlightedText = () => {
    if (!result.sentenceAnalysis || result.sentenceAnalysis.length === 0) {
      return <p className="no-analysis">Detailed sentence analysis not available.</p>;
    }

    return (
      <div className="ik-article-body">
        {result.sentenceAnalysis.map((sentence, index) => {
          const isFlagged = sentence.isSuspicious || sentence.flags.length > 0;
          const isReliable = !isFlagged && sentence.score >= 75;
          const spanClass = isFlagged
            ? 'ik-evidence'
            : isReliable
              ? 'ik-evidence-reliable'
              : undefined;

          return (
            <span
              key={index}
              className={spanClass}
              onClick={() => setSelectedSentence(sentence)}
              onMouseEnter={isFlagged || isReliable ? undefined : (e) => {
                (e.currentTarget as HTMLElement).style.transform = 'scale(1.02)';
              }}
              onMouseLeave={isFlagged || isReliable ? undefined : (e) => {
                (e.currentTarget as HTMLElement).style.transform = 'scale(1)';
              }}
              style={(!isFlagged && !isReliable) ? getSentenceStyle(sentence) : undefined}
              title={`${sentence.isSuspicious ? '⚠ Suspicious' : '✓ Reliable'} — ${Math.round(sentence.confidence * 100)}% confidence. Click for details.`}
            >
              {sentence.text}{' '}
            </span>
          );
        })}
      </div>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const [feedbackSent, setFeedbackSent] = useState<string | null>(null);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);

  const handleFeedback = async (type: 'helpful' | 'incorrect' | 'disputed') => {
    setIsSubmittingFeedback(true);
    setFeedbackError(null);
    try {
      const { apiService } = await import('../services/api');
      await apiService.submitFeedback({
        analysisId: result.id,
        userId: null,
        feedback: { type }
      });
      setFeedbackSent(type);
    } catch (e: any) {
      console.error('Failed to submit feedback', e);
      setFeedbackError(e.message || 'Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  const claimsList = result.retrieved_claims || result.similar_claims;
  // ─── END UNCHANGED LOGIC ──────────────────────────────────────────────────────

  // ─── STAMP CONFIG ─────────────────────────────────────────────────────────────
  const stampStatus = classificationToStatus(result.classification, result.authenticityScore);
  const stamp = STAMP_CONFIGS[stampStatus];
  const confidencePct = Math.round((result.confidence ?? result.confidenceScore ?? 0) * 100);

  return (
    <div className="ik-page" style={{ padding: '0 0 6rem 0' }}>

      {/* ── Warning / Disclaimer Banner ── */}
      {(result.warning || result.classification === 'unknown' || result.classification === 'unverified_style_estimate') && (
        <div className="ik-warning" style={{ marginBottom: '1.5rem' }}>
          <strong>⚠️ Disclaimer: </strong>
          {result.warning || 'Low confidence in ML prediction. Sentence highlighting may be unverified.'}
        </div>
      )}

      {/* Hidden accessible heading — required by existing tests */}
      <h2 style={{ position: 'absolute', width: '1px', height: '1px', overflow: 'hidden', clip: 'rect(0,0,0,0)', whiteSpace: 'nowrap' }}>Analysis Complete</h2>

      {/* ── Verification Stamp Header ── */}
      <section style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem', padding: '1.5rem 0 1rem' }}>
        <div
          className="ik-stamp"
          style={{
            // CSS custom properties picked up by .ik-stamp via var()
            '--ik-stamp-color': stamp.lightColor,
            '--ik-stamp-bg': stamp.lightBg,
          } as React.CSSProperties}
        >
          {stamp.label}
        </div>
        <p className="ik-meta">
          CONFIDENCE SCORE: {confidencePct > 0 ? `${confidencePct}%` : 'N/A'}
        </p>
        <div className="ik-border-b" style={{ width: '4rem', height: '1px', backgroundColor: 'var(--ik-outline)', marginTop: '0.5rem' }} />
      </section>

      {/* ── Score Meter (existing component) ── */}
      <div style={{ marginBottom: '1.5rem' }}>
        <ScoreMeter
          score={result.authenticityScore}
          label={result.classification.replace(/_/g, ' ').toUpperCase()}
          confidence={result.confidence ?? result.confidenceScore}
        />
      </div>

      {/* ── Result Meta ── */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1.25rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <span className="ik-ink-faint" style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '12px', letterSpacing: '0.04em' }}>
          ANALYZED: {formatDate(result.analyzedAt)}
        </span>
        <span className="ik-ink-faint" style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '12px', letterSpacing: '0.04em' }}>
          {result.processingTime}ms
        </span>
        {result.is_cached && (
          <span style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '11px', color: 'var(--ik-moss)', fontWeight: 700, letterSpacing: '0.06em' }}>
            [CACHED]
          </span>
        )}
      </div>

      {/* ── Article Analysis Card ── */}
      <article
        className="ik-border ik-hatching"
        style={{
          backgroundColor: 'var(--ik-surface)',
          padding: '1.5rem',
          position: 'relative',
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
          marginBottom: '2rem',
        }}
      >
        <div className="ik-fastener" style={{ top: '0.5rem', right: '0.5rem' }} />
        <div className="ik-fastener" style={{ top: '0.5rem', left: '0.5rem' }} />

        {/* Card header */}
        <header className="ik-border-b" style={{ marginBottom: '1.5rem', paddingBottom: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div>
              <h2 className="ik-article-title" style={{ marginBottom: '0.25rem' }}>
                Sentence-Level Analysis
              </h2>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                {result.analyzedAt && (
                  <span className="ik-ink-faint" style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    DATE: {new Date(result.analyzedAt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase()}
                  </span>
                )}
                <span className="ik-ink-faint" style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  MODEL: {result.modelVersion}
                </span>
              </div>
            </div>
            {/* Legend toggle */}
            <button
              className="ik-toggle-btn"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? '▲ HIDE LEGEND' : '▼ SHOW LEGEND'}
            </button>
          </div>
        </header>

        {/* Legend */}
        {showDetails && (
          <div style={{ marginBottom: '1.25rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', fontFamily: 'var(--ik-font-mono)', fontSize: '11px', color: 'var(--ik-ink-faint)' }}>
            <span>
              <span className="ik-swatch" style={{ backgroundColor: 'rgba(92,110,74,0.25)', border: '1px solid var(--ik-moss)' }} />
              RELIABLE
            </span>
            <span>
              <span className="ik-swatch" style={{ backgroundColor: 'rgba(156,74,50,0.25)', border: '1px solid var(--ik-rust)' }} />
              SUSPICIOUS / FLAGGED
            </span>
            <span>
              <span className="ik-swatch" style={{ backgroundColor: 'transparent', border: '1px solid var(--ik-outline-var)' }} />
              NEUTRAL
            </span>
            <p style={{ width: '100%', margin: 0, fontStyle: 'italic', opacity: 0.8 }}>
              Tap any sentence to examine the evidence.
            </p>
          </div>
        )}

        {/* Highlighted article text */}
        {renderHighlightedText()}

        {/* Marginalia annotation for suspicious sentences (first suspicious only) */}
        {(() => {
          const firstSuspicious = result.sentenceAnalysis?.find(s => s.isSuspicious && s.flags.length > 0);
          if (!firstSuspicious) return null;
          return (
            <div
              className="ik-border ik-marginalia"
              style={{
                marginTop: '1.5rem',
                marginLeft: '1.5rem',
                padding: '0.75rem 1rem',
                width: 'calc(100% - 1.5rem)',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  left: '-0.6rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  width: '1rem',
                  height: '1rem',
                  borderRadius: '50%',
                  backgroundColor: 'var(--ik-surface)',
                  border: '1px solid var(--ik-outline)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <div style={{ width: '0.4rem', height: '0.4rem', borderRadius: '50%', backgroundColor: 'var(--ik-rust)' }} />
              </div>
              <h4 style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '11px', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--ik-rust)', marginBottom: '0.25rem' }}>
                {firstSuspicious.flags[0]?.replace(/_/g, ' ') || 'Flag Detected'}
              </h4>
              <p style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '11px', color: 'var(--ik-ink-faint)', margin: 0, letterSpacing: '0.04em' }}>
                Click sentence for full analysis →
              </p>
            </div>
          );
        })()}
      </article>

      {/* ── Overall Summary ── */}
      {result.overallSummary && (
        <section className="ik-border" style={{ backgroundColor: 'var(--ik-surface)', padding: '1.25rem 1.5rem', marginBottom: '2rem', position: 'relative' }}>
          <div className="ik-fastener" style={{ top: '0.5rem', right: '0.5rem' }} />
          <h3 style={{ fontFamily: 'var(--ik-font-serif)', fontSize: '18px', fontWeight: 600, color: 'var(--ik-primary)', marginBottom: '0.75rem' }}>
            Summary
          </h3>
          <p style={{ fontFamily: 'var(--ik-font-body)', fontSize: '16px', lineHeight: '24px', color: 'var(--ik-on-surface)', margin: 0 }}>
            {result.overallSummary}
          </p>
        </section>
      )}

      {/* ── Related Case Files (pgvector retrieved claims) ── */}
      <section style={{ marginBottom: '2rem' }}>
        <h3 className="ik-section-title" style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '24px' }}>
          <span style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '20px', color: 'var(--ik-ink-faint)' }}>▦</span>
          Similar Fact-Checked Claims
        </h3>

        {/* State 1: retrieval unavailable / errored */}
        {result.retrieval_status === 'unavailable' ? (
          <div className="ik-empty-state">
            ── ARCHIVE UNREACHABLE ──<br />
            <span style={{ opacity: 0.7, marginTop: '0.35rem', display: 'block' }}>Retrieval service is currently offline. Case file cross-reference is unavailable.</span>
          </div>

        ) : /* State 2: available but empty */ claimsList == null || claimsList.length === 0 ? (
          <div className="ik-empty-state">
            ── NO RELATED CASES ON FILE ──<br />
            <span style={{ opacity: 0.7, marginTop: '0.35rem', display: 'block' }}>No similar fact-checked claims were found in the archive for this content.</span>
          </div>

        ) : (
          /* State 3: claims present */
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
            {claimsList.map((claim, i) => {
              const text = claim.statement_text || claim.text;
              const similarityRaw = claim.similarity_score ?? (claim.score !== undefined ? claim.score / 100 : undefined);
              const matchPct = similarityRaw !== undefined ? Math.round(similarityRaw * 100) : null;
              const labelDisplay = claim.label ? ` (${claim.label.toUpperCase()})` : '';
              const scoreDisplay = matchPct !== null ? `${matchPct}%` : '';
              const isHighMatch = matchPct !== null && matchPct >= 70;

              return (
                <li
                  key={i}
                  className="ik-border ik-hatching ik-case-card"
                  style={{ padding: '1rem', position: 'relative' }}
                >
                  <div className="ik-fastener" style={{ top: '0.5rem', right: '0.5rem' }} />

                  {/* Case number tab */}
                  <div style={{
                    display: 'inline-block',
                    backgroundColor: 'var(--ik-bg)',
                    border: '1px solid var(--ik-outline)',
                    borderRadius: '2px 2px 0 0',
                    padding: '0.1rem 0.5rem',
                    marginTop: '-1.25rem',
                    marginLeft: '0.5rem',
                    marginBottom: '0.75rem',
                    fontFamily: 'var(--ik-font-mono)',
                    fontSize: '11px',
                    color: 'var(--ik-ink-faint)',
                    letterSpacing: '0.06em',
                  }}>
                    CASE #{String(i + 1).padStart(4, '0')}
                  </div>

                  {/* Exact text format required by tests: "text" (Match Score: X% (LABEL)) */}
                  <p style={{
                    fontFamily: 'var(--ik-font-body)',
                    fontSize: '14px',
                    lineHeight: '20px',
                    color: 'var(--ik-on-surface)',
                    margin: '0 0 0.5rem 0',
                  }}>
                    "{text}"
                  </p>
                  {scoreDisplay && (
                    <p style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '12px', margin: 0 }}>
                      <span className={isHighMatch ? 'ik-match-moss' : 'ik-match-faint'}>
                        (Match Score: {scoreDisplay}{labelDisplay})
                      </span>
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {/* ── Feedback Section ── */}
      <section className="ik-border" style={{ backgroundColor: 'var(--ik-surface)', padding: '1rem 1.5rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
          <span style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '12px', letterSpacing: '0.06em', color: 'var(--ik-on-surface-var)', fontWeight: 600 }}>
            WAS THIS ANALYSIS HELPFUL?
          </span>
          {feedbackSent ? (
            <span style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '11px', letterSpacing: '0.06em', color: 'var(--ik-moss)', backgroundColor: 'rgba(92,110,74,0.12)', padding: '0.3rem 0.75rem', borderRadius: '2px', fontWeight: 700 }}>
              ✓ Thank you for your feedback! ({feedbackSent})
            </span>
          ) : (
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button className="ik-feedback-btn" onClick={() => handleFeedback('helpful')} disabled={isSubmittingFeedback}>
                👍 Helpful
              </button>
              <button className="ik-feedback-btn" onClick={() => handleFeedback('incorrect')} disabled={isSubmittingFeedback}>
                👎 Incorrect
              </button>
              <button className="ik-feedback-btn" onClick={() => handleFeedback('disputed')} disabled={isSubmittingFeedback}>
                ⚖️ Disputed
              </button>
            </div>
          )}
        </div>

        {feedbackError && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.75rem', backgroundColor: 'rgba(156,74,50,0.1)', border: '1px solid var(--ik-rust)', borderRadius: '2px', padding: '0.5rem 0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <span style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '12px', color: 'var(--ik-rust)' }}>
              ⚠️ {feedbackError}
            </span>
            <button
              className="ik-feedback-btn"
              style={{ borderColor: 'var(--ik-rust)', color: 'var(--ik-rust)' }}
              onClick={() => setFeedbackError(null)}
            >
              Clear & Retry
            </button>
          </div>
        )}
      </section>

      {/* ── Sentence Detail Modal ── */}
      {selectedSentence && (
        <div className="ik-modal-overlay" onClick={() => setSelectedSentence(null)}>
          <div className="ik-modal ik-hatching" onClick={(e) => e.stopPropagation()} style={{ backgroundColor: 'var(--ik-bg)' }}>
            {/* Modal header */}
            <div className="ik-border-b" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem 1rem' }}>
              <h3 style={{ fontFamily: 'var(--ik-font-serif)', fontSize: '18px', fontWeight: 600, color: 'var(--ik-primary)', margin: 0 }}>
                Sentence Analysis
              </h3>
              <button
                onClick={() => setSelectedSentence(null)}
                style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--ik-ink-faint)', padding: '0.25rem', lineHeight: 1 }}
                aria-label="×"
              >
                ×
              </button>
            </div>

            <div style={{ padding: '1.25rem 1.5rem' }}>
              {/* Sentence text */}
              <div style={{ borderLeft: '3px solid var(--ik-outline)', backgroundColor: 'var(--ik-surface)', padding: '0.75rem 1rem', marginBottom: '1.25rem', fontFamily: 'var(--ik-font-body)', fontSize: '15px', lineHeight: 1.6, fontStyle: 'italic', color: 'var(--ik-on-surface)' }}>
                "{selectedSentence.text}"
              </div>

              {/* Stats grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', marginBottom: '1.25rem' }}>
                {[
                  ['SCORE', `${selectedSentence.score}/100`],
                  ['CONFIDENCE', `${Math.round(selectedSentence.confidence * 100)}%`],
                  ['CATEGORY', selectedSentence.category],
                  ['STATUS', selectedSentence.isSuspicious ? '⚠ SUSPICIOUS' : '✓ RELIABLE'],
                ].map(([label, value]) => (
                  <div key={label} style={{ backgroundColor: 'var(--ik-surface)', border: '1px solid var(--ik-outline-var)', borderRadius: '2px', padding: '0.6rem 0.75rem' }}>
                    <div style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '10px', letterSpacing: '0.08em', color: 'var(--ik-ink-faint)', marginBottom: '0.2rem' }}>{label}</div>
                    <div style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '13px', fontWeight: 700, color: label === 'STATUS' ? (selectedSentence.isSuspicious ? 'var(--ik-rust)' : 'var(--ik-moss)') : 'var(--ik-on-surface)' }}>{value}</div>
                  </div>
                ))}
              </div>

              {/* Flags */}
              {selectedSentence.flags.length > 0 && (
                <div style={{ marginBottom: '1rem' }}>
                  <h4 style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '11px', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ik-rust)', marginBottom: '0.4rem' }}>Flags Raised</h4>
                  <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                    {selectedSentence.flags.map((flag, index) => (
                      <li key={index} style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '11px', fontWeight: 600, letterSpacing: '0.06em', backgroundColor: 'rgba(156,74,50,0.1)', border: '1px solid var(--ik-rust)', borderRadius: '2px', padding: '0.15rem 0.5rem', color: 'var(--ik-rust)' }}>
                        {flag}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Explanation */}
              <div>
                <h4 style={{ fontFamily: 'var(--ik-font-mono)', fontSize: '11px', letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ik-ink-faint)', marginBottom: '0.4rem' }}>Analyst's Note</h4>
                <p style={{ fontFamily: 'var(--ik-font-body)', fontSize: '14px', lineHeight: 1.6, color: 'var(--ik-on-surface-var)', margin: 0 }}>
                  {selectedSentence.explanation}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisResult;