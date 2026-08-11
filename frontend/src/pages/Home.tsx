import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArticleInput, AnalysisResult } from '../components';
import { AnalysisResult as AnalysisResultType, AnalysisHistoryItem, ApiError } from '../types';
import { apiService } from '../services/api';
import { useAuth } from '../context/AuthContext';

function Home() {
  const { isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResultType | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisHistoryItem[]>([]);
  const [recentLoading, setRecentLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      setRecentAnalyses([]);
      return;
    }
    const fetchRecent = async () => {
      setRecentLoading(true);
      try {
        const items = await apiService.getRecentAnalyses(5);
        setRecentAnalyses(items);
      } catch (err) {
        console.error('Failed to fetch recent analyses:', err);
      } finally {
        setRecentLoading(false);
      }
    };
    fetchRecent();
  }, [isAuthenticated, result]);

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
  // ── END UNCHANGED LOGIC ───────────────────────────────────────────────

  return (
    <>
      {/* ── Loading State (analysis_in_progress screen) ── */}
      {isLoading && (
        <div className="bg-lead-charcoal text-on-surface font-body-md flex flex-col overflow-hidden relative w-full min-h-[calc(100vh-80px)]">
          {/* Grid Overlay */}
          <div className="absolute inset-0 grid-overlay pointer-events-none z-0"></div>
          {/* Main Content Area */}
          <main className="flex-1 flex items-center justify-center relative z-10 px-margin-mobile md:px-margin-desktop py-12">
            {/* Scanline Animation Overlay */}
            <div
              className="absolute inset-0 pointer-events-none z-20 w-full opacity-50 mix-blend-overlay"
              style={{
                background: 'linear-gradient(to bottom, transparent, rgba(143, 48, 42, 0.2) 50%, rgba(143, 48, 42, 0.8) 100%)',
                animation: 'scan-loading 4s linear infinite',
              }}
            ></div>
            <div className="w-full max-w-3xl flex flex-col items-center">
              {/* Context Header */}
              <div className="w-full mb-12 text-center">
                <p className="font-metadata-xs text-metadata-xs text-ink-red mb-2 uppercase tracking-widest blinking-cursor">INVESTIGATION PROTOCOL: ACTIVE</p>
                <h1 className="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-primary tracking-tighter uppercase">ANALYZING EVIDENCE</h1>
                <p className="font-technical-sm text-technical-sm text-on-surface-variant mt-4 opacity-70">EXECUTION COMMENCED. AWAITING PROCESS COMPLETION.</p>
              </div>
              {/* Forensic Process Paper */}
              <div className="w-full paper-texture shadow-[0px_24px_60px_rgba(0,0,0,0.5)] border border-outline-variant relative overflow-hidden text-typewriter-ribbon p-8 md:p-12 -mt-4 z-30">
                {/* Corner details */}
                <div className="absolute top-4 left-4 w-12 h-12 border-t border-l border-outline-variant opacity-30"></div>
                <div className="absolute bottom-4 right-4 w-12 h-12 border-b border-r border-outline-variant opacity-30"></div>
                <div className="flex flex-col md:flex-row gap-12">
                  {/* Left: Process List */}
                  <div className="flex-1 border-r-0 md:border-r border-outline-variant md:pr-12">
                    <h2 className="font-label-caps text-label-caps text-outline-variant mb-6 pb-2 border-b border-outline-variant uppercase">Analysis Sequence</h2>
                    <div className="space-y-6">
                      <div className="flex items-start opacity-50">
                        <span className="font-technical-sm text-technical-sm mr-4 mt-0.5">01</span>
                        <div>
                          <p className="font-technical-sm text-technical-sm font-semibold uppercase">DOCUMENT INGESTION</p>
                          <p className="font-metadata-xs text-metadata-xs text-verification-green mt-1">STATUS: COMPLETED</p>
                        </div>
                      </div>
                      <div className="flex items-start opacity-50">
                        <span className="font-technical-sm text-technical-sm mr-4 mt-0.5">02</span>
                        <div>
                          <p className="font-technical-sm text-technical-sm font-semibold uppercase">CLAIM EXTRACTION</p>
                          <p className="font-metadata-xs text-metadata-xs text-verification-green mt-1">STATUS: COMPLETED</p>
                        </div>
                      </div>
                      <div className="flex items-start relative">
                        <div className="absolute -left-8 top-1.5 w-2 h-2 rounded-full bg-ink-red animate-pulse"></div>
                        <span className="font-technical-sm text-technical-sm mr-4 mt-0.5 text-ink-red">03</span>
                        <div>
                          <p className="font-technical-sm text-technical-sm font-bold text-ink-red uppercase">SEMANTIC COMPARISON</p>
                          <p className="font-metadata-xs text-metadata-xs mt-1 animate-pulse">STATUS: IN PROGRESS...</p>
                        </div>
                      </div>
                      <div className="flex items-start opacity-30">
                        <span className="font-technical-sm text-technical-sm mr-4 mt-0.5">04</span>
                        <div>
                          <p className="font-technical-sm text-technical-sm uppercase">EVIDENCE RETRIEVAL</p>
                          <p className="font-metadata-xs text-metadata-xs mt-1">STATUS: PENDING</p>
                        </div>
                      </div>
                      <div className="flex items-start opacity-30">
                        <span className="font-technical-sm text-technical-sm mr-4 mt-0.5">05</span>
                        <div>
                          <p className="font-technical-sm text-technical-sm uppercase">RECENCY CHECK</p>
                          <p className="font-metadata-xs text-metadata-xs mt-1">STATUS: PENDING</p>
                        </div>
                      </div>
                      <div className="flex items-start opacity-30">
                        <span className="font-technical-sm text-technical-sm mr-4 mt-0.5">06</span>
                        <div>
                          <p className="font-technical-sm text-technical-sm uppercase">CONFIDENCE CALCULATION</p>
                          <p className="font-metadata-xs text-metadata-xs mt-1">STATUS: PENDING</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  {/* Right: Real-time Output */}
                  <div className="flex-1 flex flex-col justify-between">
                    <div>
                      <h2 className="font-label-caps text-label-caps text-outline-variant mb-6 pb-2 border-b border-outline-variant uppercase">Live Telemetry</h2>
                      <div className="bg-carbon-gray text-on-surface p-4 border border-outline-variant font-technical-sm text-technical-sm h-48 overflow-hidden relative">
                        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-carbon-gray z-10 pointer-events-none"></div>
                        <ul className="space-y-2 opacity-80">
                          <li className="text-verification-green">&gt; INITIATING SEQUENCE... OK</li>
                          <li>&gt; PARSING SOURCE DOCUMENT... DONE</li>
                          <li>&gt; IDENTIFYING CLAIMS... IN PROGRESS</li>
                          <li>&gt; EXTRACTING ENTITIES... OK</li>
                          <li className="text-ink-red">&gt; INITIATING SEMANTIC MATCHING...</li>
                          <li className="blinking-cursor">&gt; COMPARING AGAINST DATASET_OMEGA</li>
                        </ul>
                      </div>
                    </div>
                    {/* Progress Bar */}
                    <div className="mt-8">
                      <div className="flex justify-between font-metadata-xs text-metadata-xs mb-2">
                        <span className="uppercase">Overall Progress</span>
                        <span>IN PROGRESS</span>
                      </div>
                      <div className="w-full h-1 bg-surface-variant relative overflow-hidden">
                        <div className="absolute top-0 left-0 h-full bg-ink-red animate-pulse" style={{ width: '45%' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              {/* Abort button */}
              <div className="mt-12 flex space-x-4">
                <button
                  className="px-6 py-3 border border-outline-variant bg-transparent text-on-surface-variant font-label-caps text-label-caps hover:bg-surface-variant transition-colors uppercase"
                  onClick={handleRetry}
                >
                  ABORT PROTOCOL
                </button>
              </div>
            </div>
          </main>
          <style>{`
            @keyframes scan-loading {
              0% { transform: translateY(-100%); }
              100% { transform: translateY(100vh); }
            }
          `}</style>
        </div>
      )}

      {/* ── Results State (analysis_findings rendered via AnalysisResult component) ── */}
      {result && !error && !isLoading && (
        <div className="w-full max-w-container-max px-margin-mobile md:px-margin-desktop py-8 mx-auto">
          <AnalysisResult result={result} />
        </div>
      )}

      {/* ── Error State ── */}
      {error && !isLoading && (
        <div className="w-full max-w-container-max px-margin-mobile md:px-margin-desktop py-8 mx-auto">
          {/* Error banner styled with Stitch design system */}
          <div className="bg-carbon-gray border border-ink-red p-6 mb-8">
            <div className="flex items-start gap-4">
              <span className="material-symbols-outlined text-ink-red text-[24px]">error</span>
              <div className="flex-1">
                <h3 className="font-technical-sm text-technical-sm text-ink-red uppercase mb-2">ANALYSIS FAILED</h3>
                <p className="font-body-md text-body-md text-on-surface-variant">{error.message}</p>
                {error.code === 'RATE_LIMITED' && (
                  <p className="font-technical-sm text-technical-sm text-on-surface-variant mt-2 opacity-70">You've reached the request limit. Please wait a moment before trying again.</p>
                )}
                {error.code === 'INVALID_INPUT' && (
                  <p className="font-technical-sm text-technical-sm text-on-surface-variant mt-2 opacity-70">Please check your input and try again.</p>
                )}
              </div>
            </div>
            <div className="mt-4">
              <button
                onClick={handleRetry}
                className="bg-ink-red hover:bg-secondary-container text-white font-label-caps text-label-caps px-6 py-3 rounded-none transition-colors flex items-center gap-2 border border-ink-red"
              >
                RETRY INVESTIGATION <span className="material-symbols-outlined text-[18px]">refresh</span>
              </button>
            </div>
          </div>
          <ArticleInput onSubmit={handleAnalyze} isLoading={isLoading} />
        </div>
      )}

      {/* ── Default / Input State (investigation_desk screen) ── */}
      {!isLoading && !result && !error && (
        <>
          {/* Archival Hero */}
          <section className="w-full bg-lead-charcoal relative py-20 px-margin-mobile md:px-margin-desktop border-b border-outline-variant overflow-hidden flex justify-center">
            <div className="absolute inset-0 grid-overlay"></div>
            <div className="max-w-container-max w-full relative z-10 flex flex-col items-center text-center">
              <div className="inline-flex items-center gap-2 mb-6 border border-outline-variant px-3 py-1 bg-surface-container-high/50">
                <span className="w-2 h-2 rounded-full bg-ink-red animate-pulse"></span>
                <span className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase">Investigation Protocol Active</span>
              </div>
              <h1 className="font-headline-lg-mobile md:font-display-lg text-headline-lg-mobile md:text-display-lg text-primary mb-4 tracking-tighter uppercase max-w-4xl">
                Don't trust the story.<br />Investigate it.
              </h1>
              <p className="font-technical-sm text-technical-sm text-on-surface-variant max-w-2xl opacity-80 uppercase">
                Enter subject testimony or archival evidence below for deep structural analysis. Irregularities will be flagged.
              </p>
            </div>
          </section>

          {/* Case Intake Workspace */}
          <section className="w-full max-w-container-max px-margin-mobile md:px-margin-desktop -mt-12 relative z-20 mb-24">
            <ArticleInput onSubmit={handleAnalyze} isLoading={isLoading} />
          </section>

          {/* Reference Section: Recent Archives */}
          <section className="w-full max-w-container-max px-margin-mobile md:px-margin-desktop mb-24">
            <div className="border-b border-outline-variant pb-2 mb-6 flex justify-between items-end">
              <h2 className="font-technical-sm text-technical-sm text-on-surface-variant uppercase tracking-widest">
                Recent Archival Pulls
              </h2>
              <span className="font-metadata-xs text-metadata-xs text-on-surface-variant opacity-50">
                {isAuthenticated ? 'CLASSIFIED ARCHIVE // USER SCOPED' : 'RESTRICTED ACCESS'}
              </span>
            </div>

            {!isAuthenticated ? (
              <div className="bg-carbon-gray border border-outline-variant p-8 text-center">
                <span className="material-symbols-outlined text-3xl text-on-surface-variant mb-2">lock</span>
                <p className="font-technical-sm text-technical-sm text-on-surface mb-4 uppercase">
                  LOG IN TO ACCESS YOUR RECENT CASE ARCHIVE PULLS
                </p>
                <Link
                  to="/login"
                  className="inline-block bg-ink-red hover:bg-secondary-container text-white font-label-caps text-label-caps px-4 py-2 uppercase no-underline transition-colors border border-ink-red"
                >
                  LOG IN TO SYSTEM
                </Link>
              </div>
            ) : recentLoading ? (
              <div className="bg-carbon-gray border border-outline-variant p-8 text-center">
                <span className="font-technical-sm text-technical-sm text-on-surface-variant uppercase animate-pulse">
                  FETCHING ARCHIVAL RECORDS...
                </span>
              </div>
            ) : recentAnalyses.length === 0 ? (
              <div className="bg-carbon-gray border border-outline-variant p-8 text-center">
                <span className="material-symbols-outlined text-3xl text-on-surface-variant mb-2">folder_off</span>
                <p className="font-technical-sm text-technical-sm text-on-surface-variant uppercase">
                  NO ARCHIVAL PULLS RECORDED YET. SUBMIT A TESTIMONY ABOVE TO BEGIN.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {recentAnalyses.map((item) => {
                  const score = Math.round(item.authenticityScore ?? item.authenticity_score ?? 0);
                  const fileId = `FILE_${item.id.slice(0, 6).toUpperCase()}`;
                  const displayTitle = item.title || (item.input_text ? item.input_text.slice(0, 60) + '...' : 'UNTITLED ANALYSIS');
                  const dateStr = item.analyzedAt || item.created_at || item.createdAt;
                  const formattedDate = dateStr ? new Date(dateStr).toLocaleDateString() : '';

                  const getClassificationColor = (cls: string) => {
                    switch (cls) {
                      case 'reliable':
                        return 'text-verification-green border-verification-green';
                      case 'unreliable':
                        return 'text-ink-red border-ink-red';
                      case 'mixed':
                        return 'text-[#FF8C42] border-[#FF8C42]';
                      default:
                        return 'text-on-surface-variant border-outline-variant';
                    }
                  };

                  return (
                    <Link
                      to="/history"
                      key={item.id}
                      className="bg-carbon-gray border border-outline-variant flex flex-col hover:border-surface-tint transition-colors group no-underline text-inherit"
                    >
                      <div className="flex justify-between items-center px-3 py-2 bg-surface-container-lowest border-b border-outline-variant">
                        <div className="flex items-center gap-2">
                          <span className="material-symbols-outlined text-[14px] text-on-surface-variant">folder_open</span>
                          <span className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase">{fileId}</span>
                        </div>
                        <span className="font-metadata-xs text-metadata-xs text-on-surface-variant/70">{formattedDate}</span>
                      </div>
                      <div className="p-4 flex-1 flex flex-col justify-between">
                        <div>
                          <h3 className="font-technical-sm text-technical-sm text-primary mb-3 uppercase line-clamp-2">
                            {displayTitle}
                          </h3>
                        </div>
                        <div className="flex justify-between items-center mt-4 pt-4 border-t border-outline-variant/50">
                          <span className={`font-label-caps text-label-caps uppercase border px-2 py-0.5 ${getClassificationColor(item.classification)}`}>
                            {item.classification} // {score}%
                          </span>
                          <span className="font-label-caps text-label-caps text-ink-red group-hover:text-secondary transition-colors">
                            VIEW CASE
                          </span>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </section>
        </>
      )}
    </>
  );
}

export default Home;