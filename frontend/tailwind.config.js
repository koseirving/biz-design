/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary Colors
        primary: {
          'tory-blue': '#1041aa',
          'royal-blue': '#346be3',
          'portage': '#89a5ee',
        },
        // Accent Colors
        accent: {
          'corn': '#e0b700',
          'wewak': '#f1a5aa',
        },
        // Status Colors
        status: {
          'salem': '#0d7554',
          'mountain-meadow': '#11a383',
        },
        // Neutral Colors
        neutral: {
          'text-dark': '#2d3748',
          'text-light': '#718096',
          'background-light': '#f8f9fa',
        },
        // Keep existing CSS variables for compatibility
        background: "var(--background)",
        foreground: "var(--foreground)",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "Arial", "Helvetica", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
    },
  },
  plugins: [],
}