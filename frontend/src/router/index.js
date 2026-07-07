import { createRouter, createWebHashHistory } from 'vue-router'
import Landing from '../views/Landing.vue'

const routes = [
  {
    path: '/',
    component: Landing,
    meta: { title: '首页 | 登录' }
  },
  {
    path: '/workspace',
    component: () => import('../layouts/DefaultLayout.vue'),
    redirect: '/workspace/chat',
    children: [
      {
        path: 'chat',
        component: () => import('../views/Chat.vue'),
        meta: { title: 'AI对话', icon: 'ChatDotRound' }
      },
      {
        path: 'skills',
        component: () => import('../views/Skills.vue'),
        meta: { title: '技能中心', icon: 'MagicStick' }
      },
      {
        path: 'teaching',
        component: () => import('../views/Teaching.vue'),
        meta: { title: '教学工作台', icon: 'Reading' }
      },
      {
        path: 'research',
        component: () => import('../views/Research.vue'),
        meta: { title: '科研工作台', icon: 'Document' }
      },
      {
        path: 'video',
        component: () => import('../views/Video.vue'),
        meta: { title: '视频分析', icon: 'VideoCamera' }
      },
      {
        path: 'knowledge',
        component: () => import('../views/Knowledge.vue'),
        meta: { title: '知识库', icon: 'Collection' }
      },
      {
        path: 'news',
        component: () => import('../views/News.vue'),
        meta: { title: '资讯', icon: 'Connection' }
      },
      {
        path: 'admin',
        component: () => import('../views/Admin.vue'),
        meta: { title: '系统管理', icon: 'Setting' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
