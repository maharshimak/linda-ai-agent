/**
 * Selector Components
 * Reusable selection buttons for options.
 */
import { motion } from 'framer-motion';
import { Globe, Clock, Film, Mic } from 'lucide-react';

/**
 * Generic option selector
 */
export function OptionSelector({
    label,
    icon: Icon,
    options,
    value,
    onChange,
    iconColor = "text-purple-400"
}) {
    return (
        <div className="space-y-4 pt-2">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide flex items-center gap-2">
                <Icon size={14} className={iconColor} />
                {label}
            </label>
            <div className="flex flex-wrap gap-2">
                {options.map((option) => (
                    <motion.button
                        key={option.value || option}
                        onClick={() => onChange(option.value || option)}
                        whileHover={{ scale: 1.05, y: -1 }}
                        whileTap={{ scale: 0.95 }}
                        className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${value === (option.value || option)
                                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30'
                                : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white border border-white/10'
                            }`}
                    >
                        {option.label || option}
                    </motion.button>
                ))}
            </div>
        </div>
    );
}

/**
 * Language Selector
 */
export function LanguageSelector({ value, onChange }) {
    const languages = ["English", "French", "Hindi", "Gujarati"];

    return (
        <OptionSelector
            label="Language"
            icon={Globe}
            iconColor="text-cyan-400"
            options={languages}
            value={value}
            onChange={onChange}
        />
    );
}

/**
 * Duration Selector
 */
export function DurationSelector({ value, onChange }) {
    const durations = ["30s", "45s", "60s"];

    return (
        <OptionSelector
            label="Duration"
            icon={Clock}
            iconColor="text-pink-400"
            options={durations}
            value={value}
            onChange={onChange}
        />
    );
}

/**
 * Style Selector
 */
export function StyleSelector({ value, onChange }) {
    const styles = [
        { value: "cinematic", label: "Cinematic" },
        { value: "noir", label: "Noir" },
        { value: "neon", label: "Neon" },
        { value: "minimal", label: "Minimal" }
    ];

    return (
        <OptionSelector
            label="Style"
            icon={Film}
            iconColor="text-purple-400"
            options={styles}
            value={value}
            onChange={onChange}
        />
    );
}

/**
 * Voice Selector
 */
export function VoiceSelector({ value, onChange }) {
    const voices = [
        { value: "nova", label: "Nova" },
        { value: "alloy", label: "Alloy" },
        { value: "echo", label: "Echo" },
        { value: "onyx", label: "Onyx" },
        { value: "shimmer", label: "Shimmer" }
    ];

    return (
        <OptionSelector
            label="Voice"
            icon={Mic}
            iconColor="text-green-400"
            options={voices}
            value={value}
            onChange={onChange}
        />
    );
}

export default {
    OptionSelector,
    LanguageSelector,
    DurationSelector,
    StyleSelector,
    VoiceSelector
};
