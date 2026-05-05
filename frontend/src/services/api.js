import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// 文本情感分析 — 对接组员B
export async function analyzeText(text) {
  console.log(`[API] POST /api/text-emotion — text: "${text}"`);
  const res = await api.post('/api/text-emotion', { text });
  return res.data;
}

// 语音情感分析 — 对接组员C
export async function analyzeVoice(audioFile) {
  console.log(`[API] POST /api/voice-emotion — file: "${audioFile.name}"`);
  const formData = new FormData();
  formData.append('audio', audioFile);
  const res = await api.post('/api/voice-emotion', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

// 获取数字分身表情/氛围 — 对接组员D
export async function getAvatarEmotions() {
  console.log('[API] GET /api/avatar/emotions');
  const res = await api.get('/api/avatar/emotions');
  return res.data;
}

// 上传数字分身基础形象
export async function uploadAvatarImage(imageFile) {
  console.log(`[API] POST /api/avatar/upload — file: "${imageFile.name}"`);
  const formData = new FormData();
  formData.append('image', imageFile);
  const res = await api.post('/api/avatar/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export default api;
