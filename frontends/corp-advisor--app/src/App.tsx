import "./App.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ChatProvider } from './ChatContext.tsx';

import Home from "./pages/Home.tsx";
import Report from "./pages/Report.tsx";
import Chatbot from "./pages/Chatbot.tsx";

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
