/**
 * Admin Dashboard
 * Analytics, user management, and video history for admins
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { adminAPI } from '../services/api';

const Icon = {
    Users: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></svg>,
    Video: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="m10 9 5 3-5 3V9z" /></svg>,
    Chart: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18" /><path d="m19 9-5 5-4-4-3 3" /></svg>,
    Dollar: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>,
    Back: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" /></svg>,
    Refresh: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" /></svg>,
};

export default function AdminDashboard() {
    const { user, isAdmin } = useAuth();
    const navigate = useNavigate();
    const [analytics, setAnalytics] = useState(null);
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [userDetails, setUserDetails] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        if (!isAdmin) {
            navigate('/');
            return;
        }
        loadData();
    }, [isAdmin, navigate]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [analyticsData, usersData] = await Promise.all([
                adminAPI.getAnalytics(),
                adminAPI.getUsers()
            ]);
            setAnalytics(analyticsData);
            setUsers(usersData);
        } catch (error) {
            console.error('Failed to load admin data:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadUserDetails = async (userId) => {
        try {
            const details = await adminAPI.getUserDetails(userId);
            setUserDetails(details);
            setSelectedUser(userId);
        } catch (error) {
            console.error('Failed to load user details:', error);
        }
    };

    if (!isAdmin) return null;

    return (
        <div className="admin-page">
            <header className="admin-header">
                <button className="admin-back-btn" onClick={() => navigate('/')}>
                    <Icon.Back />
                    Back to Generator
                </button>
                <h1>Admin Dashboard</h1>
                <button className="admin-refresh-btn" onClick={loadData}>
                    <Icon.Refresh />
                    Refresh
                </button>
            </header>

            {loading ? (
                <div className="admin-loading">
                    <div className="spinner" />
                    <p>Loading dashboard...</p>
                </div>
            ) : (
                <>
                    {/* Stats Cards */}
                    <div className="admin-stats">
                        <motion.div
                            className="stat-card stat-users"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                        >
                            <div className="stat-icon"><Icon.Users /></div>
                            <div className="stat-info">
                                <span className="stat-value">{analytics?.total_users || 0}</span>
                                <span className="stat-label">Total Users</span>
                            </div>
                        </motion.div>

                        <motion.div
                            className="stat-card stat-videos"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            <div className="stat-icon"><Icon.Video /></div>
                            <div className="stat-info">
                                <span className="stat-value">{analytics?.total_videos || 0}</span>
                                <span className="stat-label">Total Videos</span>
                            </div>
                        </motion.div>

                        <motion.div
                            className="stat-card stat-today"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                        >
                            <div className="stat-icon"><Icon.Chart /></div>
                            <div className="stat-info">
                                <span className="stat-value">{analytics?.videos_today || 0}</span>
                                <span className="stat-label">Videos Today</span>
                            </div>
                        </motion.div>

                        <motion.div
                            className="stat-card stat-cost"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                        >
                            <div className="stat-icon"><Icon.Dollar /></div>
                            <div className="stat-info">
                                <span className="stat-value">${analytics?.total_api_cost?.toFixed(2) || '0.00'}</span>
                                <span className="stat-label">Total API Cost</span>
                            </div>
                        </motion.div>
                    </div>

                    {/* Tabs */}
                    <div className="admin-tabs">
                        <button
                            className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
                            onClick={() => setActiveTab('overview')}
                        >
                            Recent Activity
                        </button>
                        <button
                            className={`tab ${activeTab === 'users' ? 'active' : ''}`}
                            onClick={() => { setActiveTab('users'); setSelectedUser(null); }}
                        >
                            All Users
                        </button>
                    </div>

                    {/* Content */}
                    <div className="admin-content">
                        <AnimatePresence mode="wait">
                            {activeTab === 'overview' && (
                                <motion.div
                                    key="overview"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="admin-table-container"
                                >
                                    <h2>Recent Video Generations</h2>
                                    <table className="admin-table">
                                        <thead>
                                            <tr>
                                                <th>User</th>
                                                <th>Topic</th>
                                                <th>Style</th>
                                                <th>Status</th>
                                                <th>Cost</th>
                                                <th>Date</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {analytics?.recent_videos?.map((video) => (
                                                <tr key={video.id}>
                                                    <td className="user-cell">{video.user_email}</td>
                                                    <td className="topic-cell" title={video.topic}>{video.topic}</td>
                                                    <td>{video.style}</td>
                                                    <td><span className={`status-badge status-${video.status}`}>{video.status}</span></td>
                                                    <td>${video.api_cost_usd?.toFixed(4) || '0.0000'}</td>
                                                    <td>{new Date(video.created_at).toLocaleString()}</td>
                                                </tr>
                                            ))}
                                            {(!analytics?.recent_videos || analytics.recent_videos.length === 0) && (
                                                <tr><td colSpan="6" className="empty-row">No videos generated yet</td></tr>
                                            )}
                                        </tbody>
                                    </table>
                                </motion.div>
                            )}

                            {activeTab === 'users' && !selectedUser && (
                                <motion.div
                                    key="users"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="admin-table-container"
                                >
                                    <h2>All Users ({users.length})</h2>
                                    <table className="admin-table">
                                        <thead>
                                            <tr>
                                                <th>Email</th>
                                                <th>Role</th>
                                                <th>Total Videos</th>
                                                <th>Videos Today</th>
                                                <th>Joined</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {users.map((u) => (
                                                <tr key={u.id}>
                                                    <td>{u.email}</td>
                                                    <td><span className={`role-badge ${u.is_admin ? 'admin' : 'user'}`}>{u.is_admin ? 'Admin' : 'User'}</span></td>
                                                    <td>{u.total_videos}</td>
                                                    <td>{u.videos_today}</td>
                                                    <td>{new Date(u.created_at).toLocaleDateString()}</td>
                                                    <td>
                                                        <button className="view-btn" onClick={() => loadUserDetails(u.id)}>
                                                            View Details
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </motion.div>
                            )}

                            {activeTab === 'users' && selectedUser && userDetails && (
                                <motion.div
                                    key="user-details"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="admin-table-container"
                                >
                                    <button className="back-link" onClick={() => { setSelectedUser(null); setUserDetails(null); }}>
                                        ← Back to Users
                                    </button>
                                    <h2>User: {userDetails.user.email}</h2>
                                    <div className="user-meta">
                                        <span>Role: <strong>{userDetails.user.is_admin ? 'Admin' : 'User'}</strong></span>
                                        <span>Joined: <strong>{new Date(userDetails.user.created_at).toLocaleDateString()}</strong></span>
                                        <span>Total Videos: <strong>{userDetails.videos.length}</strong></span>
                                    </div>

                                    <h3>Video History</h3>
                                    <table className="admin-table">
                                        <thead>
                                            <tr>
                                                <th>Topic</th>
                                                <th>Style</th>
                                                <th>Status</th>
                                                <th>Cost</th>
                                                <th>Date</th>
                                                <th>Video</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {userDetails.videos.map((video) => (
                                                <tr key={video.id}>
                                                    <td className="topic-cell" title={video.topic}>{video.topic}</td>
                                                    <td>{video.style}</td>
                                                    <td><span className={`status-badge status-${video.status}`}>{video.status}</span></td>
                                                    <td>${video.api_cost_usd?.toFixed(4) || '0.0000'}</td>
                                                    <td>{new Date(video.created_at).toLocaleString()}</td>
                                                    <td>
                                                        {video.video_path ? (
                                                            <a href={`http://localhost:8000${video.video_path}`} target="_blank" rel="noopener noreferrer" className="video-link">
                                                                Watch
                                                            </a>
                                                        ) : '-'}
                                                    </td>
                                                </tr>
                                            ))}
                                            {userDetails.videos.length === 0 && (
                                                <tr><td colSpan="6" className="empty-row">No videos generated</td></tr>
                                            )}
                                        </tbody>
                                    </table>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </>
            )}
        </div>
    );
}
