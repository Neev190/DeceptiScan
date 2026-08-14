// History page — Stitch case_archive design
// Logic (useState, fetchHistory, handleDelete, handleSelect, getScoreBadge) is UNCHANGED.
// Only JSX markup is rewrapped to match the Stitch design system.

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import apiService from '../services/api';
import { AnalysisHistoryItem } from '../types';

const History: React.FC = () => {
  // ── UNCHANGED STATE & HANDLERS ──────────────────────────────────────────
  const [items, setItems] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isUnauthenticated, setIsUnauthenticated] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);

  const fetchHistory = async (p: number) => {
    setLoading(true);
    setError(null);
    setIsUnauthenticated(false);
    try {
      const res = await apiService.getAnalysisHistory(p, 10);
      setItems(res.data || []);
      setPage(res.pagination?.page || p);
      setTotalPages(res.pagination?.totalPages || 1);
    } catch (err: any) {
      if (err.details?.status === 401 || err.message?.includes('401') || err.code === 'UNAUTHORIZED') {
        setIsUnauthenticated(true);
      } else {
        setError(err.message || 'Failed to fetch analysis history.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(page);
  }, [page]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault(); // Prevent navigation when deleting
    if (!window.confirm('Are you sure you want to delete this analysis record?')) {
      return;
    }
    try {
      await apiService.deleteAnalysis(id);
      fetchHistory(page);
    } catch (err: any) {
      alert(err.message || 'Failed to delete record.');
    }
  };

  // Legacy badge logic kept for reference — Stitch uses Tailwind classes instead
  void ((score: number) => score >= 75 ? { bg: '#dcfce7', text: '#166534', label: 'Reliable' } : score >= 40 ? { bg: '#fef3c7', text: '#92400e', label: 'Mixed' } : { bg: '#fee2e2', text: '#991b1b', label: 'Unreliable' });
  // ── END UNCHANGED LOGIC ─────────────────────────────────────────────────

  // Determine Tailwind badge classes from score
  const getStatusClasses = (score: number) => {
    if (score >= 75) return 'bg-verification-green/20 text-verification-green border border-verification-green/30';
    if (score >= 40) return 'bg-outline-variant/30 text-surface-tint border border-outline-variant';
    return 'bg-secondary-container/20 text-secondary border border-secondary-container/30';
  };

  const getStatusLabel = (score: number) => {
    if (score >= 75) return 'RELIABLE';
    if (score >= 40) return 'MIXED';
    return 'UNRELIABLE';
  };

  const getScoreColorClass = (score: number) => {
    if (score >= 75) return 'text-verification-green';
    if (score >= 40) return 'text-surface-tint';
    return 'text-secondary';
  };

  return (
    <div className="w-full max-w-container-max px-margin-mobile md:px-margin-desktop py-12 mx-auto flex flex-col">
      {/* ── Header ── */}
      <header className="flex flex-col md:flex-row md:justify-between md:items-end mb-10 pb-6 border-b-2 border-outline-variant gap-6">
            <div>
              <p className="font-technical-sm text-technical-sm text-on-surface-variant mb-2">FILE SYSTEM / ARCHIVE / INDEX</p>
              <h1 className="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-primary tracking-tight">CASE ARCHIVE</h1>
            </div>
            <button
              className="text-primary px-6 py-3 font-label-caps text-label-caps uppercase tracking-widest hover:bg-secondary-container transition-colors rounded-none flex items-center gap-2 w-fit bg-ink-red"
              onClick={() => window.location.href = '/'}
            >
              <span className="material-symbols-outlined text-sm">add</span>
              NEW INVESTIGATION
            </button>
          </header>

          {/* ── Archive List Container ── */}
          <div className="bg-carbon-gray shadow-[0px_24px_60px_rgba(0,0,0,0.5)] p-6 md:p-8 flex-grow relative overflow-hidden">
            {/* Table Header */}
            <div className="grid grid-cols-12 gap-4 pb-4 border-b border-outline-variant font-technical-sm text-technical-sm text-on-surface-variant uppercase tracking-widest mb-4 sticky top-0 bg-carbon-gray z-20 pt-2">
              <div className="col-span-2 md:col-span-2 pl-2">Case ID</div>
              <div className="col-span-6 md:col-span-5">Subject</div>
              <div className="hidden md:block md:col-span-2 text-center">Status</div>
              <div className="hidden md:block md:col-span-1 text-right">Score</div>
              <div className="col-span-4 md:col-span-2 text-right pr-2">Date</div>
            </div>

            {/* List Items */}
            <div className="flex flex-col gap-2 relative z-10">
              {loading ? (
                <div className="py-16 text-center font-technical-sm text-technical-sm text-on-surface-variant uppercase opacity-60">
                  <span className="animate-pulse">Loading archive...</span>
                </div>
              ) : isUnauthenticated ? (
                <div className="py-16 text-center">
                  <div className="border border-outline-variant p-8 mx-auto max-w-md bg-lead-charcoal/50">
                    <span className="material-symbols-outlined text-[48px] text-ink-red opacity-80 block mb-4">lock</span>
                    <h2 className="font-headline-lg-mobile text-[24px] text-primary mb-2 uppercase tracking-tight">Authentication Required</h2>
                    <p className="font-technical-sm text-technical-sm text-on-surface-variant opacity-70 mb-6 uppercase tracking-wider">
                      Please log in to access your confidential case archive and past investigation records.
                    </p>
                    <button
                      onClick={() => window.location.href = '/login'}
                      className="bg-ink-red hover:bg-secondary-container text-primary font-label-caps text-label-caps px-6 py-3 uppercase tracking-widest transition-colors flex items-center gap-2 mx-auto rounded-sm cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[16px]">login</span>
                      LOG IN TO CONTINUE
                    </button>
                  </div>
                </div>
              ) : error ? (
                <div className="py-8 border border-ink-red bg-ink-red/10 p-4 font-technical-sm text-technical-sm text-ink-red">
                  {error}
                </div>
              ) : items.length === 0 ? (
                <div className="py-16 text-center">
                  <div className="border border-outline-variant p-8 mx-auto max-w-md">
                    <span className="material-symbols-outlined text-[48px] text-on-surface-variant opacity-30 block mb-4">folder_off</span>
                    <h2 className="font-headline-lg-mobile text-[24px] text-primary mb-2 uppercase">Archive Empty</h2>
                    <p className="font-technical-sm text-technical-sm text-on-surface-variant opacity-70 mb-6">
                      No past analyses found. Submit text on the investigation desk to start building your case archive.
                    </p>
                    <button
                      onClick={() => window.location.href = '/'}
                      className="bg-ink-red hover:bg-secondary-container text-primary font-label-caps text-label-caps px-6 py-3 uppercase tracking-widest transition-colors flex items-center gap-2 mx-auto rounded-sm"
                    >
                      <span className="material-symbols-outlined text-[16px]">add</span>
                      OPEN NEW CASE
                    </button>
                  </div>
                </div>
              ) : (
                items.map((item) => {
                  const caseId = `CASE ${item.id.slice(0, 4).toUpperCase()}`;
                  const subject = item.title || item.sourceUrl || `Analysis #${item.id.slice(0, 8)}`;
                  const rawDate = item.created_at || item.createdAt;
                  const parsedDate = rawDate ? new Date(rawDate) : null;
                  const dateStr = parsedDate && !isNaN(parsedDate.getTime()) ? parsedDate.toISOString().split('T')[0] : '—';

                  return (
                    <Link
                      to={`/analysis/${item.id}`}
                      key={item.id}
                      className="grid grid-cols-12 gap-4 items-center py-4 px-2 hover:bg-surface-variant/30 transition-colors border-b border-surface-container-high group cursor-pointer relative no-underline text-inherit"
                    >
                      <div className="col-span-2 md:col-span-2 font-technical-sm text-technical-sm text-on-surface">{caseId}</div>
                      <div className="col-span-6 md:col-span-5 font-headline-lg-mobile text-lg md:text-xl text-primary group-hover:text-secondary transition-colors truncate">
                        {subject}
                      </div>
                      <div className="hidden md:flex md:col-span-2 justify-center">
                        <span className={`font-label-caps text-label-caps px-2 py-1 ${getStatusClasses(item.authenticityScore)}`}>
                          {getStatusLabel(item.authenticityScore)}
                        </span>
                      </div>
                      <div className={`hidden md:block md:col-span-1 font-technical-sm text-technical-sm text-right ${getScoreColorClass(item.authenticityScore)}`}>
                        {item.authenticityScore}/100
                      </div>
                      <div className="col-span-4 md:col-span-2 font-technical-sm text-technical-sm text-right text-on-surface-variant flex items-center justify-end gap-3">
                        <span>{dateStr}</span>
                        <button
                          onClick={(e) => handleDelete(item.id, e)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity font-metadata-xs text-metadata-xs text-ink-red hover:text-secondary uppercase bg-transparent border-none cursor-pointer"
                        >
                          DELETE
                        </button>
                      </div>
                    </Link>
                  );
                })
              )}
            </div>

            {/* Pagination */}
            {!loading && !error && totalPages > 1 && (
              <div className="mt-8 pt-4 border-t border-outline-variant flex justify-between items-center text-on-surface-variant font-technical-sm text-technical-sm">
                <span>SHOWING PAGE {page} OF {totalPages}</span>
                <div className="flex gap-4">
                  <button
                    className="hover:text-primary transition-colors disabled:opacity-50 flex items-center"
                    disabled={page <= 1}
                    onClick={() => setPage(page - 1)}
                  >
                    <span className="material-symbols-outlined text-sm">chevron_left</span> PREV
                  </button>
                  <button
                    className="hover:text-primary transition-colors disabled:opacity-50 flex items-center"
                    disabled={page >= totalPages}
                    onClick={() => setPage(page + 1)}
                  >
                    NEXT <span className="material-symbols-outlined text-sm">chevron_right</span>
                  </button>
                </div>
              </div>
            )}
          </div>
    </div>
  );
};

export default History;
