<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  result: { type: Object, default: null },
  compact: { type: Boolean, default: false },
})

const activeTab = ref('ability')

const suggestionTypeMap = {
  verb_replacement: { label: '弱动词', type: 'warning' },
  missing_quantification: { label: '缺少量化', type: 'danger' },
  structure: { label: '结构问题', type: 'info' },
  jd_gap: { label: 'JD 差距', type: 'success' },
}

const tierMap = {
  startup: { label: '初创公司', type: 'info' },
  mid: { label: '中型公司', type: 'success' },
  big_edge: { label: '大厂边缘', type: 'warning' },
  big_core: { label: '大厂核心', type: 'danger' },
}

const hasAbility = computed(() => props.result?.ability_profile)
const hasTier = computed(() => props.result?.tier_suggestion)
const hasJds = computed(() => props.result?.retrieved_jds?.length)
const hasSuggestions = computed(() => props.result?.suggestions?.length)
</script>

<template>
  <div :class="['analysis-tabs', { compact }]">
    <el-tabs v-model="activeTab" class="tabs">
      <!-- 能力评估 -->
      <el-tab-pane label="能力评估" name="ability" v-if="hasAbility">
        <div :class="['card', { compact }]">
          <div class="tag-row">
            <el-tag effect="plain" size="small">{{ result.ability_profile.tech_direction }}</el-tag>
            <el-tag effect="plain" size="small" type="info">{{ result.ability_profile.experience_level }}</el-tag>
          </div>
          <p class="summary-text">{{ result.ability_profile.summary }}</p>
          <div class="tag-group">
            <span class="group-label">核心技能</span>
            <div class="tag-cloud">
              <el-tag
                v-for="skill in result.ability_profile.skills"
                :key="skill"
                size="small"
                effect="plain"
              >{{ skill }}</el-tag>
            </div>
          </div>
          <div class="sw-row">
            <div class="sw-col">
              <span class="sw-label sw-strength">优势</span>
              <ul class="sw-list">
                <li v-for="item in result.ability_profile.strengths" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div class="sw-col">
              <span class="sw-label sw-weakness">不足</span>
              <ul class="sw-list">
                <li v-for="item in result.ability_profile.weaknesses" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 梯队建议 -->
      <el-tab-pane label="梯队建议" name="tier" v-if="hasTier">
        <div :class="['card', { compact }]">
          <div class="tier-top">
            <el-tag
              :type="tierMap[result.tier_suggestion.tier]?.type || 'info'"
              effect="dark"
              :size="compact ? 'small' : 'default'"
            >
              {{ tierMap[result.tier_suggestion.tier]?.label || result.tier_suggestion.tier }}
            </el-tag>
            <div v-if="result.tier_suggestion.alternative_tiers?.length" class="tier-alt">
              <span class="alt-label">备选</span>
              <el-tag
                v-for="t in result.tier_suggestion.alternative_tiers"
                :key="t"
                size="small"
                effect="plain"
                type="info"
              >{{ tierMap[t]?.label || t }}</el-tag>
            </div>
          </div>
          <p class="reasoning-text">{{ result.tier_suggestion.reasoning }}</p>
        </div>
      </el-tab-pane>

      <!-- 推荐岗位 -->
      <el-tab-pane :label="`推荐岗位${hasJds ? '(' + hasJds + ')' : ''}`" name="jds" v-if="hasJds">
        <div class="jd-list">
          <div
            v-for="(jd, index) in result.retrieved_jds"
            :key="index"
            :class="['jd-card', { compact }]"
          >
            <div class="jd-top">
              <span class="jd-position">{{ jd.position }}</span>
              <span v-if="jd.company" class="jd-company">{{ jd.company }}</span>
              <el-tag size="small" effect="plain" type="info">{{ tierMap[jd.tier]?.label || jd.tier }}</el-tag>
            </div>
            <p class="jd-requirements">{{ jd.requirements }}</p>
          </div>
        </div>
      </el-tab-pane>

      <!-- 优化建议 -->
      <el-tab-pane :label="`优化建议${hasSuggestions ? '(' + result.suggestions.length + ')' : ''}`" name="suggestions" v-if="hasSuggestions">
        <div class="suggestion-list">
          <div
            v-for="(item, index) in result.suggestions"
            :key="index"
            :class="['suggestion-card', { compact }]"
          >
            <div class="suggestion-top">
              <el-tag
                :type="suggestionTypeMap[item.type]?.type || 'info'"
                effect="plain"
                size="small"
                round
              >
                {{ suggestionTypeMap[item.type]?.label || item.type }}
              </el-tag>
              <span class="suggestion-loc">{{ item.location }}</span>
            </div>
            <p class="suggestion-issue">{{ item.issue }}</p>
            <div class="diff-block">
              <div class="diff-row diff-before">
                <span class="diff-tag">修改前</span>
                <p class="diff-text">{{ item.before }}</p>
              </div>
              <div class="diff-arrow-wrap">
                <el-icon class="diff-arrow"><ArrowDown /></el-icon>
              </div>
              <div class="diff-row diff-after">
                <span class="diff-tag">修改后</span>
                <p class="diff-text">{{ item.after }}</p>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.analysis-tabs {
  width: 100%;
}

/* ── Tab 样式覆写 ── */
:deep(.el-tabs__header) {
  margin: 0 0 16px 0;
}
:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: var(--border-light);
}
:deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  padding: 0 16px;
}
:deep(.el-tabs__item.is-active) {
  color: var(--text-primary);
  font-weight: 600;
}
:deep(.el-tabs__active-bar) {
  background: var(--accent);
}

.compact :deep(.el-tabs__item) {
  font-size: 13px;
  padding: 0 12px;
}
.compact :deep(.el-tabs__header) {
  margin: 0 0 12px 0;
}

/* ── 通用卡片 ── */
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 20px;
}
.card.compact {
  padding: 14px 16px;
}

/* ── 能力评估 ── */
.tag-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.compact .tag-row {
  gap: 6px;
  margin-bottom: 10px;
}

.summary-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: 16px;
}
.compact .summary-text {
  font-size: 13px;
  margin-bottom: 12px;
}

.tag-group {
  margin-bottom: 16px;
}
.compact .tag-group {
  margin-bottom: 12px;
}

.group-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 8px;
}
.compact .group-label {
  font-size: 11px;
  margin-bottom: 6px;
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.compact .tag-cloud {
  gap: 4px;
}

.sw-row {
  display: flex;
  gap: 20px;
}
.compact .sw-row {
  gap: 16px;
}

.sw-col {
  flex: 1;
}

.sw-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}
.compact .sw-label {
  font-size: 11px;
  margin-bottom: 6px;
}

.sw-strength {
  color: #5f9c5f;
}
.sw-weakness {
  color: #c45656;
}

.sw-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.sw-list li {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  padding-left: 12px;
  position: relative;
}
.compact .sw-list li {
  font-size: 12px;
  padding-left: 10px;
}
.sw-list li::before {
  content: '·';
  position: absolute;
  left: 0;
  font-weight: 700;
}

/* ── 梯队建议 ── */
.tier-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.compact .tier-top {
  gap: 8px;
  margin-bottom: 10px;
}

.tier-alt {
  display: flex;
  align-items: center;
  gap: 6px;
}
.compact .tier-alt {
  gap: 4px;
}

.alt-label {
  font-size: 12px;
  color: var(--text-tertiary);
}
.compact .alt-label {
  font-size: 11px;
}

.reasoning-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}
.compact .reasoning-text {
  font-size: 13px;
}

/* ── 推荐岗位 ── */
.jd-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.compact .jd-list {
  gap: 8px;
}

.jd-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 16px 20px;
  transition: border-color var(--duration) var(--ease);
}
.jd-card.compact {
  padding: 12px 14px;
}
.jd-card:hover {
  border-color: var(--border-default);
}

.jd-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
.compact .jd-top {
  gap: 6px;
  margin-bottom: 6px;
}

.jd-position {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.compact .jd-position {
  font-size: 13px;
}

.jd-company {
  font-size: 13px;
  color: var(--text-secondary);
}
.compact .jd-company {
  font-size: 12px;
}

.jd-requirements {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.compact .jd-requirements {
  font-size: 12px;
  -webkit-line-clamp: 2;
}

/* ── 优化建议 ── */
.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.compact .suggestion-list {
  gap: 10px;
}

.suggestion-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius);
  padding: 20px;
  transition: border-color var(--duration) var(--ease), box-shadow var(--duration) var(--ease);
}
.suggestion-card.compact {
  padding: 14px 16px;
}
.suggestion-card:hover {
  border-color: var(--border-default);
  box-shadow: var(--shadow-sm);
}

.suggestion-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.compact .suggestion-top {
  gap: 8px;
  margin-bottom: 6px;
}

.suggestion-loc {
  font-size: 13px;
  color: var(--text-secondary);
}
.compact .suggestion-loc {
  font-size: 12px;
}

.suggestion-issue {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 16px;
  line-height: 1.5;
}
.compact .suggestion-issue {
  font-size: 13px;
  margin-bottom: 12px;
}

/* ── Diff 块 ── */
.diff-block {
  display: flex;
  flex-direction: column;
  gap: 0;
  background: var(--bg-page);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.diff-row {
  padding: 12px 16px;
}
.compact .diff-row {
  padding: 10px 12px;
}

.diff-before {
  background: #fef0f0;
}
.diff-after {
  background: #f0f9eb;
}

.diff-tag {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}
.compact .diff-tag {
  font-size: 10px;
  margin-bottom: 4px;
}

.diff-text {
  font-size: 14px;
  line-height: 1.6;
}
.compact .diff-text {
  font-size: 13px;
  line-height: 1.5;
}

.diff-before .diff-text {
  color: #c45656;
  text-decoration: line-through;
  text-decoration-color: #e8a0a0;
}
.diff-after .diff-text {
  color: #5f9c5f;
}

.diff-arrow-wrap {
  display: flex;
  justify-content: center;
  padding: 2px 0;
  background: var(--bg-page);
}

.diff-arrow {
  font-size: 14px;
  color: var(--text-tertiary);
}
.compact .diff-arrow {
  font-size: 12px;
}
</style>
