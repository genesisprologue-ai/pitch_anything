<script setup>
import { ref, defineComponent, shallowRef, shallowReactive, computed } from 'vue'
import { VideoPlayer } from '@videojs-player/vue'
import 'video.js/dist/video-js.css'
import { useDavidStore } from '@/stores/david'
import { fetchEventSource, EventStreamContentType } from '@microsoft/fetch-event-source';

const store = useDavidStore();

// 
const messages = ref([
  { "role": "ai", "content": "welcome" },
  { "role": "user", "content": "hello" },
  { "role": "ai", "content": "how are you?" },
  { "role": "user", "content": "good" },
  { "role": "ai", "content": "what is your name?" },
  { "role": "user", "content": "david" },
  { "role": "ai", "content": "nice to meet you" },
  { "role": "user", "content": "nice to meet you too" },
  { "role": "ai", "content": "bye" },
])

const indexM3U8URL = store.getVideoURL('index.m3u8');

const source = shallowRef([
  {
    src: indexM3U8URL,
    type: 'application/x-mpegURL',
  },
]);

console.log(source.value)

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

const streaming = async (url, message) => {
  class RetriableError extends Error { }
  class FatalError extends Error { }

  fetchEventSource(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: message,
    }),
    async onopen(response) {
      if (response.ok && response.headers.get('content-type') === EventStreamContentType) {
        return; // everything's good
      } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
        // client-side errors are usually non-retriable:
        throw new FatalError();
      } else {
        throw new RetriableError();
      }
    },
    onmessage(msg) {
      // if the server emits an error message, throw an exception
      // so it gets handled by the onerror callback below:
      console.log(msg)
      if (msg.event === 'FatalError') {
        throw new FatalError(msg.data);
      }
    },
    onclose() {
      // if the server closes the connection unexpectedly, retry:
      throw new RetriableError();
    },
    onerror(err) {
      if (err instanceof FatalError) {
        throw err; // rethrow to stop the operation
      } else {
        // do nothing to automatically retry. You can also
        // return a specific retry interval here.
      }
    }
  })
}

const handleNewMessage = async (message) => {
  player.value.pause()
  messages.value.push(message)
  // messages.value.push({ "role": "ai", "content": "" })
  const streamingURL = await store.getStreamingURL()
  streaming(streamingURL, message)
}
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
