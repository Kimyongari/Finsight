import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import "./App.css";
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './Screens/HomeScreen';
import Report from "./Screens/ReportScreen";
import Chatbot from "./Screens/ChatbotScreen";
function App() {
    return _jsx(_Fragment, { children: _jsx(Router, { children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(Home, {}) }), "       ", _jsx(Route, { path: "/report", element: _jsx(Report, {}) }), " ", _jsx(Route, { path: "/chatbot", element: _jsx(Chatbot, {}) }), " "] }) }) });
}
export default App;
