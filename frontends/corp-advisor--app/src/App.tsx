import "./App.css";
import {BrowserRouter as Router, Routes, Route} from "react-router-dom";

import Home from "./Screens/HomeScreen.tsx";
import Report from "./Screens/ReportScreen.tsx";
import Chatbot from "./Screens/ChatbotScreen.tsx";

function App() {
  return (<> < Router > <Routes>
    <Route path="/" element={<Home />}/> {/* 홈 페이지 */}
    <Route path="/report" element={<Report />}/> {/* About 페이지 */}
    <Route path="/chatbot" element={<Chatbot />}/> {/* Contact 페이지 */}
  </Routes>
</Router>
</>);
}

export default App;
