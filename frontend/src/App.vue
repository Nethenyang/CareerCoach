<script setup>
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ═══════════════════════════════════════════════════════════════════
   TOKENS — Neutral Modern + editorial/tech blend
   ═══════════════════════════════════════════════════════════════ */
:root {
  --bg: #fafafa;
  --surface: #ffffff;
  --fg: #111111;
  --muted: #6b6b6b;
  --border: #e5e5e5;
  --accent: #2f6feb;
  --accent-on: #ffffff;
  --accent-hover: color-mix(in oklab, var(--accent), black 8%);
  --accent-active: color-mix(in oklab, var(--accent), black 14%);
  --success: #17a34a;
  --warn: #eab308;
  --danger: #dc2626;

  --font-display: 'Iowan Old Style', 'Charter', Georgia, 'Times New Roman', serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  --font-mono: ui-monospace, 'JetBrains Mono', 'SF Mono', Menlo, monospace;

  --text-xs: 12px; --text-sm: 14px; --text-base: 16px;
  --text-lg: 20px; --text-xl: 24px; --text-2xl: 32px;
  --text-3xl: 48px; --text-4xl: 64px;

  --space-1: 4px; --space-2: 8px; --space-3: 12px;
  --space-4: 16px; --space-5: 20px; --space-6: 24px;
  --space-8: 32px; --space-12: 48px; --space-20: 80px;

  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px; --radius-pill: 9999px;

  --elev-ring: 0 0 0 1px var(--border);
  --elev-raised: 0 2px 8px color-mix(in oklab, var(--fg), transparent 92%);

  --focus-ring: 0 0 0 3px color-mix(in oklab, var(--accent), transparent 70%);

  --motion-fast: 150ms; --motion-base: 200ms;
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);

  --container-max: 1200px;
  --container-gutter: 24px;

  --fs-h1: clamp(44px, 6vw, 76px);
  --fs-h2: clamp(32px, 4vw, 48px);
  --fs-h3: 22px;
  --fs-lead: 19px;
  --fs-body: 16px;
  --fs-meta: 13px;

  --gap-xs: 8px; --gap-sm: 12px; --gap-md: 20px;
  --gap-lg: 32px; --gap-xl: 56px; --gap-2xl: 96px;

  /* Element Plus 主色覆写 → 蓝色 */
  --el-color-primary: var(--accent);
  --el-color-primary-light-3: color-mix(in oklab, var(--accent), white 24%);
  --el-color-primary-light-5: color-mix(in oklab, var(--accent), white 40%);
  --el-color-primary-light-7: color-mix(in oklab, var(--accent), white 64%);
  --el-color-primary-light-8: color-mix(in oklab, var(--accent), white 76%);
  --el-color-primary-light-9: color-mix(in oklab, var(--accent), white 88%);
  --el-color-primary-dark-2: var(--accent-active);
  --el-border-radius-base: 8px;
}

/* ═══════════════════════════════════════════════════════════════════
   RESET + BASE
   ═══════════════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }
html, body { height: 100%; }
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
body {
  margin: 0; background: var(--bg); color: var(--fg);
  font-family: var(--font-body); font-size: var(--fs-body);
  line-height: 1.55; text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
}
#app { height: 100%; }
img, svg { display: block; max-width: 100%; }
a { color: inherit; text-decoration: none; }
button { font: inherit; cursor: pointer; }
p { text-wrap: pretty; }
h1, h2, h3, h4 { text-wrap: balance; margin: 0; }

/* ═══════════════════════════════════════════════════════════════════
   SCROLLBAR
   ═══════════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: var(--radius-pill);
}
::-webkit-scrollbar-thumb:hover {
  background: var(--muted);
}

/* ═══════════════════════════════════════════════════════════════════
   KEYFRAMES
   ═══════════════════════════════════════════════════════════════ */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes charReveal {
  from { opacity: 0; transform: translateY(12px) scale(0.95); filter: blur(4px); }
  to   { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
}
@keyframes shimmer {
  from { transform: translateX(-100%); }
  to   { transform: translateX(100%); }
}
@keyframes uploadPulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 color-mix(in oklab, var(--accent), transparent 85%); }
  50%      { transform: scale(1.04); box-shadow: 0 0 0 12px transparent; }
}
@keyframes msgIn {
  from { opacity: 0; transform: translateY(12px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); }
  30%            { transform: translateY(-6px); }
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-10px); }
}

/* ═══════════════════════════════════════════════════════════════════
   ROUTE TRANSITION
   ═══════════════════════════════════════════════════════════════ */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s var(--ease-standard);
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
