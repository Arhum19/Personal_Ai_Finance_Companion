import { Link } from "react-router-dom";
import {
  FaMicrophone,
  FaLightbulb,
  FaChartLine,
  FaBullseye,
  FaRobot,
} from "react-icons/fa";

const HomePage = () => {
  const features = [
    {
      icon: <FaMicrophone className="text-4xl" />,
      title: "NLP Voice Input",
      description:
        'Just speak naturally! "Spent 500 on pizza" - our AI understands and logs it instantly.',
      color: "from-blue-500 to-blue-600",
    },
    {
      icon: <FaLightbulb className="text-4xl" />,
      title: "AI-Powered Insights",
      description:
        "Get friendly, conversational advice about your spending - not robotic reports.",
      color: "from-orange-500 to-orange-600",
    },
    {
      icon: <FaRobot className="text-4xl" />,
      title: "What-If Simulator",
      description:
        'Test scenarios before they happen. "What if rent increases 20%?" - AI explains the impact.',
      color: "from-purple-500 to-purple-600",
    },
    {
      icon: <FaBullseye className="text-4xl" />,
      title: "Smart Goal Tracking",
      description:
        "Set savings goals and watch your progress. AI helps you stay on track.",
      color: "from-green-500 to-green-600",
    },
    {
      icon: <FaChartLine className="text-4xl" />,
      title: "Real-time Analytics",
      description:
        "Beautiful charts and insights that update instantly with every transaction.",
      color: "from-pink-500 to-pink-600",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-orange-50">
      {/* Hero Section */}
      <div className="w-full px-6 md:px-12 lg:px-20 py-16">
        <div className="text-center max-w-4xl mx-auto">
          {/* Logo */}
          <h1 className="text-6xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-orange-500 bg-clip-text text-transparent animate-fade-in">
            CASHDASH
          </h1>

          {/* Tagline */}
          <p className="text-2xl md:text-3xl text-gray-700 mb-4">
            Your AI-Powered Finance Companion
          </p>

          <p className="text-lg text-gray-600 mb-12 max-w-2xl mx-auto">
            Track expenses with your voice. Get smart insights that feel human.
            Make better money decisions with AI that actually understands you.
          </p>

          {/* CTA Button */}
          <Link
            to="/signup"
            className="inline-block bg-gradient-to-r from-blue-600 to-orange-500 text-white text-xl font-semibold px-12 py-4 rounded-full shadow-lg hover:shadow-2xl hover:scale-110 transition-all duration-300 transform relative group"
          >
            <span className="relative z-10">Get Started Free</span>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-700 to-orange-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10"></div>
          </Link>

          <p className="text-sm text-gray-500 mt-4">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-blue-600 font-semibold hover:text-blue-700"
            >
              Login here
            </Link>
          </p>
        </div>

        {/* Features Grid */}
        <div className="mt-24 w-full">
          <h2 className="text-4xl font-bold text-center text-gray-800 mb-12 hover:text-transparent hover:bg-gradient-to-r hover:from-blue-600 hover:to-orange-500 hover:bg-clip-text transition-all duration-300">
            What Makes CashDash Different?
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-2xl hover:-translate-y-3 transition-all duration-300 transform cursor-pointer group"
              >
                <div
                  className={`inline-flex p-4 rounded-full bg-gradient-to-r ${feature.color} text-white mb-4 group-hover:scale-125 transition-transform duration-300`}
                >
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* AI Highlight Section */}
        <div className="mt-24 bg-gradient-to-r from-blue-600 to-orange-500 rounded-3xl p-12 text-white text-center max-w-6xl mx-auto hover:shadow-2xl hover:scale-105 transition-all duration-500 cursor-pointer">
          <h2 className="text-4xl font-bold mb-6">🤖 Built with Advanced AI</h2>
          <p className="text-xl mb-8 max-w-3xl mx-auto">
            CashDash uses cutting-edge Natural Language Processing and AI to
            understand your voice, analyze your spending patterns, and give you
            advice that feels like talking to a smart friend - not a robot.
          </p>
          <div className="flex flex-wrap justify-center gap-4 md:gap-8 text-sm">
            <div className="bg-white/20 backdrop-blur-sm rounded-lg px-6 py-3 hover:bg-white/40 hover:scale-110 transition-all duration-300 cursor-pointer transform">
              ✓ Whisper AI Transcription
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-lg px-6 py-3 hover:bg-white/40 hover:scale-110 transition-all duration-300 cursor-pointer transform">
              ✓ GPT-Powered Insights
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-lg px-6 py-3 hover:bg-white/40 hover:scale-110 transition-all duration-300 cursor-pointer transform">
              ✓ Smart NLP Parser
            </div>
          </div>
        </div>

        {/* Footer CTA */}
        <div className="mt-24 text-center pb-12">
          <h2 className="text-3xl font-bold text-gray-800 mb-6">
            Ready to take control of your finances?
          </h2>
          <Link
            to="/signup"
            className="inline-block bg-blue-600 text-white text-lg font-semibold px-10 py-3 rounded-full shadow-lg hover:bg-blue-700 hover:shadow-xl transition transform hover:scale-105 duration-300"
          >
            Start Your Journey
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
