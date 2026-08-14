import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom';
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
  // Determine active route for nav highlighting
  const path = window.location.pathname;

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <header className="bg-background dark:bg-background flex justify-between items-center w-full px-margin-mobile md:px-margin-desktop py-4 max-w-container-max mx-auto border-b border-outline-variant bg-surface-container-lowest sticky top-0 z-50">
      <div className="flex items-center gap-4">
        <Link to="/" className="font-headline-lg text-headline-lg text-primary tracking-tighter uppercase no-underline">
          DECEPTISCAN
        </Link>
      </div>
      {/* Web Nav */}
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
          className="text-on-surface-variant font-label-caps text-label-caps hover:text-primary transition-colors uppercase no-underline"
        >
          About
        </Link>
      </nav>
      <div className="flex items-center gap-4">
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