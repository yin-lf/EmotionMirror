import { useEffect, useState } from 'react';
import { synthesizeExpressionGif, publishDesktopWidgetGif } from '../services/api';
import ExpressionParamsPanel from './ExpressionParamsPanel';
import SceneBackground from './SceneBackground';

export default function StepDigitalTwin({ result, avatarFile, avatarUrl, onPrev }) {
  const [gifUrl, setGifUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [desktopLoading, setDesktopLoading] = useState(false);
  const [desktopHint, setDesktopHint] = useState(null);
  const [intensity, setIntensity] = useState(3);
  const [advancedParams, setAdvancedParams] = useState(null);

  const emotion = result?.emotion || '平静';

  // 自动生成动态 GIF（首次，使用默认参数）
  useEffect(() => {
    if (!avatarFile || !result?.emotion) return;
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

  const handleRegenerate = () => {
    if (!avatarFile) return;
    setLoading(true);
    setError(null);
    synthesizeExpressionGif(avatarFile, emotion, advancedParams, intensity)
      .then((url) => setGifUrl(url))
      .catch(() => setError('表情合成失败'))
      .finally(() => setLoading(false));
  };

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

        {emotion !== '平静' && (
          <ExpressionParamsPanel
            emotion={emotion}
            onIntensityChange={setIntensity}
            onParamsChange={setAdvancedParams}
          />
        )}

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
            <SceneBackground emotion={emotion}>
              <img
                src={gifUrl}
                alt="动态表情"
                className="scene-gif"
              />
            </SceneBackground>
            <div style={{ marginTop: 'var(--space-3)', display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', justifyContent: 'center' }}>
              <a href={gifUrl} download={`emoji_${emotion}.gif`} className="btn btn-primary">
                下载动态表情 GIF
              </a>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={loading}
                onClick={handleRegenerate}
              >
                重新生成 GIF
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                disabled={desktopLoading}
                onClick={async () => {
                  setDesktopLoading(true);
                  setDesktopHint(null);
                  try {
                    const res = await fetch(gifUrl);
                    const blob = await res.blob();
                    await publishDesktopWidgetGif(blob, emotion);
                    const api = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';
                    setDesktopHint(
                      `已同步到后端。请在本机另开终端（已安装 PySide6），在 EmotionMirror 项目根目录执行：\npython -m backend.desktop_pet --api ${api.replace(/\/$/, '')}`,
                    );
                  } catch (e) {
                    console.error(e);
                    setDesktopHint('同步失败，请确认后端已启动且可访问。');
                  } finally {
                    setDesktopLoading(false);
                  }
                }}
              >
                {desktopLoading ? '同步中…' : '在桌面显示'}
              </button>
            </div>
            {desktopHint && (
              <pre
                style={{
                  marginTop: 'var(--space-4)',
                  textAlign: 'left',
                  fontSize: '12px',
                  lineHeight: 1.5,
                  padding: 'var(--space-3)',
                  background: 'var(--color-surface-elevated)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                }}
              >
                {desktopHint}
              </pre>
            )}
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
