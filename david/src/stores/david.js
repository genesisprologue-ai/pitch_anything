import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import {
  uploadMasterFile as uploadMasterFileApi,
  fetchTranscript as fetchTranscriptApi,
  fetchTaskStatus as fetchTaskStatusApi,
  BASE_URL
} from '@/api/ApiService'

export const useDavidStore = defineStore('david', () => {
  // State to hold the PDF URL
  const pitchId = ref(1)
  const pdfUrl = ref('')
  const masterTaskId = ref('')


  const getPdfURL = () => {
    return `${BASE_URL}/${pitchId.value}/master_doc`
  }

  // List of reference files for the master file
  const referenceFiles = ref([
    // { filename: 'Document 1', linkedChapter: 'Chapter 1', type: 'PDF', keywords: ['example', 'document'], id: 1 },
  ])

  // The currently edited master file (if necessary)
  const currentMasterFile = ref(null)

  // Transcript data segmented into chapters
  const transcripts = ref([])

  // Actions to upload the master file and receive the PDF URL
  async function uploadMasterFile(file) {

    try {
      const result = await uploadMasterFileApi(file)
      console.log(result)
      pitchId.value = result.pitch_id
      pdfUrl.value = BASE_URL + '/' + pitchId.value + '/master_doc'
      masterTaskId.value = result.task_id
      return result
    } catch (error) {
      console.error('Error uploading master file:', error)
      // Handle error
      throw error
    }

  }

  // Actions to upload embedding files
  async function uploadEmbeddingFile(files, dataType) {
    // Your file upload logic here
    console.log('File uploaded:', files)
    console.log('Data type:', dataType)
  }

  async function fetchMasterTaskStatus() {
    try {
      const result = await fetchTaskStatusApi(masterTaskId.value)
      console.log(result)
      // check document progress, progress is in 1:10 format for 10 page document processing at page 1
      const [currentPage, totalPages] = result.progress.split(':')
      const percentage = (parseInt(currentPage) / parseInt(totalPages)) * 100
      return Math.round(percentage) // Round the percentage to the nearest whole number
    } catch (error) {
      console.error('Error fetching master task status:', error)
      // Handle error
      throw error
    }
  }

  // Action to fetch and set the transcript for the master file
  async function fetchTranscript() {
    try {
      const result = await fetchTranscriptApi(pitchId.value)
      console.log(result)

      if (result.message !== null) {
        console.log(result.message)
        // Redirect to '/'
        transcripts.value = []
      } else {
        transcripts.value = result.transcripts
      }

      return transcripts.value
    } catch (error) {
      console.error('Error fetching transcript:', error)
      // Handle error
      throw error
    }
  }


  return {
    pitchId,
    pdfUrl,
    referenceFiles,
    currentMasterFile,
    transcripts,
    getPdfURL,
    uploadMasterFile,
    uploadEmbeddingFile,
    fetchTranscript,
    fetchMasterTaskStatus,
  }
})
