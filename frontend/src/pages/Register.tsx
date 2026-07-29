import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { ApiError } from '../types';

function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const navigate = useNavigate();

  const validateForm = (): boolean => {
    if (!email.trim() || !password.trim() || !confirmPassword.trim()) {
      setError({ code: 'INVALID_INPUT', message: 'Please fill in all fields' });
      return false;
    }

    if (password !== confirmPassword) {
      setError({ code: 'INVALID_INPUT', message: 'Passwords do not match' });
      return false;
    }

    if (password.length < 6) {
      setError({ code: 'INVALID_INPUT', message: 'Password must be at least 6 characters long' });
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError({ code: 'INVALID_INPUT', message: 'Please enter a valid email address' });
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await apiService.register({ 
        email: email.trim(), 
        password, 
        confirmPassword 
      });
      navigate('/'); // Redirect to home after successful registration
    } catch (error: any) {
      setError(error as ApiError);
    } finally {
      setIsLoading(false);
    }
  };

  const getPasswordStrength = (password: string): string => {
    if (password.length === 0) return '';
    if (password.length < 6) return 'Weak';
    if (password.length < 10) return 'Medium';
    return 'Strong';
  };

  const passwordStrength = getPasswordStrength(password);

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <Link to="/" className="brand-link">
            <h1>DeceptiScan</h1>
          </Link>
          <h2>Create Account</h2>
          <p>Join DeceptiScan to save your analysis history and get enhanced features.</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-alert">
              <p>{error.message}</p>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              disabled={isLoading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Create a strong password"
              disabled={isLoading}
              required
            />
            {password && (
              <div className={`password-strength ${passwordStrength.toLowerCase()}`}>
                Strength: {passwordStrength}
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              disabled={isLoading}
              required
            />
            {confirmPassword && password !== confirmPassword && (
              <div className="validation-error">
                Passwords do not match
              </div>
            )}
          </div>

          <button 
            type="submit" 
            className="auth-submit"
            disabled={isLoading}
          >
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account? 
            <Link to="/login" className="auth-link"> Sign in here</Link>
          </p>
          <div className="terms-notice">
            <p>
              By creating an account, you agree to our terms of service and privacy policy.
            </p>
          </div>
        </div>
      </div>

      <style>{`
        .auth-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
          padding: 1rem;
        }

        .auth-container {
          background: white;
          padding: 2.5rem;
          border-radius: 1rem;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
          width: 100%;
          max-width: 400px;
          border: 1px solid #e2e8f0;
        }

        .auth-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .brand-link {
          text-decoration: none;
          color: inherit;
        }

        .brand-link h1 {
          margin: 0 0 1rem 0;
          background: linear-gradient(135deg, var(--primary-color), #1d4ed8);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          font-size: 2rem;
          font-weight: 800;
        }

        .auth-header h2 {
          margin: 0 0 0.5rem 0;
          color: #1e293b;
          font-size: 1.5rem;
        }

        .auth-header p {
          margin: 0;
          color: #64748b;
          font-size: 0.875rem;
        }

        .auth-form {
          margin-bottom: 1.5rem;
        }

        .form-group {
          margin-bottom: 1.25rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 600;
          color: #1e293b;
          font-size: 0.875rem;
        }

        .form-group input {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #e2e8f0;
          border-radius: 0.5rem;
          font-size: 1rem;
          transition: border-color 0.2s, box-shadow 0.2s;
        }

        .form-group input:focus {
          outline: none;
          border-color: var(--primary-color);
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .form-group input:disabled {
          background-color: #f8fafc;
          opacity: 0.6;
        }

        .password-strength {
          font-size: 0.75rem;
          margin-top: 0.25rem;
          font-weight: 500;
        }

        .password-strength.weak {
          color: #ef4444;
        }

        .password-strength.medium {
          color: #f59e0b;
        }

        .password-strength.strong {
          color: #22c55e;
        }

        .validation-error {
          color: #ef4444;
          font-size: 0.75rem;
          margin-top: 0.25rem;
        }

        .error-alert {
          background-color: #fee2e2;
          color: #dc2626;
          padding: 0.75rem;
          border-radius: 0.5rem;
          margin-bottom: 1rem;
          text-align: center;
          border: 1px solid #fecaca;
        }

        .error-alert p {
          margin: 0;
          font-size: 0.875rem;
        }

        .auth-submit {
          width: 100%;
          background: var(--primary-color);
          color: white;
          border: none;
          padding: 0.875rem;
          border-radius: 0.5rem;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .auth-submit:hover:not(:disabled) {
          background: #1d4ed8;
        }

        .auth-submit:disabled {
          background: #94a3b8;
          cursor: not-allowed;
        }

        .auth-footer {
          text-align: center;
        }

        .auth-footer p {
          margin: 0 0 1rem 0;
          color: #64748b;
          font-size: 0.875rem;
        }

        .terms-notice {
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }

        .terms-notice p {
          color: #94a3b8;
          font-size: 0.75rem;
          line-height: 1.4;
        }

        .auth-link {
          color: var(--primary-color);
          text-decoration: none;
          font-weight: 600;
        }

        .auth-link:hover {
          text-decoration: underline;
        }
      `}</style>
    </div>
  );
}

export default Register;