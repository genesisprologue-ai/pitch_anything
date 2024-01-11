<script setup>
import { ref } from 'vue'
import { VuePDF, usePDF } from '@tato30/vue-pdf'
import { useDavidStore } from '@/stores/david'; // Adjust the path to where your store is defined

// Use the Pinia store
const store = useDavidStore();

const page = ref(1)
const { pdf, pages } = usePDF('https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf')

// Reference files data
const referenceFiles = store.referenceFiles;

// File upload handler function
const fileUploadHandler = store.uploadEmbeddingFile;

const fileRemoveHandler = (file_id) => {
  console.log('File removed:', file_id)
}
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
            </svg> </button>
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
        <QuillEditor theme="snow" />
      </div>
    </div>
    <div class="scrollable-list-section flex flex-row h-full justify-between m-1">
      <ReferenceFileTable :referenceFiles="referenceFiles" :fileUploadHandler="fileUploadHandler"
        :fileRemoveHandler="fileRemoveHandler"></ReferenceFileTable>
      <div class="flex flex-col justify-center">
        <button type="button"
          class="text-white bg-blue-700 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 font-medium text-sm px-5 py-2.5 text-center me-2 mb-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">Submit</button>
        <button type="button"
          class="text-white bg-green-700 hover:bg-green-800 focus:outline-none focus:ring-4 focus:ring-green-300 font-medium text-sm px-5 py-2.5 text-center me-2 mb-2 dark:bg-green-600 dark:hover:bg-green-700 dark:focus:ring-green-800">Preview</button>
      </div>
    </div>
  </main>
</template>

<script>
import { QuillEditor } from '@vueup/vue-quill'
import ReferenceFileTable from '@/components/ReferenceFileTable.vue';
import '@vueup/vue-quill/dist/vue-quill.snow.css'

export default {
  components: {
    QuillEditor,
    ReferenceFileTable
  },
}
</script>

<style scoped></style>
