import React from 'react'
import '../css/Message.css'

const Message = ({ message }) => {
  return (
    <div className={`message ${message.isUser ? 'user-message' : 'ai-message'}`}>
      <div className="message-content">
        <div className="message-text">
          {message.content}
        </div>
      </div>
    </div>
  )
}

export default Message