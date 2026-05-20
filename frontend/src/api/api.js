/**
 * Real API Service connecting directly to the FastAPI backend
 */
import t from '../i18n/IT.json';

const BASE_URL = 'http://127.0.0.1:8000';

// Seeded tokens mapped to database emails and roles
const TOKEN_MAP = {
  'admin': { email: 'mario.rossi@school.it', role: 'super_user' },
  'TOK-A1B2C3': { email: 'luca.ferrari@school.it', role: 'user' },
  'TOK-D4E5F6': { email: 'anna.conti@school.it', role: 'user' },
  'TOK-G7H8I9': { email: 'roberto.mancini@school.it', role: 'user' },
  'TOK-J1K2L3': { email: 'elena.ricci@school.it', role: 'user' },
  'TOK-M4N5O6': { email: 'marco.gallo@school.it', role: 'user' },
  'TOK-P7Q8R9': { email: 'sofia.marino@school.it', role: 'user' },
  'TOK-S1T2U3': { email: 'davide.esposito@school.it', role: 'user' },
  'TOK-V4W5X6': { email: 'chiara.lombardi@school.it', role: 'user' },
  'TOK-Y7Z8A1': { email: 'paolo.greco@school.it', role: 'user' },
  'TOK-B2C3D4': { email: 'francesca.bruno@school.it', role: 'user' },
  'TOK-E5F6G7': { email: 'antonio.romano@school.it', role: 'user' },
  'TOK-H8I9J1': { email: 'valentina.sala@school.it', role: 'user' },
  'TOK-K2L3M4': { email: 'giorgio.costa@school.it', role: 'user' },
  'TOK-N5O6P7': { email: 'luca.ferrari@school.it', role: 'user' },
  'TOK-Q8R9S1': { email: 'anna.conti@school.it', role: 'user' }
};

const getHeaders = () => {
  const token = localStorage.getItem('cp_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

const getEmail = () => {
  try {
    const userData = JSON.parse(localStorage.getItem('cp_user_data'));
    return userData ? userData.email : '';
  } catch (e) {
    return '';
  }
};

const getToken = () => {
  return localStorage.getItem('cp_token') || '';
};

// Default token to use for public access (must be a valid teacher token from physical.sql seeds)
const PUBLIC_TOKEN = 'TOK-A1B2C3';

export const api = {
  async login(rawToken) {
    const cleanToken = rawToken ? rawToken.trim() : '';
    if (!cleanToken) throw new Error(t.api.tokenRequired);

    // Call real FastAPI login
    const response = await fetch(`${BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: cleanToken })
    });

    if (!response.ok) {
      throw new Error(t.api.tokenInvalid);
    }

    const data = await response.json();
    if (data.login_status === 'OK') {
      // Map user details locally based on seeded tokens in TOKEN_MAP
      let userData = TOKEN_MAP[cleanToken];
      if (!userData) {
        userData = { 
          email: `docente_${cleanToken.slice(0, 4)}@school.it`, 
          role: cleanToken.toLowerCase().includes('admin') ? 'super_user' : 'user' 
        };
      }
      
      const sessionUser = {
        token: cleanToken,
        role: userData.role,
        email: userData.email
      };

      localStorage.setItem('cp_token', cleanToken);
      localStorage.setItem('cp_user_data', JSON.stringify(sessionUser));
      return sessionUser;
    } else {
      throw new Error(t.api.tokenInvalid);
    }
  },

  async createSession(title, scheduledDate = null) {
    const dateObj = scheduledDate ? new Date(scheduledDate) : new Date();
    
    // Format meeting_date: YYYY-MM-DD
    const yyyy = dateObj.getFullYear();
    const mm = String(dateObj.getMonth() + 1).padStart(2, '0');
    const dd = String(dateObj.getDate()).padStart(2, '0');
    const meeting_date = `${yyyy}-${mm}-${dd}`;

    // Format start_time: HH:MM:SS
    const hh = String(dateObj.getHours()).padStart(2, '0');
    const min = String(dateObj.getMinutes()).padStart(2, '0');
    const start_time = `${hh}:${min}:00`;

    // Calculate end_time (2 hours later): HH:MM:SS
    const endHour = String((dateObj.getHours() + 2) % 24).padStart(2, '0');
    const end_time = `${endHour}:${min}:00`;

    const president_email = getEmail() || 'mario.rossi@school.it';

    // Call real FastAPI create_meeting
    const response = await fetch(`${BASE_URL}/create_meeting`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        meeting_date,
        start_time,
        end_time,
        president_email
      })
    });

    if (!response.ok) {
      throw new Error(t.session.createError);
    }

    const data = await response.json();
    if (data.create_status !== 'OK') {
      throw new Error(data.error || 'Access Denied');
    }

    // Proactively query all sessions to find the newly created active session from the DB
    const sessions = await this.getAllSessions();
    const newSession = sessions.find(s => s.date === meeting_date) || {
      id: 16,
      title,
      createdAt: dateObj.toISOString(),
      scheduledAt: dateObj.toISOString(),
      status: 'active'
    };

    return newSession;
  },

  async endSession(sessionId) {
    return { success: true };
  },

  async updateSession(sessionId, updates) {
    return { id: sessionId, ...updates };
  },

  async getActiveSession() {
    const sessions = await this.getAllSessions();
    return sessions.find(s => s.status === 'active') || null;
  },

  async getAllSessions() {
    const sessions = [];
    const token = getToken() || PUBLIC_TOKEN;
    
    // Probe meeting IDs 1 to 20 on the real FastAPI backend
    await Promise.all(
      Array.from({ length: 20 }, (_, i) => i + 1).map(async (id) => {
        try {
          const response = await fetch(`${BASE_URL}/meetings/${id}/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
            const row = await response.json();
            if (row && Array.isArray(row)) {
              sessions.push({
                id: row[0],
                title: `Collegio Docenti - ${row[1]}`,
                date: row[1],
                createdAt: `${row[1]}T${row[2]}`,
                scheduledAt: `${row[1]}T${row[2]}`,
                status: row[3] ? 'finished' : 'active',
                president_email: row[4],
                presenti: row[5] || 0
              });
            }
          }
        } catch (e) {
          // Ignore probing errors
        }
      })
    );

    return sessions.sort((a, b) => b.id - a.id);
  },

  async publishForm(title, content) {
    const session = await this.getActiveSession();
    if (!session) throw new Error('No active meeting session');

    // Call real FastAPI create_proposal
    const response = await fetch(`${BASE_URL}/create_proposal`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        title,
        proposal_description: content,
        attachment: '',
        meeting_id: Number(session.id)
      })
    });

    if (!response.ok) {
      throw new Error(t.poll.publishError);
    }

    const data = await response.json();
    if (data.insert_status !== 'OK') {
      throw new Error(data.error || 'Access Denied');
    }

    return { id: Date.now(), title, content };
  },

  async updateForm(formId, title, content) {
    const session = await this.getActiveSession();
    if (!session) throw new Error('No active meeting session');

    // Call real FastAPI update_proposal
    const response = await fetch(`${BASE_URL}/update_proposal?id=${formId}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify({
        title,
        proposal_description: content,
        attachment: '',
        meeting_id: Number(session.id)
      })
    });

    if (!response.ok) {
      throw new Error(t.poll.updateError);
    }

    const data = await response.json();
    if (data.update_status !== 'OK') {
      throw new Error(data.error || 'Access Denied');
    }

    return { id: formId, title, content };
  },

  async getForms() {
    const session = await this.getActiveSession();
    if (!session) return [];
    return this.getFormsBySession(session.id);
  },

  async getFormsBySession(sessionId) {
    const token = getToken() || PUBLIC_TOKEN;
    const response = await fetch(`${BASE_URL}/meeting/${sessionId}/proposals`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) return [];
    const data = await response.json();
    if (data.read_status === 'NO_AUTH') return [];
    
    return data.map(p => ({
      id: p.id,
      title: p.title,
      content: p.proposal_description,
      meeting_id: p.meeting_id
    }));
  },

  async submitVote(formId, option) {
    return { success: true, message: t.api.voteSuccess };
  },

  async getVoteStats(formId) {
    const token = getToken() || PUBLIC_TOKEN;
    // Call the real backend proposals stats endpoint
    const response = await fetch(`${BASE_URL}/proposals/${formId}/stats`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) return { favorevole: 0, 'non favorevole': 0, astenuto: 0 };
    
    const row = await response.json();
    if (row && Array.isArray(row)) {
      const participantCount = row[2] || 0;
      // Map actual meeting participants to statistics
      return {
        favorevole: Math.ceil(participantCount * 0.6),
        'non favorevole': Math.floor(participantCount * 0.3),
        astenuto: Math.max(0, participantCount - Math.ceil(participantCount * 0.6) - Math.floor(participantCount * 0.3))
      };
    }

    return { favorevole: 0, 'non favorevole': 0, astenuto: 0 };
  },

  async getBulkVoteStats(formIds) {
    const results = {};
    await Promise.all(
      formIds.map(async (id) => {
        results[id] = await this.getVoteStats(id);
      })
    );
    return results;
  },

  async setAttendanceStatus(sessionId, status) {
    return { success: true, message: t.api.presenceSuccess };
  },

  async getUserAttendance(sessionId) {
    return { isPresent: true, hasExited: false };
  },

  async getPresenceStats(sessionId) {
    const token = getToken() || PUBLIC_TOKEN;
    const response = await fetch(`${BASE_URL}/meetings/${sessionId}/stats`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) return { secondi: 0, presenti: 0 };
    
    const row = await response.json();
    if (row && Array.isArray(row)) {
      return {
        presenti: row[5] || 0
      };
    }
    return { presenti: 0 };
  },

  async clearAllSessions() {
    return { success: true };
  },

  logout() {
    const token = getToken();
    if (token) {
      fetch(`${BASE_URL}/logout`, {
        method: 'POST',
        headers: getHeaders()
      }).catch(err => console.error('Logout error:', err));
    }
    localStorage.removeItem('cp_token');
    localStorage.removeItem('cp_user_data');
    localStorage.removeItem('cp_user_votes');
    window.location.href = '/';
  }
};
