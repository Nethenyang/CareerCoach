<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  score: { type: Number, required: true },
  size: { type: Number, default: 140 },
})

// # 1. SVG 圆环参数
const radius = computed(() => props.size / 2 - 8)
const circumference = computed(() => 2 * Math.PI * radius.value)

// # 2. 动画：从 0 到目标分数
const animatedScore = ref(0)
const dashOffset = computed(() => circumference.value * (1 - animatedScore.value / 100))

// # 3. 字号随 size 等比缩放
const scoreFontSize = computed(() => Math.round(props.size * 0.23))
const strokeWidth = computed(() => props.size > 100 ? 8 : 6)

onMounted(() => {
  requestAnimationFrame(() => {
    animatedScore.value = props.score
  })
})
</script>

<template>
  <div class="score-gauge" :style="{ width: size + 'px', height: size + 'px' }">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`">
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        stroke="var(--border)"
        :stroke-width="strokeWidth"
      />
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        stroke="var(--accent)"
        :stroke-width="strokeWidth"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
        :transform="`rotate(-90 ${size / 2} ${size / 2})`"
        class="gauge-arc"
      />
    </svg>
    <div class="gauge-center">
      <span class="gauge-score" :style="{ fontSize: scoreFontSize + 'px' }">{{ score }}</span>
      <span v-if="size > 100" class="gauge-label">综合评分 · 百分制</span>
    </div>
  </div>
</template>

<style scoped>
.score-gauge {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.gauge-arc {
  transition: stroke-dashoffset 0.8s var(--ease-standard);
}

.gauge-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.gauge-score {
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--fg);
  line-height: 1;
}

.gauge-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--muted);
  white-space: nowrap;
}
</style>
