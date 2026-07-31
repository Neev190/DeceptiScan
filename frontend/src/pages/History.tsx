import React, { useEffect, useState } from 'react';
import apiService from '../services/api';
import { AnalysisHistoryItem, AnalysisResult as AnalysisResultType } from '../types';
import AnalysisResult from '../components/AnalysisResult';

const History: React.FC = () => {
  const [items, setItems] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [selectedResult, setSelectedResult] = useState<AnalysisResultType | null>(null);

  const fetchHistory = async (p: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiService.getAnalysisHistory(p, 10);
      setItems(res.data);
      setPage(res.pagination.page);
      setTotalPages(res.pagination.totalPages);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch analysis history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(page);
  }, [page]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this analysis record?')) {
      return;
    }
    try {
      await apiService.deleteAnalysis(id);
      if (selectedResult?.id === id) {
        setSelectedResult(null);
      }
      fetchHistory(page);
    } catch (err: any) {
      alert(err.message || 'Failed to delete record.');
    }
  };

  const handleSelect = async (id: string) => {
    try {
      const detail = await apiService.getHistoryItem(id);
      setSelectedResult(detail);
    } catch (err: any) {
      alert(err.message || 'Failed to load details.');
    }
  };

  const getScoreBadge = (score: number) => {
    if (score >= 75) return { bg: '#dcfce7', text: '#166534', label: 'Reliable' };
    if (score >= 40) return { bg: '#fef3c7', text: '#92400e', label: 'Mixed' };
    return { bg: '#fee2e2', text: '#991b1b', label: 'Unreliable' };
  };

  return (
    <div className="history-page" style={{ maxWidth: '900px', margin: '2rem auto', padding: '0 1rem' }}>
      <h2 style={{ color: '#1e293b', marginBottom: '1.5rem' }}>Analysis History</h2>

      {selectedResult ? (
        <div>
          <button
            onClick={() => setSelectedResult(null)}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#f1f5f9',
              border: '1px solid #cbd5e1',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              marginBottom: '1rem',
              fontWeight: 500,
            }}
          >
            ← Back to History List
          </button>
          <AnalysisResult result={selectedResult} />
        </div>
      ) : (
        <div>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Loading history...</div>
          ) : error ? (
            <div style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '1rem', borderRadius: '0.5rem' }}>{error}</div>
          ) : items.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', background: 'white', borderRadius: '0.75rem', border: '1px solid #e2e8f0', color: '#64748b' }}>
              No past analyses found. Submit text on the home page to start analyzing articles!
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {items.map((item) => {
                const badge = getScoreBadge(item.authenticityScore);
                return (
                  <div
                    key={item.id}
                    onClick={() => handleSelect(item.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: 'white',
                      padding: '1.25rem',
                      borderRadius: '0.75rem',
                      border: '1px solid #e2e8f0',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div>
                      <h3 style={{ margin: '0 0 0.5rem 0', color: '#1e293b', fontSize: '1.1rem' }}>
                        {item.title || item.sourceUrl || `Analysis #${item.id.slice(0, 8)}`}
                      </h3>
                      <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                        Analyzed on {new Date(item.createdAt).toLocaleDateString()} at {new Date(item.createdAt).toLocaleTimeString()}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <span
                        style={{
                          backgroundColor: badge.bg,
                          color: badge.text,
                          padding: '0.35rem 0.75rem',
                          borderRadius: '1rem',
                          fontWeight: 600,
                          fontSize: '0.875rem',
                        }}
                      >
                        {item.authenticityScore}/100 ({badge.label})
                      </span>
                      <button
                        onClick={(e) => handleDelete(item.id, e)}
                        style={{
                          backgroundColor: 'transparent',
                          border: 'none',
                          color: '#ef4444',
                          cursor: 'pointer',
                          fontWeight: 600,
                          padding: '0.5rem',
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                );
              })}

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1.5rem' }}>
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                    style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1', cursor: page <= 1 ? 'not-allowed' : 'pointer' }}
                  >
                    Previous
                  </button>
                  <span style={{ display: 'flex', alignItems: 'center', padding: '0 0.75rem', color: '#475569' }}>
                    Page {page} of {totalPages}
                  </span>
                  <button
                    disabled={page >= totalPages}
                    onClick={() => setPage(page + 1)}
                    style={{ padding: '0.5rem 1rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1', cursor: page >= totalPages ? 'not-allowed' : 'pointer' }}
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default History;
