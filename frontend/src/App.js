import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import LandingPage from "@/pages/LandingPage";
import ChartPage from "@/pages/ChartPage";
import ResultsPage from "@/pages/ResultsPage";
import CosmicBackground from "@/components/CosmicBackground";

function App() {
  return (
    <div className="App min-h-screen">
      <CosmicBackground />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/create" element={<ChartPage />} />
          <Route path="/results/:sessionId" element={<ResultsPage />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
