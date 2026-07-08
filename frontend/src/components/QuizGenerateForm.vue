<script setup>
import { ref } from 'vue'

const emit = defineEmits(['generate', 'cancel'])

const title = ref('')
const questionCount = ref(8)
const userRequirements = ref('')

function handleSubmit() {
  if (!title.value.trim()) return
  emit('generate', {
    title: title.value.trim(),
    question_count: questionCount.value,
    user_requirements: userRequirements.value.trim(),
  })
}
</script>

<template>
  <div class="qgf">
    <h3 class="qgf-title">新建面试测验</h3>

    <label class="qgf-label">测验标题</label>
    <input
      v-model="title"
      class="qgf-input"
      type="text"
      placeholder="例如：微服务面试突击测验"
      maxlength="100"
      @keydown.enter.exact="handleSubmit"
    />

    <label class="qgf-label">题目数量</label>
    <div class="qgf-select-row">
      <button
        v-for="n in [5, 8, 10, 15]"
        :key="n"
        class="qgf-count-btn"
        :class="{ active: questionCount === n }"
        @click="questionCount = n"
      >{{ n }} 题</button>
    </div>

    <label class="qgf-label">自定义要求（可选）</label>
    <textarea
      v-model="userRequirements"
      class="qgf-textarea"
      rows="3"
      placeholder="例如：重点考察微服务和分布式系统相关知识点"
    ></textarea>

    <div class="qgf-actions">
      <button class="qgf-btn-cancel" @click="emit('cancel')">取消</button>
      <button class="qgf-btn-submit" :disabled="!title.trim()" @click="handleSubmit">生成测验题目</button>
    </div>
  </div>
</template>

<style scoped>
.qgf {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
}
.qgf-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--fg);
  margin: 0 0 var(--space-1);
}
.qgf-label {
  font-size: var(--fs-meta);
  font-weight: 500;
  color: var(--muted);
}
.qgf-input {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font: inherit;
  font-size: var(--text-sm);
  background: var(--bg);
  color: var(--fg);
  transition: border-color 0.15s;
}
.qgf-input:focus {
  outline: none;
  border-color: var(--accent);
}
.qgf-select-row {
  display: flex;
  gap: var(--space-2);
}
.qgf-count-btn {
  flex: 1;
  padding: 6px 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  font: inherit;
  font-size: 12px;
  font-weight: 500;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.15s;
  text-align: center;
}
.qgf-count-btn:hover { border-color: var(--accent); color: var(--accent); }
.qgf-count-btn.active {
  border-color: var(--accent);
  background: color-mix(in oklab, var(--accent), transparent 90%);
  color: var(--accent);
  font-weight: 600;
}
.qgf-textarea {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font: inherit;
  font-size: var(--fs-meta);
  background: var(--bg);
  color: var(--fg);
  resize: vertical;
  transition: border-color 0.15s;
}
.qgf-textarea:focus {
  outline: none;
  border-color: var(--accent);
}
.qgf-actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-2);
}
.qgf-btn-cancel {
  flex: 1;
  padding: 8px 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  font: inherit;
  font-size: var(--fs-meta);
  color: var(--muted);
  cursor: pointer;
  transition: all 0.15s;
}
.qgf-btn-cancel:hover { border-color: var(--fg); color: var(--fg); }
.qgf-btn-submit {
  flex: 2;
  padding: 8px 0;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  font: inherit;
  font-size: var(--fs-meta);
  font-weight: 600;
  color: var(--accent-on);
  cursor: pointer;
  transition: background 0.15s;
}
.qgf-btn-submit:hover:not(:disabled) { background: var(--accent-hover); }
.qgf-btn-submit:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
