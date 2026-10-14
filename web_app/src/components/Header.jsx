/**
 * Header Component
 * Application header with title and branding.
 */
import { motion } from 'framer-motion';

export function Header() {
    return (
        <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-12"
        >
            <h1 className="text-6xl md:text-7xl font-black mb-3 bg-gradient-to-r from-purple-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent tracking-tight">
                MAK AI
            </h1>
            <p className="text-sm text-gray-400 tracking-[0.3em] uppercase font-medium">
                ✨ Premium AI Video Generation
            </p>
        </motion.div>
    );
}

export default Header;

