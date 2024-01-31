// apiService.js

import axios from 'axios'

export const BASE_URL = import.meta.env.VITE_BASE_URL || 'http://localhost:8000';

export async function uploadMasterFile(file) {
  console.log(file)

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await axios.post(`${BASE_URL}/upload_master`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // If the request is successful, return the response data
    return response.data
  } catch (error) {
    // If the request fails, log the error to the console and throw it
    console.error('Upload failed:', error.response.data)
    throw error
  }
}

export async function uploadEmbeddingFile(file) {
  console.log(file)

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await axios.post(`${BASE_URL}/reference_doc`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    // If the request is successful, return the response data
    return response.data
  } catch (error) {
    // If the request fails, log the error to the console and throw it
    console.error('Upload failed:', error.response.data)
    throw error
  }
}

export async function resumeTranscribe(pitchUid) {
  const response = await axios.post(`${BASE_URL}/${pitchUid}/resume_transcribe`)
  return response.data
}

export async function fetchTranscribeTaskStatus(pitchUid) {
  const response = await axios.get(`${BASE_URL}/${pitchUid}/transcibe_status`)
  return response.data
}

export async function fetchTTSTaskStatus(pitchUid, taskId) {
  const response = await axios.get(`${BASE_URL}/${pitchUid}/tts_status/${taskId}`)
  return response.data
}


export async function fetchTranscript(pitchUid) {
  const response = await axios.get(`${BASE_URL}/${pitchUid}/transcript`)
  return response.data
}

export async function updateTranscript(pitchUid, transcripts) {
  const response = await axios.put(`${BASE_URL}/${pitchUid}/transcript`, transcripts)
  return response.data
}

export async function tts(pitchUid) {
  const response = await axios.post(`${BASE_URL}/${pitchUid}/tts`)
  return response.data
}

export async function listDocuments(pitchUid) {
  const response = await axios.get(`${BASE_URL}/${pitchUid}/reference_doc/`)
  return response.data
}

export async function deleteDocument(pitchUid, documentId) {
  const response = await axios.delete(`${BASE_URL}/${pitchUid}/reference_doc/${documentId}`)
  return response.data
}