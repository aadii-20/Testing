
// import axios from 'axios';

// const API_BASE = "http://localhost:8000";

// export const loginUser = (credentials) => {
//     return axios.post(`${API_BASE}/login`, credentials);
// };

// export const getStudentStats = (token) => {
//     return axios.get(`${API_BASE}/student/stats`, {
//         params: { token: token }
//     });
// };

// export const getTeacherAnalytics = (token) => {
//     return axios.get(`${API_BASE}/teacher/analytics`, {
//         params: { token: token }
//     });
// };

import axios from 'axios';

const API_BASE = "http://localhost:9010";


export const loginUser = (credentials) => {
    return axios.post(`${API_BASE}/login`, credentials);
};

export const registerUser = (userData) => {
    return axios.post(`${API_BASE}/signup`, userData);
};


export const getStudentStats = (token) => {
    return axios.get(`${API_BASE}/student/stats`, {
        params: { token: token }
    });
};

export const askAIDoubt = (questionData) => {
    return axios.post(`${API_BASE}/student/ask-ai-doubt`, questionData);
};


export const getTeacherAnalytics = (token) => {
    return axios.get(`${API_BASE}/teacher/analytics`, {
        params: { token: token }
    });
};

// --- Chat API ---

export const getSubjects = async (token, standard = null) => {
    const params = { token };
    if (standard) params.standard = standard;
    const response = await axios.get(`${API_BASE}/subjects`, {
        params,
        headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
};

export const createSession = async (token, subject, chapter, language, standard = null) => {
    const payload = { subject, chapter, language };
    if (standard) payload.standard = standard;
    const response = await axios.post(`${API_BASE}/sessions`,
        payload,
        { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
};

export const getSessions = async (token) => {
    const response = await axios.get(`${API_BASE}/sessions`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
};

export const getSession = async (token, sessionId) => {
    const response = await axios.get(`${API_BASE}/sessions/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
};

export const sendMessageToSession = async (token, sessionId, content) => {
    const response = await axios.post(`${API_BASE}/sessions/${sessionId}/message`,
        { role: 'user', content },
        { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data;
};