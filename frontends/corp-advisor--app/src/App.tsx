import "./App.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ChatProvider } from './ChatContext.tsx';

import Home from "./Screens/HomeScreen.tsx";
import Report from "./Screens/ReportScreen.tsx";
import Chatbot from "./Screens/ChatbotScreen.tsx";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route
          path="/report"
          element={
            <ChatProvider>
              <Report />
            </ChatProvider>
          }
        />
        <Route
          path="/chatbot"
          element={
            <ChatProvider>
              <Chatbot />
            </ChatProvider>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
