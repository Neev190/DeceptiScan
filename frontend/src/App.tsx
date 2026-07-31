import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import History from './pages/History';
import { AuthProvider, useAuth } from './context/AuthContext';

const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <nav style={{ background: '#1e293b', color: 'white', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <Link to="/" style={{ color: 'white', textDecoration: 'none', fontSize: '1.25rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        🔍 DeceptiScan
      </Link>
      <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
        <Link to="/" style={{ color: '#cbd5e1', textDecoration: 'none', fontWeight: 500 }}>Analyze</Link>
        {isAuthenticated ? (
          <>
            <Link to="/history" style={{ color: '#cbd5e1', textDecoration: 'none', fontWeight: 500 }}>History</Link>
            <span style={{ fontSize: '0.875rem', color: '#94a3b8' }}>{user?.email}</span>
            <button
              onClick={handleLogout}
              style={{ background: '#334155', color: 'white', border: 'none', padding: '0.4rem 0.8rem', borderRadius: '0.375rem', cursor: 'pointer', fontWeight: 500 }}
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" style={{ color: '#cbd5e1', textDecoration: 'none', fontWeight: 500 }}>Login</Link>
            <Link
              to="/register"
              style={{ background: '#2563eb', color: 'white', textDecoration: 'none', padding: '0.4rem 0.8rem', borderRadius: '0.375rem', fontWeight: 500 }}
            >
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
          <Navbar />
          <main style={{ paddingBottom: '3rem' }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/history" element={<History />} />
            </Routes>
          </main>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;