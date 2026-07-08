<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  dimensions: { type: Array, required: true },
})

// # 1. 记录每个维度下展开的子项 (key: "dimIndex-subIndex")
const expandedItems = ref(new Set())

// # 2. 分数条动画
const mounted = ref(false)

// # 3. 分数颜色：低分红色、中分黄色、高分蓝色
function scoreColor(score) {
  if (score >= 80) return 'var(--accent)'
  if (score >= 70) return 'var(--warn)'
  return '#e85d3a'
}

// # 4. toggle 子项展开/折叠
function toggleItem(dimIdx, subIdx) {
  const key = `${dimIdx}-${subIdx}`
  if (expandedItems.value.has(key)) {
    expandedItems.value.delete(key)
  } else {
    expandedItems.value.add(key)
  }
  // 触发响应式更新
  expandedItems.value = new Set(expandedItems.value)
}

// # 5. 检查子项是否展开
function isExpanded(dimIdx, subIdx) {
  return expandedItems.value.has(`${dimIdx}-${subIdx}`)
}

onMounted(() => {
  requestAnimationFrame(() => {
    mounted.value = true
  })
})
</script>

<template>
  <div class="dimension-report">
    <div v-for="(dim, di) in dimensions" :key="di" class="dim-card">
      <!-- 维度头部 -->
      <div class="dim-header">
        <span class="dim-name">{{ dim.name }}</span>
        <div class="dim-score-area">
          <div class="dim-bar-track">
            <div
              class="dim-bar-fill"
              :style="{
                width: mounted ? dim.score + '%' : '0%',
                background: scoreColor(dim.score),
                transitionDelay: di * 0.1 + 's',
              }"
            ></div>
          </div>
          <span class="dim-score" :style="{ color: scoreColor(dim.score) }">{{ dim.score }}</span>
        </div>
      </div>

      <!-- 子项列表 -->
      <div class="dim-sub-items">
        <div
          v-for="(sub, si) in dim.sub_items"
          :key="si"
          class="sub-item"
          :class="{ expanded: isExpanded(di, si) }"
        >
          <button class="sub-header" @click="toggleItem(di, si)">
            <span class="sub-toggle">{{ isExpanded(di, si) ? '▾' : '▸' }}</span>
            <span class="sub-name">{{ sub.name }}</span>
          </button>

          <!-- 展开内容 -->
          <transition name="sub-expand">
            <div v-if="isExpanded(di, si)" class="sub-detail">
              <div class="sub-row sub-pros">
                <span class="sub-label">优点</span>
                <p>{{ sub.pros }}</p>
              </div>
              <div class="sub-row sub-cons">
                <span class="sub-label">不足</span>
                <p>{{ sub.cons }}</p>
              </div>
              <div class="sub-row sub-suggestion">
                <span class="sub-label">建议</span>
                <p>{{ sub.suggestion }}</p>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dimension-report {
  display: flex;
  flex-direction: column;
  gap: var(--gap-md);
}

/* ── 维度卡片 ── */
.dim-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

/* ── 维度头部 ── */
.dim-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg);
}

.dim-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--fg);
}

.dim-score-area {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.dim-bar-track {
  width: 80px;
  height: 6px;
  background: var(--border);
  border-radius: var(--radius-pill);
  overflow: hidden;
}

.dim-bar-fill {
  height: 100%;
  border-radius: var(--radius-pill);
  transition: width 0.6s var(--ease-standard);
}

.dim-score {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: 700;
  min-width: 28px;
  text-align: right;
}

/* ── 子项列表 ── */
.dim-sub-items {
  padding: var(--space-1) 0;
}

.sub-item {
  border-top: 1px solid var(--border);
}

.sub-item:first-child {
  border-top: none;
}

.sub-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: 8px 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: var(--fg);
  text-align: left;
  transition: background 0.15s;
}

.sub-header:hover {
  background: color-mix(in oklab, var(--accent), transparent 96%);
}

.sub-toggle {
  font-size: 10px;
  color: var(--muted);
  flex-shrink: 0;
  width: 12px;
}

.sub-name {
  font-weight: 500;
}

/* ── 展开内容 ── */
.sub-expand-enter-active,
.sub-expand-leave-active {
  transition: all 0.25s var(--ease-standard);
  overflow: hidden;
}

.sub-expand-enter-from,
.sub-expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.sub-expand-enter-to,
.sub-expand-leave-from {
  opacity: 1;
  max-height: 500px;
}

.sub-detail {
  padding: var(--space-2) 16px var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.sub-row {
  display: flex;
  gap: var(--space-2);
  padding-left: 12px;
}

.sub-label {
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
  width: 32px;
  padding-top: 1px;
}

.sub-row p {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--muted);
}

/* 优点 — 绿色左边框 */
.sub-pros {
  border-left: 3px solid var(--success, #2d8f50);
}

/* 不足 — 黄色左边框 */
.sub-cons {
  border-left: 3px solid var(--warn, #c4a020);
}

/* 建议 — 蓝色左边框 */
.sub-suggestion {
  border-left: 3px solid var(--accent);
}

.sub-pros .sub-label {
  color: var(--success, #2d8f50);
}

.sub-cons .sub-label {
  color: var(--warn, #c4a020);
}

.sub-suggestion .sub-label {
  color: var(--accent);
}
</style>
