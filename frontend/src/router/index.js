import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/LandingView.vue'),
    },
    {
      path: '/app',
      component: () => import('@/layouts/AppLayout.vue'),
      redirect: '/app/resume',
      children: [
        {
          path: 'resume',
          name: 'resume',
          component: () => import('@/views/ResumeView.vue'),
        },
        {
          path: 'chat',
          name: 'chat',
          component: () => import('@/views/ChatView.vue'),
        },
      ],
    },
  ],
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isLoggedIn = userStore.isLoggedIn

  if (to.path === '/login') {
    // 已登录访问登录页 → 跳转落地页
    isLoggedIn ? next('/') : next()
  } else {
    // 未登录访问其他页面 → 跳转登录
    isLoggedIn ? next() : next('/login')
  }
})

export default router
