import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Register: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // UI-only state — not sent to API
  const [acknowledged, setAcknowledged] = useState(false);
  const [cipherStrength, setCipherStrength] = useState(0);
  const [cipherLabel, setCipherLabel] = useState<'PENDING' | 'WEAK' | 'ACCEPTABLE' | 'SECURE'>('PENDING');

  const { register, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (!isLoading && isAuthenticated) {
    return null;
  }

  // ── UNCHANGED LOGIC ──────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || !confirmPassword) {
      setError('Please fill in all fields.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    setError(null);
    setSubmitting(true);

    try {
      await register({ email, password, confirmPassword });
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };
  // ── END UNCHANGED LOGIC ───────────────────────────────────────────────

  const handlePasswordChange = (val: string) => {
    setPassword(val);
    if (val.length === 0) {
      setCipherStrength(0);
      setCipherLabel('PENDING');
      return;
    }
    let strength = 0;
    if (val.length > 5) strength += 33;
    if (val.length > 8 && /[A-Z]/.test(val) && /[0-9]/.test(val)) strength += 33;
    if (val.length > 10 && /[^A-Za-z0-9]/.test(val)) strength += 34;
    if (strength === 0 && val.length > 0) strength = 10;
    setCipherStrength(strength);
    if (strength < 40) setCipherLabel('WEAK');
    else if (strength < 80) setCipherLabel('ACCEPTABLE');
    else setCipherLabel('SECURE');
  };

  const today = new Date();
  const dateStr = `${String(today.getDate()).padStart(2, '0')}/${String(today.getMonth() + 1).padStart(2, '0')}/${today.getFullYear()}`;

  const strengthBarColor =
    cipherLabel === 'SECURE' ? '#55785A' :
    cipherLabel === 'ACCEPTABLE' ? '#b87c4c' :
    '#8F302A';

  const strengthTextColor =
    cipherLabel === 'SECURE' ? 'text-verification-green' :
    cipherLabel === 'ACCEPTABLE' ? 'text-[#b87c4c]' :
    cipherLabel === 'PENDING' ? 'text-on-primary-container' :
    'text-ink-red';

  return (
    <div className="min-h-screen flex items-center justify-center p-margin-mobile md:p-margin-desktop relative overflow-hidden bg-lead-charcoal">
      {/* Scanline overlay */}
      <div
        className="fixed inset-0 pointer-events-none z-50"
        style={{
          background: 'linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,0) 50%, rgba(0,0,0,0.05) 50%, rgba(0,0,0,0.05))',
          backgroundSize: '100% 4px',
        }}
      />
      {/* Background grid */}
      <div
        className="absolute inset-0 z-0 pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />

      <main className="w-full max-w-2xl relative z-10">
        {/* Paper card */}
        <article
          className="w-full rounded-sm overflow-hidden border border-outline relative"
          style={{
            backgroundColor: '#E9E4D8',
            color: '#1d1c14',
            boxShadow: '0px 24px 60px rgba(0,0,0,0.5)',
          }}
        >
          {/* Noise texture overlay */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.05'/%3E%3C/svg%3E")`,
              mixBlendMode: 'multiply',
            }}
          />

          {/* Header */}
          <header
            className="p-6 flex justify-between items-start relative"
            style={{ borderBottom: '2px solid #49473f', backgroundColor: '#dfd9cc' }}
          >
            {/* Faux tape corner */}
            <div className="absolute top-0 right-0 w-16 h-16 transform rotate-45 translate-x-8 -translate-y-8 bg-black/5" />
            <div>
              <h1 className="font-headline-lg-mobile md:font-headline-lg text-typewriter-ribbon tracking-tight">
                OPEN INVESTIGATOR FILE
              </h1>
              <p className="font-technical-sm text-on-primary-container mt-2">
                SYS_REQ: Create your DeceptiScan investigation account.
              </p>
            </div>
            <div className="text-right flex items-center gap-4">
              <span className="font-technical-sm tracking-widest" style={{ color: '#ff8c42' }}>SYSTEM ONLINE</span>
              <span className="material-symbols-outlined" style={{ color: '#ff8c42', fontSize: '24px' }}>fingerprint</span>
            </div>
          </header>

          {/* Metadata row */}
          <div className="flex flex-wrap" style={{ borderBottom: '2px solid #49473f' }}>
            <div className="flex-1 min-w-[200px] p-4" style={{ borderRight: '1px solid #49473f' }}>
              <span className="block font-metadata-xs text-on-primary-container mb-1 uppercase">Date Opened</span>
              <span className="block font-technical-sm text-typewriter-ribbon">{dateStr}</span>
            </div>
            <div className="flex-1 min-w-[200px] p-4">
              <span className="block font-metadata-xs text-on-primary-container mb-1 uppercase">Clearance Level</span>
              <span className="block font-technical-sm text-ink-red font-bold">PENDING APPROVAL</span>
            </div>
          </div>

          {/* Form area */}
          <div className="p-6 md:p-8 space-y-8 relative">
            {/* Background UNVERIFIED stamp */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 opacity-10 pointer-events-none z-0">
              <div
                className="font-stamp-lg"
                style={{
                  border: '6px solid #8F302A',
                  color: '#8F302A',
                  transform: 'rotate(-3deg)',
                  display: 'inline-block',
                  padding: '8px 16px',
                  textTransform: 'uppercase',
                  fontSize: '64px',
                }}
              >
                UNVERIFIED
              </div>
            </div>

            {/* Error message */}
            {error && (
              <div className="relative z-10 bg-ink-red/10 border border-ink-red text-ink-red font-technical-sm p-3 rounded-sm">
                {error}
              </div>
            )}

            <form className="space-y-6 relative z-10" onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
                {/* Investigator Name — visual only; not in RegisterRequest */}
                <div className="col-span-1 md:col-span-2">
                  <label
                    className="block font-metadata-xs text-on-primary-container mb-1 uppercase"
                    htmlFor="reg-name"
                  >
                    Investigator Name (Full)
                  </label>
                  <input
                    id="reg-name"
                    name="name"
                    type="text"
                    placeholder="LAST, FIRST M."
                    style={{
                      background: 'transparent',
                      border: 'none',
                      borderBottom: '1px solid #49473f',
                      borderRadius: 0,
                      color: '#1d1c14',
                      fontFamily: "'DM Mono', monospace",
                      padding: '8px 0',
                      width: '100%',
                      outline: 'none',
                    }}
                  />
                </div>

                {/* Email */}
                <div className="col-span-1 md:col-span-2">
                  <label
                    className="block font-metadata-xs text-on-primary-container mb-1 uppercase"
                    htmlFor="reg-email"
                  >
                    Official Comm Link (Email)
                  </label>
                  <input
                    id="reg-email"
                    name="email"
                    type="email"
                    placeholder="operator@department.gov"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      borderBottom: '1px solid #49473f',
                      borderRadius: 0,
                      color: '#1d1c14',
                      fontFamily: "'DM Mono', monospace",
                      padding: '8px 0',
                      width: '100%',
                      outline: 'none',
                    }}
                  />
                </div>

                {/* Password + Cipher Strength */}
                <div className="col-span-1 space-y-1">
                  <label
                    className="block font-metadata-xs text-on-primary-container mb-1 uppercase"
                    htmlFor="reg-password"
                  >
                    Access Cipher (Password)
                  </label>
                  <input
                    id="reg-password"
                    name="password"
                    type="password"
                    placeholder="••••••••"
                    required
                    value={password}
                    onChange={(e) => handlePasswordChange(e.target.value)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      borderBottom: '1px solid #49473f',
                      borderRadius: 0,
                      color: '#1d1c14',
                      fontFamily: "'DM Mono', monospace",
                      padding: '8px 0',
                      width: '100%',
                      outline: 'none',
                    }}
                  />
                  {/* Cipher Strength meter */}
                  <div className="mt-2 flex items-center justify-between gap-2">
                    <span className="font-metadata-xs text-on-primary-container whitespace-nowrap">CIPHER STRENGTH:</span>
                    <div className="flex-1 h-1 relative" style={{ backgroundColor: 'rgba(73,71,63,0.2)' }}>
                      <div
                        className="absolute top-0 left-0 h-full transition-all duration-300"
                        style={{ width: `${cipherStrength}%`, backgroundColor: strengthBarColor }}
                      />
                    </div>
                    <span className={`font-technical-sm whitespace-nowrap ${strengthTextColor}`}>
                      {cipherLabel}
                    </span>
                  </div>
                </div>

                {/* Confirm Password */}
                <div className="col-span-1">
                  <label
                    className="block font-metadata-xs text-on-primary-container mb-1 uppercase"
                    htmlFor="reg-confirm"
                  >
                    Verify Cipher
                  </label>
                  <input
                    id="reg-confirm"
                    name="confirm_password"
                    type="password"
                    placeholder="••••••••"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      borderBottom: '1px solid #49473f',
                      borderRadius: 0,
                      color: '#1d1c14',
                      fontFamily: "'DM Mono', monospace",
                      padding: '8px 0',
                      width: '100%',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              {/* Authorization Checkbox */}
              <div
                className="mt-8 pt-6 flex items-start space-x-3"
                style={{ borderBottom: '1px solid #49473f' }}
              >
                <div className="pt-1">
                  <input
                    id="reg-liability"
                    type="checkbox"
                    checked={acknowledged}
                    onChange={(e) => setAcknowledged(e.target.checked)}
                    className="cursor-pointer focus:ring-0 focus:ring-offset-0 rounded-none"
                    style={{
                      appearance: 'none',
                      width: '16px',
                      height: '16px',
                      border: '1px solid #49473f',
                      background: acknowledged ? '#8F302A' : 'transparent',
                      flexShrink: 0,
                      display: 'inline-block',
                      cursor: 'pointer',
                    }}
                  />
                </div>
                <label className="font-technical-sm text-typewriter-ribbon cursor-pointer select-none" htmlFor="reg-liability">
                  I acknowledge receipt of PROTOCOL_01 and agree to the LIABILITY_WVR. I understand that access to the D1F ARCHIVE is monitored and logged.
                </label>
              </div>

              {/* Form Actions */}
              <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
                <Link
                  to="/login"
                  className="font-label-caps text-on-primary-container hover:text-ink-red transition-colors duration-150 no-underline"
                >
                  RETURN TO LOGIN
                </Link>
                <button
                  type="submit"
                  disabled={submitting || !acknowledged}
                  className="bg-ink-red text-white font-label-caps px-8 py-3 rounded-none hover:bg-secondary-container transition-colors duration-150 flex items-center gap-2 group w-full sm:w-auto justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span>{submitting ? 'FILING...' : 'CREATE FILE'}</span>
                  <span className="material-symbols-outlined text-[18px] group-hover:translate-x-1 transition-transform">
                    arrow_forward
                  </span>
                </button>
              </div>
            </form>
          </div>

          {/* Footer notes */}
          <footer
            className="p-4 flex justify-between items-center text-on-primary-container opacity-70"
            style={{ backgroundColor: '#dfd9cc', borderTop: '1px solid #49473f' }}
          >
            <span className="font-technical-sm">SYS_V: 2.4.1a</span>
            <span className="font-metadata-xs">DO NOT FOLD OR MUTILATE</span>
          </footer>
        </article>
      </main>

      {/* Bottom footer shell */}
      <footer className="fixed bottom-0 left-0 w-full flex justify-between items-center px-margin-desktop py-4 bg-lead-charcoal border-t border-outline-variant z-0">
        <span className="font-technical-sm text-on-surface-variant">©1974 DEPARTMENT OF FAMILY SYSTEMS - CLASSIFIED ARCHIVE</span>
        <div className="hidden md:flex space-x-6">
          <span className="font-technical-sm text-on-surface">DECEPTISCAN // SYS_ONL</span>
        </div>
      </footer>
    </div>
  );
};

export default Register;