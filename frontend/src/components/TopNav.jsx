import { BrainCircuit } from 'lucide-react';

export default function TopNav() {
  return (
    <nav className="top-nav">
      <div className="top-nav-brand">
        <BrainCircuit size={20} className="top-nav-logo" />
        <span className="top-nav-title">EmotionMirror</span>
        <div className="top-nav-divider" />
        <span className="top-nav-subtitle">生成属于自己的情绪化数字分身</span>
      </div>
    </nav>
  );
}
