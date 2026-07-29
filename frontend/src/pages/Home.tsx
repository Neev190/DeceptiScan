import { useState } from 'react';
import { ArticleInput, AnalysisResult } from '../components';
import { AnalysisResult as AnalysisResultType, ApiError } from '../types';
import { apiService } from '../services/api';

function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResultType | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const handleAnalyze = async (content: string) => {
    if (!content.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const analysisResult = await apiService.analyzeText({
        content: content.trim(),
        language: 'en',
        contentType: 'text'
      });
      setResult(analysisResult);
    } catch (error: any) {
      console.error('Analysis failed:', error);
      setError(error as ApiError);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    setResult(null);
  };

  return (
    <div className="home-page">
      <div className="container">
        {/* Header */}
        <header className="page-header">
          <h1 className="page-title">DeceptiScan</h1>
          <p className="page-subtitle">
            AI-Powered Misinformation Detection
          </p>
          <p className="page-description">
            Submit news articles for analysis. Our AI will highlight suspicious claims 
            and provide an overall authenticity score to help you identify potential misinformation.
          </p>
        </header>

        {/* Main Content */}
        <main className="main-content">
          {/* Input Section */}
          <ArticleInput 
            onSubmit={handleAnalyze}
            isLoading={isLoading}
          />

          {/* Error Display */}
          {error && (
            <div className="error-container">
              <div className="error-content">
                <h3 className="error-title">Analysis Failed</h3>
                <p className="error-message">{error.message}</p>
                {error.code === 'RATE_LIMITED' && (
                  <p className="error-hint">
                    You've reached the request limit. Please wait a moment before trying again.
                  </p>
                )}
                {error.code === 'INVALID_INPUT' && (
                  <p className="error-hint">
                    Please check your input and try again.
                  </p>
                )}
                <button 
                  className="error-retry-btn"
                  onClick={handleRetry}
                >
                  Try Again
                </button>
              </div>
            </div>
          )}

          {/* Results Section */}
          {result && !error && (
            <AnalysisResult result={result} />
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <h3>Analyzing Content...</h3>
              <p>Our AI is examining your text for potential misinformation.</p>
            </div>
          )}
        </main>

        {/* Footer Info */}
        <footer className="page-footer">
          <div className="info-grid">
            <div className="info-item">
              <h4>How it works</h4>
              <p>Our AI analyzes text using advanced NLP models to identify suspicious claims and provide explanations.</p>
            </div>
            <div className="info-item">
              <h4>Color coding</h4>
              <p>Green highlights indicate reliable content, red highlights show potentially suspicious claims.</p>
            </div>
            <div className="info-item">
              <h4>Limitations</h4>
              <p>This tool provides analysis assistance. Always verify important information through multiple sources.</p>
            </div>
          </div>
        </footer>
      </div>

      <style>{`
        .home-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }

        .container {
          max-width: 1000px;
          margin: 0 auto;
          padding: 2rem 1rem;
        }

        .page-header {
          text-align: center;
          margin-bottom: 3rem;
        }

        .page-title {
          font-size: 3rem;
          margin: 0 0 0.5rem 0;
          background: linear-gradient(135deg, var(--primary-color), #1d4ed8);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          font-weight: 800;
        }

        .page-subtitle {
          font-size: 1.25rem;
          color: var(--secondary-color);
          margin: 0 0 1rem 0;
          font-weight: 600;
        }

        .page-description {
          max-width: 600px;
          margin: 0 auto;
          color: #64748b;
          line-height: 1.6;
        }

        .main-content {
          margin-bottom: 3rem;
        }

        .error-container {
          background: white;
          border: 1px solid #fee2e2;
          border-radius: 0.75rem;
          padding: 2rem;
          margin-bottom: 2rem;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .error-content {
          text-align: center;
          max-width: 400px;
          margin: 0 auto;
        }

        .error-title {
          color: #dc2626;
          margin: 0 0 0.5rem 0;
          font-size: 1.25rem;
        }

        .error-message {
          color: #374151;
          margin: 0 0 1rem 0;
        }

        .error-hint {
          color: #64748b;
          font-size: 0.875rem;
          margin: 0 0 1.5rem 0;
        }

        .error-retry-btn {
          background: var(--primary-color);
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 0.5rem;
          cursor: pointer;
          font-weight: 500;
          transition: background-color 0.2s;
        }

        .error-retry-btn:hover {
          background: #1d4ed8;
        }

        .loading-container {
          background: white;
          border-radius: 0.75rem;
          padding: 3rem 2rem;
          text-align: center;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          border: 1px solid #e2e8f0;
          margin-bottom: 2rem;
        }

        .loading-spinner {
          width: 3rem;
          height: 3rem;
          border: 4px solid #e2e8f0;
          border-top: 4px solid var(--primary-color);
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 1.5rem auto;
        }

        .loading-container h3 {
          margin: 0 0 0.5rem 0;
          color: #1e293b;
        }

        .loading-container p {
          margin: 0;
          color: #64748b;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .page-footer {
          margin-top: 4rem;
          padding-top: 2rem;
          border-top: 1px solid #e2e8f0;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 2rem;
        }

        .info-item {
          text-align: center;
        }

        .info-item h4 {
          margin: 0 0 0.75rem 0;
          color: #1e293b;
          font-size: 1.1rem;
        }

        .info-item p {
          margin: 0;
          color: #64748b;
          font-size: 0.875rem;
          line-height: 1.5;
        }

        @media (max-width: 768px) {
          .page-title {
            font-size: 2rem;
          }

          .container {
            padding: 1rem;
          }

          .info-grid {
            grid-template-columns: 1fr;
            gap: 1.5rem;
          }
        }
      `}</style>
    </div>
  );
}

export default Home;