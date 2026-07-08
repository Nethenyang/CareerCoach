<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { listConversations } from '@/api/conversation'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// # 1. 对话列表（下拉菜单用）
const conversationList = ref([])
const convMenuOpen = ref(false)

const activeConvId = computed(() => {
  const id = route.query.conversation_id
  return id ? Number(id) : null
})

const activeResumeId = computed(() => {
  if (!activeConvId.value) return null
  const conv = conversationList.value.find((c) => c.id === activeConvId.value)
  return conv?.resume_id || null
})

async function loadConversations() {
  try {
    const data = await listConversations(1, 50)
    conversationList.value = data.items || []
  } catch {
    // 静默失败，不影响页面
  }
}

function selectConv(id) {
  convMenuOpen.value = false
  router.push({ path: '/app/chat', query: { conversation_id: id } })
}

function handleLogout() {
  convMenuOpen.value = false
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

// # 2. 步骤点 — 与路由对应
const steps = [
  { path: '/', label: '欢迎' },
  { path: '/app/resume', label: '简历' },
  { path: '/app/chat', label: '对话' },
]

function isActiveStep(step) {
  if (step.path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(step.path)
}

function getStepState(index) {
  let currentIdx = 0
  for (let i = 0; i < steps.length; i++) {
    if (isActiveStep(steps[i])) {
      currentIdx = i
    }
  }
  if (index < currentIdx) return 'done'
  if (index === currentIdx) return 'active'
  return ''
}

const hasConversations = computed(() => conversationList.value.length > 0)

function canGoStep(step) {
  if (step.path === '/app/chat') return hasConversations.value
  return true
}

function goStep(step) {
  if (!canGoStep(step)) return
  if (step.path === '/app/resume' && activeResumeId.value) {
    router.push({ path: '/app/resume', query: { resume_id: activeResumeId.value } })
  } else {
    router.push(step.path)
  }
}

onMounted(() => {
  loadConversations()
})

// # 4. 路由变化时刷新对话列表（新建对话后能及时看到）
watch(() => route.path, () => {
  loadConversations()
})
</script>

<template>
  <div class="app-shell">
    <!-- 顶部导航 -->
    <header class="topnav">
      <div class="topnav-inner">
        <span class="logo">简历洞察</span>

        <nav class="step-nav">
          <span
            v-for="(step, i) in steps"
            :key="step.path"
            class="step-item"
            :class="[getStepState(i), { disabled: !canGoStep(step) }]"
            @click="goStep(step)"
          >
            <span class="step-num">{{ i + 1 }}</span>
            <span class="step-name">{{ step.label }}</span>
          </span>
        </nav>

        <!-- 右侧：用户菜单按钮 -->
        <div class="menu-wrapper">
          <button class="menu-btn" @click.stop="convMenuOpen = !convMenuOpen">
            <span class="menu-user">{{ userStore.userInfo?.nickname || userStore.userInfo?.username }}</span>
            <svg
              class="menu-chevron"
              :class="{ open: convMenuOpen }"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>

          <template v-if="convMenuOpen">
            <div class="menu-backdrop" @click="convMenuOpen = false"></div>
            <div class="menu-dropdown" @click.stop>
              <!-- 对话列表 -->
              <p class="menu-section-label">对话列表</p>
              <div class="menu-conv-list">
                <div
                  v-for="conv in conversationList"
                  :key="conv.id"
                  class="menu-conv-item"
                  :class="{ active: conv.id === activeConvId }"
                  @click="selectConv(conv.id)"
                >
                  <span class="menu-conv-title">{{ conv.title }}</span>
                  <span class="menu-conv-meta">{{ conv.message_count || 0 }} 条</span>
                </div>
                <div v-if="conversationList.length === 0" class="menu-conv-empty">
                  暂无对话
                </div>
              </div>

              <!-- 退出 -->
              <div class="menu-divider"></div>
              <button class="menu-logout" @click="handleLogout">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
                </svg>
                退出登录
              </button>
            </div>
          </template>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* ── 顶部导航 ── */
.topnav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.topnav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--gap-xl);
  height: 56px;
}

.logo {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--fg);
  flex-shrink: 0;
  margin-right: var(--gap-xl);
}

/* ── 步骤导航 ── */
.step-nav {
  display: flex;
  align-items: center;
  gap: 0;
}

.step-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 8px 20px;
  cursor: pointer;
  position: relative;
  color: var(--muted);
  transition: color 0.2s;
}

.step-item:not(:last-child)::after {
  content: '';
  width: 28px;
  height: 2px;
  background: var(--border);
  border-radius: 1px;
  position: absolute;
  right: -18px;
  top: 50%;
  transform: translateY(-50%);
  transition: background 0.4s;
}

.step-item.done:not(:last-child)::after {
  background: var(--success);
}

.step-item:hover:not(.disabled) {
  color: var(--fg);
}

.step-num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  font-family: var(--font-mono);
  background: var(--border);
  color: var(--muted);
  flex-shrink: 0;
  transition: all 0.3s var(--ease-standard);
}

.step-item.active .step-num {
  background: var(--accent);
  color: var(--accent-on);
}

.step-item.done .step-num {
  background: var(--success);
  color: var(--accent-on);
}

.step-name {
  font-size: var(--fs-meta);
  font-weight: 500;
  white-space: nowrap;
}

.step-item.active .step-name {
  color: var(--fg);
  font-weight: 600;
}

.step-item.done .step-name {
  color: var(--muted);
}

.step-item.disabled {
  cursor: not-allowed;
  opacity: 0.35;
}

/* ═════════════════════════════════════════════════ */
/* ── 右侧用户菜单按钮 + 下拉                          */
/* ═════════════════════════════════════════════════ */
.menu-wrapper {
  position: relative;
}

.menu-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  cursor: pointer;
  transition: all var(--motion-fast) ease;
}

.menu-btn:hover {
  border-color: var(--fg);
}

.menu-user {
  font-size: var(--fs-meta);
  font-weight: 500;
  color: var(--fg);
  max-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-chevron {
  transition: transform 0.2s var(--ease-standard);
  color: var(--muted);
  flex-shrink: 0;
}

.menu-chevron.open {
  transform: rotate(180deg);
}

.menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 99;
  background: rgba(0, 0, 0, 0.25);
}

.menu-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 280px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--elev-raised);
  z-index: 100;
  overflow: hidden;
  animation: dropdownIn 0.2s var(--ease-standard) both;
}

@keyframes dropdownIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.menu-section-label {
  font-family: var(--font-mono);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--muted);
  margin: 0;
  padding: var(--space-3) var(--space-3) var(--space-1);
}

.menu-conv-list {
  max-height: 320px;
  overflow-y: auto;
  padding: 0 var(--space-2) var(--space-1);
}

.menu-conv-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--motion-fast) ease;
}

.menu-conv-item:hover {
  background: var(--bg);
}

.menu-conv-item.active {
  background: color-mix(in oklab, var(--accent), transparent 92%);
}

.menu-conv-title {
  font-size: var(--fs-meta);
  font-weight: 500;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.menu-conv-meta {
  font-size: 11px;
  color: var(--muted);
  flex-shrink: 0;
}

.menu-conv-empty {
  padding: var(--space-4) 0;
  text-align: center;
  font-size: var(--fs-meta);
  color: var(--muted);
}

.menu-divider {
  height: 1px;
  background: var(--border);
  margin: var(--space-1) 0;
}

.menu-logout {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: var(--fs-meta);
  color: var(--muted);
  transition: all var(--motion-fast) ease;
}

.menu-logout:hover {
  color: var(--danger);
  background: color-mix(in oklab, var(--danger), transparent 95%);
}

/* ── 主内容 ── */
.content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
