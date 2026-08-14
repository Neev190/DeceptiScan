import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { AnalysisResult as AnalysisResultComponent } from '../components';
import { AnalysisResult as AnalysisResultType, ApiError } from '../types';
import { apiService } from '../services/api';

function AnalysisDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<AnalysisResultType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    if (!id) {
      navigate('/');
      return;
    }

    const fetchAnalysis = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Try to fetch from analysis endpoint first, then history endpoint
        let analysisResult: AnalysisResultType;
        try {
          analysisResult = await apiService.getAnalysis(id);
        } catch (err: any) {
          // If analysis endpoint fails (e.g., not found), try history endpoint
          if (err.code === 'NOT_FOUND' || err.response?.status === 404) {
            analysisResult = await apiService.getHistoryItem(id);
          } else {
            throw err;
          }
        }
        setResult(analysisResult);
      } catch (err: any) {
        console.error('Failed to fetch analysis:', err);
        setError(err as ApiError);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalysis();
  }, [id, navigate]);

  if (isLoading) {
    return (
      <div className="bg-lead-charcoal text-on-surface font-body-md flex flex-col overflow-hidden relative w-full min-h-[calc(100vh-80px)]">
        {/* Grid Overlay */}
        <div className="absolute inset-0 grid-overlay pointer-events-none z-0"></div>
        {/* Loading Content */}
        <main className="flex-1 flex items-center justify-center relative z-10 px-margin-mobile md:px-margin-desktop py-12">
          <div className="w-full max-w-3xl flex flex-col items-center text-center">
            <div className="mb-6">
              <span className="material-symbols-outlined text-4xl text-ink-red animate-pulse">folder_open</span>
            </div>
            <h1 className="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-primary tracking-tighter uppercase mb-4">
              RETRIEVING CASE FILE
            </h1>
            <p className="font-technical-sm text-technical-sm text-on-surface-variant uppercase animate-pulse">
              ACCESSING ARCHIVAL RECORDS...
            </p>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full max-w-container-max px-margin-mobile md:px-margin-desktop py-8 mx-auto">
        <div className="bg-carbon-gray border border-ink-red p-6 mb-8">
          <div className="flex items-start gap-4">
            <span className="material-symbols-outlined text-ink-red text-[24px]">error</span>
            <div className="flex-1">
              <h3 className="font-technical-sm text-technical-sm text-ink-red uppercase mb-2">CASE FILE ACCESS DENIED</h3>
              <p className="font-body-md text-body-md text-on-surface-variant">{error.message}</p>
              {error.code === 'NOT_FOUND' && (
                <p className="font-technical-sm text-technical-sm text-on-surface-variant mt-2 opacity-70">
                  The requested analysis could not be found or may have been deleted.
                </p>
              )}
            </div>
          </div>
          <div className="mt-4 flex gap-4">
            <Link
              to="/"
              className="bg-ink-red hover:bg-secondary-container text-white font-label-caps text-label-caps px-6 py-3 rounded-none transition-colors border border-ink-red no-underline"
            >
              NEW INVESTIGATION
            </Link>
            <Link
              to="/history"
              className="bg-transparent border border-outline-variant text-on-surface-variant hover:bg-surface-variant font-label-caps text-label-caps px-6 py-3 rounded-none transition-colors no-underline"
            >
              VIEW ARCHIVE
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  return (
    <div className="w-full max-w-container-max px-margin-mobile md:px-margin-desktop py-8 mx-auto">
      {/* Breadcrumb Navigation */}
      <nav className="mb-6 flex items-center gap-2 text-on-surface-variant font-technical-sm text-technical-sm uppercase">
        <Link to="/" className="hover:text-primary transition-colors no-underline">Investigation Desk</Link>
        <span className="material-symbols-outlined text-[14px]">chevron_right</span>
        <Link to="/history" className="hover:text-primary transition-colors no-underline">Case Archive</Link>
        <span className="material-symbols-outlined text-[14px]">chevron_right</span>
        <span className="text-ink-red">Case File #{id?.slice(0, 6).toUpperCase()}</span>
      </nav>

      {/* Analysis Result */}
      <AnalysisResultComponent result={result} />
    </div>
  );
}

export default AnalysisDetail;