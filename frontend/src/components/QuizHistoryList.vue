<script setup>
const emit = defineEmits(['select', 'delete', 'new-quiz', 'report', 'retake'])

const props = defineProps({
  items: { type: Array, default: () => [] },
})

function formatTime(time) {
  if (!time) return ''
  const d = new Date(time)
  return d.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <div class="qhl">
    <button class="qhl-new-btn" @click="emit('new-quiz')">+ 新建测验</button>

    <div class="qhl-divider"></div>
    <p class="qhl-label">测验历史</p>

    <div v-if="!items.length" class="qhl-empty">暂无测验记录</div>

    <div v-for="item in items" :key="item.id" class="qhl-item">
      <div class="qhl-item-top">
        <span class="qhl-item-title">{{ item.title }}</span>
        <div class="qhl-item-icons">
          <button
            v-if="item.status === 'completed'"
            class="qhl-icon-btn qhl-icon-report"
            @click.stop="emit('report', item.id)"
            title="查看报告"
          >
            <img src="/查看报告.svg" width="14" height="14" alt="查看报告" />
          </button>
          <button
            class="qhl-icon-btn qhl-icon-retake"
            @click.stop="emit('retake', item.id)"
            title="重新测试"
          >
            <img src="/重新测试.svg" width="14" height="14" alt="重新测试" />
          </button>
          <button
            class="qhl-icon-btn qhl-icon-del"
            @click.stop="emit('delete', item.id)"
            title="删除"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      <div class="qhl-item-meta">
        <span>{{ item.question_count }} 题</span>
        <span v-if="item.status === 'completed'" class="qhl-item-score">
          {{ item.score ?? '?' }}/{{ item.question_count }}
        </span>
        <span v-else class="qhl-item-badge">进行中</span>
        <span class="qhl-item-time">{{ formatTime(item.created_at) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.qhl { display: flex; flex-direction: column; gap: var(--space-2); padding: var(--space-4); }
.qhl-new-btn {
  padding: 8px 0;
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  font: inherit;
  font-size: var(--fs-meta);
  font-weight: 500;
  color: var(--accent);
  cursor: pointer;
  transition: all 0.15s;
  text-align: center;
}
.qhl-new-btn:hover { border-color: var(--accent); background: color-mix(in oklab, var(--accent), transparent 95%); }
.qhl-divider { height: 1px; background: var(--border); margin: var(--space-2) 0; }
.qhl-label { font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; margin: 0; }
.qhl-empty { font-size: var(--fs-meta); color: var(--muted); text-align: center; padding: var(--space-6) 0; }
.qhl-item {
  position: relative;
  padding: var(--space-3);
  padding-right: 110px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.qhl-item-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-1); }
.qhl-item-title { font-size: var(--text-sm); font-weight: 500; color: var(--fg); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.qhl-item-icons {
  position: absolute;
  right: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  display: flex; align-items: center; gap: 8px;
}
.qhl-icon-btn {
  width: 28px; height: 28px;
  border-radius: 50%; border: none;
  display: grid; place-items: center; cursor: pointer;
  transition: opacity 0.15s, transform 0.15s;
  opacity: 0.75;
}
.qhl-icon-btn:hover { opacity: 1; transform: scale(1.1); }
.qhl-icon-report { background: #34c759; }
.qhl-icon-retake { background: #ff9500; }
.qhl-icon-del { background: #ff3b30; }
.qhl-icon-btn img { filter: brightness(0) invert(1); width: 14px; height: 14px; }
.qhl-icon-del svg { color: #fff; width: 14px; height: 14px; }
.qhl-item-meta { display: flex; align-items: center; gap: var(--space-2); font-size: 11px; color: var(--muted); }
.qhl-item-score { font-family: var(--font-mono); font-weight: 600; color: var(--fg); }
.qhl-item-badge { padding: 1px 6px; border-radius: var(--radius-pill); background: color-mix(in oklab, var(--warn), transparent 85%); color: var(--warn); font-weight: 500; }
.qhl-item-time { font-family: var(--font-mono); }
</style>
