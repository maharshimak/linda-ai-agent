/**
 * Login Page
 * Premium glassmorphism design with animations
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await login(email, password);
            navigate('/');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-bg">
                <div className="auth-orb auth-orb-1" />
                <div className="auth-orb auth-orb-2" />
                <div className="auth-orb auth-orb-3" />
            </div>

            <motion.div
                className="auth-card"
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
            >
                <div className="auth-logo">
                    <div className="auth-logo-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="brain-pulse">
                            <path d="M12 2a4 4 0 0 0-4 4c0 .26.02.51.07.75A3.5 3.5 0 0 0 5 10c0 .87.32 1.67.85 2.28A3.5 3.5 0 0 0 5 15c0 1.13.53 2.13 1.36 2.77A3 3 0 0 0 9 22h6a3 3 0 0 0 2.64-4.23A3.5 3.5 0 0 0 19 15c0-.97-.39-1.85-1.03-2.48A3.5 3.5 0 0 0 19 10a3.5 3.5 0 0 0-3.07-3.25c.05-.24.07-.49.07-.75a4 4 0 0 0-4-4z" />
                            <circle cx="9" cy="10" r="1" fill="currentColor" />
                            <circle cx="15" cy="10" r="1" fill="currentColor" />
                            <circle cx="9" cy="15" r="1" fill="currentColor" />
                            <circle cx="15" cy="15" r="1" fill="currentColor" />
                        </svg>
                        <span className="auth-sparkle">✨</span>
                    </div>
                    <span>Mak AI</span>
                </div>

                <h1 className="auth-title">Welcome Back</h1>
                <p className="auth-subtitle">Sign in to continue creating amazing videos</p>

                {error && (
                    <motion.div
                        className="auth-error"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                    >
                        {error}
                    </motion.div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="auth-field">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="user-97af051a@example.test"
                            required
                            autoComplete="email"
                        />
                    </div>

                    <div className="auth-field">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            autoComplete="current-password"
                        />
                    </div>

                    <motion.button
                        type="submit"
                        className="auth-btn"
                        disabled={loading}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                    >
                        {loading ? (
                            <span className="auth-btn-loading">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="spin">
                                    <path d="M21 12a9 9 0 1 1-6.2-8.5" />
                                </svg>
                                Signing in...
                            </span>
                        ) : (
                            'Sign In'
                        )}
                    </motion.button>
                </form>

                <p className="auth-footer">
                    Don't have an account?{' '}
                    <Link to="/signup" className="auth-link">Create one</Link>
                </p>
            </motion.div>
        </div>
    );
}
