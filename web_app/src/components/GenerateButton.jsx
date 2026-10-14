/**
 * GenerateButton Component
 * Main action button for video generation.
 */
import { motion } from 'framer-motion';
import { Play, Loader2 } from 'lucide-react';

export function GenerateButton({ onClick, isGenerating, disabled }) {
    return (
        <div className="pt-8">
            <motion.button
                onClick={onClick}
                disabled={isGenerating || disabled}
                whileHover={{
                    scale: isGenerating ? 1 : 1.02,
                    y: isGenerating ? 0 : -2,
                    boxShadow: "0 10px 40px rgba(168, 85, 247, 0.5)"
                }}
                whileTap={{ scale: isGenerating ? 1 : 0.98 }}
                className={`w-full py-4 rounded-xl font-bold text-sm uppercase tracking-wide relative overflow-hidden shadow-lg transition-all ${isGenerating || disabled ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
            >
                {/* Gradient background */}
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-pink-600 to-cyan-600" />

                {/* Shimmer effect when idle */}
                {!isGenerating && !disabled && (
                    <motion.div
                        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                        initial={{ x: "-100%" }}
                        animate={{ x: "100%" }}
                        transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
                    />
                )}

                {/* Button content */}
                <span className="relative z-10 flex items-center justify-center gap-3">
                    {isGenerating ? (
                        <>
                            <Loader2 className="animate-spin" size={18} />
                            Crafting Masterpiece...
                        </>
                    ) : (
                        <>
                            <Play fill="currentColor" size={18} />
                            Generate Masterpiece
                        </>
                    )}
                </span>
            </motion.button>
        </div>
    );
}

export default GenerateButton;
