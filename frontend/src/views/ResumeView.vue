<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { uploadResume, analyzeResume, getResumeDetail } from '@/api/resume'
import { createConversation } from '@/api/conversation'
import ScoreGauge from '@/components/ScoreGauge.vue'
import SkillBars from '@/components/SkillBars.vue'
import DimensionReport from '@/components/DimensionReport.vue'

const router = useRouter()
const route = useRoute()

const uploadRef = ref()
const uploading = ref(false)
const resumeData = ref(null)

const targetJd = ref('')
const analyzing = ref(false)
const analysisResult = ref(null)
const conversationId = ref(null)

// # 1. 步骤流状态
const progressVisible = ref(false)
const flowProgress = ref(0)        // 0–100 连续进度
let flowAnimFrame = null
let flowDone = false               // 动画是否走完 100%

const progressSteps = [
  { key: 'parse', label: '解析文件结构', detail: '识别 PDF 布局、段落与字体信息' },
  { key: 'extract', label: '提取关键信息', detail: '抽取技能、经历、教育背景等核心字段' },
  { key: 'benchmark', label: '对比行业基准', detail: '与同类岗位、同级别数据进行横向比对' },
  { key: 'score', label: '生成评分报告', detail: '多维度加权计算综合能力评分' },
  { key: 'suggest', label: '生成优化建议', detail: 'AI 深度分析并撰写针对性改进方案' },
]

const stepStates = ref(['', '', '', '', ''])
let flowStartTime = 0

function startFlow() {
  flowProgress.value = 0
  flowDone = false
  stepStates.value = ['active', '', '', '', '']
  flowStartTime = Date.now()
  tickFlow()
}

function tickFlow() {
  if (flowDone) return
  const elapsed = Date.now() - flowStartTime
  // 前 4 段每段 5s，总 20s 走满
  const pct = Math.min((elapsed / 20000) * 100, 100)
  flowProgress.value = pct

  // 根据进度计算每步状态
  const si = Math.min(Math.floor(pct / 20), 4)
  for (let i = 0; i < 5; i++) {
    if (i < si) stepStates.value[i] = 'done'
    else if (i === si) stepStates.value[i] = 'active'
    else stepStates.value[i] = ''
  }

  if (pct < 100) {
    flowAnimFrame = requestAnimationFrame(tickFlow)
  } else {
    flowDone = true
  }
}

function stopFlow() {
  if (flowAnimFrame) cancelAnimationFrame(flowAnimFrame)
  flowAnimFrame = null
}

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

// 报告章节导航
const sectionNavs = computed(() => {
  if (!analysisResult.value) return []
  const navs = []
  if (analysisResult.value.score_assessment) navs.push({ id: 'sec-score', label: '技能评估' })
  if (analysisResult.value.ability_profile) navs.push({ id: 'sec-ability', label: '能力评估' })
  if (analysisResult.value.dimension_report?.strategic_suggestions?.length) navs.push({ id: 'sec-strategy', label: '综合建议' })
  if (analysisResult.value.dimension_report?.dimensions?.length) navs.push({ id: 'sec-dimension', label: '维度分析' })
  if (analysisResult.value.tier_suggestion) navs.push({ id: 'sec-tier', label: '梯队建议' })
  if (analysisResult.value.retrieved_jds?.length) navs.push({ id: 'sec-jds', label: '推荐岗位' })
  if (analysisResult.value.suggestions?.length) navs.push({ id: 'sec-suggestions', label: '优化建议' })
  return navs
})

const activeNavId = ref('')
const resumeViewRef = ref(null)
let navScrollTimer = null

function scrollToSection(id) {
  const el = document.getElementById(id)
  const container = resumeViewRef.value
  if (!el || !container) return
  const offset = el.getBoundingClientRect().top - container.getBoundingClientRect().top + container.scrollTop - 80
  container.scrollTo({ top: offset, behavior: 'smooth' })
}

function updateActiveNav() {
  const navs = sectionNavs.value
  const container = resumeViewRef.value
  if (!navs.length || !container) return
  let active = navs[0].id
  for (const nav of navs) {
    const el = document.getElementById(nav.id)
    if (!el) continue
    if (el.getBoundingClientRect().top - container.getBoundingClientRect().top < 120) active = nav.id
  }
  activeNavId.value = active
}

function onResultsScroll() {
  if (navScrollTimer) clearTimeout(navScrollTimer)
  navScrollTimer = setTimeout(updateActiveNav, 60)
}

onMounted(() => {
  const container = resumeViewRef.value
  if (container) container.addEventListener('scroll', onResultsScroll, { passive: true })
})

onBeforeUnmount(() => {
  const container = resumeViewRef.value
  if (container) container.removeEventListener('scroll', onResultsScroll)
  if (navScrollTimer) clearTimeout(navScrollTimer)
})

// 如果 URL 带了 resume_id，直接加载已有分析结果
onMounted(async () => {
  const resumeId = route.query.resume_id
  if (!resumeId) return
  try {
    const data = await getResumeDetail(Number(resumeId))
    resumeData.value = data
    // # 1.5 从后端权威数据回填已关联对话 ID（防止返回后误判为未创建）
    conversationId.value = data.conversation_id || null
    // 如果已经分析过，直接展示结果
    if (data.ability_profile || data.suggestions?.length) {
      analysisResult.value = data
    }
  } catch {
    // 加载失败，保持初始状态
  }
})

async function handleUpload(options) {
  // # 2. 校验文件类型和大小
  const file = options.file
  if (file.type !== 'application/pdf') {
    ElMessage.error('仅支持 PDF 格式')
    return
  }
  if (file.size / 1024 / 1024 > 5) {
    ElMessage.error('文件大小不能超过 5MB')
    return
  }
  // # 3. 调用上传接口
  uploading.value = true
  try {
    const data = await uploadResume(file)
    resumeData.value = data
    ElMessage.success('上传成功')
  } catch {
  } finally {
    uploading.value = false
  }
}

function removeFile() {
  resumeData.value = null
  analysisResult.value = null
  conversationId.value = null
  targetJd.value = ''
  uploadRef.value?.clearFiles()
}

async function handleAnalyze() {
  analyzing.value = true
  progressVisible.value = true
  startFlow()

  try {
    const data = await analyzeResume(resumeData.value.id, targetJd.value)
    stopFlow()
    // 全部标记完成，进度条拉到 100%
    flowProgress.value = 100
    stepStates.value = ['done', 'done', 'done', 'done', 'done']
    setTimeout(() => {
      analysisResult.value = data
      progressVisible.value = false
      ElMessage.success('分析完成')
    }, 500)
    try {
      const conv = await createConversation(resumeData.value.id)
      conversationId.value = conv.id
    } catch { /* 创建失败不阻断 */ }
  } catch {
    stopFlow()
    progressVisible.value = false
  } finally {
    analyzing.value = false
  }
}

function resetAll() {
  removeFile()
}

async function startConversation() {
  // # 9. 已有对话 ID 直接跳转
  if (conversationId.value) {
    router.push({ path: '/app/chat', query: { conversation_id: conversationId.value } })
    return
  }
  // # 10. 重试创建对话
  try {
    const conv = await createConversation(resumeData.value.id)
    conversationId.value = conv.id
    ElMessage.success('对话已创建')
    router.push({ path: '/app/chat', query: { conversation_id: conv.id } })
  } catch {
  }
}
</script>

<template>
  <div ref="resumeViewRef" class="resume-view">
    <!-- ═══ 无简历：上传区 ═══ -->
    <section v-if="!resumeData" class="screen-section">
      <p class="eyebrow center">第一步 · 上传简历</p>
      <h2 class="center heading-2">拖放文件到这里</h2>

      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="true"
        :show-file-list="false"
        :http-request="handleUpload"
        accept=".pdf"
        class="upload-zone"
      >
        <div class="upload-inner">
          <div class="upload-icon-ring">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
            </svg>
          </div>
          <h3 class="upload-title">拖放简历文件，或点击选择</h3>
          <p class="upload-hint">支持 PDF 格式 · 最大 5MB</p>
        </div>
      </el-upload>

      <div v-if="uploading" class="uploading-status">
        <span class="spinner"></span>
        <span>正在上传…</span>
      </div>
    </section>

    <!-- ═══ 已上传未分析 ═══ -->
    <section v-else-if="!analysisResult" class="screen-section">
      <p class="eyebrow center">第二步 · 确认分析</p>
      <h2 class="center heading-2">准备分析简历</h2>

      <!-- 文件预览 -->
      <div class="file-preview visible">
        <div class="file-preview-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6" />
          </svg>
        </div>
        <div class="file-preview-info">
          <div class="file-preview-name">{{ resumeData?.filename }}</div>
          <div class="file-preview-size">ID: {{ resumeData?.id }}</div>
        </div>
        <button class="file-preview-remove" @click="removeFile">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- JD 输入 -->
      <div class="jd-section">
        <label class="jd-label">目标岗位 JD（可选）</label>
        <p class="jd-hint">粘贴 JD 后，AI 会对比简历与岗位要求的差距</p>
        <el-input
          v-model="targetJd"
          type="textarea"
          :rows="5"
          placeholder="粘贴目标岗位的 JD 内容…"
          class="jd-input"
        />
      </div>

      <!-- 步骤流程 -->
      <div v-if="progressVisible" class="step-flow visible">
        <!-- 进度轨道 + 填充 -->
        <div class="flow-track">
          <div class="flow-fill" :style="{ width: flowProgress + '%' }"></div>
          <!-- 节点圆点 -->
          <div
            v-for="(step, i) in progressSteps"
            :key="step.key"
            class="flow-node"
            :class="stepStates[i]"
            :style="{ left: (i / 4 * 100) + '%' }"
          >
            <svg v-if="stepStates[i] === 'done'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M20 6L9 17l-5-5" />
            </svg>
            <span v-else class="flow-dot"></span>
          </div>
        </div>
        <!-- 标签行 -->
        <div class="flow-labels">
          <span
            v-for="(step, i) in progressSteps"
            :key="step.key"
            class="flow-label"
            :class="stepStates[i]"
          >
            <span class="flow-label-text">{{ step.label }}</span>
            <span v-if="stepStates[i] === 'active'" class="flow-label-detail">{{ step.detail }}</span>
          </span>
        </div>
      </div>

      <!-- 分析按钮 -->
      <div class="action-row">
        <button class="btn btn-primary btn-lg" :disabled="analyzing" @click="handleAnalyze">
          {{ analyzing ? '分析中…' : '开始分析' }}
        </button>
      </div>
    </section>

    <!-- ═══ 已分析：结果 ═══ -->
    <section v-else class="screen-section results">
      <!-- 头部 -->
      <div class="results-header">
        <p class="eyebrow center" style="color: var(--muted);">分析报告</p>
        <h2 class="center heading-2">{{ resumeData?.filename }}</h2>
        <div class="results-actions">
          <button class="btn btn-secondary" @click="resetAll">重新上传</button>
          <button class="btn btn-primary" @click="startConversation">
            {{ conversationId ? '进入对话' : '针对这份报告，继续提问' }}
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- 核心技能评估 -->
      <div v-if="analysisResult.score_assessment" id="sec-score" class="card section-card score-section">
        <h3 class="section-title">核心技能评估</h3>
        <div class="score-layout">
          <ScoreGauge :score="analysisResult.score_assessment.overall_score" :size="140" />
          <SkillBars :skills="analysisResult.score_assessment.skill_scores" />
        </div>
      </div>

      <!-- 能力评估 -->
      <div v-if="analysisResult.ability_profile" id="sec-ability" class="card section-card">
        <h3 class="section-title">能力评估</h3>
        <div class="ability-meta">
          <span class="tag">{{ analysisResult.ability_profile.tech_direction }}</span>
          <span class="tag tag-muted">{{ analysisResult.ability_profile.experience_level }}</span>
        </div>
        <p class="ability-summary">{{ analysisResult.ability_profile.summary }}</p>

        <div class="skill-tags">
          <span class="skill-tag-label">核心技能</span>
          <div class="tag-list">
            <span v-for="skill in analysisResult.ability_profile.skills" :key="skill" class="tag">{{ skill }}</span>
          </div>
        </div>

        <div class="grid-2 sw-grid">
          <div>
            <h4 class="sw-heading">
              <span class="sw-dot sw-dot-success"></span>
              核心优势
            </h4>
            <div class="stack sw-list">
              <div
                v-for="(item, i) in analysisResult.ability_profile.strengths"
                :key="i"
                class="insight-card"
                :style="{ animationDelay: i * 0.08 + 's' }"
              >
                <p>{{ item }}</p>
              </div>
            </div>
          </div>
          <div>
            <h4 class="sw-heading">
              <span class="sw-dot sw-dot-warn"></span>
              可优化方向
            </h4>
            <div class="stack sw-list">
              <div
                v-for="(item, i) in analysisResult.ability_profile.weaknesses"
                :key="i"
                class="insight-card weakness"
                :style="{ animationDelay: (i + 3) * 0.08 + 's' }"
              >
                <p>{{ item }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 综合建议 -->
      <div v-if="analysisResult.dimension_report?.strategic_suggestions?.length" id="sec-strategy" class="card section-card">
        <h3 class="section-title">综合建议</h3>
        <div class="strategy-list">
          <div v-for="(sg, i) in analysisResult.dimension_report.strategic_suggestions" :key="i" class="strategy-group">
            <h4 class="strategy-title">{{ sg.title }}</h4>
            <ul class="strategy-items">
              <li v-for="(item, j) in sg.items" :key="j">{{ item }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 维度分析 -->
      <div v-if="analysisResult.dimension_report?.dimensions?.length" id="sec-dimension" class="card section-card">
        <h3 class="section-title">维度分析</h3>
        <DimensionReport :dimensions="analysisResult.dimension_report.dimensions" />
      </div>

      <!-- 梯队建议 -->
      <div v-if="analysisResult.tier_suggestion" id="sec-tier" class="card section-card">
        <h3 class="section-title">梯队建议</h3>
        <div class="tier-row">
          <span class="tier-badge">{{ tierMap[analysisResult.tier_suggestion.tier] || analysisResult.tier_suggestion.tier }}</span>
          <div v-if="analysisResult.tier_suggestion.alternative_tiers?.length" class="tier-alt">
            <span class="tier-alt-label">备选</span>
            <span v-for="t in analysisResult.tier_suggestion.alternative_tiers" :key="t" class="tag tag-muted">{{ tierMap[t] || t }}</span>
          </div>
        </div>
        <p class="tier-reasoning">{{ analysisResult.tier_suggestion.reasoning }}</p>
      </div>

      <!-- 推荐岗位 -->
      <div v-if="analysisResult.retrieved_jds?.length" id="sec-jds" class="card section-card">
        <h3 class="section-title">推荐岗位</h3>
        <div class="jd-card-list">
          <div v-for="(jd, i) in analysisResult.retrieved_jds" :key="i" class="jd-item">
            <div class="jd-item-top">
              <span class="jd-position">{{ jd.position }}</span>
              <span v-if="jd.company" class="jd-company">{{ jd.company }}</span>
              <span v-if="jd.tier" class="tag tag-muted">{{ tierMap[jd.tier] || jd.tier }}</span>
            </div>
            <p class="jd-requirements">{{ jd.requirements }}</p>
          </div>
        </div>
      </div>

      <!-- 优化建议 -->
      <div v-if="analysisResult.suggestions?.length" id="sec-suggestions" class="card section-card">
        <h3 class="section-title">优化建议</h3>
        <div class="stack suggestion-list">
          <div
            v-for="(item, i) in analysisResult.suggestions"
            :key="i"
            class="suggestion-item"
            :style="{ animationDelay: i * 0.06 + 's' }"
          >
            <div class="suggestion-top">
              <span class="suggestion-type">{{ suggestionTypeMap[item.type] || item.type }}</span>
              <span class="suggestion-loc">{{ item.location }}</span>
            </div>
            <p class="suggestion-issue">{{ item.issue }}</p>
            <div class="diff-block">
              <div class="diff-row diff-before">
                <span class="diff-tag">修改前</span>
                <p class="diff-text">{{ item.before }}</p>
              </div>
              <div class="diff-row diff-after">
                <span class="diff-tag">修改后</span>
                <p class="diff-text">{{ item.after }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部 CTA -->
      <div class="bottom-cta">
        <button class="btn btn-primary btn-lg" @click="startConversation">
          {{ conversationId ? '进入对话' : '针对这份报告，继续提问' }}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </section>

    <!-- 右侧定点导航 — 放在 section 外避免 transform 影响 fixed -->
    <nav v-if="analysisResult && sectionNavs.length > 1" class="side-dots">
      <button
        v-for="nav in sectionNavs"
        :key="nav.id"
        class="side-dot"
        :class="{ active: activeNavId === nav.id }"
        :title="nav.label"
        @click="scrollToSection(nav.id)"
      ><span class="side-dot-pip"></span><span class="side-dot-label">{{ nav.label }}</span></button>
    </nav>
  </div>
</template>

<style scoped>
.resume-view {
  flex: 1;
  overflow-y: auto;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: var(--gap-xl) var(--container-gutter);
}

.screen-section {
  position: relative;
  z-index: 1;
  max-width: 900px;
  width: 100%;
  animation: fadeInUp 0.4s var(--ease-standard) both;
}

.screen-section.results {
  max-width: 860px;
}

/* ── 排版工具类 ── */
.eyebrow {
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0 0 var(--gap-md);
}
.eyebrow.center { text-align: center; }

.heading-2 {
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  line-height: 1.1;
  letter-spacing: -0.015em;
  margin: 0;
}
.center { text-align: center; }

/* ── 上传区 ── */
.upload-zone {
  width: 100%;
  margin-top: var(--gap-lg);
}

:deep(.upload-zone .el-upload-dragger) {
  width: 100%;
  padding: var(--gap-2xl) var(--gap-xl);
  border: 2px dashed var(--border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  transition: all 0.3s var(--ease-standard);
}

:deep(.upload-zone .el-upload-dragger:hover) {
  border-color: var(--accent);
  background: color-mix(in oklab, var(--accent), transparent 95%);
}

:deep(.upload-zone .el-upload-dragger.is-dragover) {
  border-color: var(--accent);
  transform: scale(1.02);
  box-shadow: var(--elev-raised);
}

.upload-inner {
  text-align: center;
}

.upload-icon-ring {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 2px solid var(--border);
  margin: 0 auto var(--gap-md);
  display: grid;
  place-items: center;
  animation: uploadPulse 2s ease-in-out infinite;
  transition: border-color 0.3s;
}

.upload-icon-ring svg {
  width: 28px;
  height: 28px;
  color: var(--muted);
}

:deep(.upload-zone .el-upload-dragger:hover) .upload-icon-ring {
  border-color: var(--accent);
  animation: none;
}

:deep(.upload-zone .el-upload-dragger:hover) .upload-icon-ring svg {
  color: var(--accent);
}

.upload-title {
  font-size: var(--text-lg);
  font-weight: 600;
  margin: 0 0 var(--space-1);
  color: var(--fg);
}

.upload-hint {
  font-size: var(--fs-meta);
  color: var(--muted);
  margin: 0;
}

.uploading-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  margin-top: var(--gap-md);
  color: var(--muted);
  font-size: var(--fs-meta);
  font-family: var(--font-mono);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: float 0.8s linear infinite;
}

/* ── 文件预览 ── */
.file-preview {
  display: flex;
  align-items: center;
  gap: var(--gap-md);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--gap-md);
  margin-top: var(--gap-lg);
}

.file-preview-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  background: color-mix(in oklab, var(--accent), transparent 90%);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  color: var(--accent);
}

.file-preview-icon svg {
  width: 22px;
  height: 22px;
}

.file-preview-info {
  flex: 1;
  min-width: 0;
}

.file-preview-name {
  font-weight: 600;
  font-size: 15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-preview-size {
  font-size: var(--fs-meta);
  color: var(--muted);
  font-family: var(--font-mono);
}

.file-preview-remove {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: transparent;
  display: grid;
  place-items: center;
  cursor: pointer;
  color: var(--muted);
  transition: all 0.15s;
  flex-shrink: 0;
}

.file-preview-remove:hover {
  border-color: var(--danger);
  color: var(--danger);
}

/* ── JD 输入 ── */
.jd-section {
  margin-top: var(--gap-lg);
}

.jd-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--fg);
}

.jd-hint {
  margin: var(--space-1) 0 var(--space-3);
  font-size: var(--fs-meta);
  color: var(--muted);
}

:deep(.jd-input .el-textarea__inner) {
  border-radius: var(--radius-sm);
  box-shadow: 0 0 0 1px var(--border) inset;
  transition: box-shadow var(--motion-fast) ease;
  font-size: var(--text-sm);
  line-height: 1.6;
  font-family: var(--font-body);
}
:deep(.jd-input .el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px var(--fg) inset;
}
:deep(.jd-input .el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px var(--accent) inset, var(--focus-ring);
}

/* ── 步骤流程 ── */
.step-flow {
  margin-top: var(--gap-xl);
  opacity: 0;
  transform: translateY(12px);
  transition: opacity 0.4s var(--ease-standard), transform 0.4s var(--ease-standard);
}

.step-flow.visible {
  opacity: 1;
  transform: translateY(0);
}

/* 进度轨道 */
.flow-track {
  position: relative;
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  margin: 0 12px;
}

.flow-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  transition: none; /* JS 驱动，不用 CSS transition */
}

/* 节点圆点 — 绝对定位在轨道上 */
.flow-node {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--surface);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  transition: border-color 0.4s, background 0.4s;
}

.flow-node.done {
  border-color: var(--success);
  background: var(--success);
}

.flow-node.done svg {
  color: var(--surface);
}

.flow-node.active {
  border-color: var(--accent);
  background: var(--accent);
}

.flow-node.active .flow-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--surface);
}

.flow-node:not(.active):not(.done) .flow-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--border);
}

@keyframes flowPulse {
  0%, 100% { box-shadow: 0 0 0 4px color-mix(in oklab, var(--accent), transparent 75%); }
  50%      { box-shadow: 0 0 0 10px transparent; }
}

.flow-node.active {
  animation: flowPulse 1.8s ease-in-out infinite;
}

/* 标签行 */
.flow-labels {
  display: flex;
  margin-top: var(--space-4);
}

.flow-label {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-1);
  transition: color 0.3s;
}

.flow-label-text {
  font-size: var(--fs-meta);
  font-weight: 500;
  color: var(--muted);
  transition: color 0.3s;
}

.flow-label.active .flow-label-text {
  color: var(--fg);
  font-weight: 600;
}

.flow-label.done .flow-label-text {
  color: var(--muted);
}

.flow-label-detail {
  font-size: 11px;
  color: var(--muted);
  line-height: 1.4;
  max-width: 150px;
  opacity: 0;
  transform: translateY(-4px);
  transition: opacity 0.4s var(--ease-standard), transform 0.4s var(--ease-standard);
}

.flow-label.active .flow-label-detail {
  opacity: 1;
  transform: translateY(0);
}

@media (max-width: 640px) {
  .flow-label-detail {
    display: none;
  }
  .flow-track {
    margin: 0 6px;
  }
}

@media (max-width: 1100px) {
  .side-dots {
    display: none;
  }
}

/* ── 按钮 ── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 20px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: -0.005em;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.05s ease;
}
.btn:active { transform: translateY(1px); }

.btn-primary {
  background: var(--accent);
  color: var(--accent-on);
  border-color: var(--accent);
}
.btn-primary:hover { background: var(--accent-hover); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-secondary {
  background: transparent;
  color: var(--fg);
  border-color: var(--border);
}
.btn-secondary:hover { border-color: var(--fg); }

.btn-lg {
  padding: 14px 28px;
  font-size: 17px;
  border-radius: var(--radius-md);
}

.action-row {
  text-align: center;
  margin-top: var(--gap-lg);
}

/* ── 结果头部 ── */
.results-header {
  text-align: center;
  margin-bottom: var(--gap-2xl);
}

.results-actions {
  display: flex;
  gap: var(--space-2);
  justify-content: center;
  margin-top: var(--gap-md);
}

/* ── 卡片 ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 28px;
}

.section-card {
  margin-bottom: var(--gap-lg);
  animation: fadeInUp 0.4s var(--ease-standard) both;
}

.section-title {
  font-size: var(--fs-h3);
  font-weight: 600;
  margin-bottom: var(--gap-md);
  color: var(--fg);
}

/* ── 综合建议 ── */
.strategy-list {
  display: flex;
  flex-direction: column;
  gap: var(--gap-md);
}

.strategy-group {
  padding-left: 14px;
  border-left: 3px solid var(--border);
}

.strategy-title {
  font-size: var(--text-sm);
  font-weight: 600;
  margin: 0 0 var(--space-2);
  color: var(--fg);
}

.strategy-items {
  margin: 0;
  padding-left: 1.2em;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.strategy-items li {
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--muted);
}

/* ── 标签 ── */
.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  background: color-mix(in oklab, var(--accent), transparent 88%);
  color: var(--accent);
  font-size: var(--fs-meta);
  font-weight: 500;
}

.tag-muted {
  background: var(--bg);
  color: var(--muted);
}

/* ── 右侧定点导航 ── */
.side-dots {
  position: fixed;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 50;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.side-dot {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 0;
  flex-direction: row-reverse;
}

.side-dot-pip {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--border);
  transition: all 0.3s var(--ease-standard);
  flex-shrink: 0;
}

.side-dot:hover .side-dot-pip {
  background: var(--muted);
  transform: scale(1.3);
}

.side-dot.active .side-dot-pip {
  background: var(--accent);
  width: 10px;
  height: 10px;
  box-shadow: 0 0 0 4px color-mix(in oklab, var(--accent), transparent 82%);
}

.side-dot-label {
  font-size: 11px;
  color: var(--muted);
  opacity: 0;
  transform: translateX(6px);
  transition: opacity 0.2s, transform 0.2s;
  white-space: nowrap;
  font-weight: 500;
}

.side-dot:hover .side-dot-label,
.side-dot.active .side-dot-label {
  opacity: 1;
  transform: translateX(0);
}

.side-dot.active .side-dot-label {
  color: var(--fg);
  font-weight: 600;
}

/* ── 评分区块 ── */
.score-section .score-layout {
  display: flex;
  align-items: center;
  gap: var(--gap-xl);
}

.score-section .score-layout > :first-child {
  flex-shrink: 0;
}

.score-section .score-layout > :last-child {
  flex: 1;
  min-width: 0;
}

@media (max-width: 640px) {
  .score-section .score-layout {
    flex-direction: column;
    gap: var(--gap-md);
  }
}

/* ── 能力评估 ── */
.ability-meta {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.ability-summary {
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--muted);
  margin-bottom: var(--space-6);
}

.skill-tags {
  margin-bottom: var(--space-6);
}

.skill-tag-label {
  display: block;
  font-size: var(--fs-meta);
  font-weight: 600;
  color: var(--muted);
  margin-bottom: var(--space-2);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

/* ── 优势/不足 ── */
.sw-grid {
  margin-top: var(--space-4);
}

.sw-heading {
  font-size: var(--text-base);
  font-weight: 600;
  margin-bottom: var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.sw-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.sw-dot-success { background: var(--success); }
.sw-dot-warn { background: var(--warn); }

.stack {
  display: flex;
  flex-direction: column;
}

.stack > * + * {
  margin-top: var(--space-2);
}

.sw-list {
  gap: var(--space-2);
}

.insight-card {
  border-left: 3px solid var(--border);
  padding: var(--gap-md) var(--gap-lg);
  background: var(--surface);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  transition: transform 0.2s, box-shadow 0.2s;
  animation: fadeInUp 0.4s var(--ease-standard) both;
}

.insight-card:hover {
  transform: translateX(4px);
  box-shadow: var(--elev-raised);
}

.insight-card.weakness {
  border-left-color: var(--warn);
}

.insight-card:not(.weakness) {
  border-left-color: var(--success);
}

.insight-card p {
  margin: 0;
  color: var(--muted);
  font-size: var(--text-sm);
  line-height: 1.55;
}

/* ── 梯队建议 ── */
.tier-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
}

.tier-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 16px;
  border-radius: var(--radius-sm);
  background: var(--fg);
  color: var(--surface);
  font-size: var(--text-sm);
  font-weight: 600;
}

.tier-alt {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.tier-alt-label {
  font-size: var(--fs-meta);
  color: var(--muted);
}

.tier-reasoning {
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--muted);
}

/* ── 推荐岗位 ── */
.jd-card-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.jd-item {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--gap-md) var(--gap-lg);
  transition: border-color 0.2s;
}

.jd-item:hover {
  border-color: var(--fg);
}

.jd-item-top {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
  flex-wrap: wrap;
}

.jd-position {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--fg);
}

.jd-company {
  font-size: var(--fs-meta);
  color: var(--muted);
}

.jd-requirements {
  font-size: var(--fs-meta);
  line-height: 1.6;
  color: var(--muted);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── 优化建议 ── */
.suggestion-list {
  gap: var(--space-3);
}

.suggestion-item {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--gap-md) var(--gap-lg);
  animation: fadeInUp 0.4s var(--ease-standard) both;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.suggestion-item:hover {
  border-color: var(--fg);
  box-shadow: var(--elev-raised);
}

.suggestion-top {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.suggestion-type {
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  background: color-mix(in oklab, var(--accent), transparent 88%);
  color: var(--accent);
  font-size: var(--text-xs);
  font-weight: 500;
}

.suggestion-loc {
  font-size: var(--fs-meta);
  color: var(--muted);
  font-family: var(--font-mono);
}

.suggestion-issue {
  font-size: var(--text-sm);
  color: var(--fg);
  margin: 0 0 var(--space-3);
  line-height: 1.5;
}

.diff-block {
  display: flex;
  flex-direction: column;
  background: var(--bg);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.diff-row {
  padding: var(--space-2) var(--space-3);
}

.diff-before {
  background: color-mix(in oklab, var(--danger), transparent 94%);
}

.diff-after {
  background: color-mix(in oklab, var(--success), transparent 94%);
}

.diff-tag {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: var(--space-1);
  font-family: var(--font-mono);
}

.diff-text {
  font-size: var(--fs-meta);
  line-height: 1.5;
  margin: 0;
}

.diff-before .diff-text {
  color: var(--danger);
  text-decoration: line-through;
  text-decoration-color: color-mix(in oklab, var(--danger), transparent 50%);
}

.diff-after .diff-text {
  color: var(--success);
}

/* ── 底部 ── */
.bottom-cta {
  text-align: center;
  margin-top: var(--gap-xl);
  padding-bottom: var(--gap-xl);
}

/* ── 响应式 ── */
@media (max-width: 920px) {
  .sw-grid {
    grid-template-columns: 1fr;
  }
  .grid-2 {
    grid-template-columns: 1fr;
  }
}
</style>
