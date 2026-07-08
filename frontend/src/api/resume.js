import request from './request'

/**
 * 获取简历分析结果
 * @param {number} resumeId
 * @returns {Promise<{id, filename, suggestions: Array, total_issues: number}>}
 */
export function getResumeDetail(resumeId) {
  return request.get(`/resume/${resumeId}`)
}

/**
 * 上传简历（PDF）
 * @param {File} file
 * @returns {Promise<{id, filename, file_url, created_at}>}
 */
export function uploadResume(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * 分析简历
 * @param {number} resumeId
 * @param {string} targetJd 目标 JD 文本（可选）
 * @returns {Promise<{id, filename, suggestions: Array, total_issues: number}>}
 */
export function analyzeResume(resumeId, targetJd = '') {
  return request.post(`/resume/analyze/${resumeId}`, { target_jd: targetJd })
}
