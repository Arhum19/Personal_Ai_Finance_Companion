import { useState } from "react";
import toast from "react-hot-toast";
import VoiceRecorder from "./VoiceRecorder";
import VoiceConfirmation from "./VoiceConfirmation";
import { voiceAPI } from "../services/api";
import { FaSpinner, FaExclamationTriangle } from "react-icons/fa";

/**
 * VoiceEntry Component
 * Main component that orchestrates the voice entry flow:
 * 1. Recording -> 2. Processing -> 3. Confirmation -> 4. Save
 */
const VoiceEntry = ({ onClose, onSuccess }) => {
  const [stage, setStage] = useState("recording"); // recording, processing, confirmation, error
  const [parsedData, setParsedData] = useState(null);
  const [transcribedText, setTranscribedText] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const handleRecordingComplete = async (audioBlob) => {
    setStage("processing");

    try {
      const response = await voiceAPI.transcribe(audioBlob);
      const data = response.data;

      if (!data.success) {
        setErrorMessage(data.message || "Could not process audio");
        setStage("error");
        return;
      }

      setTranscribedText(data.transcribed_text);
      setParsedData(data.parsed_data);
      setStage("confirmation");
    } catch (error) {
      console.error("Voice transcription error:", error);
      const errorMsg =
        error.response?.data?.detail || "Failed to process voice recording";
      setErrorMessage(errorMsg);
      setStage("error");
      toast.error(errorMsg);
    }
  };

  const handleConfirm = (result) => {
    // Success! Close the modal and trigger refresh
    onSuccess?.(result);
    onClose();
  };

  const handleRetry = () => {
    setParsedData(null);
    setTranscribedText("");
    setErrorMessage("");
    setStage("recording");
  };

  const handleCancel = () => {
    onClose();
  };

  // Processing Stage
  if (stage === "processing") {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-orange-500 to-red-500 rounded-full mb-6 animate-pulse">
            <FaSpinner className="text-4xl text-white animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Processing Voice...
          </h2>
          <p className="text-gray-500">
            Transcribing audio and analyzing your command
          </p>
          <div className="mt-6 flex items-center justify-center gap-2">
            <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce"></div>
            <div
              className="w-2 h-2 bg-orange-500 rounded-full animate-bounce"
              style={{ animationDelay: "0.1s" }}
            ></div>
            <div
              className="w-2 h-2 bg-orange-500 rounded-full animate-bounce"
              style={{ animationDelay: "0.2s" }}
            ></div>
          </div>
        </div>
      </div>
    );
  }

  // Error Stage
  if (stage === "error") {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-red-100 rounded-full mb-6">
            <FaExclamationTriangle className="text-4xl text-red-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Oops! Something went wrong
          </h2>
          <p className="text-gray-600 mb-6">{errorMessage}</p>

          <div className="flex gap-4">
            <button
              onClick={handleCancel}
              className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition font-semibold"
            >
              Cancel
            </button>
            <button
              onClick={handleRetry}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:from-orange-600 hover:to-red-600 transition font-semibold shadow-lg"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Confirmation Stage
  if (stage === "confirmation" && parsedData) {
    return (
      <VoiceConfirmation
        parsedData={parsedData}
        transcribedText={transcribedText}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
        onRetry={handleRetry}
      />
    );
  }

  // Recording Stage (default)
  return (
    <VoiceRecorder
      onRecordingComplete={handleRecordingComplete}
      onCancel={handleCancel}
    />
  );
};

export default VoiceEntry;
