/**
 * useEmotion — 情绪状态管理 Hook
 * TODO: 管理当前情绪向量、主情绪、置信度等状态
 */

import { useState } from 'react'

export default function useEmotion() {
  const [emotionVector, setEmotionVector] = useState(null)
  const [dominant, setDominant] = useState('neutral')
  const [loading, setLoading] = useState(false)

  // TODO: 封装情绪分析调用逻辑

  return { emotionVector, dominant, loading, setEmotionVector, setDominant, setLoading }
}
