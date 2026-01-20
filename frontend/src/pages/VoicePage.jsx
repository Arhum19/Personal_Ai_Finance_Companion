import { useState } from "react";
import { FaMicrophone } from "react-icons/fa";
import MainLayout from "../layouts/MainLayout";
import VoiceEntry from "../components/VoiceEntry";
import useAppStore from "../store/appStore";

const VoicePage = () => {
  const { triggerRefresh } = useAppStore();
  const [showVoiceModal, setShowVoiceModal] = useState(false);

  const handleVoiceSuccess = () => {
    triggerRefresh();
  };

  return (
    <MainLayout>
      <div className="min-h-[70vh] flex items-center justify-center">
        {/* Centered Voice Icon Button */}
        <button
          onClick={() => setShowVoiceModal(true)}
          className="flex flex-col items-center justify-center gap-4 group"
        >
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-orange-500 to-red-500 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative w-40 h-40 bg-gradient-to-br from-orange-600 to-red-600 rounded-full flex items-center justify-center shadow-2xl group-hover:shadow-3xl group-hover:scale-110 transition-all duration-300 cursor-pointer">
              <FaMicrophone className="text-white text-6xl" />
            </div>
          </div>
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-800">Voice Agent</h2>
            <p className="text-gray-600 mt-2">Click to start recording</p>
          </div>
        </button>
      </div>

      {/* Voice Entry Modal */}
      {showVoiceModal && (
        <VoiceEntry
          onClose={() => setShowVoiceModal(false)}
          onSuccess={handleVoiceSuccess}
        />
      )}
    </MainLayout>
  );
};

export default VoicePage;
