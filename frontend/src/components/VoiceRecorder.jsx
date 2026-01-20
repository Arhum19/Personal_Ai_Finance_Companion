import { useState, useRef, useEffect } from "react";
import { FaMicrophone, FaStop, FaSpinner, FaVolumeUp } from "react-icons/fa";

/**
 * VoiceRecorder Component
 * Records audio using MediaRecorder API with waveform visualization
 */
const VoiceRecorder = ({ onRecordingComplete, onCancel }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const timerRef = useRef(null);
  const streamRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Setup audio analyzer for waveform
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Setup MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });
        onRecordingComplete(audioBlob);
      };

      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

      // Start waveform animation
      updateAudioLevel();
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Could not access microphone. Please check permissions.");
    }
  };

  const updateAudioLevel = () => {
    if (analyserRef.current) {
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);

      // Calculate average level
      const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      setAudioLevel(average / 255); // Normalize to 0-1

      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);

      // Stop all tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }

      // Stop animation
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      setAudioLevel(0);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Generate waveform bars
  const generateWaveformBars = () => {
    const bars = [];
    const barCount = 30;

    for (let i = 0; i < barCount; i++) {
      const height = isRecording
        ? Math.max(5, Math.random() * audioLevel * 100 + 5)
        : 5;
      bars.push(
        <div
          key={i}
          className="w-1 bg-gradient-to-t from-orange-400 to-orange-600 rounded-full transition-all duration-75"
          style={{ height: `${height}px` }}
        />
      );
    }
    return bars;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full transform transition-all">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-orange-500 to-red-500 rounded-full mb-4">
            <FaVolumeUp className="text-3xl text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800">Voice Entry</h2>
          <p className="text-gray-500 mt-1">
            {isRecording
              ? "Speak your expense or income..."
              : "Tap the button to start recording"}
          </p>
        </div>

        {/* Waveform Visualization */}
        <div className="flex items-end justify-center h-24 gap-1 mb-6 bg-gray-50 rounded-2xl p-4">
          {generateWaveformBars()}
        </div>

        {/* Timer */}
        {isRecording && (
          <div className="text-center mb-6">
            <span className="text-4xl font-mono font-bold text-orange-600">
              {formatTime(recordingTime)}
            </span>
            <div className="flex items-center justify-center gap-2 mt-2 text-red-500">
              <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></span>
              Recording...
            </div>
          </div>
        )}

        {/* Processing State */}
        {isProcessing && (
          <div className="text-center mb-6">
            <FaSpinner className="animate-spin text-4xl text-orange-500 mx-auto mb-3" />
            <p className="text-gray-600">Processing your voice...</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={onCancel}
            className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition font-semibold"
            disabled={isProcessing}
          >
            Cancel
          </button>

          {!isRecording ? (
            <button
              onClick={startRecording}
              disabled={isProcessing}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white rounded-xl transition font-semibold shadow-lg disabled:opacity-50"
            >
              <FaMicrophone className="text-xl" />
              Start Recording
            </button>
          ) : (
            <button
              onClick={stopRecording}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-xl transition font-semibold shadow-lg animate-pulse"
            >
              <FaStop className="text-xl" />
              Stop Recording
            </button>
          )}
        </div>

        {/* Tips */}
        <div className="mt-6 p-4 bg-orange-50 rounded-xl">
          <p className="text-sm text-orange-800 font-semibold mb-2">
            💡 Voice Command Tips:
          </p>
          <ul className="text-sm text-orange-700 space-y-1">
            <li>
              • <strong>Expense:</strong> "Spent 500 on uber yesterday"
            </li>
            <li>
              • <strong>Income:</strong> "Got paid 50000 salary today"
            </li>
            <li>
              • <strong>Goal:</strong> "I want to buy laptop for 50000"
            </li>
            <li>
              • <strong>Contribute:</strong> "Add 5000 to laptop goal"
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default VoiceRecorder;
