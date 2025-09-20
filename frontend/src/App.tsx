import { useState, useRef } from 'react'
import './App.css'
import { apiClient } from './utils/apiClient'
import { ErrorHandler } from './utils/errorHandler'
import type { AppError } from './types/api'
import ErrorNotification from './components/ErrorNotification'

interface Message {
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
}

function App() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<AppError | null>(null)
  const [retryAction, setRetryAction] = useState<(() => void) | null>(null)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])

  const startRecording = async () => {
    try {
      // Clear any previous errors
      setError(null)
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        await processAudio(audioBlob)
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop())
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (error) {
      console.error('Error starting recording:', error)
      const appError = ErrorHandler.handleMicrophoneError(error)
      setError(appError)
      setRetryAction(() => startRecording)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setIsProcessing(true)
    }
  }

  const processAudio = async (audioBlob: Blob) => {
    try {
      // Clear any previous errors
      setError(null)
      
      // Step 1: Transcribe audio
      const transcribeData = await apiClient.transcribeAudio(audioBlob)
      const userMessage = transcribeData.transcript
      setTranscript(userMessage)

      // Add user message to chat
      const userMsg: Message = {
        type: 'user',
        content: userMessage,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, userMsg])

      // Step 2: Get ChatGPT response
      const chatData = await apiClient.sendChatMessage(userMessage)
      
      // Add assistant message to chat
      const assistantMsg: Message = {
        type: 'assistant',
        content: chatData.response,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, assistantMsg])

    } catch (error) {
      console.error('Error processing audio:', error)
      if (error instanceof Error && 'type' in error) {
        setError(error as AppError)
      } else {
        setError(ErrorHandler.handleApiError(error, 'processing'))
      }
      setRetryAction(() => () => processAudio(audioBlob))
    } finally {
      setIsProcessing(false)
    }
  }

  const clearChat = () => {
    setMessages([])
    setTranscript('')
    setError(null)
  }

  const handleErrorDismiss = () => {
    setError(null)
    setRetryAction(null)
  }

  const handleRetry = () => {
    if (retryAction) {
      setError(null)
      retryAction()
      setRetryAction(null)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎤 Voice Chat Assistant</h1>
        <p>Click the microphone to start talking with AI</p>
      </header>

      <main className="app-main">
        <div className="chat-container">
          <div className="messages">
            {messages.length === 0 ? (
              <div className="empty-state">
                <p>Start a conversation by clicking the microphone button below</p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div key={index} className={`message ${message.type}`}>
                  <div className="message-content">
                    <strong>{message.type === 'user' ? 'You' : 'Assistant'}:</strong>
                    <p>{message.content}</p>
                  </div>
                  <div className="message-time">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              ))
            )}
          </div>

          {transcript && (
            <div className="current-transcript">
              <strong>Last transcript:</strong> {transcript}
            </div>
          )}
        </div>

        <ErrorNotification
          error={error}
          onDismiss={handleErrorDismiss}
          onRetry={retryAction ? handleRetry : undefined}
        />

        <div className="controls">
          <button
            className={`mic-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
          >
            {isProcessing ? (
              <span>🔄 Processing...</span>
            ) : isRecording ? (
              <span>🔴 Stop Recording</span>
            ) : (
              <span>🎤 Start Recording</span>
            )}
          </button>

          {messages.length > 0 && (
            <button className="clear-button" onClick={clearChat}>
              🗑️ Clear Chat
            </button>
          )}
        </div>
      </main>
    </div>
  )
}

export default App