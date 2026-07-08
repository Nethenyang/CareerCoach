import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const userId = ref(localStorage.getItem('userId') || null)
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))

  const isLoggedIn = computed(() => userId.value !== null)

  /**
   * 登录
   */
  async function login(username, password) {
    const data = await loginApi(username, password)
    userId.value = data.id
    userInfo.value = data
    localStorage.setItem('userId', data.id)
    localStorage.setItem('userInfo', JSON.stringify(data))
    return data
  }

  /**
   * 注册
   */
  async function register(username, password, nickname) {
    return await registerApi(username, password, nickname)
  }

  /**
   * 退出登录
   */
  function logout() {
    userId.value = null
    userInfo.value = null
    localStorage.removeItem('userId')
    localStorage.removeItem('userInfo')
  }

  return { userId, userInfo, isLoggedIn, login, register, logout }
})
