import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ─── Public site ─────────────────────────────────────
    {
      path: '/',
      component: () => import('@/layouts/PublicLayout.vue'),
      children: [
        { path: '', name: 'home', component: () => import('@/pages/public/HomePage.vue') },
        { path: 'about', name: 'about', component: () => import('@/pages/public/AboutPage.vue') },
        { path: 'services', name: 'services', component: () => import('@/pages/public/ServicesPage.vue') },
        { path: 'contacts', name: 'contacts', component: () => import('@/pages/public/ContactsPage.vue') },
        { path: 'faq', name: 'faq', component: () => import('@/pages/public/FaqPage.vue') },
      ],
    },

    // ─── Auth ─────────────────────────────────────────────
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/auth/LoginPage.vue'),
    },

    // ─── Learner cabinet ──────────────────────────────────
    {
      path: '/my',
      component: () => import('@/layouts/LearnerLayout.vue'),
      meta: { requiresAuth: true, role: 'learner' },
      children: [
        { path: '', redirect: '/my/courses' },
        { path: 'courses', name: 'learner-courses', component: () => import('@/pages/learner/MyCoursesPage.vue') },
        { path: 'courses/:id', name: 'learner-course', component: () => import('@/pages/learner/CourseDetailPage.vue') },
        { path: 'test/:attemptId', name: 'learner-test', component: () => import('@/pages/learner/TestPage.vue') },
        { path: 'result/:attemptId', name: 'learner-result', component: () => import('@/pages/learner/ResultPage.vue') },
      ],
    },

    // ─── Admin panel ──────────────────────────────────────
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { requiresAuth: true, role: 'admin' },
      children: [
        { path: '', redirect: '/admin/dashboard' },
        { path: 'dashboard', name: 'admin-dashboard', component: () => import('@/pages/admin/DashboardPage.vue') },
        { path: 'users', name: 'admin-users', component: () => import('@/pages/admin/UsersPage.vue') },
        { path: 'organizations', name: 'admin-orgs', component: () => import('@/pages/admin/OrganizationsPage.vue') },
        { path: 'batches', name: 'admin-batches', component: () => import('@/pages/admin/BatchesPage.vue') },
        { path: 'batches/:id', name: 'admin-batch-detail', component: () => import('@/pages/admin/BatchDetailPage.vue') },
        { path: 'courses', name: 'admin-courses', component: () => import('@/pages/admin/CoursesPage.vue') },
        { path: 'courses/:id', name: 'admin-course-detail', component: () => import('@/pages/admin/CourseDetailPage.vue') },
        { path: 'rules', name: 'admin-rules', component: () => import('@/pages/admin/RulesPage.vue') },
        { path: 'disciplines', name: 'admin-disciplines', component: () => import('@/pages/admin/DisciplinesPage.vue') },
        { path: 'positions', name: 'admin-positions', component: () => import('@/pages/admin/PositionsPage.vue') },
        { path: 'progress', name: 'admin-progress', component: () => import('@/pages/admin/ProgressPage.vue') },
        { path: 'exports', name: 'admin-exports', component: () => import('@/pages/admin/ExportsPage.vue') },
      ],
    },

    // ─── 404 ──────────────────────────────────────────────
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/pages/NotFoundPage.vue') },
  ],
})

export default router
