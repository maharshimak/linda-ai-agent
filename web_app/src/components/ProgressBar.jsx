/**
 * ProgressBar Component
 * Shows generation progress with status text.
 */
import { motion, AnimatePresence } from 'framer-motion';

export function ProgressBar({ isVisible, progress, status }) {
    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-3 mt-6"
                >
                    {/* Status and percentage */}
                    <div className="flex justify-between text-xs font-mono">
                        <span className="text-gray-400">{status}</span>
                        <span className="font-bold text-purple-400">{progress}%</span>
                    </div>

                    {/* Progress bar */}
                    <div className="h-2 bg-black/50 rounded-full overflow-hidden">
                        <motion.div
                            className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-cyan-500"
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            transition={{ duration: 0.5, ease: "easeOut" }}
                        />
                    </div>

                    {/* Stage indicators */}
                    <div className="flex justify-between text-[10px] text-gray-600">
                        <span className={progress >= 10 ? "text-purple-400" : ""}>Script</span>
                        <span className={progress >= 40 ? "text-purple-400" : ""}>Voice</span>
                        <span className={progress >= 60 ? "text-purple-400" : ""}>Visuals</span>
                        <span className={progress >= 85 ? "text-purple-400" : ""}>Compose</span>
                        <span className={progress >= 100 ? "text-cyan-400" : ""}>Done</span>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}

export default ProgressBar;
