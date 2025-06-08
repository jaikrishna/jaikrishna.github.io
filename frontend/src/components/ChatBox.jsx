import React, { useState, useRef } from 'react'

export default function ChatBox() {
  const [messages, setMessages] = useState([])
  const inputRef = useRef()

  const sendMessage = async () => {
    const content = inputRef.current.value
    if (!content) return
    const newMessages = [...messages, { role: 'user', content }]
    setMessages(newMessages)
    inputRef.current.value = ''

    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: newMessages })
    })

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let assistantMsg = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value)
      if (chunk.startsWith('data:')) {
        const text = chunk.replace(/^data:\s*/, '')
        if (text === '[DONE]') break
        assistantMsg += text
      }
    }
    setMessages(m => [...m, { role: 'assistant', content: assistantMsg }])
  }

  return (
    <div>
      <div style={{ height: '200px', overflowY: 'auto' }}>
        {messages.map((m, idx) => (
          <div key={idx}><b>{m.role}:</b> {m.content}</div>
        ))}
      </div>
      <input ref={inputRef} type="text" placeholder="Ask a question" />
      <button onClick={sendMessage}>Send</button>
    </div>
  )
}
