<script setup>
import { ref, defineComponent, shallowRef, shallowReactive, computed, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { VideoPlayer } from '@videojs-player/vue'
import 'video.js/dist/video-js.css'
import { useDavidStore } from '@/stores/david'

const store = useDavidStore();

const route = useRoute()
let pitchUid = route.query.pitch
store.pitchUid = pitchUid

const messages = ref([])

const indexM3U8URL = store.getVideoURL('index.m3u8');
const source = shallowRef([
  {
    src: indexM3U8URL,
    type: 'application/x-mpegURL',
  },
]);

const player = shallowRef()
const state = shallowRef()
const config = shallowReactive({
  autoplay: false,
  volume: 0.8,
  playbackRate: 1,
  controls: true,
  fluid: false,
  muted: false,
  loop: false
})

const mediaConfig = computed(() => ({
  sources: [source.value],
  // sources: [{
  //   src: '//d2zihajmogu5jn.cloudfront.net/sintel/master.m3u8',
  //   type: 'application/x-mpegurl'
  // }],
  poster: '//d2zihajmogu5jn.cloudfront.net/bipbop-advanced/poster.png',
  tracks: []
}))

let eventSource;

const handleMounted = (payload) => {
  console.log('Advanced player mounted', payload)
  state.value = payload.state
  player.value = payload.player
}

const pauseOnUserInquiry = (pause) => {
  console.log('pauseOnUserInquiry', pause)
  if (pause) {
    player.value.pause()
  } else {
    player.value.play()
  }
}

const streaming = async (url) => {
  eventSource = new EventSource(url);
  messages.value.push({ "role": "ai", "content": "" })
  eventSource.onmessage = (event) => {
    console.log('eventSource.onmessage', event)
    const message = event.data
    messages.value[messages.value.length - 1].content += message
  }
  eventSource.onerror = (event) => {
    console.log('eventSource.onerror', event)
    eventSource.close()
  }
}

const handleNewMessage = async (message) => {
  player.value.pause()
  messages.value.push(message)
  // messages.value.push({ "role": "ai", "content": "" })
  const streamingURL = await store.getStreamingURL()
  const url = streamingURL + `?query=${message.content}` // todo: use URL object
  streaming(url)
}


onUnmounted(() => {
  if (eventSource) {
    eventSource.close()
  }
})
</script>
<template>
  <main class="flex flex-col items-center">
    <div class="flex justify-center" style="width: 800px; height: 600px;">
      <video-player class="video-player" :sources="mediaConfig.sources" :poster="mediaConfig.poster"
        :tracks="mediaConfig.tracks" :autoplay="config.autoplay" :playbackRates="config.playbackRates"
        :fluid="config.fluid" :loop="config.loop" crossorigin="anonymous" playsinline :width="680"
        v-model:height="config.height" v-model:volume="config.volume" v-model:playbackRate="config.playbackRate"
        v-model:controls="config.controls" v-model:muted="config.muted" @mounted="handleMounted">
      </video-player>
    </div>
    <div class="flex justify-center" style="width: 800px;">
      <ChatBox :messages="messages" @new-message="handleNewMessage" @pause-video="pauseOnUserInquiry"></ChatBox>
    </div>
  </main>
</template>
<script>
import ChatBox from '@/components/ChatBox.vue'

export default defineComponent({
  components: {
    VideoPlayer,
    ChatBox
  }
})
</script>
<style lang="scss" scoped>
.video-player {
  position: relative;
  max-width: 100%;
  max-height: 100%;
  width: 100%;
  height: 100%;

  &.loading {
    min-width: 680px;
    background-color: #000;
  }
}
</style>
