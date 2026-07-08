import request from './request'

/**
 * 用户登录
 * @param {string} username
 * @param {string} password
 * @returns {Promise<{id, username, nickname, avatar_url, status, created_at, last_login_at}>}
 */
export function login(username, password) {
  return request.post('/auth/login', { username, password })
}

/**
 * 用户注册
 * @param {string} username
 * @param {string} password
 * @param {string} nickname
 */
export function register(username, password, nickname) {
  return request.post('/auth/register', { username, password, nickname })
}
