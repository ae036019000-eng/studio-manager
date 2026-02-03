/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary gold/champagne palette
        gold: {
          50: '#FFFDF7',
          100: '#FEF9E7',
          200: '#FCF0C3',
          300: '#F9E49F',
          400: '#F5D26B',
          500: '#D4AF37', // Classic gold
          600: '#B8960F',
          700: '#96790A',
          800: '#745C08',
          900: '#524105',
        },
        champagne: {
          50: '#FFFEFB',
          100: '#FDF8F0',
          200: '#FAF0E1',
          300: '#F5E6D0',
          400: '#E8D5B5',
          500: '#D4C4A8',
          600: '#BBA88A',
          700: '#9A8A6E',
          800: '#7A6D55',
          900: '#5A503F',
        },
        cream: {
          50: '#FFFFFE',
          100: '#FDFCFA',
          200: '#FAF9F6',
          300: '#F5F4F0',
          400: '#EDECEA',
          500: '#E5E4E2',
        },
        copper: {
          400: '#D4956A',
          500: '#B87333',
          600: '#9A5F28',
        },
      },
      fontFamily: {
        serif: ['Cormorant Garamond', 'Playfair Display', 'Georgia', 'serif'],
        sans: ['Montserrat', 'Raleway', 'Helvetica Neue', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'soft-lg': '0 10px 40px -10px rgba(0, 0, 0, 0.1), 0 2px 10px -2px rgba(0, 0, 0, 0.04)',
        'gold': '0 4px 20px -2px rgba(212, 175, 55, 0.25)',
        'inner-soft': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      transitionDuration: {
        '400': '400ms',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
