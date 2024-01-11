<script setup>
import { ref } from 'vue'
import { VuePDF, usePDF } from '@tato30/vue-pdf'

const page = ref(1)
const { pdf } = usePDF('https://mozilla.github.io/pdf.js/web/compressed.tracemonkey-pldi-09.pdf')
</script>

<template>
  <main class="flex flex-col justify-begin w-full h-full">
    <div class="flex flex-row p-2">
      <div class="aspect-w-4 aspect-h-3">
        <VuePDF :pdf="pdf" :page="page" />
      </div>
      <div class="transcript-editor flex flex-col w-full">
        <QuillEditor theme="snow" />
      </div>
    </div>
    <div class="scrollable-list-section flex flex-row h-full justify-between m-1">
      <ul class="overflow-y-auto">
        <!-- List items go here -->
        <li>Dummy List Item</li>
      </ul>
      <button type="button"
        class="text-white bg-blue-700 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 font-medium rounded-full text-sm px-5 py-2.5 text-center me-2 mb-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">Default</button>
    </div>
  </main>
</template>

<script>
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'

export default {
  components: {
    QuillEditor
  },
}
</script>

<style scoped></style>
