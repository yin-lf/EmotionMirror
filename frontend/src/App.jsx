/**
 * EmotionMirror 前端入口
 * TODO: 布局搭建 — InputPanel | AvatarDisplay | EmotionRadar
 */

export default function App() {
  return (
    <div className="min-h-screen bg-dark-bg">
      {/* TODO: 布局 */}
      <header className="p-6 text-center">
        <h1 className="text-3xl font-bold text-white">EmotionMirror</h1>
        <p className="text-gray-400 mt-1">基于多模态情绪感知的数字分身系统</p>
      </header>

      <main className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* TODO: InputPanel */}
        <div className="bg-dark-card rounded-xl border border-dark-border p-6">
          <h2 className="text-lg font-semibold mb-4">输入面板</h2>
          <p className="text-gray-500">TODO: InputPanel 组件</p>
        </div>

        {/* TODO: AvatarDisplay */}
        <div className="bg-dark-card rounded-xl border border-dark-border p-6">
          <h2 className="text-lg font-semibold mb-4">数字分身</h2>
          <p className="text-gray-500">TODO: AvatarDisplay 组件</p>
        </div>

        {/* TODO: EmotionRadar */}
        <div className="bg-dark-card rounded-xl border border-dark-border p-6">
          <h2 className="text-lg font-semibold mb-4">情绪雷达</h2>
          <p className="text-gray-500">TODO: EmotionRadar 组件</p>
        </div>
      </main>
    </div>
  )
}
