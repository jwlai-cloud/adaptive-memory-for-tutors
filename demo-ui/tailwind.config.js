/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./pages/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14213d",
        paper: "#f6f4ee",
        coral: "#e76f51",
        teal: "#2a9d8f",
        sand: "#e9c46a"
      }
    }
  },
  plugins: []
};
