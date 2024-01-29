import './assets/main.css'
import 'primevue/resources/themes/lara-light-green/theme.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config';

import VueVideoPlayer from '@videojs-player/vue'
import 'video.js/dist/video-js.css'

import App from './App.vue'
import router from './router'

import './assets/base.css'

createApp(App).use(createPinia()).use(PrimeVue).use(router)
    .use(VueVideoPlayer)
    .mount('#app')
