import React, { useState } from 'react'

export default function LessonPlayer({ chapterId }) {
  const [playing, setPlaying] = useState(false)

  const startLesson = async () => {
    if (!chapterId) return
    const res = await fetch('/api/lesson', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chapter_id: chapterId })
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    setPlaying(true)
    audio.onended = () => setPlaying(false)
    audio.play()
  }

  return (
    <div>
      <button onClick={startLesson} disabled={playing}>Start Lesson</button>
    </div>
  )
}
