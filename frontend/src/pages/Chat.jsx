import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { useNavigate } from 'react-router-dom';
import {
    getSessions,
    createSession,
    getSession,
    sendMessageToSession,
    getSubjects
} from '../api';
import Sidebar from './Sidebar';
import ChatConfig from './ChatConfig';

export default function ChatScreen() {
    const navigate = useNavigate();
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role') || 'student';
    const [selectedStandard, setSelectedStandard] = useState(role === 'teacher' ? '8' : '');

    // Data State
    const [subjects, setSubjects] = useState([]);
    const [loadingSubjects, setLoadingSubjects] = useState(false);

    // Chat State
    const [sessions, setSessions] = useState([]);
    const [currentSessionId, setCurrentSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [sessionLanguage, setSessionLanguage] = useState('English'); // Track selected language

    // UI State
    const [input, setInput] = useState('');
    const [sending, setSending] = useState(false);
    const [loadingSession, setLoadingSession] = useState(false);
    const [error, setError] = useState('');

    // TTS State
    const [speakingIdx, setSpeakingIdx] = useState(null);

    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);

    // Initial Load
    useEffect(() => {
        if (!token) {
            navigate('/');
            return;
        }
        loadData();
    }, [token]);

    // Stop speech when session changes
    useEffect(() => {
        window.speechSynthesis?.cancel();
        setSpeakingIdx(null);
    }, [currentSessionId]);

    const loadData = async (stdToLoad = null) => {
        const std = stdToLoad || selectedStandard;
        setLoadingSubjects(true);
        try {
            const subs = await getSubjects(token, std);
            setSubjects(subs);

            const hist = await getSessions(token);
            setSessions(hist);
        } catch (err) {
            console.error("Failed to load data", err);
            if (err.response && err.response.status === 401) {
                navigate('/');
            }
        } finally {
            setLoadingSubjects(false);
        }
    };

    // Auto-scroll
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, sending]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
        }
    }, [input]);

    // --- TTS Handler ---
    const handleSpeak = (text, idx) => {
        if (!window.speechSynthesis) return;

        // If already speaking this message, stop it
        if (speakingIdx === idx) {
            window.speechSynthesis.cancel();
            setSpeakingIdx(null);
            return;
        }

        // Stop any ongoing speech
        window.speechSynthesis.cancel();

        // Strip markdown syntax for cleaner speech
        const plainText = text
            .replace(/#{1,6}\s/g, '')
            .replace(/\*\*(.+?)\*\*/g, '$1')
            .replace(/\*(.+?)\*/g, '$1')
            .replace(/`(.+?)`/g, '$1')
            .replace(/\[(.+?)\]\(.+?\)/g, '$1')
            .replace(/^\s*[-*+]\s/gm, '')
            .replace(/\n+/g, '. ');

        const utterance = new SpeechSynthesisUtterance(plainText);

        // Use the session's selected language for correct pronunciation
        utterance.lang = sessionLanguage.toLowerCase() === 'hindi' ? 'hi-IN' : 'en-IN';
        utterance.rate = 0.95;
        utterance.pitch = 1;

        utterance.onend = () => setSpeakingIdx(null);
        utterance.onerror = () => setSpeakingIdx(null);

        setSpeakingIdx(idx);
        window.speechSynthesis.speak(utterance);
    };

    const handleSelectSession = async (id) => {
        if (!token) return;
        setCurrentSessionId(id);
        setLoadingSession(true);
        setError('');
        try {
            const sessionData = await getSession(token, id);
            setMessages(sessionData.messages || []);
            // Restore language from session data if available
            if (sessionData.language) {
                setSessionLanguage(sessionData.language);
            }
        } catch (err) {
            console.error(err);
            setError("Failed to load chat session.");
        } finally {
            setLoadingSession(false);
        }
    };

    const handleNewChat = () => {
        window.speechSynthesis?.cancel();
        setSpeakingIdx(null);
        setCurrentSessionId(null);
        setMessages([]);
        setInput('');
        setError('');
        setSessionLanguage('English');
    };

    const handleStartChat = async (subject, chapter, language) => {
        if (!token) return;
        setLoadingSession(true);
        setSessionLanguage(language); // Store the chosen language
        try {
            const newSession = await createSession(token, subject, chapter, language, selectedStandard);
            setSessions(prev => [newSession, ...prev]);
            setCurrentSessionId(newSession.id);
            setMessages([]);
        } catch (err) {
            console.error(err);
            setError("Failed to create new session.");
        } finally {
            setLoadingSession(false);
        }
    };

    const handleSend = async (e) => {
        e?.preventDefault();
        if (!input.trim() || !currentSessionId || !token || sending) return;

        const originalInput = input;
        setInput('');
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
        setError('');

        // Optimistic update
        const tempMsg = {
            id: Date.now(),
            role: 'user',
            content: originalInput,
            created_at: new Date().toISOString()
        };
        setMessages(prev => [...prev, tempMsg]);
        setSending(true);

        try {
            const response = await sendMessageToSession(token, currentSessionId, originalInput);

            const aiMsg = {
                id: Date.now() + 1,
                role: 'assistant',
                content: response.answer,
                created_at: new Date().toISOString()
            };
            setMessages(prev => [...prev, aiMsg]);
        } catch (err) {
            console.error(err);
            setError("Failed to send message.");
        } finally {
            setSending(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleLogout = () => {
        window.speechSynthesis?.cancel();
        localStorage.removeItem('token');
        navigate('/');
    };

    return (
        <div className="app-container">
            <Sidebar
                sessions={sessions}
                currentSessionId={currentSessionId}
                onSelectSession={handleSelectSession}
                onNewChat={handleNewChat}
                onLogout={handleLogout}
            />

            <div className="chat-main">
                <button
                    onClick={() => navigate(-1)}
                    className="back-dashboard-btn"
                >
                    Back to Dashboard
                </button>

                {!currentSessionId ? (
                    <ChatConfig
                        subjects={subjects}
                        loading={loadingSubjects || loadingSession}
                        onStartChat={handleStartChat}
                        role={role}
                        selectedStandard={selectedStandard}
                        onStandardChange={(newStd) => {
                            setSelectedStandard(newStd);
                            loadData(newStd);
                        }}
                    />
                ) : (
                    <>
                        <div className="chat-scroll-area">
                            <div className="chat-content-width">
                                {loadingSession && <p style={{ textAlign: 'center', color: '#888' }}>Loading conversation...</p>}

                                {messages.map((msg, idx) => (
                                    <div key={idx} className={`message-row ${msg.role}`}>
                                        {msg.role === 'assistant' && (
                                            <div className="avatar">
                                                <svg width="100%" height="100%" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ padding: '6px' }}>
                                                    <path d="M12 4L14.4 9.6L20 12L14.4 14.4L12 20L9.6 14.4L4 12L9.6 9.6L12 4Z" fill="white" stroke="white" strokeWidth="2" strokeLinejoin="round" />
                                                </svg>
                                            </div>
                                        )}
                                        <div className="message-bubble-wrapper">
                                            <div className="message-content markdown-body">
                                                {msg.role === 'assistant' ? (
                                                    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>{msg.content}</ReactMarkdown>
                                                ) : (
                                                    msg.content
                                                )}
                                            </div>
                                            {msg.role === 'assistant' && (
                                                <button
                                                    className={`tts-btn ${speakingIdx === idx ? 'speaking' : ''}`}
                                                    onClick={() => handleSpeak(msg.content, idx)}
                                                    title={speakingIdx === idx ? 'Stop reading' : `Read aloud in ${sessionLanguage}`}
                                                    aria-label={speakingIdx === idx ? 'Stop reading' : 'Read aloud'}
                                                >
                                                    {speakingIdx === idx ? (
                                                        // Stop icon
                                                        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                                                            <rect x="6" y="6" width="12" height="12" rx="2" />
                                                        </svg>
                                                    ) : (
                                                        // Speaker / volume icon
                                                        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                                                            <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
                                                        </svg>
                                                    )}
                                                    <span className="tts-btn-label">
                                                        {speakingIdx === idx ? 'Stop' : 'Read aloud'}
                                                    </span>
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))}

                                {sending && (
                                    <div className="message-row assistant">
                                        <div className="avatar">
                                            <div className="sparkle-anim" />
                                        </div>
                                        <div className="message-content">
                                            <span style={{ fontStyle: 'italic', color: '#888' }}>Generating...</span>
                                        </div>
                                    </div>
                                )}

                                {error && <div className="error-message">{error}</div>}
                                <div ref={messagesEndRef} />
                            </div>
                        </div>

                        <div className="input-area-wrapper">
                            <div className="input-container">
                                <textarea
                                    ref={textareaRef}
                                    className="chat-input"
                                    placeholder="Enter a prompt here"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    disabled={sending}
                                />
                                <button
                                    className="send-btn"
                                    onClick={() => handleSend()}
                                    disabled={!input.trim() || sending}
                                >
                                    <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
