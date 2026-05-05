import { BarChart3 } from 'lucide-react';

const EXAMPLE_TAGS = ['开心', '平静', '惊讶', '悲伤', '愤怒', '恐惧', '厌恶'];

const DIMENSION_LABELS = ['效价(Valence)', '唤醒度(Arousal)', '优势度(Dominance)'];

export default function StepAnalysis({ result, onNext, onPrev }) {
  const hasResult = result && !result.error;
  const hasError = result && result.error;

  return (
    <div className="step-card">
      <div className="step-card-header">
        <div className="step-card-badge">Step 3</div>
        <div className="step-card-title">情绪分析</div>
        <div className="step-card-desc">基于输入内容分析情绪状态</div>
      </div>

      <div className="step-card-body">
        {hasError && (
          <div style={{
            padding: 'var(--space-3) var(--space-4)',
            background: 'var(--color-error-bg)',
            border: '1px solid var(--color-error)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--color-error)',
            fontSize: 'var(--text-sm)',
          }}>
            {result.error}
          </div>
        )}

        {hasResult ? (
          <>
            <div className="result-section">
              <div className="result-label">情绪标签</div>
              <div className="emotion-tags">
                <span className="emotion-tag primary">{result.emotion || '未知'}</span>
              </div>
            </div>

            {result.vector && result.vector.length > 0 && (
              <div className="result-section">
                <div className="result-label">情绪维度</div>
                <div className="emotion-bars">
                  {result.vector.map((val, i) => (
                    <div key={i} className="bar-row">
                      <span className="bar-label">
                        {DIMENSION_LABELS[i] || `Dim ${i}`}
                      </span>
                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{ '--bar-width': `${Math.max(0, Math.min(100, val * 100))}%` }}
                        />
                      </div>
                      <span className="bar-value">{val.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <>
            <div className="result-section">
              <div className="result-label">情绪标签</div>
              <div className="emotion-tags">
                {EXAMPLE_TAGS.map((tag) => (
                  <span key={tag} className="emotion-tag placeholder">{tag}</span>
                ))}
              </div>
            </div>

            <div className="result-section">
              <div className="result-label">情绪维度</div>
              <div className="emotion-bars">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="bar-row">
                    <span className="bar-label">{DIMENSION_LABELS[i]}</span>
                    <div className="bar-track">
                      <div className="skeleton skeleton-bar" style={{ width: ['45%', '30%', '60%'][i] }} />
                    </div>
                    <span className="bar-value">--</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="empty-state" style={{ padding: 'var(--space-4) 0' }}>
              <BarChart3 size={20} className="empty-state-icon" />
              <div className="empty-state-desc">完成输入后，分析结果将在此显示</div>
            </div>
          </>
        )}
      </div>

      <div className="step-card-actions">
        <button className="btn btn-ghost" onClick={onPrev}>
          上一步
        </button>
        <button
          className="btn btn-primary"
          onClick={onNext}
          disabled={!hasResult}
        >
          生成数字分身
        </button>
      </div>
    </div>
  );
}
