<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ParticleBg from '@/components/ParticleBg.vue'

const router = useRouter()

// # 1. 标题文字 — 逐字动画用
const headlineText = '让 AI 读懂你的简历'
const chars = ref([])

onMounted(() => {
  // # 2. 拆分标题为单个字符 span，设置 staggered animation-delay
  let arr = []
  for (let i = 0; i < headlineText.length; i++) {
    arr.push({
      ch: headlineText[i],
      delay: 0.5 + i * 0.05,
    })
  }
  chars.value = arr
})

function goUpload() {
  router.push('/app/resume')
}
</script>

<template>
  <div class="landing">
    <ParticleBg :count="50" />

    <div class="welcome-content">
      <p class="welcome-greeting">智能简历分析 · AI 驱动</p>

      <h1 class="welcome-headline">
        <span
          v-for="(item, i) in chars"
          :key="i"
          class="char"
          :style="{ animationDelay: item.delay + 's' }"
        >{{ item.ch }}</span>
      </h1>

      <p class="welcome-subtitle">
        上传一份简历，十五秒钟获得深度分析报告。<br>从排版到关键词，从经历到潜力，AI 逐项拆解。
      </p>

      <div class="welcome-cta">
        <button class="btn-primary btn-xl" @click="goUpload">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
          </svg>
          上传我的简历
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.landing {
  position: relative;
  width: 100%;
  min-height: 100vh;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.welcome-content {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 640px;
  padding: 0 var(--container-gutter);
}

.welcome-greeting {
  font-family: var(--font-mono);
  font-size: 13px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0 0 var(--gap-md);
  opacity: 0;
  animation: fadeInUp 0.6s var(--ease-standard) 0.3s forwards;
}

.welcome-headline {
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  font-weight: 600;
  line-height: 1.04;
  letter-spacing: -0.02em;
  margin: 0;
}

.welcome-headline .char {
  display: inline-block;
  opacity: 0;
  animation: charReveal 0.4s var(--ease-standard) forwards;
}

.welcome-subtitle {
  margin-top: var(--gap-md);
  font-size: var(--fs-lead);
  line-height: 1.55;
  color: var(--muted);
  max-width: 60ch;
  margin-left: auto;
  margin-right: auto;
  opacity: 0;
  animation: fadeInUp 0.6s var(--ease-standard) 1s forwards;
}

.welcome-cta {
  margin-top: var(--gap-xl);
  opacity: 0;
  animation: fadeInUp 0.6s var(--ease-standard) 1.3s forwards;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 11px 20px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--accent);
  background: var(--accent);
  color: var(--accent-on);
  font-size: 15px;
  font-weight: 500;
  letter-spacing: -0.005em;
  transition: background 0.15s ease, transform 0.05s ease;
}
.btn-primary:hover {
  background: var(--accent-hover);
}
.btn-primary:active {
  transform: translateY(1px);
}

.btn-xl {
  padding: 16px 36px;
  font-size: 18px;
  border-radius: var(--radius-md);
  position: relative;
  overflow: hidden;
}

.btn-xl::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 40%, color-mix(in oklab, var(--accent-on), transparent 70%) 50%, transparent 60%);
  animation: shimmer 2.5s ease-in-out infinite;
}

@media (max-width: 480px) {
  .welcome-headline {
    font-size: clamp(32px, 8vw, 48px);
  }
}
</style>
