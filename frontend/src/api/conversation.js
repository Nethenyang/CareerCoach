import request from './request'

/**
 * 新建对话（必须绑定简历）
 * @param {number} resumeId 关联简历 ID
 * @param {string} title 可选标题，不传则后端自动从简历文件名生成
 * @returns {Promise<{id, user_id, resume_id, title, created_at, updated_at}>}
 */
export function createConversation(resumeId, title) {
  return request.post('/conversation/create', { resume_id: resumeId, title })
}

/**
 * 发送消息
 * @param {number} conversationId
 * @param {string} content
 * @returns {Promise<{user_message: Object, ai_message: Object}>}
 */
export function sendMessage(conversationId, content) {
  return request.post(`/conversation/message/${conversationId}`, { content })
}

/**
 * 对话列表
 * @param {number} page
 * @param {number} pageSize
 * @returns {Promise<{total, page, page_size, items: Array}>}
 */
export function listConversations(page = 1, pageSize = 20) {
  return request.get('/conversation/list', { params: { page, page_size: pageSize } })
}

/**
 * 获取对话历史消息
 * @param {number} conversationId
 * @returns {Promise<{conversation_id, title, messages: Array}>}
 */
export function getMessages(conversationId) {
  return request.get(`/conversation/messages/${conversationId}`)
}

/**
 * 重命名对话
 * @param {number} conversationId
 * @param {string} title
 */
export function renameConversation(conversationId, title) {
  return request.put(`/conversation/rename/${conversationId}`, { title })
}

/**
 * 流式发送消息（逐字返回 AI 回复）
 * @param {number} conversationId
 * @param {string} content
 * @param {function(string)} onToken - 每收到一个 token 调用
 * @param {function(object)} onDone - 流结束时调用 { message_id, user_message_id, created_at }
 * @param {function(Error)} onError - 出错时调用
 */
export async function sendMessageStream(conversationId, content, onToken, onDone, onError) {
  try {
    const userId = localStorage.getItem('userId')
    const response = await fetch(`/api/conversation/message/${conversationId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(userId ? { 'X-User-Id': userId } : {}),
      },
      body: JSON.stringify({ content }),
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.message || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      // SSE 事件以 \n\n 分隔
      const lines = buffer.split('\n\n')
      // 最后一段可能不完整，保留
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data: ')) continue
        const jsonStr = trimmed.slice(6) // 去掉 "data: " 前缀
        try {
          const data = JSON.parse(jsonStr)
          if (data.type === 'token') {
            onToken(data.content)
          } else if (data.type === 'done') {
            onDone(data)
          }
        } catch {
          // 解析失败跳过
        }
      }
    }
  } catch (err) {
    onError(err)
  }
}

/**
 * 删除对话
 * @param {number} conversationId
 */
export function deleteConversation(conversationId) {
  return request.delete(`/conversation/${conversationId}`)
}
