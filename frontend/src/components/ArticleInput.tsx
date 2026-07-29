// ArticleInput component for text submission and URL input
// Based on design specifications from design.md

import React, { useState, ChangeEvent, FormEvent } from 'react';
import { ArticleInputProps } from '../types';

const ArticleInput: React.FC<ArticleInputProps> = ({ onSubmit, isLoading }) => {
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

  return (
    <div className="article-input">
      <form onSubmit={handleSubmit}>
        {/* Content Type Toggle */}
        <div className="content-type-toggle">
          <button
            type="button"
            className={`toggle-btn ${contentType === 'text' ? 'active' : ''}`}
            onClick={() => setContentType('text')}
            disabled={isLoading}
          >
            Text Input
          </button>
          <button
            type="button"
            className={`toggle-btn ${contentType === 'url' ? 'active' : ''}`}
            onClick={() => setContentType('url')}
            disabled={isLoading}
          >
            URL Analysis
          </button>
        </div>

        {/* Optional fields */}
        <div className="optional-fields">
          <div className="form-group">
            <label htmlFor="title" className="form-label">
              Article Title (Optional)
            </label>
            <input
              id="title"
              type="text"
              className="form-input"
              placeholder="Enter article title..."
              value={title}
              onChange={handleTitleChange}
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="sourceUrl" className="form-label">
              Source URL (Optional)
            </label>
            <input
              id="sourceUrl"
              type="url"
              className={`form-input ${sourceUrl && !isValidUrl(sourceUrl) ? 'error' : ''}`}
              placeholder="https://example.com/article"
              value={sourceUrl}
              onChange={handleSourceUrlChange}
              disabled={isLoading}
            />
            {sourceUrl && !isValidUrl(sourceUrl) && (
              <p className="error-text">Please enter a valid URL</p>
            )}
          </div>
        </div>

        {/* Main content area */}
        <div className="form-group">
          <label htmlFor="content" className="form-label">
            Article Content *
          </label>
          <textarea
            id="content"
            className={`form-textarea ${isNearLimit ? 'warning' : ''}`}
            placeholder={
              contentType === 'text'
                ? "Paste your article text here for analysis..."
                : "URL analysis coming soon. For now, please paste the article text."
            }
            value={content}
            onChange={handleContentChange}
            disabled={isLoading}
            rows={12}
            required
          />
          <div className="character-counter">
            <span className={isNearLimit ? 'warning' : ''}>
              {characterCount.toLocaleString()}/50,000 characters
            </span>
            {isNearLimit && (
              <span className="warning-text"> (approaching limit)</span>
            )}
          </div>
        </div>

        {/* Submit button */}
        <button
          type="submit"
          className={`submit-btn ${isSubmitDisabled ? 'disabled' : ''}`}
          disabled={!!isSubmitDisabled}
        >
          {isLoading ? (
            <>
              <span className="spinner"></span>
              Analyzing...
            </>
          ) : (
            'Analyze Content'
          )}
        </button>

        {/* Help text */}
        <p className="help-text">
          Our AI will analyze your content for potential misinformation and highlight 
          suspicious claims with explanations.
        </p>
      </form>

      <style>{`
        .article-input {
          background: white;
          padding: 2rem;
          border-radius: 0.75rem;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          border: 1px solid #e2e8f0;
          margin-bottom: 2rem;
        }

        .content-type-toggle {
          display: flex;
          margin-bottom: 1.5rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          overflow: hidden;
        }

        .toggle-btn {
          flex: 1;
          padding: 0.75rem 1rem;
          background: #f8fafc;
          border: none;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
        }

        .toggle-btn.active {
          background: var(--primary-color);
          color: white;
        }

        .toggle-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .optional-fields {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
          margin-bottom: 1.5rem;
        }

        @media (max-width: 768px) {
          .optional-fields {
            grid-template-columns: 1fr;
          }
        }

        .form-group {
          margin-bottom: 1rem;
        }

        .form-label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 600;
          color: #1e293b;
        }

        .form-input, .form-textarea {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          font-size: 1rem;
          transition: border-color 0.2s;
          font-family: inherit;
        }

        .form-input:focus, .form-textarea:focus {
          outline: none;
          border-color: var(--primary-color);
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .form-input.error {
          border-color: var(--danger-color);
        }

        .form-textarea {
          resize: vertical;
          min-height: 200px;
          line-height: 1.5;
        }

        .form-textarea.warning {
          border-color: var(--warning-color);
        }

        .character-counter {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 0.5rem;
          font-size: 0.875rem;
          color: #64748b;
        }

        .character-counter .warning {
          color: var(--warning-color);
          font-weight: 600;
        }

        .warning-text {
          color: var(--warning-color);
          font-weight: 500;
        }

        .error-text {
          color: var(--danger-color);
          font-size: 0.875rem;
          margin-top: 0.25rem;
        }

        .submit-btn {
          width: 100%;
          padding: 1rem 2rem;
          background: var(--primary-color);
          color: white;
          border: none;
          border-radius: 0.5rem;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }

        .submit-btn:hover:not(.disabled) {
          background: #1d4ed8;
          transform: translateY(-1px);
        }

        .submit-btn.disabled {
          background: #94a3b8;
          cursor: not-allowed;
          transform: none;
        }

        .spinner {
          width: 1rem;
          height: 1rem;
          border: 2px solid transparent;
          border-top: 2px solid currentColor;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .help-text {
          margin: 0;
          color: #64748b;
          font-size: 0.875rem;
          text-align: center;
          line-height: 1.5;
        }
      `}</style>
    </div>
  );
};

export default ArticleInput;