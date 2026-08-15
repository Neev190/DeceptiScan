import { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import History from './pages/History';
import About from './pages/About';
import SystemErrorReport from './pages/SystemErrorReport';
import InvestigatorProfile from './pages/InvestigatorProfile';
import AnalysisDetail from './pages/AnalysisDetail';
import { AuthProvider, useAuth } from './context/AuthContext';

const Navbar = () => {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const path = location.pathname;

  const handleLogout = async () => {
    setMobileMenuOpen(false);
    await logout();
    navigate('/');
  };

  return (
    <header className="bg-background dark:bg-background flex flex-col w-full border-b border-outline-variant bg-surface-container-lowest sticky top-0 z-50">
      <div className="flex justify-between items-center w-full px-margin-mobile md:px-margin-desktop py-4 max-w-container-max mx-auto">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            onClick={() => setMobileMenuOpen(false)}
            className="font-headline-lg text-headline-lg text-primary tracking-tighter uppercase no-underline"
          >
            DECEPTISCAN
          </Link>
        </div>
        {/* Desktop Web Nav */}
        <nav className="hidden md:flex gap-8">
          <Link
            to="/"
            className={`font-label-caps text-label-caps uppercase no-underline transition-colors ${path === '/' ? 'text-ink-red dark:text-on-secondary-container border-b-2 border-ink-red pb-1' : 'text-on-surface-variant hover:text-primary'}`}
          >
            Investigate
          </Link>
          <Link
            to="/history"
            className={`font-label-caps text-label-caps uppercase no-underline transition-colors ${path === '/history' ? 'text-ink-red dark:text-on-secondary-container border-b-2 border-ink-red pb-1' : 'text-on-surface-variant hover:text-primary'}`}
          >
            Case Archive
          </Link>
          <Link
            to="/about"
            className={`font-label-caps text-label-caps uppercase no-underline transition-colors ${path === '/about' ? 'text-ink-red dark:text-on-secondary-container border-b-2 border-ink-red pb-1' : 'text-on-surface-variant hover:text-primary'}`}
          >
            About
          </Link>
        </nav>
        <div className="hidden md:flex items-center gap-4">
          <span className="font-technical-sm text-technical-sm text-[#FF8C42] tracking-widest uppercase">SYSTEM ONLINE</span>
          <span className="material-symbols-outlined text-[#FF8C42]" style={{ fontVariationSettings: "'FILL' 0" }}>fingerprint</span>
          {isAuthenticated && (
            <div className="flex items-center gap-4 ml-4">
              <Link
                to="/profile"
                className={`font-label-caps text-label-caps uppercase no-underline transition-colors ${path === '/profile' ? 'text-ink-red dark:text-on-secondary-container border-b-2 border-ink-red pb-1' : 'text-on-surface-variant hover:text-primary'}`}
              >
                PROFILE
              </Link>
              <button
                onClick={handleLogout}
                className="font-label-caps text-label-caps text-on-surface-variant hover:text-primary transition-colors uppercase bg-transparent border-none cursor-pointer"
              >
                LOGOUT
              </button>
            </div>
          )}
          {!isAuthenticated && (
            <Link
              to="/login"
              className="font-label-caps text-label-caps text-on-surface-variant hover:text-primary transition-colors uppercase no-underline ml-4"
            >
              LOGIN
            </Link>
          )}
        </div>

        {/* Mobile Hamburger Button */}
        <div className="flex md:hidden items-center gap-3">
          <button
            id="mobile-menu-toggle"
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-primary hover:text-ink-red transition-colors bg-transparent border border-outline-variant flex items-center justify-center cursor-pointer"
          >
            <span className="material-symbols-outlined text-2xl">
              {mobileMenuOpen ? 'close' : 'menu'}
            </span>
          </button>
        </div>
      </div>

      {/* Mobile Drawer Navigation Menu */}
      {mobileMenuOpen && (
        <div id="mobile-nav-drawer" className="md:hidden w-full bg-carbon-gray border-t border-outline-variant px-margin-mobile py-6 flex flex-col gap-4 shadow-2xl">
          <div className="flex justify-between items-center pb-3 border-b border-outline-variant/50">
            <span className="font-technical-sm text-technical-sm text-[#FF8C42] tracking-widest uppercase flex items-center gap-2">
              <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 0" }}>fingerprint</span>
              SYSTEM ONLINE
            </span>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="font-label-caps text-xs text-on-surface-variant hover:text-primary uppercase bg-transparent border border-outline-variant/40 px-2 py-1 cursor-pointer flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-sm">close</span> CLOSE
            </button>
          </div>

          <nav className="flex flex-col gap-2">
            <Link
              to="/"
              onClick={() => setMobileMenuOpen(false)}
              className={`font-label-caps text-label-caps uppercase no-underline py-2.5 px-3 border border-transparent transition-colors flex items-center justify-between ${path === '/' ? 'text-ink-red bg-surface-container-high/40 border-outline-variant' : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-high/20'}`}
            >
              <span>Investigate</span>
              <span className="material-symbols-outlined text-sm">search</span>
            </Link>
            <Link
              to="/history"
              onClick={() => setMobileMenuOpen(false)}
              className={`font-label-caps text-label-caps uppercase no-underline py-2.5 px-3 border border-transparent transition-colors flex items-center justify-between ${path === '/history' ? 'text-ink-red bg-surface-container-high/40 border-outline-variant' : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-high/20'}`}
            >
              <span>Case Archive</span>
              <span className="material-symbols-outlined text-sm">folder</span>
            </Link>
            <Link
              to="/about"
              onClick={() => setMobileMenuOpen(false)}
              className={`font-label-caps text-label-caps uppercase no-underline py-2.5 px-3 border border-transparent transition-colors flex items-center justify-between ${path === '/about' ? 'text-ink-red bg-surface-container-high/40 border-outline-variant' : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-high/20'}`}
            >
              <span>About</span>
              <span className="material-symbols-outlined text-sm">info</span>
            </Link>

            <div className="h-px bg-outline-variant/50 my-2" />

            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className={`font-label-caps text-label-caps uppercase no-underline py-2.5 px-3 border border-transparent transition-colors flex items-center justify-between ${path === '/profile' ? 'text-ink-red bg-surface-container-high/40 border-outline-variant' : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-high/20'}`}
                >
                  <span>Investigator Profile</span>
                  <span className="material-symbols-outlined text-sm">badge</span>
                </Link>
                <button
                  onClick={handleLogout}
                  className="font-label-caps text-label-caps text-ink-red hover:text-secondary uppercase bg-transparent border border-ink-red/40 py-2.5 px-3 mt-2 transition-colors cursor-pointer text-left flex items-center justify-between"
                >
                  <span>TERMINATE SESSION (LOGOUT)</span>
                  <span className="material-symbols-outlined text-sm">logout</span>
                </button>
              </>
            ) : (
              <div className="flex flex-col gap-2 pt-1">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="bg-ink-red hover:bg-secondary-container text-white font-label-caps text-label-caps py-3 px-4 uppercase text-center no-underline transition-colors flex items-center justify-center gap-2"
                >
                  <span className="material-symbols-outlined text-sm">login</span>
                  <span>LOGIN TO SYSTEM</span>
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="border border-outline-variant text-on-surface-variant hover:text-primary font-label-caps text-label-caps py-2.5 px-4 uppercase text-center no-underline transition-colors"
                >
                  REGISTER AS INVESTIGATOR
                </Link>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  );
};

const Footer = () => (
  <footer className="bg-carbon-gray dark:bg-surface-container-lowest flex flex-col md:flex-row justify-between items-center w-full px-margin-desktop py-8 max-w-container-max mx-auto border-t border-outline-variant mt-12">
    <div className="mb-6 md:mb-0">
      <span className="font-stamp-lg text-stamp-lg text-ink-red opacity-50">DECEPTISCAN</span>
      <p className="font-technical-sm text-technical-sm uppercase tracking-widest text-on-surface-variant mt-2">© 2024 DECEPTISCAN FORENSICS. ALL RIGHTS RESERVED.</p>
    </div>
    <nav className="flex gap-6">
      <span className="font-technical-sm text-technical-sm uppercase tracking-widest text-on-surface-variant/70">EVIDENCE-FIRST</span>
      <span className="font-technical-sm text-technical-sm uppercase tracking-widest text-on-surface-variant/70">LEGAL</span>
      <Link to="/about" className="font-technical-sm text-technical-sm uppercase tracking-widest text-on-surface-variant hover:text-ink-red transition-colors duration-300 no-underline">PROTOCOL</Link>
    </nav>
  </footer>
);

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="bg-background text-on-surface font-body-md antialiased min-h-screen flex flex-col">
          <Navbar />
          <main className="flex-grow flex flex-col items-center w-full">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/history" element={<History />} />
              <Route path="/analysis/:id" element={<AnalysisDetail />} />
              <Route path="/about" element={<About />} />
              <Route path="/profile" element={<InvestigatorProfile />} />
              <Route path="/system-error" element={<SystemErrorReport />} />
              <Route path="*" element={<SystemErrorReport />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;