import React, { useState, useEffect } from 'react';

export default function ChatConfig({ subjects, loading, onStartChat, role, selectedStandard, onStandardChange }) {
    const [selectedSubject, setSelectedSubject] = useState('');
    const [selectedChapter, setSelectedChapter] = useState('');
    const [selectedLanguage, setSelectedLanguage] = useState('English');

    const currentSubject = subjects.find(s => s.name === selectedSubject);
    const chapters = currentSubject?.chapters || [];

    // Reset chapter when subject changes
    useEffect(() => {
        if (currentSubject && currentSubject.chapters.length > 0) {
            setSelectedChapter(currentSubject.chapters[0]);
        } else {
            setSelectedChapter('');
        }
    }, [selectedSubject, currentSubject]);

    // Auto-select first subject
    useEffect(() => {
        if (!selectedSubject && subjects.length > 0) {
            setSelectedSubject(subjects[0].name);
        }
    }, [subjects, selectedSubject]);

    const handleStart = () => {
        if (selectedSubject && selectedChapter) {
            onStartChat(selectedSubject, selectedChapter, selectedLanguage);
        }
    };

    if (loading) {
        return <div className="chat-config-container"><p>Loading courses...</p></div>;
    }

    return (
        <div className="chat-config-container">
            <h1>Select Course Material</h1>
            <p>Choose a subject and chapter to start your learning session.</p>

            <div className="config-form">
                {role === 'teacher' && (
                    <select
                        className="config-select"
                        value={selectedStandard}
                        onChange={(e) => {
                            onStandardChange(e.target.value);
                            setSelectedSubject('');
                            setSelectedChapter('');
                        }}
                    >
                        <option value="6">Standard 6</option>
                        <option value="7">Standard 7</option>
                        <option value="8">Standard 8</option>
                        <option value="9">Standard 9</option>
                        <option value="10">Standard 10</option>
                        <option value="11">Standard 11</option>
                        <option value="12">Standard 12</option>
                    </select>
                )}

                <select
                    className="config-select"
                    value={selectedSubject}
                    onChange={(e) => setSelectedSubject(e.target.value)}
                >
                    <option value="" disabled>Select Subject</option>
                    {subjects.map(s => (
                        <option key={s.name} value={s.name}>{s.name}</option>
                    ))}
                </select>

                <select
                    className="config-select"
                    value={selectedChapter}
                    onChange={(e) => setSelectedChapter(e.target.value)}
                    disabled={!selectedSubject}
                >
                    <option value="" disabled>Select Chapter</option>
                    {chapters.map(c => (
                        <option key={c} value={c}>{c}</option>
                    ))}
                </select>

                <select
                    className="config-select"
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                >
                    <option value="English">English</option>
                    <option value="Hindi">Hindi</option>
                </select>

                <button
                    className="start-chat-btn"
                    onClick={handleStart}
                    disabled={!selectedSubject || !selectedChapter}
                >
                    Start Chatting
                </button>
            </div>
        </div>
    );
}
