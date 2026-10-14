import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "./context/AuthContext";
import { videoAPI } from "./services/api";
import TrendWidget from "./components/TrendWidget";

// Floating Particles Component
const FloatingParticles = () => {
  const particles = Array.from({ length: 50 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 4 + 1,
    duration: Math.random() * 20 + 10,
    delay: Math.random() * 5,
  }));

  return (
    <div className="particles-container">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="particle"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
          }}
          animate={{
            y: [0, -30, 0],
            x: [0, Math.random() * 20 - 10, 0],
            opacity: [0.2, 0.8, 0.2],
            scale: [1, 1.5, 1],
          }}
          transition={{
            duration: p.duration,
            repeat: Infinity,
            delay: p.delay,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
};

// Animated Orbs Background
const AnimatedOrbs = () => (
  <div className="orbs-container">
    <motion.div
      className="orb orb-1"
      animate={{
        x: [0, 100, -50, 0],
        y: [0, -80, 60, 0],
        scale: [1, 1.3, 0.9, 1],
      }}
      transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
    />
    <motion.div
      className="orb orb-2"
      animate={{
        x: [0, -80, 40, 0],
        y: [0, 60, -40, 0],
        scale: [1, 0.8, 1.2, 1],
      }}
      transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
    />
  </div>
);

// Simple Clean Logo
const SimpleLogo = () => (
  <div className="simple-logo">
    <span className="logo-text">Mak</span>
    <span className="logo-accent">AI</span>
  </div>
);

const Icon = {
  Play: () => <svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21" /></svg>,
  Loader: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="spin"><path d="M21 12a9 9 0 1 1-6.2-8.5" /></svg>,
  Check: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>,
  Download: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" /></svg>,
  Video: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="m10 9 5 3-5 3V9z" /></svg>,
  Logout: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" /></svg>,
  Shield: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>,
  User: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>,
  Wand: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="m15 4-3 3m0 0-7 7a2.83 2.83 0 1 0 4 4l7-7m-4-4 3-3m0 0 2-2m-2 2-2 2m4 4 2-2m-2 2 2-2" /><path d="m21 3-1 1" /><path d="m19 5 1-1" /><path d="m21 7-1-1" /><path d="m17 3 1 1" /></svg>,
  Stars: () => <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.4H22l-6 4.6 2.3 7-6.3-4.6L5.7 21l2.3-7-6-4.6h7.6z" /></svg>,
  Magic: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 12L18 12" /><path d="M6 12L10 8" /><path d="M6 12L10 16" /><circle cx="12" cy="12" r="10" /></svg>,
};

export default function App() {
  // Magic Mode is DEFAULT
  const [isMagicMode, setIsMagicMode] = useState(true);

  const [topic, setTopic] = useState("");
  const [language, setLanguage] = useState("English");
  const [duration, setDuration] = useState("30s");
  const [style, setStyle] = useState("Cinematic");
  const [voice, setVoice] = useState("nova");
  const [videoType, setVideoType] = useState("General");
  const [enableCaptions, setEnableCaptions] = useState(true);
  const [enableStockFootage, setEnableStockFootage] = useState(false);
  const [enableMusic, setEnableMusic] = useState(true);
  const [jobId, setJobId] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState(0);
  const [videoUrl, setVideoUrl] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const [apiUsage, setApiUsage] = useState(null);
  const [error, setError] = useState(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const { user, isAdmin, videosRemaining, logout, refreshUserInfo } = useAuth();
  const navigate = useNavigate();
  const containerRef = useRef(null);

  // Mouse tracking for parallax
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setMousePosition({
          x: (e.clientX - rect.left - rect.width / 2) / 50,
          y: (e.clientY - rect.top - rect.height / 2) / 50,
        });
      }
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  // Poll job status
  useEffect(() => {
    if (!jobId || isComplete) return;

    const interval = setInterval(async () => {
      try {
        const job = await videoAPI.getJobStatus(jobId);
        setStatus(job.current_step);
        setProgress(job.progress);

        if (job.status === "complete") {
          setIsComplete(true);
          setIsGenerating(false);
          setVideoUrl(`${import.meta.env.PROD ? '' : 'http://localhost:8000'}${job.video_path}`);
          setApiUsage(job.api_usage);
          refreshUserInfo();
          clearInterval(interval);
        } else if (job.status === "failed") {
          setIsGenerating(false);
          setError(job.error || "Generation failed");
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Failed to get job status:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId, isComplete, refreshUserInfo]);

  const handleGenerate = async () => {
    if (!topic.trim()) return;

    setError(null);
    setIsGenerating(true);
    setIsComplete(false);
    setVideoUrl(null);
    setApiUsage(null);
    setProgress(0);
    setStatus("Starting magic engine...");

    try {
      if (isMagicMode) {
        // MAGIC MODE: Only usage topic
        const result = await videoAPI.magicGenerate(topic);
        setJobId(result.job_id);
      } else {
        // MANUAL MODE: All parameters
        const result = await videoAPI.generate({
          topic, language, duration, style, voice, videoType,
          enableCaptions, enableMusic, enableStockFootage
        });
        setJobId(result.job_id);
      }
    } catch (err) {
      setError(err.message);
      setIsGenerating(false);
    }
  };

  const handleTrendSelect = (selectedTopic) => {
    setTopic(selectedTopic);
    // Smooth scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Format time util
  const formatTime = (seconds) => {
    if (seconds === null) return "--:--";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="app-spectacular" ref={containerRef}>
      {/* Animated Background */}
      <FloatingParticles />
      <AnimatedOrbs />

      {/* Aurora Effect */}
      <div className="aurora">
        <div className="aurora-1"></div>
        <div className="aurora-2"></div>
        <div className="aurora-3"></div>
      </div>

      {/* Grid Lines */}
      <div className="grid-overlay"></div>

      <div className="container-spectacular">
        {/* Header */}
        <motion.header
          className="header-spectacular"
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="header-top-spectacular">
            <div className="brand-spectacular">
              <SimpleLogo />
            </div>

            <div className="user-menu-spectacular">
              {isAdmin && (
                <motion.button
                  className="admin-btn-spectacular"
                  onClick={() => navigate('/admin')}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Icon.Shield />
                  <span>Admin</span>
                </motion.button>
              )}
              <div className="user-info-spectacular">
                <span className="user-email">{user?.email}</span>
                {!isAdmin && (
                  <motion.span className="quota-spectacular">
                    {videosRemaining}/2
                  </motion.span>
                )}
              </div>
              <motion.button
                className="logout-btn-spectacular"
                onClick={handleLogout}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <Icon.Logout />
              </motion.button>
            </div>
          </div>

          <motion.div
            className="hero-spectacular"
            style={{
              transform: `translate(${mousePosition.x}px, ${mousePosition.y}px)`,
            }}
          >
            <h1 className="hero-title">
              <span className="hero-word">Create</span>
              <span className="hero-word-highlight">Viral</span>
              <span className="hero-word">Videos</span>
            </h1>
            <p className="hero-subtitle">
              Idea to Reality in 60 Seconds
            </p>
          </motion.div>
        </motion.header>

        {/* Main Card */}
        <motion.div
          className="main-card-spectacular"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
        >
          <div className="card-glow"></div>
          <div className="card-body-spectacular">
            {/* Left Panel */}
            <div className="panel-spectacular panel-left-spectacular">

              {/* Magic Mode Toggle */}
              <div className="mode-toggle-container">
                <button
                  className={`mode-btn ${isMagicMode ? 'active magic' : ''}`}
                  onClick={() => setIsMagicMode(true)}
                >
                  <span>🪄 Magic Mode</span>
                </button>
                <button
                  className={`mode-btn ${!isMagicMode ? 'active manual' : ''}`}
                  onClick={() => setIsMagicMode(false)}
                >
                  <span>⚙️ Manual</span>
                </button>
              </div>

              <motion.div className="section-spectacular">
                <div className="label-spectacular">
                  <Icon.Wand />
                  <span>{isMagicMode ? "What should we create?" : "Describe your video"}</span>
                </div>
                <motion.textarea
                  className="textarea-spectacular"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder={isMagicMode ? "e.g. The history of coffee, Quantum physics explained..." : "Enter detailed script or topic..."}
                  whileFocus={{
                    boxShadow: "0 0 40px rgba(139,92,246,0.4)",
                  }}
                />
              </motion.div>

              {/* Advanced Controls - HIDDEN in Magic Mode */}
              <AnimatePresence>
                {!isMagicMode && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    style={{ overflow: 'hidden' }}
                  >
                    <div className="options-grid">
                      <div className="option-col">
                        <label>Style</label>
                        <select value={style} onChange={(e) => setStyle(e.target.value)}>
                          {["Cinematic", "Documentary", "Minimal", "Epic", "Neon"].map(s =>
                            <option key={s} value={s}>{s}</option>
                          )}
                        </select>
                      </div>
                      <div className="option-col">
                        <label>Duration</label>
                        <select value={duration} onChange={(e) => setDuration(e.target.value)}>
                          {["30s", "45s", "60s"].map(d =>
                            <option key={d} value={d}>{d}</option>
                          )}
                        </select>
                      </div>
                      <div className="option-col">
                        <label>Voice</label>
                        <select value={voice} onChange={(e) => setVoice(e.target.value)}>
                          {["nova", "alloy", "echo", "fable", "onyx", "shimmer"].map(v =>
                            <option key={v} value={v}>{v}</option>
                          )}
                        </select>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {error && (
                <div className="error-spectacular">
                  ⚠️ {error}
                </div>
              )}

              <motion.button
                className="generate-btn-spectacular"
                onClick={handleGenerate}
                disabled={isGenerating || !topic.trim() || (!isAdmin && videosRemaining <= 0)}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
              >
                <div className="btn-bg" />
                <span className="btn-content">
                  {isGenerating ? (
                    <>
                      <Icon.Loader />
                      <span>{isMagicMode ? "Working Magic..." : "Generating..."}</span>
                    </>
                  ) : (
                    <>
                      <Icon.Stars />
                      <span>{isMagicMode ? "Create Magic Video" : "Generate Video"}</span>
                    </>
                  )}
                </span>
              </motion.button>

              {/* Trend Widget Integration */}
              <TrendWidget onSelectTopic={handleTrendSelect} />

            </div>

            {/* Right Panel - Preview */}
            <div className="panel-spectacular panel-right-spectacular">
              <div className="preview-label-spectacular">
                <span>📺</span>
                <span>Preview</span>
              </div>

              <div className="preview-box-spectacular">
                {videoUrl ? (
                  <video src={videoUrl} controls autoPlay width="100%" height="100%" />
                ) : (
                  <div className="preview-placeholder-spectacular">
                    {isGenerating ? (
                      <div className="generating-animation">
                        <div className="loader"></div>
                      </div>
                    ) : (
                      <div className="idle-content">
                        <Icon.Video />
                        <p>Your masterpiece awaits</p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {videoUrl && (
                <button
                  className="download-btn-spectacular"
                  onClick={() => window.open(videoUrl, '_blank')}
                >
                  <Icon.Download /> Download
                </button>
              )}
            </div>
          </div>
        </motion.div>
      </div>

      <style jsx>{`
        .mode-toggle-container {
          display: flex;
          background: rgba(0,0,0,0.3);
          padding: 5px;
          border-radius: 12px;
          margin-bottom: 20px;
        }
        .mode-btn {
          flex: 1;
          background: transparent;
          border: none;
          color: rgba(255,255,255,0.6);
          padding: 10px;
          cursor: pointer;
          border-radius: 8px;
          transition: all 0.3s;
          font-weight: 600;
        }
        .mode-btn.active {
          color: white;
          box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .mode-btn.active.magic {
          background: linear-gradient(135deg, #8b5cf6, #ec4899);
        }
        .mode-btn.active.manual {
          background: rgba(255,255,255,0.1);
        }
        .options-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
          margin-bottom: 20px;
          padding: 15px;
          background: rgba(255,255,255,0.03);
          border-radius: 12px;
        }
        .option-col label {
          display: block;
          color: rgba(255,255,255,0.5);
          font-size: 0.8rem;
          margin-bottom: 5px;
        }
        .option-col select {
          width: 100%;
          background: rgba(0,0,0,0.4);
          border: 1px solid rgba(255,255,255,0.1);
          color: white;
          padding: 8px;
          border-radius: 6px;
        }
        .loader {
            width: 48px;
            height: 48px;
            border: 5px solid #FFF;
            border-bottom-color: #FF3D00;
            border-radius: 50%;
            display: inline-block;
            box-sizing: border-box;
            animation: rotation 1s linear infinite;
        }
        @keyframes rotation {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .idle-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            opacity: 0.5;
        }
      `}</style>
    </div>
  );
}
