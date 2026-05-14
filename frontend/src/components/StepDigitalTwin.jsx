import { useRef, useEffect, useState } from 'react';
import { synthesizeExpressionGif } from '../services/api';

export default function StepDigitalTwin({ result, avatarFile, avatarUrl, onPrev }) {
  const [gifUrl, setGifUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const emotion = result?.emotion || '平静';

  // 自动生成动态 GIF
  useEffect(() => {
    if (!avatarFile || !result?.emotion || result.emotion === '平静') return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    synthesizeExpressionGif(avatarFile, result.emotion)
      .then((url) => {
        if (!cancelled) setGifUrl(url);
      })
      .catch((err) => {
        console.error('表情合成失败:', err);
        if (!cancelled) setError('表情合成失败');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [avatarFile, result?.emotion]);

  return (
    <div className="step-card">
      <div className="step-card-header">
        <div className="step-card-badge">Step 4</div>
        <div className="step-card-title">数字分身</div>
        <div className="step-card-desc">基于情绪分析结果生成动态表情</div>
      </div>

      <div className="step-card-body">
        <div className="placeholder-grid" style={{ marginBottom: 'var(--space-4)' }}>
          <div className="placeholder-card">
            <div className="placeholder-card-label">当前情绪</div>
            <div className="placeholder-card-value">{emotion}</div>
          </div>
          <div className="placeholder-card">
            <div className="placeholder-card-label">动态表情</div>
            <div className="placeholder-card-value">
              {loading ? '生成中...' : gifUrl ? '已完成' : '等待中'}
            </div>
          </div>
        </div>

        {error && (
          <div style={{ padding: 'var(--space-3)', background: 'var(--color-error-bg)', border: '1px solid var(--color-error)', borderRadius: 'var(--radius-sm)', color: 'var(--color-error)', marginBottom: 'var(--space-4)' }}>
            {error}
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--color-text-secondary)' }}>
            正在通过 LivePortrait 生成动态表情（约需 30 秒）...
          </div>
        )}

        {gifUrl && (
          <div style={{ textAlign: 'center', marginBottom: 'var(--space-4)' }}>
            <img
              src={gifUrl}
              alt="动态表情"
              style={{
                maxWidth: '350px',
                maxHeight: '350px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--color-border)',
              }}
            />
            <div style={{ marginTop: 'var(--space-3)' }}>
              <a href={gifUrl} download={`emoji_${emotion}.gif`} className="btn btn-primary">
                下载动态表情 GIF
              </a>
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
