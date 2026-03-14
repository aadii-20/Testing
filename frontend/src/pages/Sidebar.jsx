import React from 'react';

export default function Sidebar({ sessions, currentSessionId, onSelectSession, onNewChat, onLogout }) {
    return (
        <div className="sidebar">
            <button className="new-chat-btn" onClick={onNewChat}>
                <span style={{ fontSize: '20px', fontWeight: 300 }}>+</span> New chat
            </button>

            <div className="section-title" style={{ fontSize: '12px', paddingLeft: '10px', marginTop: '10px', color: '#888' }}>Recent</div>

            <div className="history-list">
                {sessions.map(session => (
                    <button
                        key={session.id}
                        className={`history-item ${currentSessionId === session.id ? 'active' : ''}`}
                        onClick={() => onSelectSession(session.id)}
                    >
                        {session.title || `${session.subject} - ${session.chapter}`}
                    </button>
                ))}
            </div>

            <button className="logout-btn" onClick={onLogout}>
                Log out
            </button>
        </div>
    );
}
