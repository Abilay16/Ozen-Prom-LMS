<template>
  <div>
    <!-- Hero -->
    <section class="bg-gradient-to-br from-brand-dark to-primary-700 text-white py-24 px-4">
      <div class="max-w-4xl mx-auto text-center">
        <h1 class="text-4xl md:text-5xl font-bold leading-tight mb-6">
          Онлайн-обучение по безопасности и охране труда
        </h1>
        <p class="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
          Профессиональная подготовка сотрудников по БиОТ, ПТМ и промышленной безопасности.
          Удобно, быстро, с документальным подтверждением.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <RouterLink to="/login" class="bg-white text-brand-dark font-semibold py-3 px-8 rounded-lg hover:bg-blue-50 transition-colors">
            Войти в кабинет
          </RouterLink>
          <RouterLink to="/services" class="border border-white text-white font-semibold py-3 px-8 rounded-lg hover:bg-white/10 transition-colors">
            Наши услуги
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- Benefits -->
    <section class="py-20 px-4 bg-white">
      <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center text-gray-900 mb-12">Почему выбирают нас</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="text-center p-6">
            <div class="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl">📋</div>
            <h3 class="font-semibold text-lg mb-2">Автоматизированная подготовка</h3>
            <p class="text-gray-600">Загружаете список сотрудников — система сама создаёт аккаунты и назначает курсы по должностям</p>
          </div>
          <div class="text-center p-6">
            <div class="w-14 h-14 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl">📱</div>
            <h3 class="font-semibold text-lg mb-2">С любого устройства</h3>
            <p class="text-gray-600">Обучение доступно с телефона, планшета или компьютера в любое удобное время</p>
          </div>
          <div class="text-center p-6">
            <div class="w-14 h-14 bg-yellow-100 rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl">📊</div>
            <h3 class="font-semibold text-lg mb-2">Отчёты и контроль</h3>
            <p class="text-gray-600">Полная статистика прохождения обучения и результатов тестов в Excel</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Disciplines -->
    <section class="py-20 px-4 bg-gray-50">
      <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center text-gray-900 mb-4">Направления обучения</h2>
        <p class="text-center text-gray-600 mb-12">Программы разработаны с учётом категории должности сотрудника</p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="card hover:shadow-md transition-shadow">
            <div class="text-3xl mb-3">🦺</div>
            <h3 class="font-bold text-lg mb-2">БиОТ</h3>
            <p class="text-gray-600 text-sm">Безопасность и охрана труда. Обязательный инструктаж для всех категорий сотрудников на производстве.</p>
          </div>
          <div class="card hover:shadow-md transition-shadow">
            <div class="text-3xl mb-3">🔥</div>
            <h3 class="font-bold text-lg mb-2">ПТМ</h3>
            <p class="text-gray-600 text-sm">Пожарно-техминимум. Правила поведения при пожаре, работа с первичными средствами пожаротушения.</p>
          </div>
          <div class="card hover:shadow-md transition-shadow">
            <div class="text-3xl mb-3">⚙️</div>
            <h3 class="font-bold text-lg mb-2">Промышленная безопасность</h3>
            <p class="text-gray-600 text-sm">Требования к безопасной эксплуатации оборудования и объектов промышленности.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="py-20 px-4 bg-white">
      <div class="max-w-4xl mx-auto">
        <h2 class="text-3xl font-bold text-center text-gray-900 mb-12">Как это работает</h2>
        <div class="space-y-8">
          <div class="flex gap-4">
            <div class="w-10 h-10 bg-brand-mid text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">1</div>
            <div>
              <h3 class="font-semibold mb-1">Вы присылаете список сотрудников в Excel</h3>
              <p class="text-gray-600">ФИО, должность, организация, дисциплины — стандартный формат</p>
            </div>
          </div>
          <div class="flex gap-4">
            <div class="w-10 h-10 bg-brand-mid text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">2</div>
            <div>
              <h3 class="font-semibold mb-1">Система автоматически создаёт аккаунты</h3>
              <p class="text-gray-600">Каждому сотруднику генерируется логин и пароль, назначаются курсы по должности</p>
            </div>
          </div>
          <div class="flex gap-4">
            <div class="w-10 h-10 bg-brand-mid text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">3</div>
            <div>
              <h3 class="font-semibold mb-1">Сотрудники проходят обучение онлайн</h3>
              <p class="text-gray-600">Видео, материалы и тест — всё в одном кабинете, с телефона или компьютера</p>
            </div>
          </div>
          <div class="flex gap-4">
            <div class="w-10 h-10 bg-brand-mid text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">4</div>
            <div>
              <h3 class="font-semibold mb-1">Вы получаете отчёт с результатами</h3>
              <p class="text-gray-600">Excel с итогами прохождения, статусами и датами</p>
            </div>
          </div>
        </div>
        <div class="text-center mt-12">
          <RouterLink to="/contacts" class="btn-primary py-3 px-8">Связаться с нами</RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
