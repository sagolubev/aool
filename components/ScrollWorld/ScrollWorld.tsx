'use client'
import { useEffect, useRef } from 'react'
import { scrollWorldConfig } from './scenes'
import { mountScrollWorld } from './scrub-engine.js'

export function ScrollWorld() {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (ref.current) mountScrollWorld(ref.current, scrollWorldConfig)
  }, [])
  return <div id="world" ref={ref} />
}
