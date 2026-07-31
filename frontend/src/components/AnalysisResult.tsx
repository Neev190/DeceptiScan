// AnalysisResult component for displaying analysis with highlighting
// Based on design specifications from design.md

import React, { useState } from 'react';
import { AnalysisResult as AnalysisResultType, SentenceAnalysis } from '../types';
import ScoreMeter from './ScoreMeter';

interface AnalysisResultProps {
  result: AnalysisResultType;
}

const AnalysisResult: React.FC<AnalysisResultProps> = ({ result }) => {
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
      <div className="highlighted-text">
        {result.sentenceAnalysis.map((sentence, index) => (
          <span
            key={index}
            style={getSentenceStyle(sentence)}
            onClick={() => setSelectedSentence(sentence)}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'scale(1.02)';
              e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = 'none';
            }}
            title={`Click for details - ${sentence.isSuspicious ? 'Suspicious' : 'Reliable'} (${Math.round(sentence.confidence * 100)}% confidence)`}
          >
            {sentence.text}
          </span>
        ))}
      </div>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const [feedbackSent, setFeedbackSent] = useState<string | null>(null);

  const handleFeedback = async (type: 'helpful' | 'incorrect' | 'disputed') => {
    try {
      const { apiService } = await import('../services/api');
      await apiService.submitFeedback({
        analysisId: result.id,
        userId: null,
        feedback: { type }
      });
      setFeedbackSent(type);
    } catch (e) {
      console.error('Failed to submit feedback', e);
    }
  };

  return (
    <div className="analysis-result">
      {/* Header with Score */}
      <div className="result-header">
        <div className="result-meta">
          <h2 className="result-title">Analysis Complete</h2>
          <div className="result-info">
            <span className="analysis-time">
              Analyzed: {formatDate(result.analyzedAt)}
            </span>
            <span className="processing-time">
              Processing: {result.processingTime}ms
            </span>
            {result.is_cached && (
              <span className="cached-badge" style={{ color: '#2563eb', fontWeight: 600 }}>
                (Cached Result)
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Warning / Disclaimer Banner */}
      {(result.warning || result.classification === 'unknown' || result.classification === 'unverified_style_estimate') && (
        <div className="warning-banner" style={{
          backgroundColor: '#fef3c7',
          color: '#92400e',
          padding: '1rem 1.25rem',
          borderRadius: '0.5rem',
          borderLeft: '4px solid #f59e0b',
          marginBottom: '1.5rem',
          fontSize: '0.95rem'
        }}>
          <strong>⚠️ Disclaimer: </strong>
          {result.warning || 'Low confidence in ML prediction. Sentence highlighting may be unverified.'}
        </div>
      )}

      {/* Score Meter */}
      <ScoreMeter 
        score={result.authenticityScore} 
        label={result.classification.replace(/_/g, ' ').toUpperCase()}
        confidence={result.confidence || result.confidenceScore}
      />

      {/* Overall Summary */}
      {result.overallSummary && (
        <div className="summary-section">
          <h3>Summary</h3>
          <p className="summary-text">{result.overallSummary}</p>
        </div>
      )}

      {/* Similar Claims Section */}
      {result.similar_claims && result.similar_claims.length > 0 && (
        <div className="summary-section" style={{ borderLeft: '4px solid #3b82f6' }}>
          <h3>Similar Fact-Checked Claims</h3>
          <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
            {result.similar_claims.map((claim, i) => (
              <li key={i} style={{ marginBottom: '0.5rem' }}>
                "{claim.text}" (Match Score: {claim.score}%)
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Highlighted Text */}
      <div className="text-analysis-section">
        <div className="section-header">
          <h3>Sentence-Level Analysis</h3>
          <button 
            className="toggle-details"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? 'Hide Details' : 'Show Legend'}
          </button>
        </div>

        {showDetails && (
          <div className="analysis-legend">
            <div className="legend-item">
              <span className="legend-color reliable"></span>
              <span>Reliable content (green highlight)</span>
            </div>
            <div className="legend-item">
              <span className="legend-color suspicious"></span>
              <span>Potentially suspicious content (red highlight)</span>
            </div>
            <div className="legend-item">
              <span className="legend-color neutral"></span>
              <span>Neutral content (no special highlighting)</span>
            </div>
            <p className="legend-note">
              Click on any highlighted sentence to see detailed analysis.
            </p>
          </div>
        )}

        {renderHighlightedText()}
      </div>

      {/* Feedback Section */}
      <div className="summary-section" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontWeight: 600, color: '#374151' }}>Was this analysis helpful?</span>
        {feedbackSent ? (
          <span style={{ color: '#166534', fontWeight: 600 }}>Thank you for your feedback! ({feedbackSent})</span>
        ) : (
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="toggle-details" onClick={() => handleFeedback('helpful')}>👍 Helpful</button>
            <button className="toggle-details" onClick={() => handleFeedback('incorrect')}>👎 Incorrect</button>
            <button className="toggle-details" onClick={() => handleFeedback('disputed')}>⚖️ Disputed</button>
          </div>
        )}
      </div>

      {/* Sentence Details Modal */}
      {selectedSentence && (
        <div className="sentence-modal-overlay" onClick={() => setSelectedSentence(null)}>
          <div className="sentence-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Sentence Analysis</h3>
              <button 
                className="modal-close"
                onClick={() => setSelectedSentence(null)}
              >
                ×
              </button>
            </div>
            <div className="modal-content">
              <div className="sentence-text">
                "{selectedSentence.text}"
              </div>
              <div className="sentence-stats">
                <div className="stat">
                  <span className="stat-label">Score:</span>
                  <span className="stat-value">{selectedSentence.score}/100</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Confidence:</span>
                  <span className="stat-value">{Math.round(selectedSentence.confidence * 100)}%</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Category:</span>
                  <span className="stat-value">{selectedSentence.category}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Status:</span>
                  <span 
                    className="stat-value"
                    style={{ 
                      color: selectedSentence.isSuspicious ? '#ef4444' : '#22c55e',
                      fontWeight: 'bold'
                    }}
                  >
                    {selectedSentence.isSuspicious ? 'Suspicious' : 'Reliable'}
                  </span>
                </div>
              </div>
              {selectedSentence.flags.length > 0 && (
                <div className="sentence-flags">
                  <h4>Flags:</h4>
                  <ul>
                    {selectedSentence.flags.map((flag, index) => (
                      <li key={index}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="sentence-explanation">
                <h4>Explanation:</h4>
                <p>{selectedSentence.explanation}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .analysis-result {
          margin-top: 2rem;
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .result-title {
          margin: 0;
          color: #1e293b;
          font-size: 1.5rem;
        }

        .result-info {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          font-size: 0.875rem;
          color: #64748b;
        }

        .summary-section, .text-analysis-section {
          background: white;
          padding: 1.5rem;
          border-radius: 0.75rem;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          border: 1px solid #e2e8f0;
          margin-bottom: 1.5rem;
        }

        .summary-section h3, .text-analysis-section h3 {
          margin: 0 0 1rem 0;
          color: #1e293b;
          font-size: 1.25rem;
        }

        .summary-text {
          margin: 0;
          color: #374151;
          line-height: 1.6;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        .toggle-details {
          background: #f1f5f9;
          border: 1px solid #e2e8f0;
          padding: 0.5rem 1rem;
          border-radius: 0.375rem;
          cursor: pointer;
          font-size: 0.875rem;
          color: #475569;
          transition: all 0.2s;
        }

        .toggle-details:hover {
          background: #e2e8f0;
        }

        .analysis-legend {
          background: #f8fafc;
          padding: 1rem;
          border-radius: 0.5rem;
          margin-bottom: 1.5rem;
          border: 1px solid #e2e8f0;
        }

        .legend-item {
          display: flex;
          align-items: center;
          margin-bottom: 0.5rem;
          font-size: 0.875rem;
        }

        .legend-color {
          width: 1rem;
          height: 1rem;
          border-radius: 0.25rem;
          margin-right: 0.75rem;
          border: 1px solid #e2e8f0;
        }

        .legend-color.reliable {
          background-color: #dcfce7;
        }

        .legend-color.suspicious {
          background-color: #fee2e2;
        }

        .legend-color.neutral {
          background-color: #f8fafc;
        }

        .legend-note {
          margin: 1rem 0 0 0;
          font-size: 0.75rem;
          color: #64748b;
          font-style: italic;
        }

        .highlighted-text {
          line-height: 2;
          font-size: 1rem;
          color: #1e293b;
        }

        .no-analysis {
          color: #64748b;
          font-style: italic;
          text-align: center;
          padding: 2rem;
        }

        .sentence-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 1rem;
        }

        .sentence-modal {
          background: white;
          border-radius: 0.75rem;
          max-width: 600px;
          width: 100%;
          max-height: 80vh;
          overflow-y: auto;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem 1.5rem 1rem;
          border-bottom: 1px solid #e2e8f0;
        }

        .modal-header h3 {
          margin: 0;
          color: #1e293b;
        }

        .modal-close {
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: #64748b;
          padding: 0.25rem;
        }

        .modal-close:hover {
          color: #1e293b;
        }

        .modal-content {
          padding: 1.5rem;
        }

        .sentence-text {
          background: #f8fafc;
          padding: 1rem;
          border-radius: 0.5rem;
          border-left: 4px solid var(--primary-color);
          margin-bottom: 1.5rem;
          font-style: italic;
          color: #1e293b;
        }

        .sentence-stats {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1rem;
          margin-bottom: 1.5rem;
        }

        .stat {
          display: flex;
          justify-content: space-between;
          padding: 0.75rem;
          background: #f8fafc;
          border-radius: 0.375rem;
        }

        .stat-label {
          color: #64748b;
          font-weight: 500;
        }

        .stat-value {
          color: #1e293b;
          font-weight: 600;
        }

        .sentence-flags, .sentence-explanation {
          margin-bottom: 1rem;
        }

        .sentence-flags h4, .sentence-explanation h4 {
          margin: 0 0 0.5rem 0;
          color: #1e293b;
          font-size: 1rem;
        }

        .sentence-flags ul {
          margin: 0;
          padding-left: 1.5rem;
          color: #374151;
        }

        .sentence-explanation p {
          margin: 0;
          color: #374151;
          line-height: 1.6;
        }

        @media (max-width: 768px) {
          .result-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
          }

          .result-info {
            align-items: flex-start;
          }

          .sentence-stats {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default AnalysisResult;