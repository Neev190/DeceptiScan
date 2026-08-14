// AnalysisResult component — Stitch analysis_findings design
// Logic (useState, handleFeedback, renderHighlightedText) is UNCHANGED from Phase 3.
// Only JSX markup is rewrapped to match the Stitch design system.

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AnalysisResult as AnalysisResultType, SentenceAnalysis } from '../types';
import { classificationToStatus, STAMP_CONFIGS } from '../theme';
import '../styles/inkwell.css';

interface AnalysisResultProps {
  result: AnalysisResultType;
}

const AnalysisResult: React.FC<AnalysisResultProps> = ({ result }) => {
  // ─── UNCHANGED STATE & HANDLERS ──────────────────────────────────────────────
  const navigate = useNavigate();
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
        backgroundColor: 'rgba(143, 48, 42, 0.2)',
        borderBottom: '2px solid #8F302A',
      };
    } else if (sentence.score >= 75) {
      return {
        ...baseStyle,
        backgroundColor: 'rgba(85, 120, 90, 0.2)',
        borderBottom: '2px solid #55785A',
      };
    } else {
      return {
        ...baseStyle,
        backgroundColor: 'transparent',
      };
    }
  };

  const renderHighlightedText = () => {
    if (!result.sentenceAnalysis || result.sentenceAnalysis.length === 0) {
      return <p className="font-body-md text-body-md text-typewriter-ribbon/60 italic">Detailed sentence analysis not available.</p>;
    }

    return (
      <div className="font-body-md text-body-md leading-relaxed" style={{ counterReset: 'linenumber' }}>
        {result.sentenceAnalysis.map((sentence, index) => {
          const isFlagged = sentence.isSuspicious || sentence.flags.length > 0;
          const isReliable = !isFlagged && sentence.score >= 75;

          return (
            <span
              key={index}
              onClick={() => setSelectedSentence(sentence)}
              style={getSentenceStyle(sentence)}
              title={`${sentence.isSuspicious ? '⚠ Suspicious' : '✓ Reliable'} — ${Math.round(sentence.confidence * 100)}% confidence. Click for details.`}
              className="cursor-pointer relative group"
            >
              {sentence.text}{' '}
              {/* Tooltip on hover */}
              <span className="absolute hidden group-hover:block bottom-full left-0 mb-2 w-48 bg-surface-container p-2 text-on-surface font-technical-sm text-technical-sm rounded shadow-lg border border-outline-variant z-50 text-left" style={{ fontStyle: 'normal' }}>
                {isFlagged ? `⚠ Suspicious` : isReliable ? `✓ Reliable` : `Neutral`} — {Math.round(sentence.confidence * 100)}% confidence
              </span>
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
  void STAMP_CONFIGS[stampStatus]; // kept for future use
  const confidencePct = Math.round((result.confidence ?? result.confidenceScore ?? 0) * 100);

  // Determine stamp class based on classification
  const getStampColorClass = () => {
    if (result.authenticityScore >= 75) return 'text-verification-green';
    if (result.authenticityScore >= 40) return 'text-[#ca8a04]';
    return 'text-ink-red';
  };

  const getStampLabel = () => {
    if (result.classification === 'unknown') return 'UNKNOWN';
    if (result.authenticityScore >= 75) return 'RELIABLE';
    if (result.authenticityScore >= 40) return 'MIXED';
    return 'UNRELIABLE';
  };

  return (
    <>
      {/* Accessible heading — visible to tests and screen readers */}
      <h2 className="sr-only">Analysis Complete</h2>

      {/* ── Warning / Disclaimer Banner ── */}
      {(result.warning || result.classification === 'unknown' || result.classification === 'unverified_style_estimate') && (
        <div className="bg-carbon-gray border border-[#ca8a04] p-4 mb-6 flex items-start gap-3">
          <span className="material-symbols-outlined text-[#ca8a04] text-[20px] mt-0.5">warning</span>
          <div>
            <span className="font-label-caps text-label-caps text-[#ca8a04] uppercase">⚠️ Disclaimer: </span>
            <span className="font-body-md text-body-md text-on-surface-variant">
              {result.warning || 'Low confidence in ML prediction. Sentence highlighting may be unverified.'}
            </span>
          </div>
        </div>
      )}

      {/* ── Case Header ── */}
      <div className="w-full flex flex-col md:flex-row justify-between items-start md:items-center mb-8 border-b border-outline-variant pb-6">
        <div>
          <p className="font-metadata-xs text-metadata-xs text-outline uppercase mb-2">Reference ID</p>
          <h1 className="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-primary">
            CASE {result.id.slice(0, 4).toUpperCase()} / ANALYSIS FINDINGS
          </h1>
        </div>
        <div className="flex items-center gap-6 mt-4 md:mt-0">
          <div className="flex flex-col items-end">
            <span className="font-metadata-xs text-metadata-xs text-outline uppercase">Reliability Score</span>
            <span className="font-display-lg text-display-lg text-primary leading-none">
              {result.authenticityScore}/100
            </span>
          </div>
          <div className={`stamp-border px-4 py-2 font-stamp-lg text-stamp-lg uppercase inline-block ${getStampColorClass()}`}>
            {getStampLabel()}
          </div>
        </div>
      </div>

      {/* ── Investigation Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-gutter lg:-mt-16 relative z-20">
        {/* Document Review Canvas (Left) */}
        <div className="col-span-1 lg:col-span-8 paper-texture text-typewriter-ribbon p-6 md:p-12 shadow-[0_24px_60px_rgba(0,0,0,0.5)] rounded-sm relative overflow-hidden">
          <div className="scanline"></div>
          <div className="flex justify-between items-center border-b border-outline-variant/30 pb-4 mb-8">
            <span className="font-technical-sm text-technical-sm text-inverse-primary uppercase tracking-widest">Source Document — Sentence Analysis</span>
            <div className="flex items-center gap-4">
              <span className="font-metadata-xs text-metadata-xs text-inverse-primary bg-inverse-primary/10 px-2 py-1 rounded">
                {result.modelVersion}
              </span>
              {result.is_cached && (
                <span className="font-metadata-xs text-metadata-xs bg-verification-green/20 text-verification-green px-2 py-1 rounded">[CACHED]</span>
              )}
              <button
                className="font-label-caps text-label-caps text-inverse-primary hover:text-ink-red transition-colors uppercase text-[10px]"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? '▲ HIDE LEGEND' : '▼ SHOW LEGEND'}
              </button>
            </div>
          </div>

          {/* Legend */}
          {showDetails && (
            <div className="mb-6 flex gap-4 flex-wrap font-metadata-xs text-metadata-xs text-typewriter-ribbon/60">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 inline-block" style={{ backgroundColor: 'rgba(85, 120, 90, 0.2)', borderBottom: '2px solid #55785A' }}></span>
                RELIABLE
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 inline-block" style={{ backgroundColor: 'rgba(143, 48, 42, 0.2)', borderBottom: '2px solid #8F302A' }}></span>
                SUSPICIOUS / FLAGGED
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 inline-block border border-typewriter-ribbon/20"></span>
                NEUTRAL
              </span>
              <p className="w-full m-0 italic opacity-80">Tap any sentence to examine the evidence.</p>
            </div>
          )}

          {/* Highlighted article text */}
          {renderHighlightedText()}

          {/* Meta footer */}
          <div className="mt-8 pt-4 border-t border-outline-variant/30 flex flex-wrap gap-4 font-metadata-xs text-metadata-xs text-typewriter-ribbon/50">
            <span>ANALYZED: {formatDate(result.analyzedAt)}</span>
            <span>{result.processingTime}ms</span>
          </div>
        </div>

        {/* Evidence Sidebar (Right) — Verdict Summary (matches Stitch code.html lines 196-238) */}
        <div className="col-span-1 lg:col-span-4 bg-carbon-gray border border-outline-variant rounded-sm flex flex-col p-6 h-fit lg:sticky lg:top-24 mt-8 lg:mt-16">
          <div className="border-b border-outline-variant pb-4 mb-6">
            <h2 className="font-technical-sm text-technical-sm text-on-surface-variant uppercase tracking-widest mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">analytics</span> Verdict Summary
            </h2>
            <div className="flex justify-between items-end border-b border-outline-variant/50 pb-2">
              <span className="font-label-caps text-label-caps text-outline uppercase">ML Confidence</span>
              <span className={`font-headline-lg-mobile text-headline-lg-mobile ${confidencePct >= 70 ? 'text-verification-green' : confidencePct >= 40 ? 'text-[#ca8a04]' : 'text-ink-red'}`}>
                {confidencePct > 0 ? `${confidencePct}%` : 'N/A'}
              </span>
            </div>
          </div>

              {/* Overall Summary */}
              {result.overallSummary && (
                <div className="mb-6">
                  <h3 className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase mb-2">Summary</h3>
                  <p className="font-technical-sm text-technical-sm text-on-surface-variant leading-relaxed">{result.overallSummary}</p>
                </div>
              )}

              {/* Cross-References / Claims */}
              <div className="space-y-4 flex-grow">
                <span className="font-metadata-xs text-metadata-xs text-outline uppercase tracking-widest">
                  Similar Fact-Checked Claims
                </span>

                {result.retrieval_status === 'unavailable' ? (
                  <div className="border border-outline-variant p-3 font-technical-sm text-technical-sm text-on-surface-variant opacity-60">
                    ── ARCHIVE UNREACHABLE ──<br />
                    <span className="text-[11px]">Retrieval service offline.</span>
                  </div>
                ) : claimsList == null || claimsList.length === 0 ? (
                  <div className="border border-outline-variant p-3 font-technical-sm text-technical-sm text-on-surface-variant opacity-60">
                    ── NO RELATED CASES ON FILE ──<br />
                    <span className="text-[11px]">No similar claims found.</span>
                  </div>
                ) : (
                  claimsList.slice(0, 3).map((claim, i) => {
                    const text = claim.statement_text || claim.text || '';
                    const similarityRaw = claim.similarity_score ?? (claim.score !== undefined ? claim.score / 100 : undefined);
                    const matchPct = similarityRaw !== undefined ? Math.round(similarityRaw * 100) : null;
                    const label = claim.label ? claim.label.toUpperCase() : 'CLAIM';
                    return (
                      <a key={i} className="group block border border-outline-variant p-3 hover:bg-surface-variant/20 transition-colors no-underline" href="#">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-technical-sm text-technical-sm text-primary group-hover:text-ink-red transition-colors">
                            "{text}"
                          </span>
                          <span className="material-symbols-outlined text-[14px] text-outline flex-shrink-0 ml-2">open_in_new</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="font-metadata-xs text-metadata-xs text-outline">
                            ({label})
                          </span>
                          {matchPct !== null && (
                            <span className={`font-metadata-xs text-metadata-xs ${matchPct >= 70 ? 'text-verification-green' : 'text-outline'}`}>
                              Match Score: {matchPct}%
                            </span>
                          )}
                        </div>
                      </a>
                    );
                  })
                )}
              </div>

              {/* Feedback Section */}
              <div className="mt-8 pt-6 border-t border-outline-variant">
                <div className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase mb-3">Was this analysis helpful?</div>
                {feedbackSent ? (
                  <span className="font-technical-sm text-technical-sm text-verification-green">✓ Thank you for your feedback! ({feedbackSent})</span>
                ) : (
                  <div className="flex gap-2 flex-wrap">
                    <button className="font-label-caps text-label-caps text-on-surface-variant border border-outline-variant px-3 py-2 hover:bg-surface-variant/20 transition-colors rounded-sm text-[10px]" onClick={() => handleFeedback('helpful')} disabled={isSubmittingFeedback}>👍 Helpful</button>
                    <button className="font-label-caps text-label-caps text-on-surface-variant border border-outline-variant px-3 py-2 hover:bg-surface-variant/20 transition-colors rounded-sm text-[10px]" onClick={() => handleFeedback('incorrect')} disabled={isSubmittingFeedback}>👎 Incorrect</button>
                    <button className="font-label-caps text-label-caps text-on-surface-variant border border-outline-variant px-3 py-2 hover:bg-surface-variant/20 transition-colors rounded-sm text-[10px]" onClick={() => handleFeedback('disputed')} disabled={isSubmittingFeedback}>⚖️ Disputed</button>
                  </div>
                )}
                {feedbackError && (
                  <div className="mt-2 text-ink-red font-technical-sm text-technical-sm flex items-center gap-2">
                    <span>⚠️ {feedbackError}</span>
                    <button className="underline" onClick={() => setFeedbackError(null)}>Clear {'&'} Retry</button>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-outline-variant">
                <button
                  className="w-full bg-ink-red text-primary font-label-caps text-label-caps uppercase py-4 px-6 hover:bg-secondary-container transition-colors flex items-center justify-center gap-2 rounded-sm shadow-md"
                  onClick={() => navigate(`/analysis/${result.id}`)}
                >
                  <span className="material-symbols-outlined text-[18px]">policy</span>
                  Inspect Evidence
                </button>
              </div>
        </div>
      </div>

      {/* ── Sentence Detail Modal ── */}
      {selectedSentence && (
        <div
          className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Sentence Analysis"
          onClick={() => setSelectedSentence(null)}
        >
          <div
            className="bg-background border border-outline-variant max-w-lg w-full rounded-sm shadow-[0_24px_60px_rgba(0,0,0,0.7)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="border-b border-outline-variant flex justify-between items-center p-6 pb-4">
              <h3 role="heading" className="font-headline-lg-mobile text-[20px] text-primary">Sentence Analysis</h3>
              <button
                onClick={() => setSelectedSentence(null)}
                className="text-on-surface-variant hover:text-primary transition-colors bg-transparent border-none cursor-pointer text-xl"
                aria-label="×"
              >
                ×
              </button>
            </div>
            <div className="p-6">
              <div className="border-l-4 border-outline bg-surface-container p-4 mb-6 font-body-md text-body-md italic text-on-surface">
                "{selectedSentence.text}"
              </div>
              <div className="grid grid-cols-2 gap-3 mb-6">
                {[
                  ['SCORE', `${selectedSentence.score}/100`],
                  ['CONFIDENCE', `${Math.round(selectedSentence.confidence * 100)}%`],
                  ['CATEGORY', selectedSentence.category],
                  ['STATUS', selectedSentence.isSuspicious ? '⚠ SUSPICIOUS' : '✓ RELIABLE'],
                ].map(([label, value]) => (
                  <div key={label} className="bg-surface-container border border-outline-variant rounded-sm p-3">
                    <div className="font-metadata-xs text-metadata-xs text-on-surface-variant mb-1">{label}</div>
                    <div className={`font-technical-sm text-technical-sm font-bold ${label === 'STATUS' ? (selectedSentence.isSuspicious ? 'text-ink-red' : 'text-verification-green') : 'text-on-surface'}`}>{value}</div>
                  </div>
                ))}
              </div>
              {selectedSentence.flags.length > 0 && (
                <div className="mb-4">
                  <h4 className="font-metadata-xs text-metadata-xs text-ink-red uppercase mb-2">Flags Raised</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedSentence.flags.map((flag, index) => (
                      <span key={index} className="font-metadata-xs text-metadata-xs bg-ink-red/10 border border-ink-red/30 text-ink-red px-2 py-0.5 rounded-sm">
                        {flag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <h4 className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase mb-1">Analyst&apos;s Note</h4>
                <p className="font-body-md text-[14px] text-on-surface-variant leading-relaxed">{selectedSentence.explanation}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AnalysisResult;