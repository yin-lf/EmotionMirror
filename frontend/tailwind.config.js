/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // TODO: 自定义情绪主题色
        emotion: {
          happy: '#FFD700',
          sad: '#6B7DB3',
          angry: '#FF4444',
          calm: '#88D8B0',
          fear: '#9B59B6',
          surprise: '#FF8C42',
          disgust: '#6B8E23',
          neutral: '#A0AEC0',
        },
        dark: {
          bg: '#0F172A',
          card: '#1E293B',
          border: '#334155',
        },
      },
      animation: {
        // TODO: 添加粒子、渐变等动画
      },
    },
  },
  plugins: [],
}
