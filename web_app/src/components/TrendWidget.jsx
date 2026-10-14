import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { videoAPI } from '../services/api';

const TrendWidget = ({ onSelectTopic }) => {
    const [trends, setTrends] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [niche, setNiche] = useState('technology');

    const niches = [
        { id: 'technology', label: 'Tech & AI', icon: '🤖' },
        { id: 'business', label: 'Business', icon: '💼' },
        { id: 'entertainment', label: 'Pop Culture', icon: '🎬' },
        { id: 'news', label: 'News', icon: '📰' },
        { id: 'science', label: 'Science', icon: '🧬' },
    ];

    useEffect(() => {
        fetchTrends();
    }, [niche]);

    const fetchTrends = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await videoAPI.getTrends(niche);
            setTrends(data.trends || []);
        } catch (err) {
            setError('Failed to load trends');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="trend-widget-glass">
            <div className="trend-header">
                <h3>
                    <span className="fire-icon">🔥</span>
                    Trending Now
                </h3>
                <div className="niche-selector">
                    {niches.map(n => (
                        <button
                            key={n.id}
                            className={`niche-btn ${niche === n.id ? 'active' : ''}`}
                            onClick={() => setNiche(n.id)}
                        >
                            {n.icon} {n.label}
                        </button>
                    ))}
                </div>
            </div>

            <div className="trends-list">
                <AnimatePresence mode="wait">
                    {loading ? (
                        <motion.div
                            className="trends-loading"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            <div className="spinner"></div> Finding viral gold...
                        </motion.div>
                    ) : error ? (
                        <div className="trends-error">{error}</div>
                    ) : (
                        <motion.div
                            className="trends-grid"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                        >
                            {trends.map((trend, i) => (
                                <motion.div
                                    key={i}
                                    className="trend-card"
                                    whileHover={{ scale: 1.02, backgroundColor: 'rgba(139, 92, 246, 0.15)' }}
                                    onClick={() => onSelectTopic(trend.title)}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                >
                                    <div className="trend-score">
                                        <span className="score-val">{trend.score}</span>
                                        <span className="score-label">Viral Score</span>
                                    </div>
                                    <div className="trend-info">
                                        <h4>{trend.title}</h4>
                                        <p>{trend.suggested_angle}</p>
                                    </div>
                                    <button className="use-trend-btn">
                                        Use This 🪄
                                    </button>
                                </motion.div>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <style jsx>{`
        .trend-widget-glass {
          background: rgba(15, 23, 42, 0.6);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 20px;
          padding: 20px;
          margin-top: 30px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .trend-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          flex-wrap: wrap;
          gap: 15px;
        }

        .trend-header h3 {
          margin: 0;
          font-size: 1.2rem;
          color: white;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .fire-icon {
          animation: pulse 2s infinite;
        }

        .niche-selector {
          display: flex;
          gap: 8px;
          overflow-x: auto;
          padding-bottom: 5px;
        }

        .niche-btn {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: rgba(255, 255, 255, 0.7);
          padding: 6px 12px;
          border-radius: 20px;
          cursor: pointer;
          font-size: 0.85rem;
          transition: all 0.2s;
          white-space: nowrap;
        }

        .niche-btn:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }

        .niche-btn.active {
          background: rgba(139, 92, 246, 0.2);
          border-color: rgba(139, 92, 246, 0.5);
          color: #ddd6fe;
        }

        .trends-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 15px;
        }

        .trend-card {
          display: flex;
          align-items: center;
          gap: 15px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.05);
          padding: 15px;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .trend-score {
          display: flex;
          flex-direction: column;
          align-items: center;
          background: rgba(16, 185, 129, 0.1);
          padding: 8px;
          border-radius: 8px;
          border: 1px solid rgba(16, 185, 129, 0.2);
          min-width: 60px;
        }

        .score-val {
          font-weight: bold;
          color: #34d399;
          font-size: 1.1rem;
        }

        .score-label {
          font-size: 0.6rem;
          color: rgba(255, 255, 255, 0.5);
          text-transform: uppercase;
        }

        .trend-info {
          flex: 1;
        }

        .trend-info h4 {
          margin: 0 0 4px 0;
          color: white;
          font-size: 0.95rem;
          line-height: 1.3;
        }

        .trend-info p {
          margin: 0;
          color: rgba(255, 255, 255, 0.5);
          font-size: 0.8rem;
        }

        .use-trend-btn {
          background: rgba(255, 255, 255, 0.1);
          border: none;
          color: white;
          width: 30px;
          height: 30px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s;
        }

        .trend-card:hover .use-trend-btn {
          background: #8b5cf6;
          transform: scale(1.1);
        }

        .trends-loading {
          text-align: center;
          padding: 40px;
          color: rgba(255, 255, 255, 0.5);
        }

        @keyframes pulse {
          0% { opacity: 0.6; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.1); }
          100% { opacity: 0.6; transform: scale(1); }
        }
      `}</style>
        </div>
    );
};

export default TrendWidget;
