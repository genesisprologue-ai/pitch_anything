import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import {
  uploadMasterFile as uploadMasterFileApi,
  fetchTranscript as fetchTranscriptApi,
  BASE_URL
} from '@/api/ApiService'

export const useDavidStore = defineStore('david', () => {
  // State to hold the PDF URL
  const pitchId = ref(1)
  const pdfUrl = ref('')

  // Loading states
  const isProcessingFile = ref(false)
  const isUploadingEmbeddings = ref(false)

  const getPdfURL = () => {
    return `${BASE_URL}/${pitchId.value}/master_doc`
  }

  // List of reference files for the master file
  const referenceFiles = ref([
    { filename: 'Document 1', linkedChapter: 'Chapter 1', type: 'PDF', keywords: ['example', 'document'], id: 1 },
    { filename: 'Document 2', linkedChapter: 'Chapter 2', type: 'PDF', keywords: ['sample', 'file'], id: 2 }
    // ... more files
  ])

  // The currently edited master file (if necessary)
  const currentMasterFile = ref(null)

  // Transcript data segmented into chapters
  const transcript = ref([])

  // Actions to upload the master file and receive the PDF URL
  async function uploadMasterFile(file) {
    isProcessingFile.value = true

    try {
      const result = await uploadMasterFileApi(file)
      console.log(result)
      pitchId.value = result.pitch_id
      pdfUrl.value = BASE_URL + '/' + pitchId.value + '/master_doc'
      isProcessingFile.value = false
      return result
    } catch (error) {
      console.error('Error uploading master file:', error)
      // Handle error
      isProcessingFile.value = false
      throw error
    }

  }

  // Actions to upload embedding files
  async function uploadEmbeddingFile(files, dataType) {
    // Your file upload logic here
    console.log('File uploaded:', files)
    console.log('Data type:', dataType)

    isUploadingEmbeddings.value = true
    // Logic to upload embedding files...
    // Update referenceFiles.value as necessary
    isUploadingEmbeddings.value = false
  }

  // Action to fetch and set the transcript for the master file
  async function fetchTranscript() {
    try {
      const result = await fetchTranscriptApi(pitchId.value)
      console.log(result)
      transcript.value = result.transcripts
      return result.transcripts
    } catch (error) {
      console.error('Error fetching transcript:', error)
      // Handle error
      throw error
    }
  }

  // A computed property to indicate if any loading is happening
  const isLoading = computed(() => isProcessingFile.value || isUploadingEmbeddings.value)

  return {
    pitchId,
    pdfUrl,
    isProcessingFile,
    isUploadingEmbeddings,
    referenceFiles,
    currentMasterFile,
    transcript,
    getPdfURL,
    uploadMasterFile,
    uploadEmbeddingFile,
    fetchTranscript,
    isLoading
  }
})
