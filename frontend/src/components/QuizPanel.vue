<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createQuiz, listQuizzes, getQuizDetail, answerQuestion, finishQuiz, deleteQuiz, resetQuiz } from '@/api/quiz'
import QuizHistoryList from './QuizHistoryList.vue'
import QuizGenerateForm from './QuizGenerateForm.vue'
import QuizLoading from './QuizLoading.vue'
import QuizQuestion from './QuizQuestion.vue'
import QuizReport from './QuizReport.vue'

const emit = defineEmits(['explain'])

const props = defineProps({
  conversationId: { type: Number, default: null },
})

const panelState = ref('idle')      // 'idle' | 'generating' | 'answering' | 'completed'
const showForm = ref(false)

const quizList = ref([])
const currentSession = ref(null)
const currentQuestions = ref([])
const currentQuestionIndex = ref(0)
const report = ref(null)
const lastFormData = ref(null)
const loadingType = ref('generating')  // 'generating' | 'reporting'

const currentQuestion = ref(null)

onMounted(() => {
  if (props.conversationId) loadList()
})

// conversationId 异步加载完成后，监听变化并加载列表
watch(() => props.conversationId, (id) => {
  if (id) loadList()
})

async function loadList() {
  try {
    const data = await listQuizzes(props.conversationId)
    quizList.value = data.items || []
  } catch { /* 静默 */ }
}

function handleNewQuiz() {
  showForm.value = true
  panelState.value = 'idle'
}

function handleCancelForm() {
  showForm.value = false
}

async function handleGenerate(formData) {
  showForm.value = false
  panelState.value = 'generating'
  loadingType.value = 'generating'
  lastFormData.value = { ...formData }
  try {
    const data = await createQuiz(
      props.conversationId,
      formData.title,
      formData.question_count,
      formData.user_requirements,
    )
    currentSession.value = data.session
    currentQuestions.value = data.questions
    currentQuestionIndex.value = 0
    currentQuestion.value = data.questions[0]
    panelState.value = 'answering'
    ElMessage.success('测验创建成功')
    loadList()
  } catch {
    panelState.value = 'idle'
  }
}

async function handleSelectQuiz(sessionId) {
  try {
    const data = await getQuizDetail(sessionId)
    currentSession.value = data.session
    currentQuestions.value = data.questions
    if (data.session.status === 'completed') {
      report.value = data.session.report
      panelState.value = 'completed'
    } else {
      // 找到第一个未作答的题
      const idx = data.questions.findIndex(q => !q.user_answer)
      currentQuestionIndex.value = idx >= 0 ? idx : 0
      currentQuestion.value = data.questions[currentQuestionIndex.value]
      panelState.value = 'answering'
    }
  } catch { /* 静默 */ }
}

async function handleDeleteQuiz(sessionId) {
  try {
    await deleteQuiz(sessionId)
    quizList.value = quizList.value.filter(item => item.id !== sessionId)
    if (currentSession.value?.id === sessionId) {
      currentSession.value = null
      currentQuestions.value = []
      report.value = null
      panelState.value = 'idle'
    }
    ElMessage.success('已删除')
  } catch { /* 静默 */ }
}

async function handleAnswered(selectedOptionId) {
  const q = currentQuestions.value[currentQuestionIndex.value]
  if (!q || q.user_answer) return
  // 乐观更新本地状态
  q.user_answer = selectedOptionId
  q.is_correct = selectedOptionId === q.correct_option_id
  // 异步同步到后端
  try {
    await answerQuestion(currentSession.value.id, q.id, selectedOptionId)
  } catch { /* 后端失败不影响前端交互 */ }
}

async function handlePrevQuestion() {
  if (currentQuestionIndex.value > 0) {
    currentQuestionIndex.value--
    currentQuestion.value = currentQuestions.value[currentQuestionIndex.value]
  }
}

async function handleNextQuestion() {
  const isLast = currentQuestionIndex.value >= currentQuestions.value.length - 1
  if (isLast) {
    panelState.value = 'generating'
    loadingType.value = 'reporting'
    try {
      const rep = await finishQuiz(currentSession.value.id)
      report.value = rep
      currentSession.value.status = 'completed'
      currentSession.value.score = rep.correct_count
      panelState.value = 'completed'
      ElMessage.success('测验完成')
      loadList()
    } catch {
      panelState.value = 'answering'
    }
  } else {
    currentQuestionIndex.value++
    currentQuestion.value = currentQuestions.value[currentQuestionIndex.value]
  }
}

function handleExplain(prompt) {
  emit('explain', prompt)
}

function handleReview() {
  currentQuestionIndex.value = 0
  currentQuestion.value = currentQuestions.value[0]
  panelState.value = 'answering'
}

async function handleRetake() {
  if (!currentSession.value) return
  try {
    const data = await resetQuiz(currentSession.value.id)
    currentSession.value = data.session
    currentQuestions.value = data.questions
    currentQuestionIndex.value = 0
    currentQuestion.value = data.questions[0]
    report.value = null
    panelState.value = 'answering'
    ElMessage.success('测验已重置')
  } catch { /* 静默 */ }
}

// 历史列表点"重新测试"图标
async function handleHistoryRetake(sessionId) {
  try {
    const data = await resetQuiz(sessionId)
    currentSession.value = data.session
    currentQuestions.value = data.questions
    currentQuestionIndex.value = 0
    currentQuestion.value = data.questions[0]
    report.value = null
    panelState.value = 'answering'
    showForm.value = false
    ElMessage.success('测验已重置')
  } catch { /* 静默 */ }
}

// 答题中退出 → 回到历史列表
function handleQuitQuiz() {
  panelState.value = 'idle'
  showForm.value = false
  currentSession.value = null
  currentQuestions.value = []
  report.value = null
  currentQuestionIndex.value = 0
}
</script>

<template>
  <div class="qp">
    <!-- 状态：idle（无测验/历史列表/表单） -->
    <template v-if="panelState === 'idle'">
      <QuizHistoryList
        v-if="quizList.length && !showForm"
        :items="quizList"
        @select="handleSelectQuiz"
        @delete="handleDeleteQuiz"
        @new-quiz="handleNewQuiz"
        @report="handleSelectQuiz"
        @retake="handleHistoryRetake"
      />
      <QuizGenerateForm
        v-if="showForm || !quizList.length"
        @generate="handleGenerate"
        @cancel="handleCancelForm"
      />
    </template>

    <!-- 状态：generating -->
    <QuizLoading v-if="panelState === 'generating'" :message="loadingType" />

    <!-- 状态：answering -->
    <template v-if="panelState === 'answering' && currentQuestion">
      <div class="qp-quiz-bar">
        <span class="qp-quiz-title">{{ currentSession?.title || '测验' }}</span>
        <button class="qp-quit-btn" @click="handleQuitQuiz">退出测验</button>
      </div>
      <QuizQuestion
      :question="currentQuestion"
      :current-index="currentQuestionIndex"
      :total-count="currentQuestions.length"
      :is-completed="currentSession?.status === 'completed'"
      @explain="handleExplain"
      @answered="handleAnswered"
      @prev="handlePrevQuestion"
      @next="handleNextQuestion"
      @view-report="panelState = 'completed'"
    />
    </template>

    <!-- 状态：completed -->
    <QuizReport
      v-if="panelState === 'completed' && currentSession"
      :session="currentSession"
      :report="report"
      @review="handleReview"
      @quit="handleQuitQuiz"
    />
  </div>
</template>

<style scoped>
.qp {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.qp-quiz-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.qp-quiz-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--fg);
}
.qp-quit-btn {
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  background: transparent;
  font: inherit;
  font-size: 11px;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.15s;
}
.qp-quit-btn:hover { border-color: var(--danger); color: var(--danger); }
</style>
