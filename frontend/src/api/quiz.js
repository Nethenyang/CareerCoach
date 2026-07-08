import request from './request'

/**
 * 创建测验 + AI 生成题目
 * @param {number} conversationId
 * @param {string} title
 * @param {number} questionCount
 * @param {string} userRequirements
 * @returns {Promise<{session: Object, questions: Array}>}
 */
export function createQuiz(conversationId, title, questionCount, userRequirements) {
  return request.post('/quiz/create', {
    conversation_id: conversationId,
    title,
    question_count: questionCount,
    user_requirements: userRequirements || '',
  })
}

/**
 * 提交单题答案
 * @param {number} sessionId
 * @param {number} questionId
 * @param {string} selectedOptionId
 * @returns {Promise<{is_correct: boolean, correct_option_id: string, explanation: string}>}
 */
export function answerQuestion(sessionId, questionId, selectedOptionId) {
  return request.post(`/quiz/answer/${sessionId}`, {
    question_id: questionId,
    selected_option_id: selectedOptionId,
  })
}

/**
 * 结束测验并生成报告
 * @param {number} sessionId
 * @returns {Promise<Object>}
 */
export function finishQuiz(sessionId) {
  return request.post(`/quiz/finish/${sessionId}`)
}

/**
 * 测验历史列表
 * @param {number} conversationId
 * @param {number} page
 * @param {number} pageSize
 * @returns {Promise<{total: number, items: Array}>}
 */
export function listQuizzes(conversationId, page = 1, pageSize = 20) {
  return request.get('/quiz/list', { params: { conversation_id: conversationId, page, page_size: pageSize } })
}

/**
 * 测验详情（含所有题目 + 报告）
 * @param {number} sessionId
 * @returns {Promise<{session: Object, questions: Array}>}
 */
export function getQuizDetail(sessionId) {
  return request.get(`/quiz/${sessionId}`)
}

/**
 * 删除测验
 * @param {number} sessionId
 */
export function deleteQuiz(sessionId) {
  return request.delete(`/quiz/${sessionId}`)
}

/**
 * 重置测验（清空答案和报告，恢复 in_progress）
 * @param {number} sessionId
 * @returns {Promise<{session: Object, questions: Array}>}
 */
export function resetQuiz(sessionId) {
  return request.post(`/quiz/reset/${sessionId}`)
}
