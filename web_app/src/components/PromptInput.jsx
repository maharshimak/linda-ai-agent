/**
 * PromptInput Component
 * Text input for video topic/script with enhance button.
 */
import { Sparkles, Wand2 } from 'lucide-react';
import { motion } from 'framer-motion';

export function PromptInput({ value, onChange, onEnhance }) {
    return (
        <div className="space-y-4">
            {/* Section Header */}
            <div className="pt-5">
                <h2 className="text-2xl font-bold text-white mb-3 flex items-center gap-2">
                    <Sparkles className="text-purple-400" size={20} />
                    Your Vision
                </h2>
                <p className="text-sm text-gray-400 leading-relaxed">
                    Describe your video concept and let AI bring it to life with cinematic intelligence.
                </p>
            </div>

            {/* Textarea */}
            <textarea
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="Example: A journey through the cosmos, exploring distant galaxies and nebulae with epic orchestral music..."
                className="w-full h-36 bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder:text-gray-600 focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 outline-none resize-none transition-all"
            />

            {/* Enhance Button */}
            <div className="pt-2">
                <motion.button
                    onClick={onEnhance}
                    whileHover={{ scale: 1.02, boxShadow: "0 0 20px rgba(168, 85, 247, 0.3)" }}
                    whileTap={{ scale: 0.98 }}
                    className="px-4 py-2 bg-purple-600/20 border border-purple-500/30 rounded-lg text-xs font-semibold text-purple-300 hover:border-purple-500/50 transition-all flex items-center gap-2"
                >
                    <Wand2 size={14} />
                    Enhance with AI
                </motion.button>
            </div>
        </div>
    );
}

export default PromptInput;
