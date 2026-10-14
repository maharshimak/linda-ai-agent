/**
 * VideoPreview Component
 * Video player and download options.
 */
import { motion } from 'framer-motion';
import { Play, Download, Video, CheckCircle2 } from 'lucide-react';

export function VideoPreview({ videoUrl }) {
    return (
        <div className="space-y-6">
            {/* Section Header */}
            <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Video size={16} className="text-purple-400" />
                Preview
            </h3>

            {videoUrl ? (
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="relative group"
                >
                    {/* Video Container */}
                    <div className="relative rounded-xl overflow-hidden border border-white/10 shadow-xl">
                        <video
                            src={videoUrl}
                            controls
                            className="w-full"
                            autoPlay
                        />

                        {/* Download Button Overlay */}
                        <motion.a
                            href={videoUrl}
                            download
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            className="absolute top-3 right-3 p-2 bg-black/80 hover:bg-purple-600 rounded-full opacity-0 group-hover:opacity-100 transition-all"
                        >
                            <Download size={16} />
                        </motion.a>
                    </div>

                    {/* Download Actions */}
                    <div className="flex gap-2 mt-4">
                        <motion.a
                            href={videoUrl}
                            download
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className="flex-1 py-2 px-4 bg-purple-600/20 border border-purple-500/30 rounded-lg text-xs font-semibold text-purple-300 hover:border-purple-500/50 transition-all flex items-center justify-center gap-2"
                        >
                            <Download size={14} />
                            Download MP4
                        </motion.a>
                    </div>
                </motion.div>
            ) : (
                <div className="aspect-video bg-black/30 border border-white/10 rounded-xl flex flex-col items-center justify-center relative overflow-hidden p-8">
                    {/* Background gradient */}
                    <div className="absolute inset-0 bg-gradient-to-br from-purple-600/10 to-cyan-600/10" />

                    {/* Placeholder content */}
                    <Play size={48} className="text-white/20 mb-3" strokeWidth={1.5} />
                    <p className="text-xs text-gray-500">Your video will appear here</p>
                </div>
            )}

            {/* Quality Guarantees */}
            <div className="bg-black/20 border border-white/10 rounded-xl p-5 space-y-3">
                <h4 className="text-sm font-bold text-white">Quality Guarantees</h4>
                <div className="space-y-2 text-xs text-gray-400">
                    <div className="flex items-start gap-2">
                        <CheckCircle2 size={14} className="text-green-400 flex-shrink-0 mt-0.5" />
                        <span>AI Creative Intelligence with emotion-driven styling</span>
                    </div>
                    <div className="flex items-start gap-2">
                        <CheckCircle2 size={14} className="text-green-400 flex-shrink-0 mt-0.5" />
                        <span>Human-like narration with natural pacing</span>
                    </div>
                    <div className="flex items-start gap-2">
                        <CheckCircle2 size={14} className="text-green-400 flex-shrink-0 mt-0.5" />
                        <span>Cinematic camera movements and effects</span>
                    </div>
                    <div className="flex items-start gap-2">
                        <CheckCircle2 size={14} className="text-green-400 flex-shrink-0 mt-0.5" />
                        <span>Zero watermarks, production-grade output</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default VideoPreview;
