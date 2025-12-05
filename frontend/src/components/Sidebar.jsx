import React from 'react'
import '../css/Sidebar.css'

const NewChatIcon = ({ size = 18, color = 'black' }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 -3 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {/* 对话气泡 */}
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      {/* 加号 */}
      <line x1="12" y1="7" x2="12" y2="13" />
      <line x1="9" y1="10" x2="15" y2="10" />
    </svg>
  );
};

const Sidebar = ({ isOpen, onClose, onNewChat, activeChat, onChatSelect }) => {
  const chatHistory = [
    { id: 1, title: "" },
    // { id: 2, title: "产品经理简历评分" },
    // { id: 3, title: "数据分析师简历建议" },
    // { id: 4, title: "Java开发工程师简历修改"},
    // { id: 5, title: "UI设计师简历优化建议" },
  ]

  const handleChatClick = (chatId) => {
    if (onChatSelect) {
      onChatSelect(chatId)
    }
  }

  return (
    <>
      <div className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <div className="app-title">简历打分助手</div>
          <button className="new-chat-button" onClick={onNewChat}>
            <NewChatIcon />
            开启新对话
          </button>
          {/* 移动端显示关闭按钮 */}
          {window.innerWidth <= 768 && (
            <button className="close-button" onClick={onClose}>×</button>
          )}
        </div>

        <div className="chat-history">
          <div className="history-title">最近对话</div>
          {chatHistory.map(chat => (
            <div
              key={chat.id}
              className={`chat-item ${activeChat === chat.id ? 'active' : ''}`}
              onClick={() => handleChatClick(chat.id)}
            >
              <div className="chat-title">{chat.title}</div>
              <div className="chat-date">{chat.date}</div>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">U</div>
            <div className="user-name">用户</div>
          </div>
        </div>
      </div>
    </>
  )
}

export default Sidebar