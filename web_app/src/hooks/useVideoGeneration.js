/**
 * useVideoGeneration Hook
 * Custom hook for video generation state and logic.
 */
import { useState, useCallback, useRef } from 'react';
import { videoAPI } from '../services/api';

const GENERATION_STEPS = [
    { progress: 10, status: "Initializing AI Core..." },
    { progress: 25, status: "Interpreting prompt with AI..." },
    { progress: 40, status: "Generating cinematic script..." },
    { progress: 55, status: "Creating voice-over..." },
    { progress: 70, status: "Generating visuals..." },
    { progress: 85, status: "Composing video..." },
    { progress: 95, status: "Applying cinematic effects..." }
];

export function useVideoGeneration() {
    const [isGenerating, setIsGenerating] = useState(false);
    const [status, setStatus] = useState("");
    const [progress, setProgress] = useState(0);
    const [videoUrl, setVideoUrl] = useState(null);
    const [error, setError] = useState(null);
    const [apiUsage, setApiUsage] = useState(null);  // API usage tracking

    // Wake Lock Ref - MUST be at top for proper initialization
    const wakeLockRef = useRef(null);

    // Request Wake Lock helper - prevents PC from sleeping
    const requestWakeLock = useCallback(async () => {
        if ('wakeLock' in navigator) {
            try {
                wakeLockRef.current = await navigator.wakeLock.request('screen');
                console.log('🔒 Screen Wake Lock ACTIVATED - PC will not sleep');

                // Re-acquire wake lock if page becomes visible again
                document.addEventListener('visibilitychange', async () => {
                    if (wakeLockRef.current !== null && document.visibilityState === 'visible') {
                        wakeLockRef.current = await navigator.wakeLock.request('screen');
                        console.log('🔒 Wake Lock re-acquired after visibility change');
                    }
                });
            } catch (err) {
                console.error(`Wake Lock error: ${err.name}, ${err.message}`);
            }
        } else {
            console.warn('⚠️ Wake Lock API not supported in this browser');
        }
    }, []);

    // Release wake lock helper
    const releaseWakeLock = useCallback(async () => {
        if (wakeLockRef.current) {
            try {
                await wakeLockRef.current.release();
                wakeLockRef.current = null;
                console.log('🔓 Wake Lock RELEASED - PC can sleep now');
            } catch (e) {
                console.error('Wake Lock release error', e);
            }
        }
    }, []);

    // Simulate progress steps while waiting for backend
    const simulateProgress = useCallback(() => {
        let stepIndex = 0;
        const interval = setInterval(() => {
            if (stepIndex < GENERATION_STEPS.length) {
                const step = GENERATION_STEPS[stepIndex];
                setProgress(step.progress);
                setStatus(step.status);
                stepIndex++;
            }
        }, 3000);
        return interval;
    }, []);

    const generate = useCallback(async (params) => {
        const { topic, language, duration, style } = params;

        if (!topic) {
            setError("Please enter a topic");
            return null;
        }

        setIsGenerating(true);
        setError(null);
        setVideoUrl(null);
        setProgress(5);
        setStatus("Starting generation...");

        // Start progress simulation
        const progressInterval = simulateProgress();

        try {
            console.log("🎬 Generating video (Polling Mode):", params);

            // 1. Start generation (gets job_id)
            const response = await videoAPI.generate({
                topic,
                language,
                duration,
                style
            });

            if (response.status === "queued" || response.status === "processing") {
                const jobId = response.job_id;
                setStatus("Queueing job...");

                // 2. Poll for status
                const pollInterval = setInterval(async () => {
                    try {
                        const statusRes = await fetch(`http://localhost:8000/api/v1/generate/${jobId}`).then(r => r.json());

                        console.log("Job Status:", statusRes);

                        if (statusRes.status === "complete") {
                            clearInterval(pollInterval);
                            clearInterval(progressInterval);
                            setProgress(100);
                            setVideoUrl(`http://localhost:8000${statusRes.video_path}`);
                            setStatus("Masterpiece Complete!");
                            setIsGenerating(false);

                            // Capture API usage
                            if (statusRes.api_usage) {
                                setApiUsage(statusRes.api_usage);
                                console.log('💰 API Usage:', statusRes.api_usage);
                            }
                        } else if (statusRes.status === "failed") {
                            clearInterval(pollInterval);
                            clearInterval(progressInterval);
                            setError(statusRes.error || "Generation failed in background");
                            setStatus(`Error: ${statusRes.error || "Generation failed"}`);
                            setProgress(0);
                            setIsGenerating(false); // Set to false on failure
                        } else {
                            // Update status/progress if available
                            if (statusRes.current_step) setStatus(statusRes.current_step);
                            if (statusRes.progress > progress && statusRes.progress < 100) {
                                setProgress(statusRes.progress);
                            }
                        }
                    } catch (e) {
                        console.error("Polling error:", e);
                        clearInterval(pollInterval);
                        clearInterval(progressInterval);
                        setError(e.message || "Polling failed");
                        setStatus(`Error: ${e.message || "Polling failed"}`);
                        setProgress(0);
                        setIsGenerating(false); // Set to false on polling error
                    }
                }, 2000); // Poll every 2s

            } else if (response.status === "success" && response.video_path) {
                // Legacy/Sync fallback
                clearInterval(progressInterval);
                setProgress(100);
                setVideoUrl(`http://localhost:8000${response.video_path}`);
                setStatus("Masterpiece Complete!");
                setIsGenerating(false); // Set to false for sync completion
            } else {
                throw new Error(response.message || "Generation failed");
            }
        } catch (err) {
            clearInterval(progressInterval);
            console.error("❌ Generation error:", err);
            setError(err.message);
            setStatus(`Error: ${err.message}`);
            setProgress(0);
            setIsGenerating(false);
            return null;
        } finally {
            // Release wake lock when generation completes
            await releaseWakeLock();
        }
    }, [simulateProgress, progress, releaseWakeLock]);

    const reset = useCallback(() => {
        setIsGenerating(false);
        setStatus("");
        setProgress(0);
        setVideoUrl(null);
        setError(null);
    }, []);

    // (wakeLockRef and requestWakeLock moved to top of hook)

    return {
        // State
        isGenerating,
        status,
        progress,
        videoUrl,
        error,
        apiUsage,  // API usage data

        // Actions
        generate: async (params) => {
            await requestWakeLock();
            return generate(params);
        },
        reset,

        // Computed
        isComplete: progress === 100 && videoUrl,
        hasError: !!error
    };
}

export default useVideoGeneration;
