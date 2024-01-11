<script setup>
import { ref, onMounted } from 'vue'
import { initFlowbite } from 'flowbite'

// Props to accept the upload handler function
const props = defineProps({
  onUpload: {
    type: Function,
    required: true
  }
});

// Ref for the hidden file input element
const fileInputRef = ref(null);

// Trigger file input when dropdown item is clicked
const triggerFileInput = (fileType) => {
  if (fileInputRef.value) {
    fileInputRef.value.setAttribute('data-file-type', fileType);
    fileInputRef.value.click();
  }
};

// Handle file selection
const handleFiles = (event) => {
  const files = event.target.files;
  if (files.length > 0) {
    // Call the upload handler function with the selected files
    props.onUpload(files, event.target.getAttribute('data-file-type'));
    // Clear the file input to allow for a new file to be selected
    event.target.value = '';
  }
};

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

    <!-- Hidden file input to handle actual file selection -->
    <input type="file" ref="fileInputRef" class="hidden" @change="handleFiles" />

    <!-- Dropdown menu -->
    <div id="dropdown" class="z-10 hidden bg-white divide-y divide-gray-100 rounded shadow w-44 dark:bg-gray-700">
      <ul class="py-1 text-sm text-gray-700 dark:text-gray-200" aria-labelledby="dropdownDefaultButton">
        <li>
          <a href="#" class="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 dark:hover:text-white"
            @click.prevent="triggerFileInput('video')">Video</a>
        </li>
        <li>
          <a href="#" class="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 dark:hover:text-white"
            @click.prevent="triggerFileInput('audio')">Audio</a>
        </li>
        <li>
          <a href="#" class="block px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 dark:hover:text-white"
            @click.prevent="triggerFileInput('document')">Document</a>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
/* Your styles here */
</style>