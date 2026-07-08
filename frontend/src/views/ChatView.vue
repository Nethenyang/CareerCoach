<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  listConversations,
  getMessages,
  sendMessageStream,
} from '@/api/conversation'
import { getResumeDetail } from '@/api/resume'
import { useUserStore } from '@/stores/user'
import ScoreGauge from '@/components/ScoreGauge.vue'
import SkillBars from '@/components/SkillBars.vue'
import DimensionReport from '@/components/DimensionReport.vue'
import QuizPanel from '@/components/QuizPanel.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const conversationList = ref([])
const activeConversationId = ref(null)

const messages = ref([])
const messageLoading = ref(false)
const aiTyping = ref(false)

const inputContent = ref('')
const sending = ref(false)

const scrollContainer = ref()

// # 1. 分析结果 — 左侧标签页 + 右侧常驻建议
const analysisResult = ref(null)
const analysisLoading = ref(false)

const activeResumeId = computed(() => {
  if (!activeConversationId.value) return null
  const conv = conversationList.value.find((c) => c.id === activeConversationId.value)
  return conv?.resume_id || null
})

function goFullReport() {
  if (!activeResumeId.value) return
  router.push({ path: '/app/resume', query: { resume_id: activeResumeId.value } })
}
const chatTab = ref('ability')
const suggestionIndex = ref(0)

// 右侧栏 Tab 切换
const rightPanelTab = ref('suggestions')  // 'suggestions' | 'quiz'

function prevSuggestion() {
  if (!analysisResult.value?.suggestions) return
  const len = analysisResult.value.suggestions.length
  suggestionIndex.value = (suggestionIndex.value - 1 + len) % len
}
function nextSuggestion() {
  if (!analysisResult.value?.suggestions) return
  const len = analysisResult.value.suggestions.length
  suggestionIndex.value = (suggestionIndex.value + 1) % len
}

function insertSuggestionToChat() {
  const sug = analysisResult.value?.suggestions?.[suggestionIndex.value]
  if (!sug) return
  const type = suggestionTypeMap[sug.type] || sug.type
  inputContent.value = `关于「${sug.location}」的${type}建议（${sug.issue}），能详细展开说说吗？`
}

// QuizPanel Explain → 填聊天区输入框
function handleQuizExplain(prompt) {
  inputContent.value = prompt
}

const chatTabs = [
  { key: 'ability', label: '能力评估' },
  { key: 'dimension', label: '维度分析' },
  { key: 'tier', label: '梯队建议' },
  { key: 'jobs', label: '推荐岗位' },
]

const availableChatTabs = computed(() => {
  if (!analysisResult.value) return []
  const tabs = []
  if (analysisResult.value.ability_profile) tabs.push('ability')
  if (analysisResult.value.dimension_report?.dimensions?.length) tabs.push('dimension')
  if (analysisResult.value.tier_suggestion) tabs.push('tier')
  if (analysisResult.value.retrieved_jds?.length) tabs.push('jobs')
  return tabs
})

const quickAsks = [
  '这份简历最大的优势是什么？',
  '如何优化排版让 ATS 更容易通过？',
  '我的技能标签够不够全面？',
  '适合投递哪些公司的什么岗位？',
]

const tierMap = {
  startup: '初创公司',
  mid: '中型公司',
  big_edge: '大厂边缘',
  big_core: '大厂核心',
}

const suggestionTypeMap = {
  verb_replacement: '弱动词',
  missing_quantification: '缺少量化',
  structure: '结构问题',
  jd_gap: 'JD 差距',
}

function truncate(text, maxLen) {
  if (!text) return ''
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + '…'
}

function renderMarkdown(text) {
  if (!text) return ''
  // 1) 先把代码块和内联代码提走，占位保护
  const blocks = []
  let html = text
    .replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
      blocks.push(`<pre class="md-code"><code${lang ? ` class="language-${lang}"` : ''}>${code.trim().replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`)
      return `\x00BLOCK${blocks.length - 1}\x00`
    })
    .replace(/`([^`\n]+)`/g, (_, code) => {
      blocks.push(`<code class="md-inline-code">${code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code>`)
      return `\x00BLOCK${blocks.length - 1}\x00`
    })
  // 2) 转义剩余 HTML
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  // 2.5) 提取表格（先于 Markdown 转换，避免管道符干扰）
  html = html.replace(/(?:^\|.+?\|[ \t]*\n)+/gm, (tableBlock) => {
    const lines = tableBlock.trim().split('\n')
    if (lines.length < 2) return tableBlock
    const parseRow = (line) =>
      line.replace(/^\||\|$/g, '').split('|').map((c) => c.trim())
    const headers = parseRow(lines[0])
    // 跳过分隔行 lines[1]
    let t = '<table class="md-table"><thead><tr>'
    headers.forEach((h) => { t += `<th>${h}</th>` })
    t += '</tr></thead><tbody>'
    for (let i = 2; i < lines.length; i++) {
      t += '<tr>'
      parseRow(lines[i]).forEach((c) => { t += `<td>${c}</td>` })
      t += '</tr>'
    }
    t += '</tbody></table>'
    return t
  })
  // 3) Markdown → HTML
  html = html
    .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a class="md-link" href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>')
    .replace(/^# (.+)$/gm, '<h3 class="md-h3">$1</h3>')
    .replace(/^[\-\*] (.+)$/gm, '<li class="md-li">$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li class="md-li">$1</li>')
    .replace(/((?:<li class="md-li">.*<\/li>\n?)+)/g, '<ul class="md-ul">$1</ul>')
    .replace(/^&gt; (.+)$/gm, '<blockquote class="md-quote"><p>$1</p></blockquote>')
    .replace(/^(---|\*\*\*)$/gm, '<hr class="md-hr">')
  // 4) 段落处理
  html = html.replace(/\n\n+/g, '</p><p class="md-p">')
  html = html.replace(/\n/g, '<br>')
  html = '<p class="md-p">' + html + '</p>'
  html = html.replace(/<p class="md-p"><\/p>/g, '')
  // 5) 还原代码块
  html = html.replace(/\x00BLOCK(\d+)\x00/g, (_, i) => blocks[+i] || '')
  return html
}

async function loadList() {
  try {
    const data = await listConversations(1, 50)
    conversationList.value = data.items || []
    const queryId = route.query.conversation_id
    if (queryId) {
      // # 2. URL 带了 conversation_id，直接选中
      selectConversation(Number(queryId))
    } else if (conversationList.value.length > 0) {
      // # 3. 没有指定，自动选第一个并更新 URL（让 AppLayout 下拉高亮）
      const firstId = conversationList.value[0].id
      router.replace({ path: '/app/chat', query: { conversation_id: firstId } })
    }
  } catch {
  }
}

async function selectConversation(id) {
  if (activeConversationId.value === id) return
  activeConversationId.value = id
  messages.value = []
  messageLoading.value = true

  // # 4. 加载右侧分析结果
  const conv = conversationList.value.find((c) => c.id === id)
  if (conv && conv.resume_id) {
    loadAnalysis(conv.resume_id)
  } else {
    analysisResult.value = null
    suggestionIndex.value = 0
  }

  try {
    const data = await getMessages(id)
    messages.value = data.messages || []
    scrollToBottom()
  } catch {
  } finally {
    messageLoading.value = false
  }
}

async function loadAnalysis(resumeId) {
  analysisLoading.value = true
  analysisResult.value = null
  try {
    const data = await getResumeDetail(resumeId)
    analysisResult.value = data
    // 自动选第一个有数据的标签
    if (data.ability_profile) chatTab.value = 'ability'
    else if (data.tier_suggestion) chatTab.value = 'tier'
    else if (data.retrieved_jds?.length) chatTab.value = 'jobs'
  } catch {
    analysisResult.value = null
    suggestionIndex.value = 0
  } finally {
    analysisLoading.value = false
  }
}

async function handleSend(text) {
  const content = (text || inputContent.value).trim()
  if (!content) return
  if (!activeConversationId.value) {
    ElMessage.warning('请先选择一个对话')
    return
  }

  sending.value = true
  inputContent.value = ''
  // 乐观插入用户消息
  const tempUserMsg = {
    id: Date.now(),
    conversation_id: activeConversationId.value,
    role: 'user',
    content,
    created_at: new Date().toISOString(),
  }
  messages.value.push(tempUserMsg)
  scrollToBottom()

  // 插入占位 AI 消息（流式填充）
  const aiPlaceholderId = Date.now() + 1
  const aiPlaceholder = {
    id: aiPlaceholderId,
    conversation_id: activeConversationId.value,
    role: 'ai',
    content: '',
    created_at: new Date().toISOString(),
  }
  messages.value.push(aiPlaceholder)
  aiTyping.value = true

  sendMessageStream(
    activeConversationId.value,
    content,
    // onToken
    (token) => {
      const msg = messages.value.find(m => m.id === aiPlaceholderId)
      if (msg) {
        msg.content += token
        scrollToBottom()
      }
    },
    // onDone
    (data) => {
      const msg = messages.value.find(m => m.id === aiPlaceholderId)
      if (msg) {
        msg.id = data.message_id
        msg.created_at = data.created_at
      }
      // 替换临时用户消息 ID
      if (data.user_message_id) {
        tempUserMsg.id = data.user_message_id
      }
      const conv = conversationList.value.find((c) => c.id === activeConversationId.value)
      if (conv) {
        conv.message_count = (conv.message_count || 0) + 2
      }
      aiTyping.value = false
      sending.value = false
      scrollToBottom()
    },
    // onError
    (err) => {
      messages.value = messages.value.filter(
        (m) => m.id !== aiPlaceholderId && m.id !== tempUserMsg.id,
      )
      inputContent.value = content
      aiTyping.value = false
      sending.value = false
    },
  )
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTo({
        top: scrollContainer.value.scrollHeight,
        behavior: 'smooth',
      })
    }
  })
}

function formatTime(time) {
  if (!time) return ''
  const d = new Date(time)
  return d.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  loadList()
})

watch(
  () => route.query.conversation_id,
  (newId) => {
    if (!newId) return
    const id = Number(newId)
    if (!id || id === activeConversationId.value) return
    // # 7. 从 AppLayout 下拉切换对话时，加载消息
    if (conversationList.value.length > 0) {
      selectConversation(id)
    } else {
      loadList()
    }
  },
)
</script>

<template>
  <div class="chat-view">
    <!-- ═══ 左栏 — 分析报告 ═══ -->
    <aside v-if="analysisResult" class="analysis-panel">
      <div class="ap-header">
        <span class="ap-title">分析报告</span>
        <button v-if="activeResumeId" class="ap-report-btn" @click="goFullReport" title="查看完整分析报告">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8" />
          </svg>
        </button>
      </div>
      <div class="ap-tabs">
        <button
          v-for="tab in chatTabs"
          :key="tab.key"
          class="ap-tab-btn"
          :class="{ active: chatTab === tab.key, disabled: !availableChatTabs.includes(tab.key) }"
          :disabled="!availableChatTabs.includes(tab.key)"
          @click="chatTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="ap-body">
        <!-- 紧凑评分 -->
        <div v-if="analysisResult.score_assessment" class="ca-score-section">
          <ScoreGauge :score="analysisResult.score_assessment.overall_score" :size="80" />
          <SkillBars :skills="analysisResult.score_assessment.skill_scores" compact />
        </div>

        <!-- 紧凑维度概览 -->
        <div v-if="analysisResult.dimension_report?.dimensions?.length" class="ca-dimension-section">
          <div v-for="d in analysisResult.dimension_report.dimensions" :key="d.name" class="ca-dim-row">
            <span class="ca-dim-name">{{ d.name }}</span>
            <span class="ca-dim-score">{{ d.score }}分</span>
          </div>
        </div>

        <!-- 能力评估 -->
        <div v-if="chatTab === 'ability'" class="ca-section">
          <div class="ca-tag-row">
            <span class="ca-tag">{{ analysisResult.ability_profile.tech_direction }}</span>
            <span class="ca-tag ca-tag-muted">{{ analysisResult.ability_profile.experience_level }}</span>
          </div>
          <p class="ca-summary">{{ analysisResult.ability_profile.summary }}</p>
          <div v-if="analysisResult.ability_profile.skills?.length" class="ca-skill-row">
            <span v-for="sk in analysisResult.ability_profile.skills" :key="sk" class="ca-skill-chip">{{ sk }}</span>
          </div>
          <div v-if="analysisResult.ability_profile.strengths?.length" class="ca-insight-group">
            <h5 class="ca-sub-title" style="color:var(--success)">核心优势</h5>
            <div v-for="(item, i) in analysisResult.ability_profile.strengths" :key="'s'+i" class="ca-insight-item s-good">
              <span class="ca-insight-num">{{ i + 1 }}</span>
              <p>{{ item }}</p>
            </div>
          </div>
          <div v-if="analysisResult.ability_profile.weaknesses?.length" class="ca-insight-group">
            <h5 class="ca-sub-title" style="color:var(--warn)">可优化方向</h5>
            <div v-for="(item, i) in analysisResult.ability_profile.weaknesses" :key="'w'+i" class="ca-insight-item s-warn">
              <span class="ca-insight-num">{{ i + 1 }}</span>
              <p>{{ item }}</p>
            </div>
          </div>
        </div>

        <!-- 维度分析 -->
        <div v-if="chatTab === 'dimension'" class="ca-section">
          <DimensionReport
            v-if="analysisResult.dimension_report?.dimensions?.length"
            :dimensions="analysisResult.dimension_report.dimensions"
          />
          <div v-if="analysisResult.dimension_report?.strategic_suggestions?.length" class="ca-strategy-section">
            <h5 class="ca-sub-title">综合建议</h5>
            <div v-for="(sg, i) in analysisResult.dimension_report.strategic_suggestions" :key="i" class="ca-strategy-group">
              <span class="ca-strategy-title">{{ sg.title }}</span>
              <ul class="ca-strategy-items">
                <li v-for="(item, j) in sg.items" :key="j">{{ item }}</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- 梯队建议 -->
        <div v-if="chatTab === 'tier'" class="ca-section">
          <div class="ca-tier-hero">
            <span class="ca-tier-badge">{{ tierMap[analysisResult.tier_suggestion.tier] || analysisResult.tier_suggestion.tier }}</span>
            <div v-if="analysisResult.tier_suggestion.alternative_tiers?.length" class="ca-tier-alt">
              <span class="ca-tier-alt-label">备选</span>
              <span v-for="t in analysisResult.tier_suggestion.alternative_tiers" :key="t" class="ca-tier-alt-chip">{{ tierMap[t] || t }}</span>
            </div>
          </div>
          <p class="ca-reasoning">{{ analysisResult.tier_suggestion.reasoning }}</p>
        </div>

        <!-- 推荐岗位 -->
        <div v-if="chatTab === 'jobs'" class="ca-section">
          <div v-for="(jd, i) in analysisResult.retrieved_jds" :key="i" class="ca-jd-card">
            <div class="ca-jd-top">
              <span class="ca-jd-num">{{ i + 1 }}</span>
              <div class="ca-jd-info">
                <span class="ca-jd-position">{{ jd.position }}</span>
                <span v-if="jd.company" class="ca-jd-company">{{ jd.company }}</span>
              </div>
              <span v-if="jd.tier" class="ca-jd-tier-tag">{{ tierMap[jd.tier] || jd.tier }}</span>
            </div>
            <p class="ca-jd-req">{{ jd.requirements }}</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- ═══ 中栏 — 对话 ═══ -->
    <div class="chat-area">
      <div v-if="!activeConversationId" class="chat-empty">
        <div class="chat-empty-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
        </div>
        <p class="chat-empty-text">完成简历分析后，将自动创建对话</p>
        <router-link to="/app/resume" class="chat-empty-link">去简历分析</router-link>
      </div>

      <template v-else>
        <!-- 消息列表 -->
        <div ref="scrollContainer" class="chat-messages" v-loading="messageLoading">
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="chat-msg"
            :class="msg.role === 'user' ? 'user' : 'ai'"
          >
            <div class="chat-msg-avatar">
              <svg v-if="msg.role === 'ai'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M12 2a4 4 0 014 4v2a4 4 0 01-8 0V6a4 4 0 014-4z" />
                <path d="M6 20v-2a4 4 0 014-4h4a4 4 0 014 4v2M12 11v3M8 13h8" />
                <circle cx="10" cy="6.5" r="1" fill="currentColor" />
                <circle cx="14" cy="6.5" r="1" fill="currentColor" />
              </svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
            <div class="chat-msg-main">
              <div class="chat-msg-body" v-html="renderMarkdown(msg.content)"></div>
              <span class="chat-msg-time">{{ formatTime(msg.created_at) }}</span>
            </div>
          </div>

          <!-- AI 输入中动画 -->
          <div v-if="aiTyping" class="chat-typing visible">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>

        <!-- 快捷提问 -->
        <div v-if="messages.length <= 1 && !aiTyping" class="quick-asks">
          <button
            v-for="(q, i) in quickAsks"
            :key="i"
            class="quick-ask"
            @click="handleSend(q)"
          >{{ q }}</button>
        </div>

        <!-- 输入区 -->
        <div class="chat-input-row">
          <input
            v-model="inputContent"
            class="chat-input"
            type="text"
            placeholder="输入你的问题…"
            maxlength="300"
            @keydown.enter.exact.prevent="handleSend()"
            :disabled="sending"
          />
          <button
            class="chat-send"
            @click="handleSend()"
            :disabled="!inputContent.trim() || sending"
            aria-label="发送消息"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </div>
      </template>
    </div>

    <!-- ═══ 右栏 — 优化建议翻页 ═══ -->
    <aside class="result-panel">
      <div class="result-panel-header">
        <div class="rp-tabs">
          <button
            class="rp-tab-btn"
            :class="{ active: rightPanelTab === 'suggestions' }"
            @click="rightPanelTab = 'suggestions'"
          >优化建议</button>
          <button
            class="rp-tab-btn"
            :class="{ active: rightPanelTab === 'quiz' }"
            @click="rightPanelTab = 'quiz'"
          >面试测验</button>
        </div>
      </div>

      <!-- Tab: 优化建议 -->
      <div v-show="rightPanelTab === 'suggestions'" v-loading="analysisLoading" class="result-panel-body">
        <div v-if="!analysisResult && !analysisLoading" class="result-empty">
          <p>暂无分析结果</p>
          <router-link to="/app/resume" class="result-empty-link">去简历分析</router-link>
        </div>

        <div v-if="analysisResult && !analysisResult.suggestions?.length && !analysisLoading" class="result-empty">
          <p>暂无优化建议</p>
        </div>

        <template v-if="analysisResult?.suggestions?.length">
          <div class="rp-section" :key="suggestionIndex">
            <div class="rp-suggestion">
              <!-- 类型标签 -->
              <span class="rp-badge">{{
                suggestionTypeMap[analysisResult.suggestions[suggestionIndex].type]
                || analysisResult.suggestions[suggestionIndex].type
              }}</span>

              <!-- 位置信息 -->
              <div class="rp-location">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                <span>{{ analysisResult.suggestions[suggestionIndex].location }}</span>
              </div>

              <!-- 问题描述 -->
              <p class="rp-suggestion-issue">{{ analysisResult.suggestions[suggestionIndex].issue }}</p>

              <!-- 修改前后对比 -->
              <div class="rp-diff-block">
                <div class="rp-diff-row rp-diff-before">
                  <span class="rp-diff-tag">修改前</span>
                  <p class="rp-diff-text">{{ analysisResult.suggestions[suggestionIndex].before }}</p>
                </div>
                <div class="rp-diff-row rp-diff-after">
                  <span class="rp-diff-tag">修改后</span>
                  <p class="rp-diff-text">{{ analysisResult.suggestions[suggestionIndex].after }}</p>
                </div>
              </div>

              <!-- 插入对话 -->
              <button class="rp-ask-btn" @click="insertSuggestionToChat">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
                </svg>
                就这条建议提问
              </button>
            </div>
          </div>

          <!-- 翻页按钮 -->
          <div class="rp-nav">
            <button class="rp-nav-btn" @click="prevSuggestion" :disabled="analysisResult.suggestions.length <= 1" title="上一条">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6" /></svg>
            </button>
            <span class="rp-nav-dots">
              <span
                v-for="(_, i) in analysisResult.suggestions"
                :key="i"
                class="rp-nav-dot"
                :class="{ active: i === suggestionIndex }"
                @click="suggestionIndex = i"
              ></span>
            </span>
            <button class="rp-nav-btn" @click="nextSuggestion" :disabled="analysisResult.suggestions.length <= 1" title="下一条">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6" /></svg>
            </button>
          </div>
        </template>
      </div>

      <!-- Tab: 面试测验 -->
      <div v-show="rightPanelTab === 'quiz'" class="result-panel-body result-panel-quiz">
        <QuizPanel
          :conversation-id="activeConversationId"
          @explain="handleQuizExplain"
        />
      </div>
    </aside>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex: 1;
  overflow: hidden;
  background: var(--bg);
}

/* ── 聊天区 ── */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--gap-md);
}

.chat-empty-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--muted);
}

.chat-empty-text {
  font-size: var(--text-sm);
  color: var(--muted);
}

.chat-empty-link {
  font-size: var(--fs-meta);
  color: var(--accent);
  text-decoration: none;
}
.chat-empty-link:hover {
  text-decoration: underline;
}

/* ── 消息列表 ── */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--gap-md) var(--gap-xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.chat-msg {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  width: 100%;
  animation: msgIn 0.35s var(--ease-standard) both;
}

.chat-msg.ai {
  align-items: flex-start;
}

.chat-msg.user {
  align-items: flex-end;
}

/* 头像 */
.chat-msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-msg.ai .chat-msg-avatar {
  background: var(--bg);
  color: var(--muted);
  border: 1px solid var(--border);
}

.chat-msg.user .chat-msg-avatar {
  background: var(--accent);
  color: var(--accent-on);
}

/* 消息主体 */
.chat-msg-main {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chat-msg.ai .chat-msg-main {
  align-items: flex-start;
}

.chat-msg.user .chat-msg-main {
  align-items: flex-end;
}

.chat-msg-body {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: 15px;
  line-height: 1.55;
  word-break: break-word;
  width: 100%;
}

.chat-msg.ai .chat-msg-body {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md) var(--radius-md) var(--radius-md) 4px;
}

.chat-msg.user .chat-msg-body {
  background: var(--accent);
  color: var(--accent-on);
  border-radius: var(--radius-md) var(--radius-md) 4px var(--radius-md);
}

.chat-msg-time {
  font-size: 10px;
  opacity: 0.5;
  font-family: var(--font-mono);
  padding: 0 var(--space-1);
}

.chat-msg.user .chat-msg-time {
  color: var(--muted);
}

.chat-msg.ai .chat-msg-time {
  color: var(--muted);
}

/* ── Markdown 渲染 ── */
.chat-msg-body {
  word-break: break-word;
}

.chat-msg-body :deep(.md-p) {
  margin: 0;
}
.chat-msg-body :deep(.md-p + .md-p) {
  margin-top: 0.6em;
}

.chat-msg-body :deep(.md-h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 0.6em 0 0.3em;
  line-height: 1.3;
}
.chat-msg-body :deep(.md-h4) {
  font-size: 15px;
  font-weight: 600;
  margin: 0.5em 0 0.2em;
  line-height: 1.3;
}

.chat-msg-body :deep(.md-code) {
  display: block;
  margin: 0.4em 0;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  background: var(--bg);
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre;
  border: 1px solid var(--border);
}

.chat-msg-body :deep(.md-inline-code) {
  padding: 1px 6px;
  border-radius: 4px;
  background: color-mix(in oklab, var(--fg), transparent 92%);
  font-family: var(--font-mono);
  font-size: 0.9em;
}

.chat-msg.user .chat-msg-body :deep(.md-inline-code) {
  background: rgba(255,255,255,0.18);
}

.chat-msg-body :deep(.md-ul) {
  margin: 0.3em 0;
  padding-left: 1.4em;
}

.chat-msg-body :deep(.md-li) {
  margin: 2px 0;
}

.chat-msg-body :deep(.md-quote) {
  margin: 0.4em 0;
  padding: 6px 14px;
  border-left: 3px solid var(--accent);
  background: color-mix(in oklab, var(--accent), transparent 95%);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}
.chat-msg-body :deep(.md-quote p) {
  margin: 0;
}

.chat-msg.user .chat-msg-body :deep(.md-quote) {
  border-left-color: rgba(255,255,255,0.5);
  background: rgba(255,255,255,0.1);
}

.chat-msg-body :deep(.md-link) {
  color: var(--accent);
  text-decoration: underline;
}
.chat-msg.user .chat-msg-body :deep(.md-link) {
  color: rgba(255,255,255,0.9);
}

/* 表格 */
.chat-msg-body :deep(.md-table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.5em 0;
  font-size: 13px;
}
.chat-msg-body :deep(.md-table th),
.chat-msg-body :deep(.md-table td) {
  padding: 8px 12px;
  border: 1px solid var(--border);
  text-align: left;
}
.chat-msg-body :deep(.md-table th) {
  background: var(--bg);
  font-weight: 600;
  color: var(--fg);
}
.chat-msg-body :deep(.md-table td) {
  color: var(--muted);
}

.chat-msg-body :deep(.md-hr) {
  border: 0;
  border-top: 1px solid var(--border);
  margin: 0.5em 0;
}

.chat-msg-body :deep(strong) {
  font-weight: 600;
}

/* ── AI 输入中动画 ── */
.chat-typing {
  align-self: flex-start;
  display: none;
  align-items: center;
  gap: 4px;
  padding: var(--gap-sm) var(--gap-md);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md) var(--radius-md) var(--radius-md) 4px;
}

.chat-typing.visible {
  display: flex;
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--muted);
  animation: typingBounce 1.2s ease-in-out infinite;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.3s;
}

/* ── 快捷提问 ── */
.quick-asks {
  display: flex;
  flex-wrap: wrap;
  gap: var(--gap-xs);
  padding: 0 var(--gap-xl);
  margin-bottom: var(--space-2);
  flex-shrink: 0;
}

.quick-ask {
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: var(--fs-meta);
  color: var(--muted);
  transition: all 0.2s;
}

.quick-ask:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* ── 输入区 ── */
.chat-input-row {
  display: flex;
  gap: var(--gap-sm);
  padding: var(--gap-md) var(--gap-xl);
  border-top: 1px solid var(--border);
  align-items: center;
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  font: inherit;
  font-size: 15px;
  background: var(--surface);
  color: var(--fg);
  transition: border-color 0.2s;
}

.chat-input:focus {
  outline: none;
  border-color: var(--accent);
}

.chat-input::placeholder {
  color: var(--muted);
}

.chat-send {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: var(--accent-on);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  flex-shrink: 0;
}

.chat-send:hover:not(:disabled) {
  background: var(--accent-hover);
}

.chat-send:active:not(:disabled) {
  transform: scale(0.94);
}

.chat-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ═════════════════════════════════════════════════ */
/* ── 左栏 — 分析报告 (340px)                       ── */
/* ═════════════════════════════════════════════════ */
.analysis-panel {
  width: 380px;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  background: var(--surface);
}

.ap-header {
  display: flex;
  align-items: center;
  height: 48px;
  padding: 0 var(--gap-md);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.ap-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--fg);
}

.ap-report-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  color: var(--muted);
  transition: border-color 0.15s, color 0.15s, background 0.15s;
  flex-shrink: 0;
}

.ap-report-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: color-mix(in oklab, var(--accent), transparent 93%);
}

.ap-tabs {
  display: flex;
  padding: var(--space-2) var(--space-2) 0;
  gap: 2px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
}

.ap-tab-btn {
  flex: 1;
  padding: 7px 2px;
  border: 1px solid transparent;
  border-bottom: none;
  background: transparent;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: var(--muted);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: all 0.15s;
  text-align: center;
}

.ap-tab-btn:hover:not(:disabled) {
  color: var(--fg);
  background: color-mix(in oklab, var(--surface), transparent 50%);
}

.ap-tab-btn.active {
  color: var(--fg);
  background: var(--surface);
  border-color: var(--border);
  margin-bottom: -1px;
  padding-bottom: 8px;
}

.ap-tab-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.ap-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--gap-md);
}

/* 紧凑评分区块 */
.ca-score-section {
  display: flex;
  align-items: center;
  gap: var(--gap-md);
  padding-bottom: var(--gap-md);
  margin-bottom: var(--gap-md);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.ca-score-section > :first-child {
  flex-shrink: 0;
}

.ca-score-section > :last-child {
  flex: 1;
  min-width: 0;
}

/* 紧凑维度概览 */
.ca-dimension-section {
  padding-bottom: var(--gap-md);
  margin-bottom: var(--gap-md);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ca-dim-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
}

.ca-dim-name {
  color: var(--muted);
  font-weight: 500;
}

.ca-dim-score {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--fg);
}

/* 维度tab — 战略建议 */
.ca-strategy-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: var(--gap-md);
  padding-top: var(--gap-md);
  border-top: 1px solid var(--border);
}

.ca-strategy-group {
  padding-left: 10px;
  border-left: 2px solid var(--border);
}

.ca-strategy-title {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--fg);
  margin-bottom: 4px;
}

.ca-strategy-items {
  margin: 0;
  padding-left: 1.1em;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ca-strategy-items li {
  font-size: 11px;
  line-height: 1.5;
  color: var(--muted);
}

/* 内容区块 — 复用 ca-* 类名，单列布局 */
.ca-section {
  animation: fadeInUp 0.25s var(--ease-standard) both;
  display: flex;
  flex-direction: column;
  gap: var(--gap-md);
}

.ca-tag-row {
  display: flex;
  gap: var(--space-1);
  flex-wrap: wrap;
}

.ca-tag {
  display: inline-flex;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  background: color-mix(in oklab, var(--accent), transparent 88%);
  color: var(--accent);
  font-size: 12px;
  font-weight: 500;
}

.ca-tag-muted {
  background: var(--bg);
  color: var(--muted);
}

.ca-summary {
  font-size: 13px;
  line-height: 1.55;
  color: var(--muted);
  margin: 0;
}

.ca-skill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ca-skill-chip {
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  background: color-mix(in oklab, var(--accent), transparent 90%);
  color: var(--accent);
  font-size: 11px;
  font-weight: 500;
}

.ca-insight-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ca-sub-title {
  font-size: 11px;
  font-weight: 600;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-family: var(--font-mono);
}

.ca-insight-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2);
  background: var(--bg);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--border);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.ca-insight-item.s-good { border-left-color: var(--success); }
.ca-insight-item.s-warn { border-left-color: var(--warn); }

.ca-insight-num {
  font-size: 10px;
  font-weight: 600;
  color: var(--muted);
  font-family: var(--font-mono);
  flex-shrink: 0;
  width: 14px;
  text-align: center;
}

.ca-insight-item p {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--muted);
  flex: 1;
  min-width: 0;
}

.ca-tier-hero {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-bottom: var(--space-3);
}

.ca-tier-badge {
  display: inline-flex;
  padding: 5px 16px;
  border-radius: var(--radius-sm);
  background: var(--fg);
  color: var(--surface);
  font-size: 15px;
  font-weight: 600;
}

.ca-tier-alt {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.ca-tier-alt-label {
  font-size: 11px;
  color: var(--muted);
  font-family: var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.ca-tier-alt-chip {
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  background: var(--bg);
  color: var(--muted);
  font-size: 11px;
}

.ca-reasoning {
  font-size: 13px;
  line-height: 1.6;
  color: var(--muted);
  margin: 0;
}

.ca-jd-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
  margin-bottom: var(--space-2);
  transition: border-color 0.2s;
  background: var(--bg);
}

.ca-jd-card:hover { border-color: var(--fg); }

.ca-jd-top {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.ca-jd-num {
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  font-family: var(--font-mono);
  flex-shrink: 0;
  width: 18px;
}

.ca-jd-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ca-jd-position {
  font-size: 13px;
  font-weight: 600;
  color: var(--fg);
}

.ca-jd-company {
  font-size: 11px;
  color: var(--muted);
}

.ca-jd-tier-tag {
  padding: 1px 6px;
  border-radius: var(--radius-pill);
  background: var(--bg);
  color: var(--muted);
  font-size: 10px;
  flex-shrink: 0;
  border: 1px solid var(--border);
}

.ca-jd-req {
  font-size: 12px;
  line-height: 1.55;
  color: var(--muted);
  margin: 0;
}

/* ═════════════════════════════════════════════════ */
/* ── 右侧面板 — 常驻优化建议                        ── */
/* ═════════════════════════════════════════════════ */
.result-panel {
  width: 380px;
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  background: var(--surface);
}

.result-panel-header {
  display: flex;
  align-items: flex-end;
  height: 48px;
  padding: 0;
  flex-shrink: 0;
  background: var(--bg);
}

/* 双标签切换 */
.rp-tabs {
  display: flex;
  flex: 1;
  align-self: stretch;
  padding: var(--space-2) var(--space-2) 0;
  gap: 2px;
  border-bottom: 1px solid var(--border);
}
.rp-tab-btn {
  flex: 1;
  border: 1px solid transparent;
  border-bottom: none;
  background: transparent;
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--muted);
  cursor: pointer;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  padding: 7px 16px;
  transition: all 0.15s;
}
.rp-tab-btn:hover {
  color: var(--fg);
  background: color-mix(in oklab, var(--surface), transparent 50%);
}
.rp-tab-btn.active {
  color: var(--fg);
  background: var(--surface);
  border-color: var(--border);
  margin-bottom: -1px;
  padding-bottom: 8px;
}

.panel-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--fg);
}

.panel-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: var(--radius-pill);
  background: var(--accent);
  color: var(--accent-on);
  font-size: 11px;
  font-weight: 600;
  font-family: var(--font-mono);
}

.result-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--gap-md);
  display: flex;
  flex-direction: column;
}

.result-panel-quiz {
  padding: 0;
}

.result-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  color: var(--muted);
  font-size: var(--fs-meta);
}

.result-empty-link {
  font-size: var(--fs-meta);
  color: var(--accent);
  text-decoration: none;
}
.result-empty-link:hover { text-decoration: underline; }

.rp-section {
  display: flex;
  flex-direction: column;
  gap: var(--gap-sm);
}

/* 建议卡片 */
.rp-suggestion {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-5) var(--space-4);
  animation: fadeInUp 0.3s var(--ease-standard) both;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* 类型标签 */
.rp-badge {
  align-self: flex-start;
  padding: 4px 14px;
  border-radius: var(--radius-sm);
  background: var(--fg);
  color: var(--surface);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* 位置信息 */
.rp-location {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  background: var(--bg);
  font-size: 12px;
  color: var(--muted);
  font-family: var(--font-mono);
  letter-spacing: 0.02em;
}

.rp-location svg {
  color: var(--muted);
  flex-shrink: 0;
}

.rp-suggestion-issue {
  font-size: 15px;
  color: var(--fg);
  margin: 0;
  line-height: 1.55;
  font-weight: 500;
}

.rp-diff-block {
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-sm);
  overflow: hidden;
  gap: 1px;
  background: var(--border);
}

.rp-diff-row {
  padding: var(--space-3) var(--space-4);
}

.rp-diff-before {
  background: color-mix(in oklab, var(--danger), transparent 93%);
}

.rp-diff-after {
  background: color-mix(in oklab, var(--success), transparent 93%);
}

.rp-diff-tag {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: var(--space-1);
  font-family: var(--font-mono);
}

.rp-diff-text {
  font-size: 14px;
  line-height: 1.55;
  margin: 0;
}

.rp-diff-before .rp-diff-text {
  color: var(--danger);
}

.rp-diff-after .rp-diff-text {
  color: var(--success);
}

/* 插入对话按钮 */
.rp-ask-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 7px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: var(--surface);
  cursor: pointer;
  font-size: var(--fs-meta);
  color: var(--muted);
  transition: all 0.15s;
  align-self: flex-start;
}

.rp-ask-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: color-mix(in oklab, var(--accent), transparent 95%);
}

/* 翻页导航 */
.rp-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  padding: var(--space-3) 0 var(--space-1);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
  margin-top: auto;
}

.rp-nav-btn {
  width: 28px;
  height: 28px;
  border: 1px solid var(--border);
  border-radius: 50%;
  background: var(--surface);
  cursor: pointer;
  display: grid;
  place-items: center;
  color: var(--muted);
  transition: all 0.15s;
}

.rp-nav-btn:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.rp-nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.rp-nav-dots {
  display: flex;
  gap: 5px;
  padding: 0 var(--space-1);
}

.rp-nav-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--border);
  cursor: pointer;
  transition: all 0.2s;
}

.rp-nav-dot.active {
  background: var(--accent);
  width: 16px;
  border-radius: var(--radius-pill);
}

/* ── 响应式 ── */
@media (max-width: 1200px) {
  .analysis-panel {
    width: 270px;
  }
  .result-panel {
    width: 280px;
  }
  .chat-messages {
    padding: var(--gap-md);
  }
  .chat-input-row {
    padding: var(--gap-md);
  }
  .quick-asks {
    padding: 0 var(--gap-md);
  }
}

@media (max-width: 920px) {
  .analysis-panel {
    display: none;
  }
  .result-panel {
    display: none;
  }
  .chat-msg-body {
    font-size: 14px;
  }
}
</style>
