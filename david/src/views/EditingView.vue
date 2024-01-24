<script setup>
import { ref, onMounted, watch } from 'vue'
import router from '@/router'
import { VuePDF, usePDF } from '@tato30/vue-pdf'
import { useDavidStore } from '@/stores/david' // Adjust the path to where your store is defined
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

const fileRemoveHandler = (file_id) => {
  console.log('File removed:', file_id)
}

// Fetch transcripts from backend using pitchId on store
onMounted(async () => {
  await store.fetchTranscript()
  // After fetching, set the initial transcript based on the first page
  if (store.transcripts.length > 0) {
    editorContent.value = store.transcripts[0]
    console.log(editorContent.value)
  } else {
    router.push('/');
  }
})

watch(page, (newPageIndex) => {
  if (store.transcript && store.transcript.length > 0) {
    console.log('Page changed:', newPageIndex)
    const transcriptIndex = newPageIndex - 1
    if (transcriptIndex >= 0 && transcriptIndex < store.transcript.length) {
      editorContent.value = store.transcript[transcriptIndex]
    }
  }
})
</script>
<template>
  <main class="flex flex-col justify-begin w-full h-full">
    <div class="flex flex-row p-2">
      <div class="aspect-w-4 aspect-h-3">
        <VuePDF :pdf="pdf" :page="page" />
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
      <div class="transcript-editor flex flex-col w-full">
        <ProgressBar :value="transcriptProgress" />
        <Editor v-model="editorContent" editorStyle="height: 100vh" />
      </div>
    </div>
    <div class="scrollable-list-section flex flex-row h-full justify-between m-1">
      <ReferenceFileTable :referenceFiles="referenceFiles" :fileUploadHandler="fileUploadHandler"
        :fileRemoveHandler="fileRemoveHandler"></ReferenceFileTable>
      <div class="flex flex-col justify-center">
        <button type="button"
          class="text-white bg-blue-700 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 font-medium text-sm px-5 py-2.5 text-center me-2 mb-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
          Submit
        </button>
        <button type="button"
          class="text-white bg-green-700 hover:bg-green-800 focus:outline-none focus:ring-4 focus:ring-green-300 font-medium text-sm px-5 py-2.5 text-center me-2 mb-2 dark:bg-green-600 dark:hover:bg-green-700 dark:focus:ring-green-800">
          Preview
        </button>
      </div>
    </div>
  </main>
</template>

<script>
import ReferenceFileTable from '@/components/ReferenceFileTable.vue'
import Editor from 'primevue/editor'
import ProgressBar from 'primevue/progressbar'
// import { useToast } from 'primevue/usetoast'

export default {
  components: {
    Editor,
    ProgressBar,
    ReferenceFileTable
  }
}
</script>

<style scoped></style>
