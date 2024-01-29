// apiService.js

import axios from 'axios'

export const BASE_URL = 'http://localhost:8000'

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

export async function resumeTranscribe(pitchId) {
  const response = await axios.post(`${BASE_URL}/${pitchId}/resume_transcribe`)
  return response.data
}

export async function fetchTaskStatus(taskId) {
  const response = await axios.get(`${BASE_URL}/tasks/${taskId}`)
  return response.data
}

export async function fetchTranscript(pitchId) {
  const response = await axios.get(`${BASE_URL}/${pitchId}/transcript`)
  return response.data
}

export async function updateTranscript(pitchId, transcripts) {
  const response = await axios.put(`${BASE_URL}/${pitchId}/transcript`, transcripts)
  return response.data
}

export async function tts(pitchId) {
  const response = await axios.post(`${BASE_URL}/${pitchId}/tts`)
  return response.data
}

export async function conversation(pitchId, message) {
  const response = await axios.post(`${BASE_URL}/${pitchId}/conversation`, {"query": message}, {
    headers: {
      'Content-Type': 'application/json'
    }
  })
  return response.data
}