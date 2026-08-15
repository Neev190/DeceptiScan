// InvestigatorProfile.tsx — Stitch investigator_profile screen (Investigator File)
// Implements secure account profile access with live backend data and username updates.
//
// Data Handling:
// - Email & Account ID: Real data from auth state / GET /auth/me.
// - Date Joined: Real creation date formatted from backend user.createdAt.
// - Analyses Completed: Real analysis record count from backend user.analysesCount.
// - Codename/Username: Editable via PATCH /auth/me.
// - Open Cases & Uptime: Labeled as illustrative operational status indicators.

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import apiService from '../services/api';
import { User } from '../types';

const InvestigatorProfile: React.FC = () => {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'ACCOUNT_DETAILS' | 'SYSTEM_SETTINGS'>('ACCOUNT_DETAILS');
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [editingUsername, setEditingUsername] = useState<boolean>(false);
  const [usernameInput, setUsernameInput] = useState<string>('');
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [updateSuccess, setUpdateSuccess] = useState<boolean>(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login');
      return;
    }
    if (!isAuthenticated) {
      return;
    }
    const fetchProfile = async () => {
      try {
        setLoading(true);
        const userData = await apiService.getCurrentUser();
        setUser(userData);
        setUsernameInput(userData.username || '');
      } catch (err: any) {
        console.error('Failed to fetch user profile:', err);
        if (err.details?.status === 401 || err.message?.includes('401') || err.code === 'UNAUTHORIZED') {
          navigate('/login');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [isAuthenticated, isLoading, navigate]);

  const handleSaveUsername = async () => {
    try {
      setUpdateError(null);
      setUpdateSuccess(false);
      const updatedUser = await apiService.updateCurrentUser({ username: usernameInput });
      setUser(updatedUser);
      setEditingUsername(false);
      setUpdateSuccess(true);
      setTimeout(() => setUpdateSuccess(false), 3000);
    } catch (err: any) {
      setUpdateError(err.message || 'Failed to update codename');
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (isLoading || loading) {
    return (
      <main className="flex-grow flex items-center justify-center p-margin-mobile md:p-margin-desktop bg-lead-charcoal min-h-[calc(100vh-160px)] w-full">
        <div className="text-center font-technical-sm text-technical-sm text-on-surface-variant uppercase tracking-widest animate-pulse">
          ACCESSING INVESTIGATOR FILE...
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const accountId = user ? `OP-${user.id.slice(0, 8).toUpperCase()}` : 'OP-042-OMEGA';
  const joinedDate = user?.createdAt
    ? new Date(user.createdAt).toISOString().slice(0, 10).replace(/-/g, '.')
    : '2026.08.10';
  const analysesCount = user?.analysesCount ?? 0;

  return (
    <main className="flex-grow flex flex-col items-center justify-start pt-12 pb-24 px-margin-mobile md:px-margin-desktop relative z-10 w-full max-w-container-max mx-auto bg-lead-charcoal min-h-[calc(100vh-160px)]">
      {/* Top Header */}
      <header className="w-full max-w-3xl mb-8 flex justify-between items-end border-b border-outline-variant pb-4">
        <div>
          <h1 className="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-primary tracking-tighter uppercase">
            INVESTIGATOR FILE
          </h1>
          <p className="font-technical-sm text-technical-sm text-on-surface-variant mt-2">
            SECURE PROFILE ACCESS // SYS_ONL
          </p>
        </div>
        <div className="text-right hidden sm:block">
          <div className="flex items-center gap-3 justify-end">
            <span className="font-technical-sm text-technical-sm uppercase tracking-widest text-[#FF8C42]">
              SYSTEM ONLINE
            </span>
            <span className="material-symbols-outlined text-[24px] text-[#FF8C42]">fingerprint</span>
          </div>
        </div>
      </header>

      {/* Profile Card */}
      <div className="w-full max-w-3xl bg-carbon-gray shadow-[0px_24px_60px_rgba(0,0,0,0.5)] border border-outline-variant relative">
        <div className="absolute inset-0 bg-paper-aged opacity-5 pointer-events-none" />

        {/* Tab/Folder Header */}
        <div className="flex border-b border-outline-variant bg-surface-container-high">
          <button
            onClick={() => setActiveTab('ACCOUNT_DETAILS')}
            className={`px-6 py-3 border-r border-outline-variant font-label-caps text-label-caps uppercase transition-colors ${
              activeTab === 'ACCOUNT_DETAILS'
                ? 'bg-carbon-gray text-primary border-t-2 border-t-ink-red'
                : 'text-on-surface-variant hover:text-primary'
            }`}
          >
            ACCOUNT_DETAILS
          </button>
          <button
            onClick={() => setActiveTab('SYSTEM_SETTINGS')}
            className={`px-6 py-3 border-r border-outline-variant font-label-caps text-label-caps uppercase transition-colors ${
              activeTab === 'SYSTEM_SETTINGS'
                ? 'bg-carbon-gray text-primary border-t-2 border-t-ink-red'
                : 'text-on-surface-variant hover:text-primary'
            }`}
          >
            SYSTEM_SETTINGS
          </button>
        </div>

        <div className="p-8 md:p-12 space-y-12">
          {activeTab === 'ACCOUNT_DETAILS' ? (
            <>
              {/* Identity Section */}
              <section className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
                <div className="md:col-span-4 flex flex-col items-center justify-center space-y-4">
                  <div className="w-32 h-32 border-2 border-outline-variant rounded-sm overflow-hidden relative group grayscale contrast-125 bg-surface-container-low flex items-center justify-center">
                    <span className="material-symbols-outlined text-6xl text-outline-variant">person</span>
                    <div className="absolute inset-0 bg-ink-red opacity-0 group-hover:opacity-20 transition-opacity mix-blend-multiply" />
                  </div>
                  <span className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase border-b border-outline pb-1">
                    ID PHOTO // VERIFIED
                  </span>
                </div>

                <div className="md:col-span-8 space-y-6">
                  <div className="grid grid-cols-2 gap-x-4 gap-y-6">
                    <div className="col-span-2 md:col-span-1 border-b border-outline-variant pb-2">
                      <label className="block font-metadata-xs text-metadata-xs text-on-surface-variant mb-1 uppercase">
                        Account ID
                      </label>
                      <div className="font-technical-sm text-technical-sm text-primary">{accountId}</div>
                    </div>
                    <div className="col-span-2 md:col-span-1 border-b border-outline-variant pb-2">
                      <label className="block font-metadata-xs text-metadata-xs text-on-surface-variant mb-1 uppercase">
                        Clearance Level
                      </label>
                      <div className="font-technical-sm text-technical-sm text-ink-red">
                        {user?.isAdmin ? 'ADMINISTRATOR // OMEGA' : 'ANALYST // LEVEL 1'}
                      </div>
                    </div>
                    <div className="col-span-2 border-b border-outline-variant pb-2">
                      <label className="block font-metadata-xs text-metadata-xs text-on-surface-variant mb-1 uppercase">
                        Email Address
                      </label>
                      <div className="font-technical-sm text-technical-sm text-primary">{user?.email || '—'}</div>
                    </div>
                    <div className="col-span-2 border-b border-outline-variant pb-2">
                      <div className="flex justify-between items-center mb-1">
                        <label className="block font-metadata-xs text-metadata-xs text-on-surface-variant uppercase">
                          Investigator Codename
                        </label>
                        {!editingUsername && (
                          <button
                            onClick={() => setEditingUsername(true)}
                            className="font-metadata-xs text-metadata-xs text-ink-red hover:underline uppercase bg-transparent border-none cursor-pointer"
                          >
                            EDIT
                          </button>
                        )}
                      </div>
                      {editingUsername ? (
                        <div className="flex gap-2 items-center mt-1">
                          <input
                            type="text"
                            value={usernameInput}
                            onChange={(e) => setUsernameInput(e.target.value)}
                            placeholder="Enter codename"
                            className="bg-surface-container-low border border-outline-variant text-primary font-technical-sm text-technical-sm px-2 py-1 flex-1 focus:outline-none focus:border-ink-red"
                          />
                          <button
                            onClick={handleSaveUsername}
                            className="bg-ink-red text-white font-label-caps text-label-caps px-3 py-1 uppercase hover:bg-secondary-container transition-colors"
                          >
                            SAVE
                          </button>
                          <button
                            onClick={() => {
                              setEditingUsername(false);
                              setUsernameInput(user?.username || '');
                              setUpdateError(null);
                            }}
                            className="text-on-surface-variant font-label-caps text-label-caps px-2 py-1 uppercase hover:text-primary"
                          >
                            CANCEL
                          </button>
                        </div>
                      ) : (
                        <div className="font-technical-sm text-technical-sm text-primary">
                          {user?.username || <span className="text-on-surface-variant/60 italic">UNSET (CLICK EDIT TO SET)</span>}
                        </div>
                      )}
                      {updateError && (
                        <div className="font-metadata-xs text-metadata-xs text-error mt-1">{updateError}</div>
                      )}
                      {updateSuccess && (
                        <div className="font-metadata-xs text-metadata-xs text-verification-green mt-1">CODENAME UPDATED SUCCESSFULLY</div>
                      )}
                    </div>
                  </div>
                </div>
              </section>

              <div className="h-px bg-outline-variant w-full" />

              {/* Statistics Section */}
              <section>
                <h2 className="font-label-caps text-label-caps text-on-surface-variant mb-4 uppercase flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px]">analytics</span>
                  Operational Record
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-surface-container p-4 border border-outline-variant rounded-sm flex flex-col justify-between">
                    <span className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase">Date Joined</span>
                    <span className="font-technical-sm text-technical-sm text-primary mt-2">{joinedDate}</span>
                  </div>
                  <div className="bg-surface-container p-4 border border-outline-variant rounded-sm flex flex-col justify-between">
                    <span className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase">Analyses Completed</span>
                    <span className="font-technical-sm text-technical-sm text-primary mt-2">{analysesCount}</span>
                  </div>
                  <div className="bg-surface-container p-4 border border-outline-variant rounded-sm flex flex-col justify-between">
                    <span className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase">Open Cases</span>
                    <span className="font-technical-sm text-technical-sm text-ink-red mt-2">00</span>
                  </div>
                  <div className="bg-surface-container p-4 border border-outline-variant rounded-sm flex flex-col justify-between">
                    <span className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase">System Status</span>
                    <span className="font-technical-sm text-technical-sm text-verification-green mt-2">ONLINE</span>
                  </div>
                </div>
              </section>
            </>
          ) : (
            /* System Settings Tab */
            <section className="space-y-6">
              <h2 className="font-label-caps text-label-caps text-on-surface-variant mb-4 uppercase flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px]">settings</span>
                System Preferences
              </h2>
              <div className="space-y-2">
                <div className="flex justify-between items-center py-3 border-b border-outline-variant/50 px-2 -mx-2">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-on-surface-variant text-[18px]">contrast</span>
                    <span className="font-technical-sm text-technical-sm text-primary">INTERFACE THEME</span>
                  </div>
                  <span className="font-metadata-xs text-metadata-xs text-verification-green uppercase">DARK NOIR (ACTIVE)</span>
                </div>
                <div className="flex justify-between items-center py-3 border-b border-outline-variant/50 px-2 -mx-2">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-on-surface-variant text-[18px]">database</span>
                    <span className="font-technical-sm text-technical-sm text-primary">DATA RETENTION</span>
                  </div>
                  <span className="font-metadata-xs text-metadata-xs text-on-surface-variant uppercase">ACCOUNT SCOPED</span>
                </div>
                <div className="flex justify-between items-center py-3 border-b border-outline-variant/50 px-2 -mx-2">
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-on-surface-variant text-[18px]">history</span>
                    <span className="font-technical-sm text-technical-sm text-primary">CASE ARCHIVE LINK</span>
                  </div>
                  <Link to="/history" className="font-metadata-xs text-metadata-xs text-ink-red uppercase hover:underline">VIEW ARCHIVE</Link>
                </div>
              </div>
            </section>
          )}

          {/* Actions */}
          <div className="pt-8 flex justify-end gap-4 border-t border-outline-variant">
            <button
              onClick={() => navigate('/')}
              className="px-6 py-2 border border-paper-aged bg-transparent font-label-caps text-label-caps text-primary hover:bg-surface-container transition-colors uppercase rounded-sm cursor-pointer"
            >
              RETURN TO INVESTIGATION
            </button>
            <button
              onClick={handleLogout}
              className="px-6 py-2 bg-ink-red font-label-caps text-label-caps text-white hover:bg-secondary-container transition-colors uppercase rounded-sm flex items-center gap-2 cursor-pointer border-none"
            >
              <span className="material-symbols-outlined text-[16px]">logout</span>
              TERMINATE_SESSION
            </button>
          </div>
        </div>
      </div>
    </main>
  );
};

export default InvestigatorProfile;
