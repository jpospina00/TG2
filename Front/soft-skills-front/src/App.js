// App.js
// Propósito: Enrutamiento principal de la aplicación con protección de rutas
// Dependencias: react, react-router-dom, @auth0/auth0-react
// Fecha: 2026-03-20

import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import Login from "./components/login/Login";
import Dashboard from "./components/dashboard/Dashboard";
import Module from "./components/module/Module";
import SimpleChallenge from "./components/challenge/SimpleChallenge";
import ConversationalChallenge from "./components/challenge/ConversationalChallenge";
import Feedback from "./components/feedback/Feedback";
import Guide from "./components/guide/Guide";
import NotFound from "./components/shared/NotFound";
import Diagnostic from "./components/diagnostic/Diagnostic";
import LevelUp from "./components/shared/LevelUp";

const LoadingScreen = () => (
  <div style={{
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "rgba(241,245,249,0.5)",
    fontSize: "14px"
  }}>
    Cargando...
  </div>
);

function PrivateRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth0();
  if (isLoading) return <LoadingScreen />;
  return isAuthenticated ? children : <Navigate to="/" />;
}

function App() {
  const { isAuthenticated, isLoading } = useAuth0();

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            isLoading ? <LoadingScreen /> :
            isAuthenticated ? <Navigate to="/dashboard" /> :
            <Login />
          }
        />
        <Route
          path="/dashboard"
          element={<PrivateRoute><Dashboard /></PrivateRoute>}
        />
        <Route
          path="/module/:moduleId"
          element={<PrivateRoute><Module /></PrivateRoute>}
        />
        <Route path="/challenge/simple/:challengeId" element={<PrivateRoute><SimpleChallenge /></PrivateRoute>} />
        <Route path="/challenge/conversational/:challengeId" element={<PrivateRoute><ConversationalChallenge /></PrivateRoute>} />
        <Route path="/feedback/:conversationId" element={<PrivateRoute><Feedback /></PrivateRoute>} />
        <Route path="/module/:moduleId/guide" element={<PrivateRoute><Guide /></PrivateRoute>} />
        <Route path="/module/:moduleId/diagnostic" element={<PrivateRoute><Diagnostic /></PrivateRoute>} />
        <Route path="/levelup" element={<PrivateRoute><LevelUp /></PrivateRoute>} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;