import { ref } from 'vue'
import { defineStore } from 'pinia'
import {
  uploadMasterFile as uploadMasterFileApi,
  fetchTranscript as fetchTranscriptApi,
  fetchTaskStatus as fetchTaskStatusApi,
  updateTranscript as updateTranscriptApi,
  tts,
  conversation as conversationApi,
  BASE_URL
} from '@/api/ApiService'

export const useDavidStore = defineStore('david', () => {
  // State to hold the PDF URL
  const pitchId = ref(1)
  const pdfUrl = ref('')
  const masterTaskId = ref('708ff06a-828d-4e46-9ef3-4fa13b05065a')
  const videoTaskId = ref('')


  const getPdfURL = () => {
    return `${BASE_URL}/${pitchId.value}/master_doc`
  }

  // List of reference files for the master file
  const referenceFiles = ref([
    // { filename: 'Document 1', linkedChapter: 'Chapter 1', type: 'PDF', keywords: ['example', 'document'], id: 1 },
  ])

  // Transcript data segmented into chapters
  const transcripts = ref([])

  const getVideoURL = (name) => {
    return BASE_URL + '/pitch_video/' + pitchId.value + `/${name}`
  }
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

  async function fetchVideoTaskStatus() {
    try {
      const result = await fetchTaskStatusApi(videoTaskId.value)
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

  async function updateTranscript() {
    try {
      const result = await updateTranscriptApi(pitchId.value, transcripts.value)
      console.log(result)

      if (result.message !== null) {
        console.log(result.message)
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

  async function generateVideo() {
    try {
      const result = await tts(pitchId.value)
      console.log(result)
      videoTaskId.value = result.task_id
      return result
    } catch (error) {
      console.error('Error generating video:', error)
      // Handle error
      throw error
    }
  }

  async function sendConversation(message) {
    try {
      const result = await conversationApi(pitchId.value, message)
      console.log(result)
      return { "role": "ai", "content": result.content }
    } catch (error) {
      console.error('Error generating video:', error)
      // Handle error
      throw error
    }
  }


  return {
    pitchId,
    pdfUrl,
    masterTaskId,
    referenceFiles,
    transcripts,
    getPdfURL,
    uploadMasterFile,
    uploadEmbeddingFile,
    fetchTranscript,
    fetchMasterTaskStatus,
    fetchVideoTaskStatus,
    updateTranscript,
    generateVideo,
    getVideoURL,
    sendConversation,
  }
})
