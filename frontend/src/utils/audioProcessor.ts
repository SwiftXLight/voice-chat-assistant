export class AudioProcessor {
  private static instance: AudioProcessor;
  
  static getInstance(): AudioProcessor {
    if (!AudioProcessor.instance) {
      AudioProcessor.instance = new AudioProcessor();
    }
    return AudioProcessor.instance;
  }

  /**
   * Compress audio blob to reduce file size
   */
  async compressAudio(audioBlob: Blob, quality = 0.7): Promise<Blob> {
    try {
      // Create audio context for processing
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // Convert blob to array buffer
      const arrayBuffer = await audioBlob.arrayBuffer();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      
      // Reduce sample rate more conservatively for compression
      // Use 22kHz instead of 16kHz to preserve more speech details
      const targetSampleRate = Math.min(audioBuffer.sampleRate, 22050); // 22kHz preserves more speech quality
      const compressionRatio = targetSampleRate / audioBuffer.sampleRate;
      
      // Create new buffer with reduced sample rate
      const compressedBuffer = audioContext.createBuffer(
        1, // Mono for speech
        Math.floor(audioBuffer.length * compressionRatio),
        targetSampleRate
      );
      
      // Downsample and convert to mono
      const sourceData = audioBuffer.getChannelData(0);
      const targetData = compressedBuffer.getChannelData(0);
      
      for (let i = 0; i < targetData.length; i++) {
        const sourceIndex = Math.floor(i / compressionRatio);
        targetData[i] = sourceData[sourceIndex] || 0;
      }
      
      // Convert back to blob
      const compressedBlob = await this.audioBufferToBlob(compressedBuffer, quality);
      
      await audioContext.close();
      
      console.log(`Audio compressed: ${audioBlob.size} -> ${compressedBlob.size} bytes (${Math.round((1 - compressedBlob.size / audioBlob.size) * 100)}% reduction)`);
      
      return compressedBlob;
    } catch (error) {
      console.warn('Audio compression failed, using original:', error);
      return audioBlob;
    }
  }

  /**
   * Convert AudioBuffer to Blob
   */
  private async audioBufferToBlob(audioBuffer: AudioBuffer, quality: number): Promise<Blob> {
    const numberOfChannels = audioBuffer.numberOfChannels;
    const length = audioBuffer.length;
    const sampleRate = audioBuffer.sampleRate;
    
    // Create WAV file
    const buffer = new ArrayBuffer(44 + length * numberOfChannels * 2);
    const view = new DataView(buffer);
    
    // WAV header
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length * numberOfChannels * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numberOfChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numberOfChannels * 2, true);
    view.setUint16(32, numberOfChannels * 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length * numberOfChannels * 2, true);
    
    // Convert float samples to 16-bit PCM
    let offset = 44;
    for (let i = 0; i < length; i++) {
      for (let channel = 0; channel < numberOfChannels; channel++) {
        const sample = Math.max(-1, Math.min(1, audioBuffer.getChannelData(channel)[i]));
        view.setInt16(offset, sample * 0x7FFF * quality, true);
        offset += 2;
      }
    }
    
    return new Blob([buffer], { type: 'audio/wav' });
  }


  /**
   * Apply noise reduction (basic implementation)
   */
  async applyNoiseReduction(audioBlob: Blob): Promise<Blob> {
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const arrayBuffer = await audioBlob.arrayBuffer();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      
      // Simple high-pass filter to remove low-frequency noise
      const filteredBuffer = audioContext.createBuffer(
        audioBuffer.numberOfChannels,
        audioBuffer.length,
        audioBuffer.sampleRate
      );
      
      for (let channel = 0; channel < audioBuffer.numberOfChannels; channel++) {
        const inputData = audioBuffer.getChannelData(channel);
        const outputData = filteredBuffer.getChannelData(channel);
        
        // Gentle high-pass filter (removes low-frequency noise but preserves speech)
        let prevInput = 0;
        let prevOutput = 0;
        const alpha = 0.85; // Less aggressive filter coefficient
        
        for (let i = 0; i < inputData.length; i++) {
          outputData[i] = alpha * (prevOutput + inputData[i] - prevInput);
          prevInput = inputData[i];
          prevOutput = outputData[i];
        }
      }
      
      const processedBlob = await this.audioBufferToBlob(filteredBuffer, 0.8);
      await audioContext.close();
      
      return processedBlob;
    } catch (error) {
      console.warn('Noise reduction failed, using original:', error);
      return audioBlob;
    }
  }
}
