<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const isLogin = ref(true)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const registerForm = reactive({
  username: '',
  password: '',
  nickname: '',
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名 3-50 字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码 6-128 字符', trigger: 'blur' },
  ],
}

const loginFormRef = ref()
const registerFormRef = ref()

async function handleLogin() {
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login(loginForm.username, loginForm.password)
      ElMessage.success('登录成功')
      router.push('/')
    } catch {
    } finally {
      loading.value = false
    }
  })
}

async function handleRegister() {
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.register(
        registerForm.username,
        registerForm.password,
        registerForm.nickname,
      )
      ElMessage.success('注册成功，请登录')
      loginForm.username = registerForm.username
      loginForm.password = ''
      isLogin.value = true
    } catch {
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <div class="login-page">
    <div class="login-brand">
      <h1>简历洞察</h1>
      <p>AI 简历分析与面试辅导平台</p>
    </div>

    <transition name="slide-fade" mode="out-in">
      <div :key="isLogin ? 'login' : 'register'" class="login-card">
        <h2 class="form-title">{{ isLogin ? '登录' : '注册' }}</h2>

        <!-- 登录表单 -->
        <el-form
          v-if="isLogin"
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          label-width="0"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="用户名"
              size="large"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              size="large"
              show-password
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="submit-btn"
            @click="handleLogin"
          >
            登录
          </el-button>
          <p class="switch-text">
            还没有账号？
            <a class="switch-link" @click="isLogin = false">去注册</a>
          </p>
        </el-form>

        <!-- 注册表单 -->
        <el-form
          v-else
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          label-width="0"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="用户名（3-50 字符）"
              size="large"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="密码（6-128 字符）"
              size="large"
              show-password
            />
          </el-form-item>
          <el-form-item prop="nickname">
            <el-input
              v-model="registerForm.nickname"
              placeholder="昵称（可选）"
              size="large"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="submit-btn"
            @click="handleRegister"
          >
            注册
          </el-button>
          <p class="switch-text">
            已有账号？
            <a class="switch-link" @click="isLogin = true">去登录</a>
          </p>
        </el-form>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: var(--bg);
}

.login-brand {
  text-align: center;
  margin-bottom: var(--space-8);
  animation: fadeInUp 0.5s var(--ease-standard) both;
}

.login-brand h1 {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--fg);
}

.login-brand p {
  margin-top: var(--space-2);
  font-size: var(--fs-meta);
  color: var(--muted);
}

.login-card {
  width: 400px;
  max-width: calc(100vw - 48px);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-8) var(--space-8) var(--space-6);
  animation: fadeInUp 0.5s var(--ease-standard) 0.1s both;
}

.form-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 600;
  margin-bottom: var(--space-6);
  color: var(--fg);
}

.submit-btn {
  width: 100%;
  margin-top: var(--space-1);
  font-weight: 500;
  border-radius: var(--radius-sm);
  transition: background var(--motion-fast) ease, transform 0.05s ease;
}
.submit-btn:active {
  transform: translateY(1px);
}

.switch-text {
  text-align: center;
  margin-top: var(--space-5);
  font-size: var(--fs-meta);
  color: var(--muted);
}

.switch-link {
  color: var(--accent);
  cursor: pointer;
  font-weight: 500;
}
.switch-link:hover {
  text-decoration: underline;
}

/* 表单切换过渡 */
.slide-fade-enter-active {
  transition: all 0.3s var(--ease-standard);
}
.slide-fade-leave-active {
  transition: all 0.2s var(--ease-standard);
}
.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(12px);
}
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}

/* Element Plus 输入框覆写 */
:deep(.el-input__wrapper) {
  border-radius: var(--radius-sm);
  box-shadow: 0 0 0 1px var(--border) inset;
  transition: box-shadow var(--motion-fast) ease;
}
:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--fg) inset;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--accent) inset, var(--focus-ring);
}
</style>
