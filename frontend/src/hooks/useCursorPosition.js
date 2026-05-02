/**
 * useCursorPosition — 鼠标位置 Hook
 * 负责人：组员E
 *
 * TODO(组员E): 实现鼠标位置追踪
 */

import { useState, useEffect } from 'react'

export default function useCursorPosition() {
  const [position, setPosition] = useState({ x: 0, y: 0 })

  // TODO(组员E): 监听 mousemove 事件

  return position
}
