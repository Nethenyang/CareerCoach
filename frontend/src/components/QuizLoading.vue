<script setup>
defineProps({
  message: { type: String, default: 'generating' },  // 'generating' | 'reporting'
})
</script>

<template>
  <div class="quiz-loading">
    <div class="ql-spinner"></div>
    <p class="ql-title">{{ message === 'reporting' ? '正在生成评估报告…' : '正在生成测验题目…' }}</p>
    <p class="ql-desc">{{ message === 'reporting' ? 'AI 正在分析答题结果并撰写报告，请稍候' : 'AI 正在分析 JD 并定制化出题，请稍候' }}</p>
  </div>
</template>

<style scoped>
.quiz-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) var(--gap-md);
  gap: var(--space-4);
  text-align: center;
}
.ql-spinner {
  width: 36px; height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: qlSpin 0.7s linear infinite;
}
@keyframes qlSpin {
  to { transform: rotate(360deg); }
}
.ql-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--fg);
  margin: 0;
}
.ql-desc {
  font-size: var(--fs-meta);
  color: var(--muted);
  margin: 0;
}
</style>
