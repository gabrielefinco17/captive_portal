/**
 * Mock API Service
 */
import t from '../i18n/IT.json';

const STORAGE_KEYS = {
  TOKEN: 'cp_token',
  USER_DATA: 'cp_user_data',
  SESSION: 'cp_active_session',
  SESSIONS_LIST: 'cp_sessions_list',
  FORMS: 'cp_published_forms',
  VOTES: 'cp_all_votes',
  ATTENDANCE: 'cp_attendance',
};

const delay = (ms = 800) => new Promise(resolve => setTimeout(resolve, ms));

const sanitizeToken = (token) => {
  if (!token) return '';
  return token.toString().replace(/['"%;()=<>]/g, '').trim();
};

export const mockApi = {
  async login(rawToken) {
    await delay();
    const token = sanitizeToken(rawToken);
    if (!token) throw new Error(t.api.tokenRequired);

    let userData = null;
    if (token.includes('admin')) {
      userData = { token, role: 'super_user', email: 'admin@captiveportal.it' };
    } else if (token.length > 3) {
      userData = { token, role: 'user', email: `utente_${token.slice(0, 4)}@guest.it` };
    }

    if (userData) {
      localStorage.setItem(STORAGE_KEYS.TOKEN, token);
      localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
      return userData;
    } else {
      throw new Error(t.api.tokenInvalid);
    }
  },

  async createSession(title, scheduledDate = null) {
    await delay();
    const now = new Date();
    const scheduled = scheduledDate ? new Date(scheduledDate) : now;
    const isActive = scheduled <= now;

    const session = {
      id: Date.now(),
      title,
      createdAt: now.toISOString(),
      scheduledAt: scheduled.toISOString(),
      status: isActive ? 'active' : 'scheduled',
      forms: [],
    };

    // If it's active, set as current session
    if (isActive) {
      localStorage.setItem(STORAGE_KEYS.SESSION, JSON.stringify(session));
      localStorage.setItem(STORAGE_KEYS.FORMS, JSON.stringify([]));
    }

    // Add to the sessions list
    const allSessions = JSON.parse(localStorage.getItem(STORAGE_KEYS.SESSIONS_LIST) || '[]');
    allSessions.unshift(session);
    localStorage.setItem(STORAGE_KEYS.SESSIONS_LIST, JSON.stringify(allSessions));

    return session;
  },

  async endSession(sessionId) {
    await delay();
    const allSessions = JSON.parse(localStorage.getItem(STORAGE_KEYS.SESSIONS_LIST) || '[]');
    const idx = allSessions.findIndex(s => s.id === sessionId);
    if (idx !== -1) {
      allSessions[idx].status = 'finished';
      localStorage.setItem(STORAGE_KEYS.SESSIONS_LIST, JSON.stringify(allSessions));
    }

    const activeSession = JSON.parse(localStorage.getItem(STORAGE_KEYS.SESSION));
    if (activeSession && activeSession.id === sessionId) {
      localStorage.removeItem(STORAGE_KEYS.SESSION);
      localStorage.removeItem(STORAGE_KEYS.FORMS);
    }
    return { success: true };
  },

  async updateSession(sessionId, updates) {
    await delay();
    const allSessions = JSON.parse(localStorage.getItem(STORAGE_KEYS.SESSIONS_LIST) || '[]');
    const idx = allSessions.findIndex(s => s.id === sessionId);
    if (idx === -1) throw new Error('Session not found');

    if (allSessions[idx].status === 'finished') {
      throw new Error('Cannot modify a finished session');
    }

    allSessions[idx] = { ...allSessions[idx], ...updates };
    localStorage.setItem(STORAGE_KEYS.SESSIONS_LIST, JSON.stringify(allSessions));

    // Update active session if it's the same one
    const activeSession = JSON.parse(localStorage.getItem(STORAGE_KEYS.SESSION));
    if (activeSession && activeSession.id === sessionId) {
      localStorage.setItem(STORAGE_KEYS.SESSION, JSON.stringify(allSessions[idx]));
    }

    return allSessions[idx];
  },

  async getActiveSession() {
    await delay(300);
    const session = localStorage.getItem(STORAGE_KEYS.SESSION);
    return session ? JSON.parse(session) : null;
  },

  /**
   * Get all sessions (for the public dashboard dropdown)
   */
  async getAllSessions() {
    await delay(300);
    const sessions = localStorage.getItem(STORAGE_KEYS.SESSIONS_LIST);
    return sessions ? JSON.parse(sessions) : [];
  },

  async publishForm(title, content) {
    await delay();
    const newForm = {
      id: Date.now(),
      title,
      content,
      publishedAt: new Date().toISOString(),
    };

    // Add to current session forms
    const existingForms = JSON.parse(localStorage.getItem(STORAGE_KEYS.FORMS) || '[]');
    const updatedForms = [newForm, ...existingForms];
    localStorage.setItem(STORAGE_KEYS.FORMS, JSON.stringify(updatedForms));

    // Also update the session in the sessions list
    const session = JSON.parse(localStorage.getItem(STORAGE_KEYS.SESSION));
    if (session) {
      const allSessions = JSON.parse(localStorage.getItem(STORAGE_KEYS.SESSIONS_LIST) || '[]');
      const idx = allSessions.findIndex(s => s.id === session.id);
      if (idx !== -1) {
        allSessions[idx].forms = updatedForms;
        localStorage.setItem(STORAGE_KEYS.SESSIONS_LIST, JSON.stringify(allSessions));
      }
    }

    return newForm;
  },

  async updateForm(formId, title, content) {
    await delay();
    
    // Update current session forms
    const existingForms = JSON.parse(localStorage.getItem(STORAGE_KEYS.FORMS) || '[]');
    const formIdx = existingForms.findIndex(f => f.id === formId);
    if (formIdx === -1) throw new Error('Form not found');
    
    existingForms[formIdx] = { 
      ...existingForms[formIdx], 
      title, 
      content,
      updatedAt: new Date().toISOString()
    };
    
    localStorage.setItem(STORAGE_KEYS.FORMS, JSON.stringify(existingForms));

    // Also update the session in the sessions list
    const session = JSON.parse(localStorage.getItem(STORAGE_KEYS.SESSION));
    if (session) {
      const allSessions = JSON.parse(localStorage.getItem(STORAGE_KEYS.SESSIONS_LIST) || '[]');
      const idx = allSessions.findIndex(s => s.id === session.id);
      if (idx !== -1) {
        allSessions[idx].forms = existingForms;
        localStorage.setItem(STORAGE_KEYS.SESSIONS_LIST, JSON.stringify(allSessions));
      }
    }

    return existingForms[formIdx];
  },

  async getForms() {
    await delay(300);
    const forms = localStorage.getItem(STORAGE_KEYS.FORMS);
    return forms ? JSON.parse(forms) : [];
  },

  /**
   * Get forms for a specific session (for public dashboard)
   */
  async getFormsBySession(sessionId) {
    await delay(300);
    const allSessions = JSON.parse(localStorage.getItem(STORAGE_KEYS.SESSIONS_LIST) || '[]');
    const session = allSessions.find(s => s.id === sessionId);
    return session ? (session.forms || []) : [];
  },

  async submitVote(formId, option) {
    await delay(500);
    // Store vote in aggregated stats
    const allVotes = JSON.parse(localStorage.getItem(STORAGE_KEYS.VOTES) || '{}');
    if (!allVotes[formId]) {
      allVotes[formId] = { favorevole: 0, 'non favorevole': 0, astenuto: 0 };
    }
    allVotes[formId][option] = (allVotes[formId][option] || 0) + 1;
    localStorage.setItem(STORAGE_KEYS.VOTES, JSON.stringify(allVotes));

    return { success: true, message: t.api.voteSuccess };
  },

  /**
   * Get vote stats for a specific form (public dashboard)
   */
  async getVoteStats(formId) {
    await delay(100);
    const allVotes = JSON.parse(localStorage.getItem(STORAGE_KEYS.VOTES) || '{}');
    return allVotes[formId] || { favorevole: 0, 'non favorevole': 0, astenuto: 0 };
  },

  /**
   * Get vote stats for multiple forms at once
   */
  async getBulkVoteStats(formIds) {
    await delay(200);
    const allVotes = JSON.parse(localStorage.getItem(STORAGE_KEYS.VOTES) || '{}');
    const result = {};
    formIds.forEach(id => {
      result[id] = allVotes[id] || { favorevole: 0, 'non favorevole': 0, astenuto: 0 };
    });
    return result;
  },

  /**
   * Mark attendance status for the current user in a session
   */
  async setAttendanceStatus(sessionId, status) {
    await delay(300);
    const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
    if (!token) throw new Error(t.api.tokenRequired);

    const attendance = JSON.parse(localStorage.getItem(STORAGE_KEYS.ATTENDANCE) || '{}');
    if (!attendance[sessionId]) {
      attendance[sessionId] = { present: [], exited: [] };
    } else if (Array.isArray(attendance[sessionId])) {
      // Migrate old array format to object format
      attendance[sessionId] = { present: attendance[sessionId], exited: [] };
    }

    if (status === 'present') {
      if (!attendance[sessionId].present.includes(token)) {
        attendance[sessionId].present.push(token);
      }
    } else if (status === 'exited') {
      if (!attendance[sessionId].exited.includes(token)) {
        attendance[sessionId].exited.push(token);
      }
    }

    localStorage.setItem(STORAGE_KEYS.ATTENDANCE, JSON.stringify(attendance));
    return { success: true, message: t.api.presenceSuccess };
  },

  /**
   * Check if current user is present
   */
  async getUserAttendance(sessionId) {
    await delay(100);
    const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
    let sessionAtt = JSON.parse(localStorage.getItem(STORAGE_KEYS.ATTENDANCE) || '{}')[sessionId];
    
    if (!sessionAtt) return { isPresent: false, hasExited: false };
    if (Array.isArray(sessionAtt)) {
      sessionAtt = { present: sessionAtt, exited: [] };
    }

    return {
      isPresent: sessionAtt.present.includes(token),
      hasExited: sessionAtt.exited.includes(token)
    };
  },

  /**
   * Get total present count for a session (people who marked present but haven't marked exited)
   */
  async getPresenceStats(sessionId) {
    await delay(100);
    let sessionAtt = JSON.parse(localStorage.getItem(STORAGE_KEYS.ATTENDANCE) || '{}')[sessionId];
    if (!sessionAtt) return { presenti: 0 };
    if (Array.isArray(sessionAtt)) {
      return { presenti: sessionAtt.length };
    }
    
    // Total number of unique people who have marked presence at any point
    return {
      presenti: sessionAtt.present.length
    };
  },

  async clearAllSessions() {
    await delay(500);
    localStorage.removeItem(STORAGE_KEYS.SESSION);
    localStorage.removeItem(STORAGE_KEYS.SESSIONS_LIST);
    localStorage.removeItem(STORAGE_KEYS.FORMS);
    localStorage.removeItem(STORAGE_KEYS.VOTES);
    localStorage.removeItem(STORAGE_KEYS.ATTENDANCE);
    return { success: true };
  },

  logout() {
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER_DATA);
    window.location.href = '/';
  }
};
