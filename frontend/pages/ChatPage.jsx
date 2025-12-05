import React, { useState, useRef, useEffect } from 'react'
import Sidebar from '../src/components/Sidebar'
import ChatArea from '../src/components/ChatArea'
import InputArea from '../src/components/InputArea'
import {
  resumeOptimizationAPI,
  resumeOptimizationChatAPI,
  getResumeOptimizationResult
} from '../src/utils/api'
import '../src/css/ChatPage.css'

// 创建简历内容上下文（如果需要全局共享）
export const ResumeContext = React.createContext()

const ChatPage = () => {
  const [messages, setMessages] = useState([])
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [activeChat, setActiveChat] = useState(null)
  const [mode, setMode] = useState('chat')
  const [pendingTaskId, setPendingTaskId] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)

  // 添加完整的简历优化全局状态
  const [resumeOptimizationData, setResumeOptimizationData] = useState({
    // 简历内容
    resumeContent: '',

    // 用户提交的优化信息
    jobName: '',           // 岗位名称
    jobDescription: '',    // 岗位描述
    companyInfo: '',       // 公司信息
    userRequest: '',       // 用户备注或特殊要求

    // 元数据
    lastUpdated: null,     // 最后更新时间
    hasOptimization: false // 是否有优化记录
  })

  // 保持向后兼容
  const [cleanedResumeText, setCleanedResumeText] = useState('')

  // 移除原来的 interval 状态，改用 ref 来管理
  const pollingIntervalRef = useRef(null)
  const pollingTimeoutRef = useRef(null)
  const maxPollingTimeRef = useRef(3000000)
  const pollingStartTimeRef = useRef(null)

  // 轮询参数配置
  const POLLING_CONFIG = {
    initialDelay: 2000, // 首次查询延迟2秒
    interval: 3000, // 轮询间隔3秒
    maxAttempts: 100, // 最大轮询次数
    backoffFactor: 1.5, // 退避因子
    maxInterval: 10000, // 最大间隔10秒
  }

  // 清理轮询相关资源
  const cleanupPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    if (pollingTimeoutRef.current) {
      clearTimeout(pollingTimeoutRef.current)
      pollingTimeoutRef.current = null
    }
    pollingStartTimeRef.current = null
  }

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      cleanupPolling()
    }
  }, [])

  // 更新简历优化数据的函数
  const updateResumeOptimizationData = (data) => {
    setResumeOptimizationData(prev => ({
      ...prev,
      ...data,
      lastUpdated: new Date().toISOString(),
      hasOptimization: true
    }))
  }

  // 更新特定字段的函数
  const updateResumeContent = (content) => {
    updateResumeOptimizationData({ resumeContent: content })
    setCleanedResumeText(content) // 保持向后兼容
  }

  // 解析后端返回的混合内容，分离系统回复和简历内容
  const parseMixedContent = (content) => {
    if (!content || typeof content !== 'string') {
      return {
        systemReply: content || '',
        resumeText: ''
      }
    }

    // 匹配格式：系统回复###$$$简历文本$$$###：简历内容
    const separator = '###$$$简历文本$$$###：'
    const separatorIndex = content.indexOf(separator)

    if (separatorIndex === -1) {
      // 如果没有分隔符，整个内容作为系统回复
      return {
        systemReply: content,
        resumeText: ''
      }
    }

    // 分离系统回复和简历内容
    const systemReply = content.substring(0, separatorIndex).trim()
    const resumeText = content.substring(separatorIndex + separator.length).trim()

    return {
      systemReply,
      resumeText
    }
  }

  // 轮询任务结果的方法
  const pollResumeOptimizationResult = async (taskId) => {
    cleanupPolling() // 先清理之前的轮询

    pollingStartTimeRef.current = Date.now()
    let pollCount = 0
    let currentInterval = POLLING_CONFIG.interval
    let processingMessageId = null

    // 添加处理中的消息
    const addProcessingMessage = () => {
      const message = {
        id: Date.now(),
        content: '简历正在处理中，请稍候...',
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        mode: 'resume',
        isProgress: true
      }
      setMessages(prev => [...prev, message])
      return message.id
    }

    processingMessageId = addProcessingMessage()

    // 轮询函数
    const pollTask = async () => {
      const elapsedTime = Date.now() - pollingStartTimeRef.current

      // // 检查是否超时
      // if (elapsedTime > maxPollingTimeRef.current) {
      //   cleanupPolling()
      //   setMessages(prev => prev.filter(msg => msg.id !== processingMessageId))
      //
      //   const timeoutMessage = {
      //     id: Date.now(),
      //     content: '简历处理超时（已等待5分钟），请稍后重试或联系客服',
      //     isUser: false,
      //     timestamp: new Date().toLocaleTimeString(),
      //     mode: 'resume',
      //     isError: true
      //   }
      //   setMessages(prev => [...prev, timeoutMessage])
      //
      //   setPendingTaskId(null)
      //   setIsProcessing(false)
      //   return
      // }

      pollCount++

      try {
        const result = await getResumeOptimizationResult(taskId)

        if (result.status === 'success') {
          // 任务完成，清理轮询并显示结果
          cleanupPolling()
          setMessages(prev => prev.filter(msg => msg.id !== processingMessageId))

          // 获取返回内容
          const resultContent = result.message || result.optimized_content || ''

          // 解析混合内容
          const { systemReply, resumeText } = parseMixedContent(resultContent)

          // 存储简历内容到全局状态
          if (resumeText) {
            updateResumeContent(resumeText)
          }

          // 添加成功消息（只显示系统回复部分）
          const successMessage = {
            id: Date.now(),
            content: systemReply,
            isUser: false,
            timestamp: new Date().toLocaleTimeString(),
            mode: 'resume',
            isOptimizedResult: true,
            // 存储简历内容和优化说明
            resumeContent: resumeText,
          }
          setMessages(prev => [...prev, successMessage])

          setPendingTaskId(null)
          setIsProcessing(false)

        } else if (result.status === 'processing') {
          // 任务仍在处理中，更新等待消息
          setMessages(prev => prev.map(msg =>
            msg.id === processingMessageId
              ? {
                  ...msg,
                  content: getProcessingMessage(pollCount, elapsedTime)
                }
              : msg
          ))

          // 使用退避策略
          if (pollCount > 5) {
            currentInterval = Math.min(
              currentInterval * POLLING_CONFIG.backoffFactor,
              POLLING_CONFIG.maxInterval
            )

            // 重新设置轮询间隔
            cleanupPolling()
            pollingIntervalRef.current = setInterval(pollTask, currentInterval)
          }

        } else if (result.status === 'not_found') {
          // 任务未找到
          cleanupPolling()
          setMessages(prev => prev.filter(msg => msg.id !== processingMessageId))

          const errorMessage = {
            id: Date.now(),
            content: '任务处理失败或任务ID无效',
            isUser: false,
            timestamp: new Date().toLocaleTimeString(),
            mode: 'resume',
            isError: true
          }
          setMessages(prev => [...prev, errorMessage])

          setPendingTaskId(null)
          setIsProcessing(false)

        } else {
          // 其他错误状态
          cleanupPolling()
          setMessages(prev => prev.filter(msg => msg.id !== processingMessageId))

          const errorMessage = {
            id: Date.now(),
            content: `处理失败: ${result.message || '未知错误'}`,
            isUser: false,
            timestamp: new Date().toLocaleTimeString(),
            mode: 'resume',
            isError: true
          }
          setMessages(prev => [...prev, errorMessage])

          setPendingTaskId(null)
          setIsProcessing(false)
        }

      } catch (error) {
        console.error('轮询任务结果失败:', error)

        // 更新错误消息，继续轮询
        setMessages(prev => prev.map(msg =>
          msg.id === processingMessageId
            ? {
                ...msg,
                content: `连接服务器失败，正在重试... (${pollCount}次)`
              }
            : msg
        ))

        // 发生错误时也使用退避策略
        if (pollCount > 3) {
          currentInterval = Math.min(
            currentInterval * POLLING_CONFIG.backoffFactor,
            POLLING_CONFIG.maxInterval
          )

          cleanupPolling()
          pollingIntervalRef.current = setInterval(pollTask, currentInterval)
        }
      }
    }

    // 根据轮询次数和等待时间生成不同的处理消息
    const getProcessingMessage = (count, elapsed) => {
      const elapsedSeconds = Math.floor(elapsed / 1000)
        return '简历正在处理中，请稍候...'
      // if (elapsedSeconds < 30) {
      //
      // } else if (elapsedSeconds < 60) {
      //   return `简历处理中，可能需要更多时间... (${elapsedSeconds}秒)`
      // } else {
      //   return `简历仍在处理，请耐心等待... (${elapsedSeconds}秒，已查询${count}次)`
      // }
    }

    // 首次延迟后开始轮询
    pollingTimeoutRef.current = setTimeout(() => {
      pollTask() // 立即执行一次
      pollingIntervalRef.current = setInterval(pollTask, currentInterval)
    }, POLLING_CONFIG.initialDelay)
  }

  // 当 pendingTaskId 变化时启动轮询
  useEffect(() => {
    if (pendingTaskId && !pollingIntervalRef.current) {
      pollResumeOptimizationResult(pendingTaskId)
    }

    // 清理函数
    return () => {
      if (!pendingTaskId) {
        cleanupPolling()
      }
    }
  }, [pendingTaskId])

  const handleSendMessage = async (message, currentMode, resumeData = null) => {
    if (isProcessing) {
      console.log('系统正在处理中，请稍候...')
      return
    }

    const newMessage = {
      id: Date.now(),
      content: message,
      isUser: true,
      timestamp: new Date().toLocaleTimeString(),
      mode: currentMode
    }
    setMessages(prev => [...prev, newMessage])

    try {
      setIsProcessing(true)

      if (currentMode === 'resume' && resumeData) {
        // 保存完整的简历优化信息
        const optimizationData = {
          jobName: resumeData.jobName || '',
          jobDescription: resumeData.jobDescription || '',
          companyInfo: resumeData.companyInfo || '',
          userRequest: resumeData.userRequest || message
        }

        updateResumeOptimizationData(optimizationData)

        const result = await resumeOptimizationAPI(
          resumeData.resumeFile,
          optimizationData
        )

        if (result.status === "success" && result.message) {
          // 后端返回任务ID，开始轮询
          setPendingTaskId(result.message)
        } else {
          throw new Error(result.message || '任务提交失败')
        }
      } else {
        // 自由问答模式 - 构建包含完整简历优化信息的res_opt_record
        // 1. 获取当前模式下的聊天记录
        const chatHistoryMessages = messages.filter(msg => msg.mode === 'chat')

        // 2. 构建历史聊天记录字符串（限制最大字符量）
        let historyChatRecord = ''
        const MAX_CHAT_HISTORY_LENGTH = 3000

        // 逆序获取最近的聊天记录，直到达到最大限制
        for (let i = chatHistoryMessages.length - 1; i >= 0; i--) {
          const msg = chatHistoryMessages[i]
          const formattedMsg = `${msg.isUser ? '用户' : '助手'}: ${msg.content}\n`

          if ((historyChatRecord.length + formattedMsg.length) > MAX_CHAT_HISTORY_LENGTH) {
            break
          }
          historyChatRecord = formattedMsg + historyChatRecord // 保持时间顺序
        }

        // 3. 构建简历优化记录 - 包含完整的简历优化信息
        let resOptRecord = ''
        const MAX_RESUME_RECORD_LENGTH = 6000 // 增加长度限制，因为要包含更多信息

        // 第一部分：简历优化基本信息
        const resumeRecordItems = []

        // 1.1 简历文本（最近一次的完整简历）
        if (resumeOptimizationData.resumeContent) {
          resumeRecordItems.push('[简历文本（最近一次优化）]')
          resumeRecordItems.push(getTruncatedResumeText(resumeOptimizationData.resumeContent, 1800))
        }

        // 1.2 岗位信息
        if (resumeOptimizationData.jobName || resumeOptimizationData.jobDescription) {
          resumeRecordItems.push('[岗位信息]')
          if (resumeOptimizationData.jobName) {
            resumeRecordItems.push(`岗位名称: ${resumeOptimizationData.jobName}`)
          }
          if (resumeOptimizationData.jobDescription) {
            resumeRecordItems.push(`岗位描述: ${getTruncatedText(resumeOptimizationData.jobDescription, 1000)}`)
          }
        }

        // 1.3 公司信息
        if (resumeOptimizationData.companyInfo) {
          resumeRecordItems.push('[公司信息]')
          resumeRecordItems.push(getTruncatedText(resumeOptimizationData.companyInfo, 1200))
        }

        // 1.4 用户备注或特殊要求
        if (resumeOptimizationData.userRequest) {
          resumeRecordItems.push('[用户备注/特殊要求]')
          resumeRecordItems.push(resumeOptimizationData.userRequest)
        }

        // 如果没有任何简历相关信息，添加一个标记
        if (resumeRecordItems.length === 0) {
          resumeRecordItems.push('[暂无简历优化记录]')
        }

        // 4. 组合并限制总长度
        let currentResumeText = resumeRecordItems.join('\n')

        // 智能压缩策略：优先保留核心信息
        if (currentResumeText.length > MAX_RESUME_RECORD_LENGTH) {
          console.log('简历优化记录过长，进行智能压缩...')

          // 创建重要性权重：简历文本 > 岗位信息 > 用户要求 > 其他信息
          const importantItems = []
          const lessImportantItems = []

          for (const item of resumeRecordItems) {
            if (item.includes('[简历文本') || item.includes('岗位名称') ||
                item.includes('岗位描述') || item.includes('[用户备注')) {
              importantItems.push(item)
            } else {
              lessImportantItems.push(item)
            }
          }

          // 先构建重要信息
          let compressedText = importantItems.join('\n')
          let remainingSpace = MAX_RESUME_RECORD_LENGTH - compressedText.length

          // 如果还有空间，添加次要信息
          if (remainingSpace > 100) {
            for (const item of lessImportantItems) {
              if (remainingSpace - item.length - 1 > 0) {
                compressedText += '\n' + item
                remainingSpace -= (item.length + 1)
              } else {
                break
              }
            }
          }

          resOptRecord = compressedText
        } else {
          resOptRecord = currentResumeText
        }

        console.log('发送到后端的参数:')
        console.log('history_chat_record 长度:', historyChatRecord.length)
        console.log('user_prompt:', message)
        console.log('res_opt_record 长度:', resOptRecord.length)
        console.log('简历优化信息包含:')
        console.log('- 简历文本:', resumeOptimizationData.resumeContent ? '是' : '否')
        console.log('- 岗位名称:', resumeOptimizationData.jobName || '无')
        console.log('- 岗位描述:', resumeOptimizationData.jobDescription ? '是' : '否')
        console.log('- 公司信息:', resumeOptimizationData.companyInfo ? '是' : '否')
        console.log('- 用户要求:', resumeOptimizationData.userRequest || '无')

        // 5. 调用API
        const result = await resumeOptimizationChatAPI({
          history_chat_record: historyChatRecord,
          user_prompt: message,
          res_opt_record: resOptRecord
        })

        const aiMessage = {
          id: Date.now() + 1,
          content: result.message || result.content || "收到您的请求，正在处理中...",
          isUser: false,
          timestamp: new Date().toLocaleTimeString(),
          mode: currentMode
        }
        setMessages(prev => [...prev, aiMessage])

        setIsProcessing(false)
      }
    } catch (error) {
      console.error('API调用失败:', error)
      setIsProcessing(false)

      // 清理轮询（如果有）
      cleanupPolling()
      setPendingTaskId(null)

      const errorMessage = {
        id: Date.now() + 1,
        content: `抱歉，服务暂时不可用：${error.message}`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString(),
        mode: currentMode,
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  // 辅助函数：获取截断后的简历文本
  const getTruncatedResumeText = (text, maxLength) => {
    if (!text) return ''

    if (text.length > maxLength) {
      return text.substring(0, maxLength) + '...（内容已截断）'
    }
    return text
  }

  // 辅助函数：获取截断后的文本
  const getTruncatedText = (text, maxLength) => {
    if (!text) return ''

    if (text.length > maxLength) {
      return text.substring(0, maxLength) + '...'
    }
    return text
  }

  // 添加函数：清除所有简历优化内容
  const clearResumeOptimizationData = () => {
    setResumeOptimizationData({
      resumeContent: '',
      jobName: '',
      jobDescription: '',
      companyInfo: '',
      userRequest: '',
      optimizedResume: '',
      optimizationNotes: '',
      lastUpdated: null,
      hasOptimization: false
    })
    setCleanedResumeText('')
  }

  const handleModeChange = (newMode) => {
    if (isProcessing) {
      console.log('系统正在处理中，请稍候再切换模式')
      return
    }

    setMode(newMode)
    // 清理轮询状态
    cleanupPolling()
    setPendingTaskId(null)
  }

  const handleNewChat = () => {
    if (isProcessing) {
      console.log('系统正在处理中，请稍候再开始新对话')
      return
    }

    setMessages([])
    clearResumeOptimizationData()
    setActiveChat(null)

    // 清理轮询状态
    cleanupPolling()
    setPendingTaskId(null)
    setIsProcessing(false)
  }

  const handleRetryTaskQuery = () => {
    if (pendingTaskId && !isProcessing) {
      // 重新开始轮询
      cleanupPolling()
      pollResumeOptimizationResult(pendingTaskId)
    }
  }

  // 添加缺失的函数
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen)
  }

  const handleChatSelect = (chatId) => {
    setActiveChat(chatId)
  }

  const getCurrentModeMessages = () => {
    return messages.filter(msg => msg.mode === mode)
  }

  return (
    <div className="chat-page">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onNewChat={handleNewChat}
        activeChat={activeChat}
        onChatSelect={handleChatSelect}
        isProcessing={isProcessing}
        // 传递简历优化数据给子组件
        resumeOptimizationData={resumeOptimizationData}
        onUpdateResumeOptimizationData={updateResumeOptimizationData}
      />
      <div className={`main-content ${!isSidebarOpen ? 'full-width' : ''}`}>
        <div className="header">
          {/*<button*/}
          {/*  className="menu-button"*/}
          {/*  onClick={toggleSidebar}*/}
          {/*  disabled={isProcessing}*/}
          {/*>*/}
          {/*  ☰*/}
          {/*</button>*/}
          {/*<h1>{mode === 'resume' ? '简历优化' : '自由问答'}</h1>*/}
          {(isProcessing || pendingTaskId) && (
            <div className="processing-indicator">
              🔄 {'处理中...'}
            </div>
          )}
        </div>
        <div className="chat-container">
          <ChatArea
            messages={getCurrentModeMessages()}
            mode={mode}
            onRetryTask={handleRetryTaskQuery}
            canRetry={!!pendingTaskId && !isProcessing}
            // 传递简历优化数据给ChatArea
            resumeOptimizationData={resumeOptimizationData}
            onUpdateResumeOptimizationData={updateResumeOptimizationData}
          />
          <InputArea
            onSendMessage={handleSendMessage}
            mode={mode}
            onModeChange={handleModeChange}
            disabled={isProcessing || !!pendingTaskId}
            isProcessing={isProcessing}
            // 传递简历优化数据给InputArea
            resumeOptimizationData={resumeOptimizationData}
          />
        </div>
      </div>
    </div>
  )
}

export default ChatPage