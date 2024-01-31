import { ref } from 'vue'
import { defineStore } from 'pinia'
import {
  uploadMasterFile as uploadMasterFileAPI,
  uploadEmbeddingFile as uploadEmbeddingFileAPI,
  fetchTranscript as fetchTranscriptAPI,
  updateTranscript as updateTranscriptAPI,
  fetchTranscribeTaskStatus as fetchTranscribeTaskStatusAPI,
  fetchTTSTaskStatus as fetchTTSTaskStatusAPI,
  listDocuments as listDocumentsAPI,
  deleteDocument as deleteDocumentAPI,
  tts,
  BASE_URL
} from '@/api/ApiService'

export const useDavidStore = defineStore('david', () => {
  // State to hold the PDF URL
  const pitchUid = ref('')
  const pdfUrl = ref('')
  const ttsTaskId = ref('')

  // List of reference files for the master file
  const referenceFiles = ref([
    // { filename: 'Document 1', linkedChapter: 'Chapter 1', type: 'PDF', keywords: ['example', 'document'], id: 1 },
  ])

  // Transcript data segmented into chapters
  const transcripts = ref([])

  const getPdfURL = () => {
    return `${BASE_URL}/${pitchUid.value}/master_doc`
  }


  const getVideoURL = (name) => {
    return BASE_URL + '/pitch_video/' + pitchUid.value + `/${name}`
  }
  // Actions to upload the master file and receive the PDF URL
  async function uploadMasterFile(file) {

    try {
      const result = await uploadMasterFileAPI(file)
      console.log(result)
      pitchUid.value = result.pitch_uid
      pdfUrl.value = BASE_URL + '/' + pitchUid.value + '/master_doc'
      return result
    } catch (error) {
      console.error('Error uploading master file:', error)
      // Handle error
      throw error
    }

  }

  // Actions to upload embedding files
  async function uploadEmbeddingFile(param) {
    // Your file upload logic here
    console.log('File uploaded:', param.files)
    console.log('Keywords', param.keywords)
    if (param.files.length > 0) {
      const file = param.files[0]; // Get the first file from the file input
      // Call uploadMasterFile with the file
      try {
        const result = await uploadEmbeddingFileAPI(file)
        console.log(result)
        return result
      } catch (error) {
        console.error('Error uploading master file:', error)
        // Handle error
        throw error
      }
    }
  }

  const transcribeStageMap = {
    0: 'KICKOFF',
    1: 'SEGMENT',
    2: 'DRAFT',
    3: 'GEN_TRANSCRIPT',
    4: 'FINISH'
  }
  async function fetchTranscribeTaskStage() {
    try {
      const result = await fetchTranscribeTaskStatusAPI(pitchUid.value)
      console.log(result)


      const stage = transcribeStageMap[result.status]
      console.log('Stage:', stage)

      return stage
    } catch (error) {
      console.error('Error fetching master task status:', error)
      // Handle error
      throw error
    }
  }

  const ttsStageMap = {
    101: 'PROCESSING',
    102: 'AUDIO',
    103: 'VIDEO',
    104: 'FINISH',
    199: 'FAILED'
  }
  async function fetchTTSTaskStage() {
    try {
      const result = await fetchTTSTaskStatusAPI(pitchUid.value, ttsTaskId.value)
      console.log(result)


      const stage = ttsStageMap[result.status]
      console.log('Stage:', stage)

      return stage
    } catch (error) {
      console.error('Error fetching master task status:', error)
      // Handle error
      throw error
    }
  }


  // Action to fetch and set the transcript for the master file
  async function fetchTranscript() {
    try {
      const result = await fetchTranscriptAPI(pitchUid.value)
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
      const result = await updateTranscriptAPI(pitchUid.value, transcripts.value)
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
      const result = await tts(pitchUid.value)
      console.log('tts result:', result)
      ttsTaskId.value = result.task_id;
      return result
    } catch (error) {
      console.error('Error generating video:', error)
      // Handle error
      throw error
    }
  }

  async function getStreamingURL() {
    return `${BASE_URL}/${pitchUid.value}/streaming`
  }

  async function fetchDocuments() {
    try {
      const data = await listDocumentsAPI(pitchUid.value)
      if (data.message !== null) {
        console.warn(data)
        return
      }
      referenceFiles.value = data.docs
    } catch (error) {
      console.error('Error fetching documents:', error)
      // Handle error
      throw error
    }
  }

  async function removeReference(file_id) {
    try {
      const data = await deleteDocumentAPI(pitchUid.value, file_id)
      console.log(data)
      if (data.message !== null) {
        console.warn(data)
        return
      }
      referenceFiles.value = referenceFiles.value.filter((file) => file.id !== file_id)
    } catch (error) {
      console.error('Error fetching documents:', error)
      // Handle error
      throw error
    }
  }


  return {
    pitchUid,
    pdfUrl,
    referenceFiles,
    transcripts,
    getPdfURL,
    uploadMasterFile,
    uploadEmbeddingFile,
    fetchTranscript,
    fetchTranscribeTaskStage,
    fetchTTSTaskStage,
    updateTranscript,
    generateVideo,
    getVideoURL,
    getStreamingURL,
    fetchDocuments,
    removeReference,
  }
})
