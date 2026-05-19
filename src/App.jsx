import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import UserDashboard from './pages/UserDashboard';
import SuperUserDashboard from './pages/SuperUserDashboard';
import MeetingsList from './pages/MeetingsList';
import './index.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/user" element={<UserDashboard />} />
        <Route path="/admin" element={<SuperUserDashboard />} />
        <Route path="/admin/meetings" element={<MeetingsList />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
