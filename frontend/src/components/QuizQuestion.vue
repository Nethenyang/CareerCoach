<script setup>
import { ref, watch } from 'vue'

const emit = defineEmits(['explain', 'prev', 'next', 'answered', 'viewReport'])

const props = defineProps({
  question: { type: Object, required: true },
  currentIndex: { type: Number, required: true },
  totalCount: { type: Number, required: true },
  isCompleted: { type: Boolean, default: false },
})

const selectedOptionId = ref(null)
const showResult = ref(false)
const isCorrect = ref(false)

// 切题时重置本地状态；如果题目已有历史答案则直接展示结果
watch(() => props.question, (q) => {
  if (q.user_answer) {
    selectedOptionId.value = q.user_answer
    isCorrect.value = q.user_answer === q.correct_option_id
    showResult.value = true
  } else {
    selectedOptionId.value = null
    showResult.value = false
    isCorrect.value = false
  }
}, { immediate: true })

function selectOption(optId) {
  if (showResult.value) return
  selectedOptionId.value = optId
  isCorrect.value = optId === props.question.correct_option_id
  showResult.value = true
  emit('answered', optId)
}

function handleExplain() {
  const q = props.question
  const isRight = isCorrect.value
  const userText = q.options.find(o => o.id === selectedOptionId.value)?.text || selectedOptionId.value
  const correctOption = q.options.find(o => o.id === q.correct_option_id)
  const correctText = correctOption ? `${correctOption.label}. ${correctOption.text}` : q.correct_option_id

  let prompt = 'I am taking a quiz on this material and was given this question: "' + q.stem + '"\n\n'
  prompt += 'I chose this as the answer: "' + userText + '"\n\n'
  if (!isRight) {
    prompt += 'That answer was incorrect. The correct answer is "' + correctText + '"\n\n'
    prompt += 'Help me understand why my answer was incorrect and learn more about this topic.'
  } else {
    prompt += 'That answer was correct.\n\n'
    prompt += 'Help me understand more about this topic and deepen my knowledge.'
  }
  emit('explain', prompt)
}

function prev() { emit('prev') }
function next() { emit('next') }
</script>

<template>
  <div class="qq">
    <!-- 进度 -->
    <div class="qq-progress">
      <span class="qq-progress-num">{{ currentIndex + 1 }} / {{ totalCount }}</span>
      <span v-if="question.category" class="qq-cat-tag">{{ question.category === 'basic' ? '基础' : question.category === 'project' ? '项目' : '行为' }}</span>
    </div>

    <!-- 题干 -->
    <div class="qq-stem">{{ question.stem }}</div>

    <!-- 选项 -->
    <div class="qq-options">
      <button
        v-for="opt in question.options"
        :key="opt.id"
        class="qq-opt"
        :class="{
          'qq-opt-correct': showResult && opt.id === question.correct_option_id,
          'qq-opt-incorrect': showResult && selectedOptionId === opt.id && opt.id !== question.correct_option_id,
          'qq-opt-locked': showResult,
        }"
        @click="selectOption(opt.id)"
        :disabled="showResult"
      >
        <span class="qq-opt-label">{{ opt.label }}</span>
        <div class="qq-opt-body">
          <span class="qq-opt-text">{{ opt.text }}</span>
          <span v-if="showResult" class="qq-opt-desc">{{ opt.description }}</span>
        </div>
        <span v-if="showResult && opt.id === question.correct_option_id" class="qq-opt-icon">&#10003;</span>
        <span v-else-if="showResult && selectedOptionId === opt.id && opt.id !== question.correct_option_id" class="qq-opt-icon qq-opt-icon-wrong">&#10007;</span>
      </button>
    </div>

    <!-- 解析 -->
    <div v-if="showResult" class="qq-explanation">
      <div class="qq-explanation-label">{{ isCorrect ? '回答正确' : '回答错误' }}</div>
      <p class="qq-explanation-text">{{ question.explanation }}</p>
    </div>

    <!-- 底部按钮 -->
    <div class="qq-actions">
      <div class="qq-actions-left">
        <button
          v-if="showResult"
          class="qq-btn-explain"
          @click="handleExplain"
        >Explain</button>
      </div>
      <div class="qq-actions-right">
        <button class="qq-btn-nav" @click="prev" :disabled="currentIndex === 0">上一题</button>
        <button class="qq-btn-nav qq-btn-primary" @click="props.isCompleted && currentIndex === totalCount - 1 ? emit('viewReport') : next()">
          {{ props.isCompleted && currentIndex === totalCount - 1 ? '查看报告' : (currentIndex === totalCount - 1 ? '生成报告' : '下一题') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.qq { display: flex; flex-direction: column; gap: var(--space-4); padding: var(--space-4); }
.qq-progress { display: flex; align-items: center; gap: var(--space-2); }
.qq-progress-num { font-size: var(--text-sm); font-weight: 600; color: var(--fg); font-family: var(--font-mono); }
.qq-cat-tag {
  padding: 1px 8px; border-radius: var(--radius-pill);
  background: color-mix(in oklab, var(--accent), transparent 88%);
  color: var(--accent); font-size: 11px; font-weight: 500;
}
.qq-stem {
  font-size: var(--text-base); font-weight: 600; color: var(--fg); line-height: 1.55;
}
.qq-options { display: flex; flex-direction: column; gap: var(--space-2); }
.qq-opt {
  display: flex; align-items: flex-start; gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm); border: 1.5px solid var(--border);
  background: var(--bg); cursor: pointer;
  text-align: left; font: inherit; color: var(--fg);
  transition: all 0.15s;
  width: 100%;
}
.qq-opt:hover:not(:disabled) { border-color: var(--accent); }
.qq-opt:disabled { cursor: default; }
.qq-opt-correct { background: #c8f2d4; border-color: #006b2f; }
.qq-opt-incorrect { background: #fff4f4; border-color: #b00020; }
.qq-opt-label {
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--surface); border: 1.5px solid var(--border);
  display: grid; place-items: center; font-size: 12px; font-weight: 600;
  color: var(--muted); flex-shrink: 0; transition: all 0.15s;
}
.qq-opt-correct .qq-opt-label { background: #006b2f; border-color: #006b2f; color: #fff; }
.qq-opt-incorrect .qq-opt-label { background: #b00020; border-color: #b00020; color: #fff; }
.qq-opt-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.qq-opt-text { font-size: var(--text-sm); font-weight: 500; line-height: 1.45; }
.qq-opt-desc { font-size: 11px; color: var(--muted); line-height: 1.4; }
.qq-opt-icon { font-size: 14px; font-weight: 700; flex-shrink: 0; }
.qq-opt-correct .qq-opt-icon { color: #006b2f; }
.qq-opt-icon-wrong { color: #b00020; }
.qq-explanation {
  padding: var(--space-3); border-radius: var(--radius-sm);
  background: color-mix(in oklab, var(--accent), transparent 93%);
  border-left: 3px solid var(--accent);
}
.qq-explanation-label { font-size: 11px; font-weight: 600; color: var(--accent); margin-bottom: var(--space-1); }
.qq-explanation-text { font-size: var(--fs-meta); color: var(--fg); line-height: 1.55; margin: 0; }
.qq-actions { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2); }
.qq-actions-left, .qq-actions-right { display: flex; align-items: center; gap: var(--space-2); }
.qq-btn-explain {
  padding: 6px 14px; border: 1px solid var(--border); border-radius: var(--radius-pill);
  background: var(--bg); font: inherit; font-size: var(--fs-meta); font-weight: 500;
  color: var(--muted); cursor: pointer; transition: all 0.15s;
}
.qq-btn-explain:hover { border-color: var(--accent); color: var(--accent); }
.qq-btn-nav {
  padding: 6px 14px; border: 1px solid var(--border); border-radius: var(--radius-pill);
  background: var(--bg); font: inherit; font-size: var(--fs-meta); font-weight: 500;
  color: var(--muted); cursor: pointer; transition: all 0.15s;
}
.qq-btn-nav:hover:not(:disabled) { border-color: var(--fg); color: var(--fg); }
.qq-btn-nav:disabled { opacity: 0.35; cursor: default; }
.qq-btn-primary {
  background: var(--accent); color: var(--accent-on); border-color: var(--accent);
}
.qq-btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
</style>
