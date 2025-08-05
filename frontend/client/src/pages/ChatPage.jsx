// src/pages/ChatPage.jsx
import { useState, useEffect } from "react";
import axios from "axios";

// Function to process markdown-style bold text
function processMarkdownText(text) {
  if (!text) return text;
  
  // Replace **text** with <strong>text</strong>
  const boldRegex = /\*\*(.*?)\*\*/g;
  return text.replace(boldRegex, '<strong>$1</strong>');
}

// Function to render text with HTML
function renderTextWithHTML(text) {
  const processedText = processMarkdownText(text);
  return <span dangerouslySetInnerHTML={{ __html: processedText }} />;
}

// Enhanced Swipeable Card Component
function SwipeableCarCard({ car, onSwipe, isActive, zIndex }) {
  const [startX, setStartX] = useState(0);
  const [currentX, setCurrentX] = useState(0);
  const [isDragging, setIsDragging] = useState(false);

  const handleStart = (e) => {
    setIsDragging(true);
    setStartX(e.type === 'mousedown' ? e.clientX : e.touches[0].clientX);
    setCurrentX(0);
  };

  const handleMove = (e) => {
    if (!isDragging) return;
    e.preventDefault();
    const x = e.type === 'mousemove' ? e.clientX : e.touches[0].clientX;
    setCurrentX(x - startX);
  };

  const handleEnd = () => {
    if (!isDragging) return;
    setIsDragging(false);
    
    if (Math.abs(currentX) > 100) {
      onSwipe(currentX > 0 ? 'right' : 'left');
    }
    setCurrentX(0);
  };

  const rotateY = currentX * 0.1;
  const opacity = 1 - Math.abs(currentX) * 0.002;
  const scale = 1 - Math.abs(currentX) * 0.0005;

  return (
    <div
      className={`absolute inset-0 cursor-grab ${isDragging ? 'cursor-grabbing' : ''} ${isActive ? 'z-10' : ''}`}
      style={{ zIndex, transform: `translateX(${currentX}px) rotateY(${rotateY}deg) scale(${scale})`, opacity }}
      onMouseDown={handleStart}
      onMouseMove={handleMove}
      onMouseUp={handleEnd}
      onMouseLeave={handleEnd}
      onTouchStart={handleStart}
      onTouchMove={handleMove}
      onTouchEnd={handleEnd}
    >
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 p-6 h-[500px] max-w-lg mx-auto transform transition-all duration-300 hover:shadow-3xl overflow-y-auto">
        
        {/* Car Header */}
        <div className="text-center mb-6">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            {car.marka} {car.seri}
          </h3>
          <p className="text-lg text-gray-600 dark:text-gray-300">{car.model}</p>
          <div className="mt-4 p-4 bg-gradient-to-r from-green-100 to-blue-100 dark:from-green-900 dark:to-blue-900 rounded-xl">
            <span className="text-3xl font-bold text-green-600 dark:text-green-400">
              {typeof car.fiyat === 'number' ? car.fiyat.toLocaleString('tr-TR') : car.fiyat} TL
            </span>
          </div>
        </div>

        {/* Car Details Grid */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="flex justify-between items-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600 rounded-lg shadow-sm">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Yıl:</span>
              <span className="text-sm font-bold text-gray-900 dark:text-white">{car.yil}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600 rounded-lg shadow-sm">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">KM:</span>
              <span className="text-sm font-bold text-gray-900 dark:text-white">{car.km}</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex justify-between items-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600 rounded-lg shadow-sm">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Yakıt:</span>
              <span className="text-sm font-bold text-gray-900 dark:text-white">{car.yakit || car.fuel}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600 rounded-lg shadow-sm">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Vites:</span>
              <span className="text-sm font-bold text-gray-900 dark:text-white">{car.vites || car.transmission}</span>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="flex justify-between items-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600 rounded-lg shadow-sm">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Kasa:</span>
              <span className="text-sm font-bold text-gray-900 dark:text-white">{car.kasa_tipi || car.body_type || car.type}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600 rounded-lg shadow-sm">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Renk:</span>
              <span className="text-sm font-bold text-gray-900 dark:text-white">{car.renk || car.color}</span>
            </div>
          </div>
        </div>

        {/* Link to view car */}
        {car.link && (
          <div className="mt-6">
            <a 
              href={car.link} 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold rounded-xl transition-all duration-300 transform hover:scale-105 hover:shadow-lg shadow-md"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              İlanı Görüntüle
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

// Enhanced Swipeable Cards Container
function SwipeableCarCards({ cars, darkMode }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const nextCard = () => {
    if (currentIndex < cars.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const prevCard = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const resetCards = () => {
    setCurrentIndex(0);
  };

  const handleSwipe = (direction) => {
    if (direction === 'left') {
      nextCard();
    } else {
      // Handle right swipe (like functionality can be added here)
      nextCard();
    }
  };

  if (!cars || cars.length === 0) {
    return (
      <div className="text-center text-gray-500 dark:text-gray-400 py-8">
        <div className="text-4xl mb-2">🚗</div>
        <p>Araç bulunamadı</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-lg mx-auto">
      {/* Cards Stack */}
      <div className="relative h-[500px] mb-6">
        {cars.map((car, index) => (
          <SwipeableCarCard
            key={index}
            car={car}
            onSwipe={handleSwipe}
            isActive={index === currentIndex}
            zIndex={cars.length - Math.abs(index - currentIndex)}
          />
        ))}
      </div>

      {/* Enhanced Navigation */}
      <div className="flex justify-center items-center space-x-4 mt-6">
        <button
          onClick={prevCard}
          disabled={currentIndex === 0}
          className="p-3 bg-gradient-to-r from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600 text-gray-700 dark:text-gray-300 rounded-full hover:from-gray-300 hover:to-gray-400 dark:hover:from-gray-600 dark:hover:to-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-110 active:scale-95 shadow-lg"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <button
          onClick={resetCards}
          className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full hover:from-purple-600 hover:to-pink-600 transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-lg font-medium"
        >
          🔄 Baştan
        </button>

        <button
          onClick={nextCard}
          disabled={currentIndex === cars.length - 1}
          className="p-3 bg-gradient-to-r from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600 text-gray-700 dark:text-gray-300 rounded-full hover:from-gray-300 hover:to-gray-400 dark:hover:from-gray-600 dark:hover:to-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-110 active:scale-95 shadow-lg"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Progress bar */}
      <div className="mt-4 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div 
          className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
          style={{ width: `${((currentIndex + 1) / cars.length) * 100}%` }}
        ></div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Generate or get session ID
  const getSessionId = () => {
    if (!currentSessionId) {
      const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      setCurrentSessionId(newSessionId);
      return newSessionId;
    }
    return currentSessionId;
  };

  // Load chat sessions from localStorage on component mount
  useEffect(() => {
    const savedSessions = localStorage.getItem('chatSessions');
    if (savedSessions) {
      setChatSessions(JSON.parse(savedSessions));
    }
  }, []);

  // Save chat sessions to localStorage
  const saveChatSessions = (sessions) => {
    setChatSessions(sessions);
    localStorage.setItem('chatSessions', JSON.stringify(sessions));
  };

  // Create new chat session
  const createNewSession = () => {
    const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const newSession = {
      id: newSessionId,
      title: "Yeni Sohbet",
      messages: [],
      createdAt: new Date().toISOString()
    };
    
    const updatedSessions = [newSession, ...chatSessions];
    saveChatSessions(updatedSessions);
    setCurrentSessionId(newSessionId);
    setMessages([]);
  };

  // Load chat session
  const loadChatSession = (sessionId) => {
    const session = chatSessions.find(s => s.id === sessionId);
    if (session) {
      setCurrentSessionId(sessionId);
      setMessages(session.messages || []);
    }
  };

  // Update current session
  const updateCurrentSession = (newMessages) => {
    if (currentSessionId) {
      const updatedSessions = chatSessions.map(session => {
        if (session.id === currentSessionId) {
          return {
            ...session,
            messages: newMessages,
            title: newMessages.length > 0 ? newMessages[0].text.substring(0, 30) + '...' : "Yeni Sohbet",
            updatedAt: new Date().toISOString()
          };
        }
        return session;
      });
      saveChatSessions(updatedSessions);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const sendMessage = async () => {
    if (!userInput.trim() || isLoading) return;

    const sessionId = getSessionId();
    const userMessage = { sender: "user", text: userInput };
    const newMessages = [...messages, userMessage];
    
    setMessages(newMessages);
    setUserInput("");
    setIsLoading(true);

    try {
      const response = await axios.post("http://aracasistani.duckdns.org:8000/chat", {
        user_query: userInput,
        session_id: sessionId
      });

      const botMessage = {
        sender: "bot",
        text: response.data.response,
        results: response.data.results || []
      };

      const finalMessages = [...newMessages, botMessage];
      setMessages(finalMessages);
      updateCurrentSession(finalMessages);

    } catch (error) {
      console.error("API Error:", error);
      const errorMessage = {
        sender: "bot",
        text: "Özür dilerim, bir hata oluştu. Lütfen tekrar deneyin."
      };
      const finalMessages = [...newMessages, errorMessage];
      setMessages(finalMessages);
      updateCurrentSession(finalMessages);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      darkMode ? 'dark bg-gray-900' : 'bg-gradient-to-br from-blue-50 via-white to-purple-50'
    }`}>
      
      {/* Desktop Layout Container */}
      <div className="flex h-screen">
        
        {/* Chat Sessions Sidebar */}
        <div className={`${sidebarOpen ? 'w-80' : 'w-16'} transition-all duration-300 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm border-r border-gray-200 dark:border-gray-700 flex flex-col`}>
          
          {/* Sidebar Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              {sidebarOpen && (
                <h2 className="text-lg font-semibold text-gray-800 dark:text-white">Sohbetler</h2>
              )}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sidebarOpen ? "M15 19l-7-7 7-7" : "M9 5l7 7-7 7"} />
                </svg>
              </button>
            </div>
          </div>

          {/* New Chat Button */}
          {sidebarOpen && (
            <div className="p-4">
              <button
                onClick={createNewSession}
                className="w-full p-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all duration-200 font-medium shadow-lg"
              >
                + Yeni Sohbet
              </button>
            </div>
          )}

          {/* Chat Sessions List */}
          <div className="flex-1 overflow-y-auto">
            {sidebarOpen && chatSessions.map((session) => (
              <div
                key={session.id}
                onClick={() => loadChatSession(session.id)}
                className={`p-4 border-b border-gray-100 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                  currentSessionId === session.id ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500' : ''
                }`}
              >
                <div className="text-sm font-medium text-gray-800 dark:text-white truncate">
                  {session.title}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {new Date(session.createdAt).toLocaleDateString('tr-TR')}
                </div>
              </div>
            ))}
            
            {sidebarOpen && chatSessions.length === 0 && (
              <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                <div className="text-4xl mb-2">💬</div>
                <p className="text-sm">Henüz sohbet yok</p>
                <p className="text-xs">Yeni bir sohbet başlatın</p>
              </div>
            )}
          </div>

          {/* Dark Mode Toggle in Sidebar */}
          {sidebarOpen && (
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="w-full p-3 bg-gray-100 dark:bg-gray-700 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200 flex items-center justify-center space-x-2"
              >
                <span>{darkMode ? '🌞' : '🌙'}</span>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {darkMode ? 'Açık Tema' : 'Koyu Tema'}
                </span>
              </button>
            </div>
          )}
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          
          {/* Header */}
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700 p-6">
            <div className="max-w-7xl mx-auto">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center">
                    <img src="/vite.svg" alt="Logo" className="w-20 h-20" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                      Araba Asistanı
                    </h1>
                    <p className="text-gray-600 dark:text-gray-300">
                      Size en uygun arabayı bulmanıza yardımcı oluyorum! ✨
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto">
              <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 h-full flex flex-col">
                
                {/* Messages Container */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                  {messages.length === 0 ? (
                    <div className="text-center text-gray-500 dark:text-gray-400 py-16">
                      <div className="text-8xl mb-6">👋</div>
                      <h2 className="text-2xl font-semibold mb-4">Merhaba! Size nasıl yardımcı olabilirim?</h2>
                      <p className="text-lg mb-6">En uygun arabayı bulmanız için buradayım</p>
                      <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4 max-w-2xl mx-auto">
                        <p className="text-sm font-medium mb-2">Örnek sorular:</p>
                        <ul className="text-sm space-y-1 text-left">
                          <li>• "100.000 TL bütçem var, otomatik vites bir sedan arıyorum"</li>
                          <li>• "Aile için geniş ve güvenli bir araç istiyorum"</li>
                          <li>• "Şehir içi kullanım için ekonomik bir araç"</li>
                        </ul>
                      </div>
                    </div>
                  ) : (
                    messages.map((msg, index) => (
                      <div key={index} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                        <div className={`max-w-4xl p-6 rounded-2xl shadow-lg ${
                          msg.sender === "user" 
                            ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white" 
                            : "bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-600"
                        }`}>
                          <div className="mb-2 text-lg">{renderTextWithHTML(msg.text)}</div>
                          
                          {/* Enhanced car results display */}
                          {msg.sender === "bot" && msg.results && msg.results.length > 0 && (
                            <div className={`mt-6 p-6 rounded-xl ${darkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
                              <h4 className="font-semibold mb-4 text-center text-xl">🎯 Arama Sonuçları ({msg.results.length} araç bulundu)</h4>
                              <p className="text-center mb-6 text-gray-600 dark:text-gray-400">
                                💡 Kartları sola/sağa kaydırarak araçları inceleyin
                              </p>
                              <SwipeableCarCards cars={msg.results} darkMode={darkMode} />
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                  
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-white dark:bg-gray-700 p-6 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-600">
                        <div className="flex space-x-2">
                          <div className="w-4 h-4 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-bounce"></div>
                          <div className="w-4 h-4 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-4 h-4 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Input Area */}
                <div className="p-6 border-t border-gray-200 dark:border-gray-600 bg-gray-50/50 dark:bg-gray-800/50">
                  <div className="flex space-x-4">
                    <textarea
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Mesajınızı yazın... (örn: 'Kırmızı renk, otomatik vites araba istiyorum')"
                      className="flex-1 p-4 border border-gray-300 dark:border-gray-600 rounded-xl resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 shadow-sm text-lg"
                      rows="3"
                      disabled={isLoading}
                    />
                    <button
                      onClick={sendMessage}
                      disabled={isLoading || !userInput.trim()}
                      className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-lg font-medium text-lg"
                    >
                      {isLoading ? (
                        <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Fixed Footer Credit */}
      <div className="fixed bottom-6 right-6 z-50">
        <div className="bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm px-4 py-2 rounded-xl shadow-lg border border-gray-200 dark:border-gray-600">
          <div className="text-gray-700 dark:text-gray-300 text-sm font-medium flex items-center space-x-2">
            <span>⚡</span>
            <span>made by</span>
            <span className="font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Code in White
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
