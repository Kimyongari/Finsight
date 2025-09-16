import "./App.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ChatProvider } from "./ChatContext.tsx";
import { useCsvData } from './hooks/useCsvData.ts';

import Home from "./pages/Home.tsx";
import Report from "./pages/Report.tsx";
import Chatbot from "./pages/Chatbot.tsx";

function App() {
  const { data, loading, error } = useCsvData("/csv/company_with_corp_code.csv");
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route
          path="/report"
          element={
            <ChatProvider>
              <Report csvData={data} isLoading={loading} loadError={error} />
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
