<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  skills: { type: Array, required: true },
  compact: { type: Boolean, default: false },
})

// # 1. 动画用：初始 width = 0，mounted 后过渡到目标
const mounted = ref(false)

onMounted(() => {
  requestAnimationFrame(() => {
    mounted.value = true
  })
})
</script>

<template>
  <div class="skill-bars" :class="{ compact }">
    <div v-for="(item, i) in skills" :key="i" class="skill-bar">
      <span class="skill-label">{{ item.skill }}</span>
      <div class="skill-track">
        <div
          class="skill-fill"
          :style="{
            width: mounted ? item.score + '%' : '0%',
            transitionDelay: i * 0.08 + 's',
          }"
        ></div>
      </div>
      <span class="skill-score">{{ item.score }}</span>
    </div>
  </div>
</template>

<style scoped>
.skill-bars {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.skill-bars.compact {
  gap: var(--space-2);
}

.skill-bar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.compact .skill-bar {
  gap: var(--space-2);
}

.skill-label {
  width: 144px;
  font-size: var(--fs-meta);
  font-weight: 500;
  color: var(--fg);
  flex-shrink: 0;
  text-align: right;
  white-space: nowrap;
}

.compact .skill-label {
  width: 104px;
  font-size: 11px;
}

.skill-track {
  flex: 1;
  height: 8px;
  background: var(--border);
  border-radius: var(--radius-pill);
  overflow: hidden;
}

.compact .skill-track {
  height: 6px;
}

.skill-fill {
  height: 100%;
  background: var(--fg);
  border-radius: var(--radius-pill);
  transition: width 0.6s var(--ease-standard);
}

.skill-score {
  font-size: var(--fs-meta);
  font-weight: 600;
  color: var(--fg);
  font-family: var(--font-mono);
  flex-shrink: 0;
  width: 28px;
  text-align: right;
}

.compact .skill-score {
  font-size: 11px;
  width: 22px;
}
</style>
