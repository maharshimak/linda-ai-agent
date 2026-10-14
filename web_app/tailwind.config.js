/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                glass: "rgba(255, 255, 255, 0.05)",
                neon: {
                    blue: "#00f3ff",
                    purple: "#bc13fe",
                    pink: "#ff0055",
                    cyan: "#06f6ff"
                },
                primary: {
                    DEFAULT: "rgb(168, 85, 247)",
                    50: "rgba(168, 85, 247, 0.05)",
                    100: "rgba(168, 85, 247, 0.1)",
                    200: "rgba(168, 85, 247, 0.2)",
                    500: "rgb(168, 85, 247)",
                    600: "rgb(147, 51, 234)",
                },
                secondary: {
                    DEFAULT: "rgb(236, 72, 153)",
                    500: "rgb(236, 72, 153)",
                },
                accent: {
                    DEFAULT: "rgb(6, 182, 212)",
                    500: "rgb(6, 182, 212)",
                }
            },
            backdropBlur: {
                xs: '2px',
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                display: ['Space Grotesk', 'Inter', 'sans-serif'],
            },
            animation: {
                'shimmer': 'shimmer 3s infinite',
                'float': 'float 6s ease-in-out infinite',
                'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
                'gradient-shift': 'gradient-shift 4s ease infinite',
                'morph': 'morph 15s ease-in-out infinite',
            },
            keyframes: {
                shimmer: {
                    '100%': { transform: 'translateX(100%)' },
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                'pulse-glow': {
                    '0%, 100%': { boxShadow: '0 0 20px rgba(168, 85, 247, 0.3)' },
                    '50%': { boxShadow: '0 0 40px rgba(168, 85, 247, 0.6), 0 0 60px rgba(6, 182, 212, 0.3)' },
                },
                'gradient-shift': {
                    '0%': { backgroundPosition: '0% 50%' },
                    '50%': { backgroundPosition: '100% 50%' },
                    '100%': { backgroundPosition: '0% 50%' },
                },
                morph: {
                    '0%, 100%': { borderRadius: '40% 60% 70% 30% / 40% 50% 60% 50%' },
                    '25%': { borderRadius: '70% 30% 50% 50% / 30% 30% 70% 70%' },
                    '50%': { borderRadius: '50% 60% 30% 60% / 70% 40% 70% 40%' },
                    '75%': { borderRadius: '30% 50% 70% 40% / 50% 60% 30% 60%' },
                },
            },
            boxShadow: {
                'glow-purple': '0 0 40px rgba(168, 85, 247, 0.4)',
                'glow-pink': '0 0 40px rgba(236, 72, 153, 0.3)',
                'glow-cyan': '0 0 40px rgba(6, 182, 212, 0.4)',
                'glass': '0 8px 32px rgba(0, 0, 0, 0.4)',
            },
        },
    },
    plugins: [],
}
