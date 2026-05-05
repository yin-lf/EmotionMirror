import { useState, useRef } from 'react';
import { Type, Mic, Upload, FileAudio } from 'lucide-react';
import { analyzeText, analyzeVoice } from '../services/api';

export default function StepInput({ onResult, onNext }) {
  const [modality, setModality] = useState('text');
  const [text, setText] = useState('');
  const [voiceFile, setVoiceFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (f) => {
    if (f && f.type.startsWith('audio/')) {
      setVoiceFile(f);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      let result;
      if (modality === 'text') {
        if (!text.trim()) { setLoading(false); return; }
        result = await analyzeText(text);
      } else {
        if (!voiceFile) { setLoading(false); return; }
        result = await analyzeVoice(voiceFile);
      }
      onResult(result);
      onNext();
    } catch (err) {
      console.error('分析失败:', err);
      onResult({ error: '后端服务未就绪，请稍后重试', emotion: null, vector: [] });
    } finally {
      setLoading(false);
    }
  };

  const canSubmit = modality === 'text' ? text.trim().length > 0 : voiceFile !== null;

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <div className="step-card">
      <div className="step-card-header">
        <div className="step-card-badge">Step 1</div>
        <div className="step-card-title">情绪输入</div>
        <div className="step-card-desc">选择输入模态，提供需要分析的内容</div>
      </div>

      <div className="step-card-body">
        <div className="modality-switch">
          <button
            className={`modality-btn ${modality === 'text' ? 'active' : ''}`}
            onClick={() => setModality('text')}
          >
            <Type size={16} className="modality-btn-icon" />
            文本
          </button>
          <button
            className={`modality-btn ${modality === 'voice' ? 'active' : ''}`}
            onClick={() => setModality('voice')}
          >
            <Mic size={16} className="modality-btn-icon" />
            语音
          </button>
        </div>

        {modality === 'text' ? (
          <>
            <textarea
              className="text-input-area"
              rows={6}
              placeholder="输入你想表达的内容，例如：今天面试通过了我真的太开心了！"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <div className="text-input-footer">
              <span className="text-input-hint">输入带有情绪色彩的文本以获得更准确的分析</span>
              <span className="text-input-count">{text.length} 字</span>
            </div>
          </>
        ) : (
          <>
            <div
              className={`upload-area ${dragging ? 'dragging' : ''} ${voiceFile ? 'has-file' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".wav,.mp3,.m4a,audio/*"
                hidden
                onChange={(e) => handleFile(e.target.files[0])}
              />
              {voiceFile ? (
                <div className="file-preview">
                  <div className="file-preview-icon">
                    <FileAudio size={20} />
                  </div>
                  <div className="file-preview-info">
                    <span className="file-preview-name">{voiceFile.name}</span>
                    <span className="file-preview-size">{formatSize(voiceFile.size)}</span>
                  </div>
                </div>
              ) : (
                <>
                  <Upload size={24} className="upload-icon" />
                  <div className="upload-title">上传语音文件</div>
                  <div className="upload-desc">拖拽文件到此处，或点击选择文件</div>
                  <div className="upload-formats">
                    <span className="upload-format-tag">WAV</span>
                    <span className="upload-divider">·</span>
                    <span className="upload-format-tag">MP3</span>
                    <span className="upload-divider">·</span>
                    <span className="upload-format-tag">M4A</span>
                  </div>
                </>
              )}
            </div>
            {voiceFile && (
              <audio className="audio-player" controls src={URL.createObjectURL(voiceFile)} />
            )}
          </>
        )}
      </div>

      <div className="step-card-actions">
        <div />
        <button
          className="btn btn-primary"
          onClick={handleSubmit}
          disabled={!canSubmit || loading}
        >
          {loading ? '分析中...' : '分析并继续'}
        </button>
      </div>
    </div>
  );
}
