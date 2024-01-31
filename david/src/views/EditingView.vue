<script setup>
import _ from 'lodash'
import { ref, shallowRef, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { VuePDF, usePDF } from '@tato30/vue-pdf'
import { useDavidStore } from '@/stores/david'
import router from '@/router'


const store = useDavidStore()
const page = ref(1)
const editorContent = ref('')
// Reference files data
const referenceFiles = shallowRef([])
const editorVisible = shallowRef(false);
const videoProgressVisible = shallowRef(false);
// stage indicator
const transcribeStage = ref('Loading')
const videoStages = ref([])

let pitchUid = shallowRef('')
const route = useRoute()
pitchUid.value = store.pitchUid || route.query.pitch
if (pitchUid.value === undefined) {
  router.push({ name: 'home' })
}
store.pitchUid = pitchUid.value

const { pdf, pages } = usePDF(store.getPdfURL())

// File upload handler function
const fileUploadHandler = store.uploadEmbeddingFile

// Update transcript
const updateTranscript = async () => {
  store.transcripts[page.value - 1] = editorContent.value
  await store.updateTranscript()
}

const fileRemoveHandler = async (file_id) => {
  await store.removeReference(file_id)
}


const generateVideo = async () => {
  const started = performance.now();
  await store.generateVideo()

  videoProgressVisible.value = true
  videoStages.value.push('Started New')

  const fetchTTSTaskStage = async () => {
    let stage = await store.fetchTTSTaskStage()
    const elapsed = performance.now() - started
    videoStages.value.push(`${stage}-elapsed:${elapsed}ms`)

    if (stage === 'FINISH') {
      videoProgressVisible.value = false
      throttledFetchTTSTaskStage.cancel() // Cancel the throttled function
      router.push({ name: 'preview', query: { pitch: pitchUid.value } })
    } else if (stage == 'FAILED') {
      throttledFetchTTSTaskStage.cancel() // Cancel the throttled function
    } else {
      throttledFetchTTSTaskStage()
    }
  }

  const throttledFetchTTSTaskStage = _.throttle(fetchTTSTaskStage, 10000)

  throttledFetchTTSTaskStage()
}

// Fetch transcripts from backend using pitchUid on store
onMounted(async () => {
  // Fetch transcribe task stage
  const fetchTranscribeTaskStage = async () => {
    let stage = await store.fetchTranscribeTaskStage()
    transcribeStage.value = stage
    if (stage === 'FINISH') {
      editorVisible.value = true
      await store.fetchTranscript()
      editorContent.value = store.transcripts[0]
      throttledFetchTranscriptTask.cancel() // Cancel the throttled function
    } else {
      throttledFetchTranscriptTask()
    }
  }

  const throttledFetchTranscriptTask = _.throttle(fetchTranscribeTaskStage, 10000)
  throttledFetchTranscriptTask() // Fetch transcript status every 10 seconds
})

watch(page, (newPageIndex) => {
  if (store.transcripts && store.transcripts.length > 0) {
    console.log('Page changed:', newPageIndex)
    const transcriptIndex = newPageIndex - 1
    if (transcriptIndex >= 0 && transcriptIndex < store.transcripts.length) {
      editorContent.value = store.transcripts[transcriptIndex]
    }
  }
})
</script>
<template>
  <main class="flex flex-col justify-begin w-full h-full">
    <div class="flex flex-col justify-center p-2 ">
      <div class="flex flex-row justify-center">

        <div class="flex-col w-1/6" v-if="videoProgressVisible">
          <div v-for="stage in videoStages" v-bind:key="stage"
            class="h-8 p-2 mb-1 w-full text-sm text-center text-blue-800 bg-blue-50 dark:bg-gray-800 dark:text-blue-400"
            role="alert">
            <span class="font-medium">{{ stage }}</span>
          </div>
        </div>

        <div class="aspect-w-4 aspect-h-3">
          <div class="flex justify-center">
            <VuePDF :pdf="pdf" :page="page" />
          </div>
          <div class="flex flex-row justify-center items-center">
            <button @click="page = page > 1 ? page - 1 : 1">
              <svg class="w-[16px] h-[16px] text-gray-800 dark:text-white" aria-hidden="true"
                xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 18 2">
                <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M1 1h16" />
              </svg>
            </button>
            <span class="px-3">{{ page }} / {{ pages }}</span>
            <button @click="page = page < pages ? page + 1 : pages">
              <svg class="w-[16px] h-[16px] text-gray-800 dark:text-white" aria-hidden="true"
                xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 18 18">
                <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9 1v16M1 9h16" />
              </svg>
            </button>
          </div>
        </div>

        <div class="scrollable-list-section h-full justify-between m-1">
          <ReferenceFileTable :referenceFiles="referenceFiles" :fileUploadHandler="fileUploadHandler"
            :fileRemoveHandler="fileRemoveHandler"></ReferenceFileTable>
        </div>
      </div>
      <div class="transcript-editor flex flex-col items-center">
        <div class="w-4/6">
          <LoadingEditor v-if="!editorVisible" />
          <Editor v-if="editorVisible" v-model="editorContent" editorStyle="" />
        </div>
        <div class="justify-center m-3">
          <button type="button"
            class="text-white bg-blue-700 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 font-medium text-sm px-5 py-2.5 text-center me-2 mb-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
            @click="updateTranscript()">
            Save Transcript
          </button>
          <button type="button"
            class="text-white bg-green-700 hover:bg-green-800 focus:outline-none focus:ring-4 focus:ring-green-300 font-medium text-sm px-5 py-2.5 text-center me-2 mb-2 dark:bg-green-600 dark:hover:bg-green-700 dark:focus:ring-green-800"
            @click="generateVideo()">
            Create Video
          </button>
        </div>
      </div>
    </div>
  </main>
</template>

<script>
import ReferenceFileTable from '@/components/ReferenceFileTable.vue'
import Editor from 'primevue/editor'
import LoadingEditor from '@/components/LoadingEditor.vue'

export default {
  components: {
    Editor,
    LoadingEditor,
    ReferenceFileTable
  }
}
</script>

<style scoped></style>
