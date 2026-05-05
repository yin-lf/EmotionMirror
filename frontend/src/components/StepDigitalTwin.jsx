import { UserRound, Layers, Eye, Sparkles } from 'lucide-react';

export default function StepDigitalTwin({ result, onPrev }) {
  return (
    <div className="step-card">
      <div className="step-card-header">
        <div className="step-card-badge">Step 4</div>
        <div className="step-card-title">数字分身</div>
        <div className="step-card-desc">基于情绪分析结果驱动数字分身交互</div>
      </div>

      <div className="step-card-body">
        {result && result.avatar_url ? (
          <div className="image-preview-wrapper">
            <img className="image-preview" src={result.avatar_url} alt="数字分身" />
          </div>
        ) : (
          <div className="coming-soon">
            <div className="coming-soon-badge">
              <Layers size={14} />
              等待 Layer 3/4 对接
            </div>

            <div className="coming-soon-title">数字分身生成</div>
            <div className="coming-soon-desc">
              该模块由组员D（表情生成）和组员E（桌面展示）负责开发，完成后将在此展示情绪化数字分身。
            </div>

            <div className="coming-soon-steps">
              <div className="coming-soon-step">
                <div className="coming-soon-step-dot" />
                <UserRound size={14} />
                <span>数字分身表情生成（Layer 3）</span>
              </div>
              <div className="coming-soon-step">
                <div className="coming-soon-step-dot" />
                <Eye size={14} />
                <span>桌面交互与视线追踪（Layer 4）</span>
              </div>
              <div className="coming-soon-step">
                <div className="coming-soon-step-dot" />
                <Sparkles size={14} />
                <span>氛围效果与背景色调调整</span>
              </div>
            </div>

            <div className="placeholder-grid" style={{ marginTop: 'var(--space-8)' }}>
              <div className="placeholder-card">
                <div className="placeholder-card-label">当前情绪</div>
                <div className="placeholder-card-value">
                  {result?.emotion || '等待分析'}
                </div>
              </div>
              <div className="placeholder-card">
                <div className="placeholder-card-label">分身状态</div>
                <div className="placeholder-card-value">等待生成</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="step-card-actions">
        <button className="btn btn-ghost" onClick={onPrev}>
          上一步
        </button>
        <div />
      </div>
    </div>
  );
}
