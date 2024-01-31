<script setup>
import { ref, onMounted } from 'vue'
import { initFlowbite } from 'flowbite'
import Dialog from 'primevue/dialog';

// Props to accept the upload handler function
const props = defineProps({
  onUpload: {
    type: Function,
    required: true
  }
});

const dialogVisible = ref(false)

// Ref for the hidden file input element
const fileRef = ref(null);
const keywordsRef = ref(null)

const handleForm = (doc_type) => {
  // If fileRef and keywordsRef are properly referenced, they should not be null
  if (fileRef.value && keywordsRef.value) {
    const files = fileRef.value.files; // This will give us the FileList
    const keywords = keywordsRef.value.value; // Access the `value` of the keywords input

    if (files.length === 0 || keywords.trim() === '') {
      console.log('No file selected.');
      return;
    }

    props.onUpload({ files, keywords });
  } else {
    console.log('The refs are not correctly set up.');
  }
}

// initialize components based on data attribute selectors
onMounted(() => {
  initFlowbite();
});
</script>

<template>
  <div>
    <button id="dropdownDefaultButton" data-dropdown-toggle="dropdown"
      class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
      type="button">Upload References
      <svg class="w-2.5 h-2.5 ml-2" aria-hidden="true" fill="none" viewBox="0 0 20 20">
        <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 8l8 8 8-8" />
      </svg>
    </button>
    <!-- Dropdown menu -->
    <div id="dropdown" class="z-10 hidden bg-white divide-y divide-gray-100 rounded shadow w-44 dark:bg-gray-700">
      <ul class="py-1 text-sm text-gray-700 dark:text-gray-200" aria-labelledby="dropdownDefaultButton">
        <!-- <li>
          <a href="#" class="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 dark:hover:text-white"
            @click.prevent="triggerFileInput('video')">Video</a>
        </li>
        <li>
          <a href="#" class="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 dark:hover:text-white"
            @click.prevent="triggerFileInput('audio')">Audio</a>
        </li> -->
        <li>
          <a href="#" class="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 dark:hover:text-white"
            @click.prevent="dialogVisible = true">Document</a>
        </li>
      </ul>
    </div>

    <!-- dialog form -->
    <Dialog v-model:visible="dialogVisible" modal header="Upload Reference" :style="{ width: '25rem' }">
      <form>
        <div class="mb-6">
          <label class="block mb-2 text-sm font-medium text-gray-900 dark:text-white" for="file_input">Upload file</label>
          <input
            class="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
            ref="fileRef" id="file_input" type="file">
        </div>
        <div class="mb-6">
          <label for="keywords" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Keywords</label>
          <input type="text" id="keywords" ref="keywordsRef"
            class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
            placeholder="finance,market" required />
        </div>
      </form>
      <div class="flex justify-content-end gap-2">
        <button type="button"
          class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-blue-600 dark:hover:bg-blue-700 focus:outline-none dark:focus:ring-blue-800"
          label="Save" @click="handleForm('document')">Save</button>
        <button type="button"
          class="text-white bg-gray-800 hover:bg-gray-900 focus:outline-none focus:ring-4 focus:ring-gray-300 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 dark:bg-gray-800 dark:hover:bg-gray-700 dark:focus:ring-gray-700 dark:border-gray-700"
          label="Cancel" severity="secondary" @click="dialogVisible = false">Cancel</button>
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
/* Your styles here */
</style>