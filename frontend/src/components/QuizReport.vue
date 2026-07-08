<script setup>
import { computed } from 'vue'

const emit = defineEmits(['quit', 'review'])

const props = defineProps({
  session: { type: Object, required: true },
  report: { type: Object, default: null },
})

const totalAnswered = computed(() => {
  const rep = props.report
  if (rep) return rep.total_questions || props.session.question_count
  return props.session.question_count
})
const correctCount = computed(() => {
  if (props.report) return props.report.correct_count ?? 0
  return props.session.score ?? 0
})
const incorrectCount = computed(() => {
  if (props.report) return props.report.incorrect_count ?? 0
  return totalAnswered.value - correctCount.value
})
const scorePercent = computed(() => {
  if (props.report) return props.report.score_percent ?? 0
  if (totalAnswered.value === 0) return 0
  return Math.round((correctCount.value / totalAnswered.value) * 100)
})
const grade = computed(() => props.report?.grade || (scorePercent.value >= 90 ? '优秀' : scorePercent.value >= 70 ? '良好' : scorePercent.value >= 50 ? '一般' : '需要加强'))
const categories = computed(() => props.report?.categories || [])
const strengths = computed(() => props.report?.strengths || [])
const weaknesses = computed(() => props.report?.weaknesses || [])
const suggestions = computed(() => props.report?.suggestions || [])

const R = 52
const circ = 2 * Math.PI * R
const dashOffset = computed(() => circ * (1 - scorePercent.value / 100))
</script>

<template>
  <div class="qr">
    <!-- 迷你摘要 -->
    <div class="qr-mini">
      <div class="qr-ring-wrap">
        <svg class="qr-ring-svg" width="120" height="120" viewBox="0 0 120 120">
          <circle class="qr-ring-bg" cx="60" cy="60" :r="R" />
          <circle
            class="qr-ring-fg"
            cx="60" cy="60" :r="R"
            :stroke-dasharray="circ"
            :stroke-dashoffset="dashOffset"
          />
        </svg>
        <div class="qr-ring-center">
          <span class="qr-ring-num">{{ correctCount }}/{{ totalAnswered }}</span>
          <span class="qr-ring-pct">{{ scorePercent }}%</span>
        </div>
      </div>
      <div class="qr-mini-meta">
        <div class="qr-mini-grade">{{ grade }}</div>
        <div class="qr-mini-stats">正确 {{ correctCount }} · 错误 {{ incorrectCount }}</div>
      </div>
    </div>

    <!-- 完整报告 -->
    <div class="qr-full">
      <!-- 分类得分 -->
      <div v-if="categories.length" class="qr-section">
        <h4 class="qr-section-title">分类得分</h4>
        <div v-for="c in categories" :key="c.name" class="qr-cat-row">
          <div class="qr-cat-head">
            <span class="qr-cat-name">{{ c.name }}</span>
            <span class="qr-cat-pct">{{ c.correct }}/{{ c.total }} · {{ c.percent }}%</span>
          </div>
          <div class="qr-cat-bar">
            <div class="qr-cat-fill" :class="c.percent >= 80 ? 'good' : c.percent >= 50 ? 'mid' : 'weak'" :style="{ width: c.percent + '%' }"></div>
          </div>
        </div>
      </div>

      <!-- 强项 -->
      <div v-if="strengths.length" class="qr-section">
        <h4 class="qr-section-title qr-title-good">强项</h4>
        <div v-for="(s, i) in strengths" :key="i" class="qr-sw-item good">{{ s }}</div>
      </div>

      <!-- 弱项 -->
      <div v-if="weaknesses.length" class="qr-section">
        <h4 class="qr-section-title qr-title-weak">薄弱项</h4>
        <div v-for="(w, i) in weaknesses" :key="i" class="qr-sw-item weak">{{ w }}</div>
      </div>

      <!-- 学习建议 -->
      <div v-if="suggestions.length" class="qr-section">
        <h4 class="qr-section-title">学习建议</h4>
        <div v-for="(sug, i) in suggestions" :key="i" class="qr-sug-card">
          <span class="qr-sug-topic">{{ sug.topic }}</span>
          <span class="qr-sug-tip">{{ sug.tip }}</span>
        </div>
      </div>
    </div>

    <div class="qr-actions">
      <button class="qr-btn" @click="emit('review')">回顾测试</button>
      <button class="qr-btn" @click="emit('quit')">退出</button>
    </div>
  </div>
</template>

<style scoped>
.qr { display: flex; flex-direction: column; gap: var(--space-4); padding: var(--space-4); }
.qr-mini { display: flex; align-items: center; gap: var(--space-5); }
.qr-ring-wrap { position: relative; width: 120px; height: 120px; flex-shrink: 0; }
.qr-ring-svg { transform: rotate(-90deg); }
.qr-ring-bg { fill: none; stroke: var(--border); stroke-width: 8; }
.qr-ring-fg {
  fill: none; stroke: var(--accent); stroke-width: 8; stroke-linecap: round;
  transition: stroke-dashoffset 0.8s ease;
}
.qr-ring-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.qr-ring-num { font-family: var(--font-display); font-size: 20px; font-weight: 600; color: var(--fg); }
.qr-ring-pct { font-size: 11px; color: var(--muted); }
.qr-mini-meta { display: flex; flex-direction: column; gap: var(--space-1); }
.qr-mini-grade { font-size: var(--text-lg); font-weight: 600; color: var(--fg); }
.qr-mini-stats { font-size: var(--fs-meta); color: var(--muted); }

.qr-full { display: flex; flex-direction: column; gap: var(--space-4); border-top: 1px solid var(--border); padding-top: var(--space-4); }
.qr-section { display: flex; flex-direction: column; gap: var(--space-1); }
.qr-section-title { font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; margin: 0 0 var(--space-1); }
.qr-title-good { color: var(--success); }
.qr-title-weak { color: var(--danger); }

.qr-cat-row { margin-bottom: var(--space-1); }
.qr-cat-head { display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 2px; }
.qr-cat-name { color: var(--fg); font-weight: 500; }
.qr-cat-pct { font-family: var(--font-mono); color: var(--muted); }
.qr-cat-bar { height: 4px; border-radius: 2px; background: var(--border); overflow: hidden; }
.qr-cat-fill { height: 100%; border-radius: 2px; transition: width 0.6s ease; }
.qr-cat-fill.good { background: var(--success); }
.qr-cat-fill.mid  { background: var(--warn); }
.qr-cat-fill.weak { background: var(--danger); }

.qr-sw-item { font-size: 11px; line-height: 1.5; padding: 3px 0 3px 10px; border-left: 2px solid; }
.qr-sw-item.good { border-color: var(--success); color: var(--muted); }
.qr-sw-item.weak { border-color: var(--danger); color: var(--muted); }

.qr-sug-card { display: flex; flex-direction: column; gap: 2px; padding: var(--space-2); border-radius: var(--radius-sm); background: var(--bg); border: 1px solid var(--border); }
.qr-sug-topic { font-size: 11px; font-weight: 600; color: var(--fg); }
.qr-sug-tip { font-size: 11px; color: var(--muted); line-height: 1.45; }

.qr-actions { display: flex; justify-content: space-between; border-top: 1px solid var(--border); padding-top: var(--space-3); }
.qr-btn {
  padding: 6px 12px; border: 1px solid var(--border); border-radius: var(--radius-pill);
  background: var(--bg); font: inherit; font-size: 11px; font-weight: 500;
  color: var(--muted); cursor: pointer; transition: all 0.15s;
}
.qr-btn:hover { border-color: var(--fg); color: var(--fg); }
.qr-btn-primary { background: var(--accent); color: var(--accent-on); border-color: var(--accent); }
.qr-btn-primary:hover { background: var(--accent-hover); }
.qr-btn-primary:hover { background: var(--accent-hover); }
</style>
