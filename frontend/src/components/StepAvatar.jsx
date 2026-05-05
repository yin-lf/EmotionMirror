import { useState, useRef } from 'react';
import { Upload, ImageIcon, X } from 'lucide-react';
import { uploadAvatarImage } from '../services/api';

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export default function StepAvatar({ onNext, onPrev }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (f) => {
    if (f && ACCEPTED_TYPES.includes(f.type)) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const clearFile = (e) => {
    e.stopPropagation();
    setFile(null);
    setPreview(null);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    try {
      await uploadAvatarImage(file);
      onNext();
    } catch (err) {
      console.error('上传失败:', err);
      onNext();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="step-card">
      <div className="step-card-header">
        <div className="step-card-badge">Step 2</div>
        <div className="step-card-title">数字形象</div>
        <div className="step-card-desc">上传数字分身的基础形象，作为情绪表达的载体</div>
      </div>

      <div className="step-card-body">
        <div
          className={`upload-area ${dragging ? 'dragging' : ''} ${preview ? 'has-file' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_TYPES.join(',')}
            hidden
            onChange={(e) => handleFile(e.target.files[0])}
          />
          {preview ? (
            <>
              <div className="image-preview-wrapper">
                <img className="image-preview" src={preview} alt="数字分身形象预览" />
              </div>
              <div style={{ marginTop: 'var(--space-3)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-2)' }}>
                <span className="upload-desc">点击更换图片</span>
                <button
                  className="btn btn-ghost"
                  onClick={clearFile}
                  style={{ padding: 'var(--space-1)' }}
                >
                  <X size={16} />
                </button>
              </div>
            </>
          ) : (
            <>
              <ImageIcon size={24} className="upload-icon" />
              <div className="upload-title">上传数字分身形象</div>
              <div className="upload-desc">支持自拍、二次元角色或卡通人物</div>
              <div className="upload-formats">
                <span className="upload-format-tag">JPG</span>
                <span className="upload-divider">·</span>
                <span className="upload-format-tag">PNG</span>
                <span className="upload-divider">·</span>
                <span className="upload-format-tag">WebP</span>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="step-card-actions">
        <button className="btn btn-ghost" onClick={onPrev}>
          上一步
        </button>
        <button
          className="btn btn-primary"
          onClick={handleSubmit}
          disabled={!file || loading}
        >
          {loading ? '上传中...' : '确认并继续'}
        </button>
      </div>
    </div>
  );
}
