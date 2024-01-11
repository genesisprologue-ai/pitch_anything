import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useDavidStore = defineStore('david', () => {
    // State to hold the PDF URL
    const pdfUrl = ref('');

    // Loading states
    const isProcessingFile = ref(false);
    const isUploadingEmbeddings = ref(false);

    // List of reference files for the master file
    const referenceFiles = ref([
        { filename: 'Document 1', linkedChapter: 'Chapter 1', type: 'PDF', keywords: ['example', 'document'], id: 1 },
        { filename: 'Document 2', linkedChapter: 'Chapter 2', type: 'PDF', keywords: ['sample', 'file'], id: 2 },
        // ... more files
    ]);

    // The currently edited master file (if necessary)
    const currentMasterFile = ref(null);

    // Transcript data segmented into chapters
    const transcript = ref({
        chapters: [],
        // Other transcript-related data...
    });

    // Actions to upload the master file and receive the PDF URL
    async function uploadMasterFile(file) {
        isProcessingFile.value = true;
        // Logic to upload file and get the PDF URL...
        // For example:
        // pdfUrl.value = await fileUploadService.upload(file);
        isProcessingFile.value = false;
    }

    // Actions to upload embedding files
    async function uploadEmbeddingFile(files, dataType) {
        // Your file upload logic here
        console.log('File uploaded:', files);
        console.log('Data type:', dataType);

        isUploadingEmbeddings.value = true;
        // Logic to upload embedding files...
        // Update referenceFiles.value as necessary
        isUploadingEmbeddings.value = false;
    }

    // Action to fetch and set the transcript for the master file
    async function fetchTranscript(masterFileId) {
        // Logic to fetch transcript data...
        // For example:
        // transcript.value = await transcriptService.fetch(masterFileId);
    }

    // A computed property to indicate if any loading is happening
    const isLoading = computed(() => isProcessingFile.value || isUploadingEmbeddings.value);

    return {
        pdfUrl,
        isProcessingFile,
        isUploadingEmbeddings,
        referenceFiles,
        currentMasterFile,
        transcript,
        uploadMasterFile,
        uploadEmbeddingFile,
        fetchTranscript,
        isLoading,
    };
});