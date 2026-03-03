/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
        "./public/index.html"
    ],
    theme: {
        extend: {
            fontFamily: {
                cinzel: ['Cinzel', 'serif'],
                inter: ['Inter', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            colors: {
                cosmic: {
                    bg: {
                        primary: '#05020a',
                        secondary: '#0f0c29',
                        tertiary: '#1a1638',
                    },
                    text: {
                        primary: '#ffffff',
                        secondary: '#aebbff',
                        muted: '#6b7280',
                        accent: '#ffd700',
                    },
                    brand: {
                        primary: '#7c3aed',
                        secondary: '#4c1d95',
                        accent: '#ffd700',
                        glow: 'rgba(124, 58, 237, 0.5)',
                    },
                    chart: {
                        border: '#ffd700',
                        houseBg: 'rgba(255, 255, 255, 0.03)',
                        planetText: '#e0e7ff',
                        signText: '#9ca3af',
                    }
                },
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)'
            },
            keyframes: {
                'accordion-down': {
                    from: { height: '0' },
                    to: { height: 'var(--radix-accordion-content-height)' }
                },
                'accordion-up': {
                    from: { height: 'var(--radix-accordion-content-height)' },
                    to: { height: '0' }
                },
                'pulse-glow': {
                    '0%, 100%': { 
                        boxShadow: '0 0 20px rgba(124, 58, 237, 0.3)',
                        borderColor: 'rgba(124, 58, 237, 0.5)'
                    },
                    '50%': { 
                        boxShadow: '0 0 40px rgba(124, 58, 237, 0.5)',
                        borderColor: 'rgba(124, 58, 237, 0.8)'
                    }
                },
                'float': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' }
                },
                'twinkle': {
                    '0%, 100%': { opacity: '0.3' },
                    '50%': { opacity: '1' }
                },
                'fadeIn': {
                    '0%': { opacity: '0', transform: 'translateY(10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' }
                },
                'slideIn': {
                    '0%': { opacity: '0', transform: 'translateX(-20px)' },
                    '100%': { opacity: '1', transform: 'translateX(0)' }
                }
            },
            animation: {
                'accordion-down': 'accordion-down 0.2s ease-out',
                'accordion-up': 'accordion-up 0.2s ease-out',
                'pulse-glow': 'pulse-glow 3s ease-in-out infinite',
                'float': 'float 6s ease-in-out infinite',
                'twinkle': 'twinkle 3s ease-in-out infinite',
                'fadeIn': 'fadeIn 0.5s ease-out forwards',
                'slideIn': 'slideIn 0.3s ease-out forwards'
            },
            backgroundImage: {
                'cosmic-gradient': 'radial-gradient(ellipse at top, #0f0c29, #05020a)',
                'gold-gradient': 'linear-gradient(135deg, #ffd700, #ffaa00)',
            }
        }
    },
    plugins: [require("tailwindcss-animate")],
};
