import React, { useState } from 'react';
import Header from './components/Header';
import ChatWidget from './components/ChatWidget';
import Home from './pages/Home';
import Explorer from './pages/Explorer';
import About from './pages/About';
import Resources from './pages/Resources';
import { ChatProvider } from './context/ChatContext'
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [isDarkMode, setIsDarkMode] = useState(false);

  const renderPage = () => {
    switch (currentPage) {
      case 'explorer': return <Explorer />;
      case 'about': return <About />;
      case 'resources': return <Resources />;
      default: return <Home onNavigate={setCurrentPage} />;
    }
  };

  return (
    <ChatProvider>
      <div className={`app ${isDarkMode ? 'dark' : 'light'}`}>
        <Header 
          currentPage={currentPage} 
          onNavigate={setCurrentPage}
          isDarkMode={isDarkMode}
          onThemeToggle={() => setIsDarkMode(!isDarkMode)}
        />
        <main className="main-content">
              {renderPage()}
          </main>
          <ChatWidget />
      </div>
    </ChatProvider>
  );
}

export default App;