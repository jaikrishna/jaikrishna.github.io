import React from 'react'
import ReactDOM from 'react-dom/client'
import LessonPlayer from './components/LessonPlayer'
import ChatBox from './components/ChatBox'

function App() {
  const [chapterId, setChapterId] = React.useState('')
  const fileRef = React.useRef()

  const upload = async () => {
    const file = fileRef.current.files[0]
    if (!file) return
    const form = new FormData()
    form.append('file', file)
    const res = await fetch('/api/chapters', { method: 'POST', body: form })
    const data = await res.json()
    setChapterId(data.chapter_id)
  }

  return (
    <div>
      <h1>Voice Tutor</h1>
      <input type="file" ref={fileRef} />
      <button onClick={upload}>Upload Chapter</button>
      {chapterId && <LessonPlayer chapterId={chapterId} />}
      <ChatBox />
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />)
