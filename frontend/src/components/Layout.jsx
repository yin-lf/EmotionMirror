/**
 * Layout — 页面布局容器
 * TODO: 整体页面布局
 */

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-dark-bg text-gray-200">
      {children}
    </div>
  )
}
