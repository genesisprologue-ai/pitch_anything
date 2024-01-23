import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config';

import App from './App.vue'
import router from './router'

import './assets/base.css'

createApp(App).use(createPinia()).use(PrimeVue).use(router).mount('#app')
