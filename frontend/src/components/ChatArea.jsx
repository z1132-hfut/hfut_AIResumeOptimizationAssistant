import React, { useEffect, useRef } from 'react'
import Message from './Message'
import '../css/ChatArea.css'

const ChatArea = ({ messages, mode }) => {
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 根据模式显示不同的欢迎信息
  const getWelcomeMessage = (currentMode) => {
    return {
        title: '今天有什么可以帮到你？😊',
        description: '我是你的简历打分助手，可以帮你系统评估简历'
      }
  }

  const welcomeInfo = getWelcomeMessage(mode)

  return (
    <div className="chat-area">
      {messages.length === 0 ? (
        <div className="welcome-message">
          <h2>{welcomeInfo.title}</h2>
          <p>{welcomeInfo.description}</p>
        </div>
      ) : (
        <div className="messages-container">
          {messages.map(message => (
            <Message key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  )
}

export default ChatArea