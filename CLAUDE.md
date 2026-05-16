# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EmotionMirror is a multimodal emotion analysis and facial expression synthesis system. Users input text or voice, the system analyzes the emotion, then generates an animated facial expression GIF via LivePortrait. A React frontend provides a 4-step wizard UI; a FastAPI backend handles analysis and synthesis. A PySide6 desktop pet is also included.

All emotion labels and UI text are in Chinese (开心/悲伤/愤怒/焦虑/恐惧/平静/厌恶/惊讶).

## Development Commands

### Backend (requires conda env `emotion`)
```bash
conda activate emotion
uvicorn backend.app:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # http://localhost:5173, proxies /api to backend:8000
npm run build
npm run lint
```

### Desktop pet (requires local display + PySide6)
```bash
python -m backend.desktop_pet --api http://127.0.0.1:8000
```

No test framework is configured. No CI/CD pipeline exists.

## Architecture

### Data Flow
```
Text/Voice Input → Emotion Analysis → EMOTION_PARAMS lookup → LivePortrait Retargeting → GIF
```

1. **Text emotion** (`backend/text_emotion/analyzer.py`): Rule-based keyword matching with VAD (Valence-Arousal-Dominance) vector output. 95 keywords across 8 emotions.

2. **Voice emotion** (`backend/voice_emotion/analyzer.py`): librosa 312-dim features → LSTM (128 units) → softmax over 6 classes. Maps to same VAD format.

3. **Unified response** (`backend/schemas.py`): `EmotionResponse(emotion: str, vector: [V, A, D])` shared by both modalities.

4. **Emotion-to-expression mapping** (`backend/expression/synthesis.py`): `EMOTION_PARAMS` dict maps each emotion label to LivePortrait parameters (smile, eyebrow, lip_variation_*, eyeball_direction_*).

5. **LivePortrait engine** (`backend/expression/LivePortrait/`): Forked LivePortrait repo. `GradioPipeline.execute_image_retargeting()` applies delta parameters to 21 facial keypoints, then warp-decode-paste.

6. **GIF generation** (`synthesize_expression_gif`): 24 frames (12 up + 12 down), cosine ease-in-out interpolation, subtle head micro-sway (yaw/pitch/roll), transparent background via rembg.

7. **Scene backgrounds** (`frontend/src/utils/sceneConfig.js`): Maps (emotion × time-of-day) to CSS gradient + animation (rain, stars, fire, fog, lightning, sparkle).

8. **LLM chat** (`backend/app.py` lines 262-415): OpenAI-compatible `/chat/completions` integration. Configured via `.env` (`LLM_API_KEY`, `LLM_API_URL`, `LLM_MODEL`). Falls back to preset replies from `backend/presets/chat_presets.json`.

### Frontend
React 19 + Vite, no router, no TypeScript. Step wizard pattern in `App.jsx` with 4 steps: Input → Avatar → Analysis → DigitalTwin. All API calls in `frontend/src/services/api.js`.

### Key Dependencies
- Backend: FastAPI, PyTorch, LivePortrait, rembg, librosa, TensorFlow (voice LSTM)
- Frontend: React 19, Vite 8, Axios
- Optional: PySide6 (desktop pet, requires `pip install PySide6`)

## Important Files

| File | Purpose |
|------|---------|
| `backend/app.py` | All FastAPI routes, LLM config, `.env` loader |
| `backend/expression/synthesis.py` | EMOTION_PARAMS, intensity control, GIF pipeline |
| `backend/expression/__init__.py` | Public exports for expression module |
| `backend/text_emotion/analyzer.py` | Text emotion + VAD |
| `backend/voice_emotion/analyzer.py` | Voice emotion + VAD |
| `backend/presets/chat_presets.json` | Chat system prompt + fallback replies |
| `frontend/src/services/api.js` | All API calls |
| `frontend/src/utils/sceneConfig.js` | Emotion × time scene mapping |

## Conventions

- Pretrained weights are gitignored. Download LivePortrait weights: `cd backend && huggingface-cli download KlingTeam/LivePortrait --local-dir pretrained_weights --exclude "*.git*" "README.md" "docs"`
- `.env` is gitignored (contains API keys). Create from: `LLM_API_KEY=...`, `LLM_API_URL=...`, `LLM_MODEL=...`
- The `lip_array.pkl` resource is also gitignored — download from LivePortrait repo if missing.
- LivePortrait subdirectory is not a git repo — it's vendored source with local modifications (notably `base_config.py` redirects weight paths to `backend/pretrained_weights/`).
