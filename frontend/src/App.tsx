import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import MissionPlanner from "./pages/MissionPlanner";
import DocumentIngest from "./pages/DocumentIngest";
import AlertQueue from "./pages/AlertQueue";
import MissionReview from "./pages/MissionReview";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="planner" element={<MissionPlanner />} />
        <Route path="ingest" element={<DocumentIngest />} />
        <Route path="alerts" element={<AlertQueue />} />
        <Route path="review" element={<MissionReview />} />
      </Route>
    </Routes>
  );
}
