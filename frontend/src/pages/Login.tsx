// Login page — Stitch investigator_login design
// Logic (useState, handleSubmit, useAuth, useNavigate) is UNCHANGED.
// Only JSX markup is rewrapped to match the Stitch design system.

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Login: React.FC = () => {
  // ── UNCHANGED STATE & HANDLERS ──────────────────────────────────────────
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { login, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (!isLoading && isAuthenticated) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }
    setError(null);
    setSubmitting(true);

    try {
      await login({ email, password });
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };
  // ── END UNCHANGED LOGIC ─────────────────────────────────────────────────

  return (
    <div className="flex-grow flex items-center justify-center w-full px-margin-mobile md:px-margin-desktop py-12 relative">
      {/* Grid overlay */}
      <div className="absolute inset-0 grid-overlay z-0 pointer-events-none"></div>

      {/* Login card */}
      <div className="w-full max-w-md bg-paper-aged text-typewriter-ribbon relative shadow-[0px_24px_60px_rgba(0,0,0,0.5)] rounded-sm overflow-hidden z-10">
        {/* Noise texture */}
        <div className="absolute inset-0 noise-texture"></div>

        <div className="p-8 relative z-10">
          {/* Header */}
          <div className="mb-10 border-b-2 border-outline-variant pb-6">
            <h1 className="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-typewriter-ribbon mb-2 uppercase tracking-tighter">
              Deceptiscan
              <span className="block text-xl">Information Forensics</span>
            </h1>
            <h2 className="font-technical-sm text-technical-sm tracking-widest text-on-primary-fixed-variant">ACCESS INVESTIGATION DESK</h2>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-ink-red/10 border border-ink-red text-ink-red font-technical-sm text-technical-sm p-3 mb-6 rounded-sm">
              {error}
            </div>
          )}

          {/* Form */}
          <form className="space-y-8" onSubmit={handleSubmit}>
            <div>
              <label className="block font-label-caps text-label-caps text-on-primary-fixed-variant mb-2 uppercase" htmlFor="identifier">
                Identifier [OP-ID]
              </label>
              <input
                className="w-full bg-transparent border-0 border-b border-outline-variant focus:ring-0 focus:border-ink-red font-technical-sm text-technical-sm text-typewriter-ribbon px-0 py-2 rounded-none placeholder-outline outline-none"
                id="identifier"
                name="identifier"
                placeholder="Enter Operator ID (email)"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={submitting}
                required
              />
            </div>
            <div>
              <label className="block font-label-caps text-label-caps text-on-primary-fixed-variant mb-2 uppercase" htmlFor="password">
                Passphrase
              </label>
              <input
                className="w-full bg-transparent border-0 border-b border-outline-variant focus:ring-0 focus:border-ink-red font-technical-sm text-technical-sm text-typewriter-ribbon px-0 py-2 rounded-none placeholder-outline outline-none"
                id="password"
                name="password"
                placeholder="Enter Passphrase"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={submitting}
                required
              />
            </div>
            <div className="pt-4">
              <button
                className="w-full bg-ink-red text-primary font-label-caps text-label-caps py-4 rounded-sm hover:bg-secondary-container transition-colors uppercase tracking-widest flex items-center justify-center gap-2 group"
                type="submit"
                disabled={submitting}
              >
                <span>{submitting ? 'Authenticating...' : 'Access Desk'}</span>
                <span className="material-symbols-outlined text-[16px] group-hover:translate-x-1 transition-transform">login</span>
              </button>
            </div>
          </form>

          {/* Footer */}
          <div className="mt-12 pt-6 border-t border-outline-variant flex justify-between items-center text-on-primary-fixed-variant">
            <div className="font-metadata-xs text-metadata-xs uppercase">
              Auth Level: <span className="text-typewriter-ribbon">Standard</span>
            </div>
            <div className="flex items-center gap-2 font-technical-sm text-technical-sm tracking-widest" style={{ color: 'rgb(255, 140, 66)' }}>
              <span>SYSTEM ONLINE</span>
              <span className="material-symbols-outlined text-[20px]">fingerprint</span>
            </div>
          </div>
          <p className="mt-4 font-metadata-xs text-metadata-xs text-on-primary-fixed-variant text-center">
            No account? <Link to="/register" className="text-ink-red hover:underline font-bold">Register as Investigator</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;