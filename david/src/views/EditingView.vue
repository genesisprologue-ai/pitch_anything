<script setup>
import { ref, onMounted, watch } from 'vue'
import router from '@/router'
import { VuePDF, usePDF } from '@tato30/vue-pdf'
import { useDavidStore } from '@/stores/david'
// Use the Pinia store
const store = useDavidStore()

const page = ref(1)
const pageURL = store.getPdfURL()
const { pdf, pages } = usePDF(pageURL)

const editorContent = ref('')


// Reference files data
const referenceFiles = store.referenceFiles

// File upload handler function
const fileUploadHandler = store.uploadEmbeddingFile

// progress indicator
const transcriptProgress = ref(10)
const videoInProgress = ref(0)

// Update transcript
const updateTranscript = async () => {
  store.transcripts[page.value - 1] = editorContent.value
  await store.updateTranscript()
}
const fileRemoveHandler = (file_id) => {
  console.log('File removed:', file_id)
}

const generateVideo = async () => {
  await store.generateVideo()

  while (videoInProgress.value < 100) {
    videoInProgress.value = await store.fetchVideoTaskStatus()
  }
}

// Fetch transcripts from backend using pitchId on store
onMounted(async () => {
  await store.fetchTranscript()
  // After fetching, set the initial transcript based on the first page
  if (store.transcripts.length > 0) {
    editorContent.value = store.transcripts[0]
    console.log(editorContent.value)
  } else {
    router.push('/')
  }

  transcriptProgress.value = await store.fetchMasterTaskStatus()

  while (transcriptProgress.value < 100) {
    transcriptProgress.value = await store.fetchMasterTaskStatus()
  }
})

// page updates
const updatePage = (direction) => {
  if (direction === 'next') {
    page.value = page.value < pages.value ? page.value + 1 : pages.value
  } else if (direction === 'prev') {
    page.value = page.value > 1 ? page.value - 1 : 1
  }
}

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
    <div class="p-4" v-if="videoInProgress < 100 && videoInProgress !== 0">
      <ProgressBar :value="videoInProgress" />
    </div>

    <div class="flex flex-row p-2">
      <div class="aspect-w-4 aspect-h-3">
        <VuePDF :pdf="pdf" :page="page" />
        <div class="flex flex-row justify-center items-center">
          <button @click="updatePage('prev')">
            <svg class="w-[16px] h-[16px] text-gray-800 dark:text-white" aria-hidden="true"
                 xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 18 2">
              <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M1 1h16" />
            </svg>
          </button>
          <span class="px-3">{{ page }} / {{ pages }}</span>
          <button @click="updatePage('next')">
            <svg class="w-[16px] h-[16px] text-gray-800 dark:text-white" aria-hidden="true"
                 xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 18 18">
              <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M9 1v16M1 9h16" />
            </svg>
          </button>
        </div>
      </div>
      <div class="transcript-editor flex flex-col">
        <div class="m-1">
          <ProgressBar :value="transcriptProgress" v-if="transcriptProgress < 100" />
        </div>
        <div>
          <Editor v-model="editorContent" editorStyle="" />
        </div>
        <div class="scrollable-list-section flex flex-row h-full justify-between m-1">
          <ReferenceFileTable :referenceFiles="referenceFiles" :fileUploadHandler="fileUploadHandler"
                              :fileRemoveHandler="fileRemoveHandler"></ReferenceFileTable>
        </div>
        <div class="flex flex-col justify-center">
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
import ProgressBar from 'primevue/progressbar'

export default {
  components: {
    Editor,
    ProgressBar,
    ReferenceFileTable
  }
}
</script>

<style scoped></style>
