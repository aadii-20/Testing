import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  BookOpen, 
  HelpCircle, 
  Trophy, 
  Activity, 
  MessageSquare, 
  PlayCircle, 
  LogOut, 
  ArrowRight, 
  Book, 
  Flame, 
  Brain, 
  Target, 
  Star, 
  Calculator, 
  Globe, 
  Languages 
} from "lucide-react";

// Assuming these are new imports the user wants to add, but they are not used in the provided snippet.
// import { getStudentStats, getSubjects, createSession } from '../api';

const API_BASE = "http://localhost:9010";
const SUBJECT_CHAPTERS = {
    "Science": 10,
    "Math": 12,
    "English": 9,
    "Social Science": 5,
    "Hindi": 13
};

function StudentDashboard() {
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [activeTab, setActiveTab] = useState('dashboard');
    const [question, setQuestion] = useState("");
    const [chatHistory, setChatHistory] = useState([]);
    const [loadingAI, setLoadingAI] = useState(false);

    // --- NEW QUIZ STATES ---
    const [quizData, setQuizData] = useState([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [quizSettings, setQuizSettings] = useState({
        subject: "Science",
        chapter: "Chapter 1",
        type: "MCQ",
        difficulty: "Medium",
        num_questions: 10
    });
    const [userQuizAnswers, setUserQuizAnswers] = useState({});
    const [isQuizSubmitted, setIsQuizSubmitted] = useState(false);
    const [quizScore, setQuizScore] = useState(null);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = '/';
            return;
        }

        // Fetching stats from backend
        // Use full URL or rely on proxy/CORS. Fixed in previous steps to allow 9010.
        axios.get(`${API_BASE}/student/stats`, {
            headers: { Authorization: `Bearer ${token}` }
        })
            .then(res => setData(res.data))
            .catch(err => {
                console.error("Error loading stats", err);
                if (err.response?.status === 401) {
                    localStorage.clear();
                    window.location.href = '/';
                }
            });
    }, []);

    const handleAskAI = async () => {
        if (!question.trim()) return;
        const userMsg = { role: 'user', text: question };
        setChatHistory(prev => [...prev, userMsg]);
        setLoadingAI(true);

        try {
            const token = localStorage.getItem('token');
            const res = await axios.post(`${API_BASE}/student/ask-ai-doubt`,
                { question },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setChatHistory(prev => [...prev, { role: 'ai', text: res.data.answer }]);
            setQuestion("");
        } catch (err) {
            setChatHistory(prev => [...prev, { role: 'ai', text: "AI is offline. Please try again later." }]);
        } finally {
            setLoadingAI(false);
        }
    };

    const handleGenerateQuiz = async () => {
        setIsGenerating(true);
        setQuizData([]);
        setIsQuizSubmitted(false);
        setUserQuizAnswers({});
        setQuizScore(null);

        try {
            const res = await axios.post(`${API_BASE}/generate-quiz`, quizSettings);
            setQuizData(res.data);
        } catch (err) {
            alert("Quiz generation failed! Check if backend is running and PDF exists.");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSubmitQuiz = async () => {
        let correctScores = 0;
        quizData.forEach((q, idx) => {
            const userAnswer = userQuizAnswers[idx]?.toString().trim().toLowerCase() || "";
            const correctAnswer = q.answer?.toString().trim().toLowerCase() || "";

            if (userAnswer === correctAnswer) {
                correctScores += 1;
            } else if (userAnswer !== "" && correctAnswer.includes(userAnswer)) {
                correctScores += 1;
            } else if (userAnswer !== "" && userAnswer.includes(correctAnswer)) {
                correctScores += 1;
            }
        });

        setQuizScore({ score: correctScores, total: quizData.length });
        setIsQuizSubmitted(true);

        try {
            const token = localStorage.getItem('token');
            await axios.post(`${API_BASE}/student/submit-quiz`, {
                score: correctScores,
                total: quizData.length,
                subject: quizSettings.subject
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            const res = await axios.get(`${API_BASE}/student/stats`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setData(res.data);
        } catch (err) {
            console.error("Failed to sync score to dashboard", err);
        }
    };

    if (!data) return (
        <div className="app-container" style={{ justifyContent: 'center', alignItems: 'center' }}>
            <h2 style={{ color: 'var(--accent-blue)' }}>Syncing AI Data...</h2>
        </div>
    );

    return (
        <div className="app-container">
            {/* Sidebar - Reusing styles from main Sidebar */}
            <nav className="sidebar">
                <h2 className="dashboard-nav-logo">CORE<span style={{ color: '#fff' }}>AI</span></h2>
                <ul style={{ listStyle: 'none', padding: 0, flex: 1 }}>
                    <li
                        className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
                        onClick={() => setActiveTab('dashboard')}
                    >
                        Dashboard
                    </li>
                    <li
                        className="nav-item"
                        onClick={() => navigate('/chat')}
                    >
                        Ask Doubts
                    </li>
                    <li
                        className={`nav-item ${activeTab === 'quizzes' ? 'active' : ''}`}
                        onClick={() => setActiveTab('quizzes')}
                    >
                        Quizzes
                    </li>
                    <li
                        className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
                        onClick={() => setActiveTab('settings')}
                    >
                        Settings
                    </li>
                </ul>
                {isQuizSubmitted && quizScore && (
                    <div style={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        padding: '15px',
                        borderRadius: '12px',
                        marginBottom: '15px',
                        textAlign: 'center',
                        color: '#bae6fd'
                    }}>
                        <h4 style={{ margin: 0, fontSize: '0.9rem', color: '#94a3b8', letterSpacing: '0.5px' }}>RECENT SCORE</h4>
                        <div style={{ fontSize: '2.5rem', fontWeight: 'bold', margin: '10px 0', color: '#38bdf8' }}>
                            {quizScore.score} <span style={{ fontSize: '1.2rem', color: '#64748b' }}>/ {quizScore.total}</span>
                        </div>
                        <div style={{
                            fontSize: '0.8rem',
                            padding: '4px 10px',
                            backgroundColor: '#38bdf820',
                            display: 'inline-block',
                            borderRadius: '12px'
                        }}>
                            {Math.round((quizScore.score / quizScore.total) * 100)}% Accuracy
                        </div>
                    </div>
                )}
                <button onClick={() => { localStorage.clear(); window.location.href = '/'; }} className="logout-btn">Logout</button>
            </nav>

            {/* Main Content */}
            <main className="dashboard-main">
                <header className="dashboard-header">
                    <h1 style={{ color: '#fff', fontSize: '2rem' }}>
                        {activeTab === 'dashboard' && "Welcome back, "}
                        {activeTab === 'doubts' && "Instant "}
                        {activeTab === 'quizzes' && "Active "}
                        {activeTab === 'settings' && "Account "}
                        <span style={{ color: 'var(--accent-blue)' }}>
                            {activeTab === 'dashboard' ? data.student_name : activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
                        </span>
                    </h1>
                </header>

                {/* DASHBOARD VIEW */}
                {activeTab === 'dashboard' && (
                    <>
                        <div className="stat-card-row">
                            <div className="stat-card">
                                <h3 className="stat-label">ACCURACY</h3>
                                <p className="stat-value">{data.accuracy}%</p>
                                <div className="progress-track">
                                    <div className="progress-fill" style={{ width: `${data.accuracy}%` }}></div>
                                </div>
                            </div>
                            <div className="stat-card">
                                <h3 className="stat-label">CHAPTERS</h3>
                                <p className="stat-value">{data.chapters}</p>
                            </div>
                        </div>
                        <div className="dashboard-grid">
                            <div className="section-card">
                                <h3 style={{ marginBottom: '20px', color: 'var(--accent-blue)' }}>Subject Mastery</h3>
                                {data.subjects && data.subjects.map((sub, i) => (
                                    <div key={i} style={{ marginBottom: '20px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                                            <span>{sub.name}</span><span>{sub.progress}%</span>
                                        </div>
                                        <div className="progress-track" style={{ height: '6px', backgroundColor: '#0f172a' }}>
                                            <div className="progress-fill" style={{ width: `${sub.progress}%`, boxShadow: '0 0 10px rgba(56, 189, 248, 0.3)' }}></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <div className="section-card">
                                <h3 style={{ marginBottom: '20px', color: 'var(--accent-blue)' }}>Recent Logs</h3>
                                {data.recent_activity && data.recent_activity.length > 0 ? (
                                    data.recent_activity.map((act, i) => (
                                        <div key={i} className="activity-item">
                                            <p className="activity-task">{act.task}</p>
                                        </div>
                                    ))
                                ) : (
                                    <p style={{ color: 'var(--text-secondary)' }}>No recent activity found.</p>
                                )}
                            </div>
                        </div>
                    </>
                )}

                {/*DOUBT VIEW (Fallback/Mini if needed, though button goes to /chat now)*/}
                {activeTab === 'doubts' && (
                    <div className="section-card">
                        <h3 style={{ color: 'var(--accent-blue)', marginBottom: '15px' }}>Instant Chapter Help</h3>
                        {/* Reusing Styles similar to chat for consistency */}
                        <div style={{ height: '300px', overflowY: 'auto', backgroundColor: '#0f172a', borderRadius: '15px', padding: '20px', border: '1px solid var(--border-color)', marginBottom: '20px' }}>
                            {chatHistory.map((msg, i) => (
                                <div key={i} className={`message-row ${msg.role}`} style={{ marginBottom: '10px' }}>
                                    <div className="message-content" style={{
                                        backgroundColor: msg.role === 'user' ? 'var(--user-bubble)' : 'transparent',
                                        padding: msg.role === 'user' ? '10px 15px' : '0',
                                        borderRadius: '10px'
                                    }}>
                                        <strong>{msg.role === 'user' ? "You: " : "🤖 AI: "}</strong> {msg.text}
                                    </div>
                                </div>
                            ))}
                            {loadingAI && <div style={{ color: 'var(--text-secondary)' }}><strong>🤖 AI: </strong> Thinking...</div>}
                        </div>
                        <div className="input-container">
                            <input
                                className="chat-input"
                                placeholder="Ask a question..."
                                value={question}
                                onChange={(e) => setQuestion(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleAskAI()}
                            />
                            <button className="send-btn" onClick={handleAskAI} disabled={loadingAI}>
                                <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                                </svg>
                            </button>
                        </div>
                    </div>
                )}

                {/* QUIZZES VIEW (INTEGRATED) */}
                {activeTab === 'quizzes' && (
                    <div style={styles.sectionCard}>
                        <h3 style={{ color: '#38bdf8', marginBottom: '20px' }}>AI Quiz Master</h3>

                        {/* Config Panel */}
                        <div style={{ display: 'flex', gap: '15px', marginBottom: '30px', flexWrap: 'wrap' }}>
                            <select style={styles.selectInput} value={quizSettings.subject} onChange={(e) => setQuizSettings({ ...quizSettings, subject: e.target.value, chapter: "Chapter 1" })}>
                                {Object.keys(SUBJECT_CHAPTERS).map((subj) => (
                                    <option key={subj} value={subj}>{subj}</option>
                                ))}
                            </select>


                            <select style={styles.selectInput} value={quizSettings.chapter.replace('Chapter ', '')} onChange={(e) => setQuizSettings({ ...quizSettings, chapter: `Chapter ${e.target.value}` })}>
                                {[...Array(SUBJECT_CHAPTERS[quizSettings.subject] || 10)].map((_, i) => <option key={i + 1} value={i + 1}>Chapter {i + 1}</option>)}
                            </select>

                            <select style={styles.selectInput} onChange={(e) => setQuizSettings({ ...quizSettings, type: e.target.value })}>
                                <option value="MCQ">MCQ</option>
                                <option value="Fill in blanks">Fill in Blanks</option>
                                <option value="Short Answer">Short Answer</option>
                                <option value="Long Answer">Long Answer</option>
                            </select>

                            <select style={styles.selectInput} value={quizSettings.num_questions} onChange={(e) => setQuizSettings({ ...quizSettings, num_questions: parseInt(e.target.value) })}>
                                {[...Array(15)].map((_, i) => <option key={i + 1} value={i + 1}>{i + 1} Questions</option>)}
                            </select>

                            <button style={{ ...styles.aiBtnSmall, height: '45px' }} onClick={handleGenerateQuiz} disabled={isGenerating}>
                                {isGenerating ? "Processing..." : "🚀 Generate Quiz"}
                            </button>
                        </div>

                        {/* Quiz Display Area */}
                        <div style={styles.quizScrollArea}>
                            {quizData.map((q, idx) => (
                                <div key={idx} style={styles.questionContainer}>
                                    <p style={{ fontWeight: 'bold', color: '#fff' }}>Q{idx + 1}: {q.question}</p>

                                    {quizSettings.type === "MCQ" && q.options ? (
                                        <div style={{ marginTop: '10px' }}>
                                            {q.options.map((opt, oIdx) => (
                                                <label key={oIdx} style={styles.optionLabel}>
                                                    <input
                                                        type="radio"
                                                        name={`q${idx}`}
                                                        disabled={isQuizSubmitted}
                                                        onChange={() => setUserQuizAnswers({ ...userQuizAnswers, [idx]: opt[0] })}
                                                    /> {opt}
                                                </label>
                                            ))}
                                        </div>
                                    ) : quizSettings.type === "Fill in blanks" ? (
                                        <input
                                            style={{ ...styles.input, marginTop: '10px', width: '100%', boxSizing: 'border-box' }}
                                            placeholder="Your answer..."
                                            disabled={isQuizSubmitted}
                                            onChange={(e) => setUserQuizAnswers({ ...userQuizAnswers, [idx]: e.target.value })}
                                        />
                                    ) : (
                                        <textarea
                                            style={{ ...styles.input, marginTop: '10px', width: '100%', boxSizing: 'border-box', minHeight: '80px', borderRadius: '12px', resize: 'vertical' }}
                                            placeholder="Type your answer here..."
                                            disabled={isQuizSubmitted}
                                            onChange={(e) => setUserQuizAnswers({ ...userQuizAnswers, [idx]: e.target.value })}
                                        />
                                    )}

                                    {isQuizSubmitted && (
                                        <div style={{ ...styles.explanationBox, borderLeftColor: (userQuizAnswers[idx]?.toString().toUpperCase() === q.answer?.toString().toUpperCase()) ? '#10b981' : '#f87171' }}>
                                            <p><strong>Correct Answer:</strong> {q.answer}</p>
                                            <p style={{ fontSize: '0.9rem', color: '#94a3b8' }}>💡 {q.explanation}</p>
                                        </div>
                                    )}
                                </div>
                            ))}

                            {quizData.length > 0 && !isQuizSubmitted && (
                                <button style={{ ...styles.aiBtnSmall, width: '100%', marginTop: '20px', height: '45px' }} onClick={handleSubmitQuiz}>
                                    ✅ Submit Quiz
                                </button>
                            )}
                        </div>
                    </div>
                )}

                {/* SETTINGS VIEW */}
                {activeTab === 'settings' && (
                    <div className="section-card">
                        <h3 style={{ color: 'var(--accent-blue)', marginBottom: '20px' }}>Preferences</h3>
                        <div className="activity-item">
                            <p className="activity-task">Account Type</p>
                            <span className="activity-date">Student Profile</span>
                        </div>
                        <div className="activity-item">
                            <p className="activity-task">Dark Mode</p>
                            <span className="activity-date">Always On</span>
                        </div>
                        <button className="logout-btn" style={{ width: '200px', marginTop: '20px' }}>Reset AI Model</button>
                    </div>
                )}
            </main>
        </div>
    );
}

const styles = {
    dashboard: {
        display: 'flex',
        height: '100vh',
        backgroundColor: '#131314',
        color: '#e3e3e3',
        fontFamily: "'Google Sans', sans-serif",
    },
    sidebar: {
        width: '300px',
        backgroundColor: '#1e1f20',
        padding: '2rem 1.5rem',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid #444746',
    },
    logo: {
        fontSize: '1.8rem',
        fontWeight: 'bold',
        color: '#8ab4f8',
        marginBottom: '2rem',
        letterSpacing: '1px',
    },
    navList: {
        listStyle: 'none',
        flex: 1,
    },
    navItem: {
        padding: '12px 16px',
        borderRadius: '12px',
        cursor: 'pointer',
        color: '#c4c7c5',
        marginBottom: '8px',
        transition: '0.2s',
    },
    activeNavItem: {
        padding: '12px 16px',
        borderRadius: '12px',
        cursor: 'pointer',
        marginBottom: '8px',
        backgroundColor: '#004a77',
        color: '#c2e7ff',
        fontWeight: 'bold',
    },
    mainContent: {
        flex: 1,
        padding: '40px',
        overflowY: 'auto',
    },
    header: {
        marginBottom: '30px',
    },
    nameHighlight: {
        color: '#8ab4f8',
    },
    topRow: {
        display: 'flex',
        gap: '20px',
        marginBottom: '30px',
    },
    statCard: {
        flex: 1,
        backgroundColor: '#1e1f20',
        padding: '25px',
        borderRadius: '20px',
        border: '1px solid #444746',
    },
    cardTitle: {
        fontSize: '0.8rem',
        color: '#c4c7c5',
        letterSpacing: '1px',
    },
    statValue: {
        fontSize: '2.5rem',
        fontWeight: 'bold',
        margin: '10px 0',
    },
    grid: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '25px',
    },
    sectionCard: {
        backgroundColor: '#1e1f20',
        padding: '25px',
        borderRadius: '20px',
        border: '1px solid #444746',
    },
    miniBar: {
        height: '6px',
        backgroundColor: '#334155',
        borderRadius: '3px',
        marginTop: '10px',
    },
    miniFill: {
        height: '100%',
        backgroundColor: '#8ab4f8',
        borderRadius: '3px',
    },
    subProgress: {
        marginBottom: '15px',
    },
    subLabel: {
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: '5px',
        fontSize: '0.9rem',
    },
    progressContainer: {
        height: '8px',
        backgroundColor: '#334155',
        borderRadius: '4px',
    },
    progressLine: {
        height: '100%',
        backgroundColor: '#8ab4f8',
        borderRadius: '4px',
    },
    chatWindow: {
        height: '300px',
        overflowY: 'auto',
        padding: '15px',
        backgroundColor: '#131314',
        borderRadius: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
    },
    userMsg: {
        alignSelf: 'flex-end',
        backgroundColor: '#282a2c',
        padding: '10px 15px',
        borderRadius: '15px 15px 2px 15px',
        maxWidth: '80%',
    },
    aiMsg: {
        alignSelf: 'flex-start',
        padding: '10px 15px',
        color: '#e3e3e3',
        maxWidth: '80%',
    },
    input: {
        flex: 1,
        padding: '12px 18px',
        borderRadius: '25px',
        border: '1px solid #444746',
        backgroundColor: '#1e1f20',
        color: '#fff',
        outline: 'none',
    },
    selectInput: {
        padding: '10px',
        borderRadius: '8px',
        backgroundColor: '#1e1f20',
        color: '#fff',
        border: '1px solid #444746',
    },
    aiBtnSmall: {
        padding: '0 20px',
        borderRadius: '25px',
        backgroundColor: '#8ab4f8',
        color: '#0b2245',
        border: 'none',
        fontWeight: 'bold',
        cursor: 'pointer',
    },
    logoutBtn: {
        padding: '12px',
        borderRadius: '10px',
        border: '1px solid #444746',
        backgroundColor: 'transparent',
        color: '#c4c7c5',
        cursor: 'pointer',
        marginTop: '20px'
    },
    quizScrollArea: {
        marginTop: '20px',
        maxHeight: '500px',
        overflowY: 'auto'
    },
    questionContainer: {
        padding: '15px',
        borderBottom: '1px solid #444746',
        marginBottom: '15px'
    },
    optionLabel: {
        display: 'block',
        padding: '8px',
        cursor: 'pointer',
        color: '#c4c7c5'
    },
    explanationBox: {
        marginTop: '15px',
        padding: '10px',
        backgroundColor: '#2d2e2f',
        borderLeft: '4px solid',
        borderRadius: '4px'
    }
};
export default StudentDashboard;