/**
 * StatusMessage Component
 * Shows success or error status messages.
 */
import { motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, XCircle } from 'lucide-react';

export function StatusMessage({ status, isSuccess, isError }) {
    if (!status) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex items-center gap-2 p-3 rounded-lg border ${isSuccess
                    ? 'bg-green-500/10 border-green-500/30'
                    : isError
                        ? 'bg-red-500/10 border-red-500/30'
                        : 'bg-black/30 border-white/10'
                }`}
        >
            {isSuccess ? (
                <>
                    <CheckCircle2 size={16} className="text-green-400" />
                    <span className="text-xs font-semibold text-green-400">{status}</span>
                </>
            ) : isError ? (
                <>
                    <XCircle size={16} className="text-red-400" />
                    <span className="text-xs font-semibold text-red-400">{status}</span>
                </>
            ) : (
                <>
                    <AlertCircle size={16} className="text-yellow-400" />
                    <span className="text-xs font-semibold text-yellow-400">{status}</span>
                </>
            )}
        </motion.div>
    );
}

export default StatusMessage;
