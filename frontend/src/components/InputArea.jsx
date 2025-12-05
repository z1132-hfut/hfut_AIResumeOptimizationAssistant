import React, { useState, useRef, useEffect } from 'react'
import '../css/InputArea.css'

const InputArea = ({ onSendMessage, mode, onModeChange, disabled, isProcessing }) => {
  const [message, setMessage] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [jobName, setJobName] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [companyInfo, setCompanyInfo] = useState('')
  const [userRequest, setUserRequest] = useState('')
  const [isResizing, setIsResizing] = useState(false)
  const [resumeContainerHeight, setResumeContainerHeight] = useState(400)

  // 新增：拖拽相关引用和状态
  const startY = useRef(0)
  const initialHeight = useRef(0)
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)
  const containerRef = useRef(null)
  const resizeHandleRef = useRef(null)
  const formRef = useRef(null)

  // 处理调整高度（兼容桌面端鼠标和移动端触摸）
  useEffect(() => {
    const handleMove = (e) => {
      if (!isResizing || mode !== 'resume' || !containerRef.current) return

      // 阻止默认行为（滚动、缩放等）干扰拖拽
      e.preventDefault()
      e.stopPropagation()

      // 区分鼠标和触摸事件，获取正确的Y坐标
      const clientY = e.type.includes('touch')
        ? e.touches[0].clientY
        : e.clientY

      // 计算高度变化（基于初始高度 + 位移差）
      const deltaY = startY.current - clientY
      let newHeight = initialHeight.current + deltaY

      // 明确高度限制：最小200px，最大为屏幕高度的60%
      const minHeight = 200
      const maxHeight = window.innerHeight * 0.6
      newHeight = Math.max(minHeight, Math.min(maxHeight, newHeight))

      setResumeContainerHeight(newHeight)
      containerRef.current.style.height = `${newHeight}px`
    }

    const handleEnd = () => {
      setIsResizing(false)
      document.body.style.cursor = 'default'
      document.body.style.userSelect = 'auto'
      // 移除所有事件监听，避免内存泄漏
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleEnd)
      document.removeEventListener('touchmove', handleMove)
      document.removeEventListener('touchend', handleEnd)
      document.removeEventListener('touchcancel', handleEnd)
    }

    if (isResizing) {
      // 同时监听鼠标和触摸事件
      document.addEventListener('mousemove', handleMove)
      document.addEventListener('mouseup', handleEnd)
      document.addEventListener('touchmove', handleMove, { passive: false }) // 允许阻止默认行为
      document.addEventListener('touchend', handleEnd)
      document.addEventListener('touchcancel', handleEnd) // 处理触摸中断

      document.body.style.cursor = 'ns-resize'
      document.body.style.userSelect = 'none'
    }

    // 清理函数
    return () => {
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleEnd)
      document.removeEventListener('touchmove', handleMove)
      document.removeEventListener('touchend', handleEnd)
      document.removeEventListener('touchcancel', handleEnd)
    }
  }, [isResizing, mode, isProcessing])

  // 初始化容器高度（确保在限制范围内）
  useEffect(() => {
    if (mode === 'resume' && containerRef.current) {
      const minHeight = 200
      const maxHeight = window.innerHeight * 0.6
      // 确保初始高度在限制范围内
      const initialValidHeight = Math.max(minHeight, Math.min(maxHeight, resumeContainerHeight))
      setResumeContainerHeight(initialValidHeight)
      containerRef.current.style.height = `${initialValidHeight}px`
    } else if (containerRef.current) {
      containerRef.current.style.height = 'auto'
    }
  }, [mode, resumeContainerHeight])

  // 自动调整textarea高度 - 只在自由问答模式下生效
  const adjustTextareaHeight = () => {
    if (mode !== 'resume') {
      const textarea = textareaRef.current
      if (textarea) {
        const currentScrollTop = textarea.scrollTop

        textarea.style.height = 'auto'

        const lineHeight = parseInt(getComputedStyle(textarea).lineHeight)
        const minHeight = lineHeight * 2

        const newHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, 200))
        textarea.style.height = newHeight + 'px'

        textarea.scrollTop = currentScrollTop
      }
    }
  }

  useEffect(() => {
    adjustTextareaHeight()
  }, [message, mode])

  // 拖拽开始（兼容鼠标和触摸）
  const handleResizeStart = (e) => {
    e.preventDefault()
    e.stopPropagation()

    // 记录初始位置和初始高度
    if (e.type === 'mousedown') {
      startY.current = e.clientY
    } else if (e.type === 'touchstart') {
      startY.current = e.touches[0].clientY
    }

    initialHeight.current = resumeContainerHeight
    setIsResizing(true)
  }

  const handleSubmit = (e) => {
    if (e) e.preventDefault()

    if (isProcessing) {
      alert('系统正在处理中，请稍候...')
      return
    }

    if (mode === 'resume') {
      if (!resumeFile || !jobName.trim() || !jobDescription.trim()) {
        alert('请完成所有必填项：上传简历、填写岗位名称和岗位描述')
        return
      }

      const resumeData = {
        resumeFile,
        jobName: jobName.trim(),
        jobDescription: jobDescription.trim(),
        companyInfo: companyInfo.trim(),
        userRequest: userRequest.trim()
      }

      const resumeMessage = `请帮我评估简历`

      onSendMessage(resumeMessage, mode, resumeData)

      setResumeFile(null)
      setJobName('')
      setJobDescription('')
      setCompanyInfo('')
      setUserRequest('')
      setMessage('')

      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } else {
      if (message.trim()) {
        onSendMessage(message.trim(), mode)
        setMessage('')
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto'
          const lineHeight = parseInt(getComputedStyle(textareaRef.current).lineHeight)
          textareaRef.current.style.height = (lineHeight * 2) + 'px'
        }
      }
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && mode !== 'resume') {
      if (isProcessing) {
        e.preventDefault()
        alert('系统正在处理中，请稍候...')
        return
      }
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleModeChange = (newMode) => {
    if (isProcessing) {
      alert('系统正在处理中，请稍候再切换模式')
      return
    }

    onModeChange(newMode)
    if (newMode !== 'resume') {
      setResumeFile(null)
      setJobName('')
      setJobDescription('')
      setCompanyInfo('')
      setUserRequest('')
      if (containerRef.current) {
        containerRef.current.style.height = 'auto'
      }
    } else {
      setMessage('')
      // 切换到简历模式时，确保高度在限制范围内
      const minHeight = 200
      const maxHeight = window.innerHeight * 0.6
      const validHeight = Math.max(minHeight, Math.min(maxHeight, resumeContainerHeight))
      setResumeContainerHeight(validHeight)
      if (containerRef.current) {
        containerRef.current.style.height = `${validHeight}px`
      }
    }
  }

  // 处理文件上传 - 阻止事件冒泡，避免重复触发
  const handleFileUpload = (e) => {
    e.stopPropagation()
    const file = e.target.files[0]
    if (file) {
      // 增强文件类型验证，兼容不同设备的MIME类型
      if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
        alert('请上传PDF格式的简历文件')
        return
      }
      if (file.size > 10 * 1024 * 1024) {
        alert('文件大小不能超过10MB')
        return
      }
      setResumeFile(file)
    }
  }

  // 移除文件 - 阻止事件冒泡
  const removeFile = (e) => {
    e.stopPropagation()
    setResumeFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // 检查简历打分模式是否可发送
  const canSendResume = () => {
    return resumeFile && jobName.trim() && jobDescription.trim()
  }

  // 检查智能问答模式是否可发送
  const canSendChat = () => {
    return message.trim()
  }

  // 发送按钮禁用逻辑
  const isSendDisabled = mode === 'resume'
    ? !canSendResume() || isProcessing
    : !canSendChat() || isProcessing

  return (
    <div className="input-area">
      <form ref={formRef} onSubmit={handleSubmit} className="input-form">
        {/* 拖拽手柄 - 绑定鼠标和触摸事件 */}
        {mode === 'resume' && (
          <div
            className={`resize-handle`}
            ref={resizeHandleRef}
            onMouseDown={handleResizeStart}
            onTouchStart={handleResizeStart} // 新增：移动端触摸事件
            title={'拖拽调整高度'}
            style={{ touchAction: 'none' }} // 禁止默认触摸行为
          >
            <div className="resize-dots">
              <span className="resize-dot"></span>
              <span className="resize-dot"></span>
              <span className="resize-dot"></span>
            </div>
          </div>
        )}

        {/* 容器添加明确的高度限制 */}
        <div
          className={`input-container ${mode === 'resume' ? 'resume-mode' : ''}`}
          ref={containerRef}
          style={mode === 'resume' ? {
            height: `${resumeContainerHeight}px`,
            overflow: 'auto',
            minHeight: '200px', // 最小高度
            maxHeight: `${window.innerHeight * 0.6}px`, // 最大高度（屏幕60%）
            transition: 'height 0.1s ease' // 平滑过渡
          } : {}}
        >
          <div className="input-content">
            {/* 消息输入区域 - 只在自由问答模式下显示 */}
            {mode !== 'resume' && (
              <div className="message-input-container">
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => !isProcessing && setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={isProcessing ? '系统正在处理中，请稍候...' : '输入您的问题...'}
                  rows="1"
                  className="message-input"
                  disabled={isProcessing}
                />
              </div>
            )}

            {/* 简历打分信息上传模块 */}
            {mode === 'resume' && (
              <div className="resume-upload-section">
                <div className="upload-section">
                  <h4>简历信息</h4>

                  {/* 简历文件上传 - 修复重复选择问题 */}
                  <div className="form-group">
                    <label className="required">上传简历 (PDF格式)</label>
                    <div className="file-upload-area">
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,application/pdf"
                        onChange={handleFileUpload}
                        className="file-input"
                        style={{
                          position: 'absolute',
                          opacity: 0,
                          width: '100%',
                          height: '100%',
                          cursor: 'pointer',
                          zIndex: 10,
                          top: 0,
                          left: 0,
                          margin: 0,
                          padding: 0
                        }}
                        onClick={(e) => e.stopPropagation()} // 阻止输入框点击事件冒泡
                      />
                      <div className="upload-placeholder" style={{ zIndex: 1 }}>
                        {resumeFile ? (
                          <div className="file-info">
                            <span className="file-name">{resumeFile.name}</span>
                            <button
                              type="button"
                              onClick={removeFile}
                              className="remove-file"
                            >
                              移除
                            </button>
                          </div>
                        ) : (
                          <>
                            <span>{'点击或拖拽PDF文件到此区域'}</span>
                            <span className="file-hint">仅支持PDF格式，最大10MB</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* 岗位名称 */}
                  <div className="form-group">
                    <label className="required">岗位名称</label>
                    <input
                      type="text"
                      value={jobName}
                      onChange={(e) => setJobName(e.target.value)}
                      placeholder="例如：后端开发工程师"
                      className="form-input"
                      disabled={isProcessing}
                      style={{
                        WebkitAppearance: 'none',
                        borderRadius: '4px'
                      }}
                    />
                  </div>

                  {/* 岗位描述 */}
                  <div className="form-group">
                    <label className="required">岗位描述</label>
                    <textarea
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      placeholder="请粘贴招聘信息中的岗位描述和要求..."
                      rows="3"
                      className="form-textarea"
                      disabled={isProcessing}
                      style={{
                        WebkitAppearance: 'none',
                        borderRadius: '4px'
                      }}
                    />
                  </div>

                  {/* 公司信息 */}
                  <div className="form-group">
                    <label>公司信息 (选填)</label>
                    <textarea
                      value={companyInfo}
                      onChange={(e) => setCompanyInfo(e.target.value)}
                      placeholder="请添加公司名称、基本情况等其他信息..."
                      rows="2"
                      className="form-textarea"
                      disabled={isProcessing}
                      style={{
                        WebkitAppearance: 'none',
                        borderRadius: '4px'
                      }}
                    />
                  </div>

                  {/* 特殊要求 */}
                  <div className="form-group">
                    <label>用户备注或特殊要求 (选填)</label>
                    <textarea
                      value={userRequest}
                      onChange={(e) => setUserRequest(e.target.value)}
                      placeholder="请输入您的特殊要求..."
                      rows="2"
                      className="form-textarea"
                      disabled={isProcessing}
                      style={{
                        WebkitAppearance: 'none',
                        borderRadius: '4px'
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            <div className="mode-selector">
              <button
                type="button"
                className={`mode-button ${mode === 'resume' ? 'active' : ''}`}
                onClick={() => handleModeChange('resume')}
                disabled={isProcessing}
              >
                简历打分
              </button>
              <button
                type="button"
                className={`mode-button ${mode === 'chat' ? 'active' : ''}`}
                onClick={() => handleModeChange('chat')}
                disabled={isProcessing}
              >
                自由问答
              </button>
              <div className="send-button-container">
                <button
                  type="submit"
                  className="send-button"
                  disabled={isSendDisabled}
                  title={isProcessing ? '系统正在处理中' : ''}
                  style={{
                    touchAction: 'manipulation',
                    WebkitTapHighlightColor: 'transparent'
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  )
}

export default InputArea