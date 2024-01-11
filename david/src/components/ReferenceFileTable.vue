<template>
    <table class="w-full text-sm text-left rtl:text-right text-gray-500 dark:text-gray-400 mx-5">
        <thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
            <tr>
                <th scope="col" class="px-6 py-3">
                    Filename
                </th>
                <th scope="col" class="px-6 py-3">
                    Linked Chapter
                </th>
                <th scope="col" class="px-6 py-3">
                    Type
                </th>
                <th scope="col" class="px-6 py-3">
                    Keywords
                </th>
                <th scope="col" class="px-6 py-3 text-center">
                    <UploadDropdown :on-upload="fileUploadHandler"></UploadDropdown>
                </th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="(file, index) in referenceFiles" :key="index"
                class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                <th scope="row" class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    {{ file.filename }}
                </th>
                <td class="px-6 py-4">
                    {{ file.linkedChapter }}
                </td>
                <td class="px-6 py-4">
                    {{ file.type }}
                </td>
                <td class="px-6 py-4">
                    {{ file.keywords.join(', ') }}
                </td>
                <td class="px-6 py-4 text-center">
                    <a href="#" class="font-medium text-blue-600 dark:text-blue-500 hover:underline">Remove</a>
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script>
import UploadDropdown from '@/components/UploadDropdown.vue';
import { ref, reactive, computed, watchEffect } from 'vue';

export default {
    name: 'ReferenceFileTable',
    components: {
        UploadDropdown,
    },
    props: {
        referenceFiles: {
            type: Array,
            required: true
        },
        fileUploadHandler: {
            type: Function,
            required: true
        },
    },
    setup() {
        // Define reactive data
        const data = reactive({
            files: [],
            selectedFile: null,
        });

        // Define computed property
        const filteredFiles = computed(() => {
            // Filter files based on some condition
            return data.files.filter(file => file.name.includes('example'));
        });

        // Define a ref
        const isLoading = ref(false);

        // Define a watcher
        watchEffect(() => {
            // Perform some action when selectedFile changes
            console.log('Selected file changed:', data.selectedFile);
        });

        // Define methods
        const fetchFiles = async () => {
            isLoading.value = true;
            // Fetch files from an API
            // Assign the response to data.files
            isLoading.value = false;
        };

        // Call fetchFiles on component mount
        fetchFiles();

        // Return the reactive data, computed properties, and methods
        return {
            data,
            filteredFiles,
            isLoading,
            fetchFiles,
        };
    },

};
</script>

<style>
/* Your component styles here */
</style>
