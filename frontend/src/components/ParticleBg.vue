<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  count: { type: Number, default: 50 },
})

const canvas = ref(null)
let ctx = null
let particles = []
let animId = null
let resizeObserver = null

// # 1. 粒子色调 — 与 --accent #2f6feb 一致
const accentRGB = [47, 111, 235]

function initParticles(width, height) {
  particles = []
  for (let i = 0; i < props.count; i++) {
    // # 2. 每个粒子随机位置、速度、半径、透明度
    let p = {
      x: Math.random() * width,
      y: Math.random() * height,
      r: Math.random() * 2.5 + 0.8,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4 - 0.3,
      alpha: Math.random() * 0.35 + 0.08,
    }
    particles.push(p)
  }
}

function draw(width, height) {
  ctx.clearRect(0, 0, width, height)

  // # 3. 逐帧更新粒子位置 + 绘制圆点
  for (let i = 0; i < particles.length; i++) {
    let p = particles[i]
    p.x += p.vx
    p.y += p.vy
    // # 4. 边界环绕（非反弹）
    if (p.x < 0) p.x = width
    if (p.x > width) p.x = 0
    if (p.y < 0) p.y = height
    if (p.y > height) p.y = 0
    // # 5. 画粒子
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(' + accentRGB[0] + ',' + accentRGB[1] + ',' + accentRGB[2] + ',' + p.alpha + ')'
    ctx.fill()
  }

  // # 6. 相邻粒子连线
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      let dx = particles[i].x - particles[j].x
      let dy = particles[i].y - particles[j].y
      let dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < 110) {
        let lineAlpha = 0.04 * (1 - dist / 110)
        ctx.beginPath()
        ctx.moveTo(particles[i].x, particles[i].y)
        ctx.lineTo(particles[j].x, particles[j].y)
        ctx.strokeStyle = 'rgba(' + accentRGB[0] + ',' + accentRGB[1] + ',' + accentRGB[2] + ',' + lineAlpha + ')'
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    }
  }
}

function loop() {
  if (!ctx || !canvas.value) return
  draw(canvas.value.width, canvas.value.height)
  animId = requestAnimationFrame(loop)
}

function resize() {
  if (!canvas.value) return
  let parent = canvas.value.parentElement
  canvas.value.width = parent.clientWidth
  canvas.value.height = parent.clientHeight
  initParticles(canvas.value.width, canvas.value.height)
}

onMounted(() => {
  ctx = canvas.value.getContext('2d')
  resize()
  loop()
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(canvas.value.parentElement)
})

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
  if (resizeObserver) resizeObserver.disconnect()
})
</script>

<template>
  <canvas ref="canvas" class="particle-canvas" aria-hidden="true"></canvas>
</template>

<style scoped>
.particle-canvas {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
</style>
