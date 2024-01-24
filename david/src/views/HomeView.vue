<script setup>
import { onMounted } from 'vue';
import router from '@/router';
import { useDavidStore } from '@/stores/david'; // Adjust the path to where your store is defined
import { initFlowbite } from 'flowbite'

// Use the Pinia store
const store = useDavidStore();

const handleUpload = async (event) => {
  const fileInput = event.target;

  if (fileInput.files.length > 0) {
    const file = fileInput.files[0]; // Get the first file from the file input
    // Call uploadMasterFile with the file
    try {
      const response = await store.uploadMasterFile(file)
      console.log('File uploaded successfully', response);
      router.push('/editing');
    } catch (error) {
      console.error('Error uploading file', error);
    }
  }
}

// initialize components based on data attribute selectors
onMounted(() => {
  initFlowbite();
});
</script>

<template>
  <main class="flex justify-between items-center w-full my-12">
    <div class="flex items-center justify-center flex-row w-full">
      <label for="dropzone-file"
        class="flex flex-col items-center justify-center w-1/3 h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:hover:bg-bray-800 dark:bg-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:hover:border-gray-500 dark:hover:bg-gray-600">
        <div class="flex flex-col items-center justify-center pt-5 pb-6">
          <svg class="w-8 h-8 mb-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"
            fill="none" viewBox="0 0 20 16">
            <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2" />
          </svg>
          <p class="mb-2 text-sm text-gray-500 dark:text-gray-400"><span class="font-semibold">Click to upload</span> or
            drag and drop</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">.pptx, ppt</p>
        </div>
        <input id="dropzone-file" type="file" class="absolute top-0 left-0 w-full h-full opacity-0 cursor-pointer"
          @change="handleUpload" />
      </label>
    </div>

  </main>
</template>
