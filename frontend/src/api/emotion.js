/**
 * API 调用封装
 * TODO: 对接后端 API
 */

import axios from 'axios'

const API_BASE = '/api'

/**
 * TODO: 文本情绪识别
 * POST /api/predict/text
 */
export async function predictText(text) {
  // TODO: 实现
  throw new Error('TODO: 实现 predictText API 调用')
}

/**
 * TODO: 语音情绪识别
 * POST /api/predict/speech
 */
export async function predictSpeech(audioFile) {
  // TODO: 实现
  throw new Error('TODO: 实现 predictSpeech API 调用')
}

/**
 * TODO: 多模态融合
 * POST /api/predict/multimodal
 */
export async function predictMultimodal(data) {
  // TODO: 实现
  throw new Error('TODO: 实现 predictMultimodal API 调用')
}

/**
 * TODO: 上传头像
 * POST /api/upload/avatar
 */
export async function uploadAvatar(file) {
  // TODO: 实现
  throw new Error('TODO: 实现 uploadAvatar API 调用')
}
