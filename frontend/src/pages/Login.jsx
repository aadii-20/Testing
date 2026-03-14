import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginUser, registerUser } from '../api';

function Login() {
    const [activeTab, setActiveTab] = useState('login');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('student');
    const [standard, setStandard] = useState('9');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (activeTab === 'login') {
                // --- LOGIN FLOW ---
                const response = await loginUser({ email, password });
                const { token, role: userRole } = response.data;

                localStorage.setItem('token', token);
                localStorage.setItem('role', userRole);

                if (userRole === 'student') navigate('/student-dashboard');
                else if (userRole === 'teacher') navigate('/teacher-dashboard');

            } else {
                // --- SIGNUP FLOW ---
                const registrationData = {
                    email,
                    password,
                    role,
                    standard: role === 'student' ? standard : null
                };

                await registerUser(registrationData);


                // Switch to login after signup
                setActiveTab('login');
                setPassword('');
                alert("Account created! Please login.");
            }
        } catch (err) {
            console.error("Auth Error:", err);
            const message = err.response?.data?.detail || 'Connection error';
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    const switchTab = (tab) => {
        setActiveTab(tab);
        setError('');
        // Optional: clear fields or keep them
    };

    return (
        <div id="loginScreen" className="login-container">
            <div className="login-card">
                <h2>CORE AI</h2>
                <div className="tab-buttons">
                    <button
                        className={`tab-button ${activeTab === 'login' ? 'active' : ''}`}
                        onClick={() => switchTab('login')}
                    >
                        Login
                    </button>
                    <button
                        className={`tab-button ${activeTab === 'signup' ? 'active' : ''}`}
                        onClick={() => switchTab('signup')}
                    >
                        Sign Up
                    </button>
                </div>

                <form className="auth-form" onSubmit={handleSubmit}>
                    <label>
                        Email
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </label>
                    <label>
                        Password
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </label>

                    {activeTab === 'signup' && (
                        <>
                            <label>
                                Role
                                <select value={role} onChange={(e) => setRole(e.target.value)}>
                                    <option value="student">Student</option>
                                    <option value="teacher">Teacher</option>
                                </select>
                            </label>

                            {role === 'student' && (
                                <label>
                                    Class / Standard
                                    <select value={standard} onChange={(e) => setStandard(e.target.value)}>
                                        <option value="8">Class 8</option>
                                        <option value="9">Class 9</option>
                                        <option value="10">Class 10</option>
                                        <option value="11">Class 11</option>
                                        <option value="12">Class 12</option>
                                    </select>
                                </label>
                            )}
                        </>
                    )}

                    {error && <p className="error-message">{error}</p>}

                    <button type="submit" disabled={loading}>
                        {loading ? (activeTab === 'login' ? 'Logging in...' : 'Signing up...') : (activeTab === 'login' ? 'Login' : 'Sign Up')}
                    </button>
                </form>

                <p className="test-credentials">
                    Welcome to the upgraded experience.
                </p>
            </div>
        </div>
    );
}


const styles = {
    // --- CONTAINER & CARD ---
    container: {
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        backgroundColor: '#131314', // Gemini Dark Bg
        fontFamily: "'Google Sans', sans-serif",
    },
    loginCard: {
        backgroundColor: '#1e1f20',
        width: '100%',
        maxWidth: '420px',
        padding: '40px',
        borderRadius: '28px',
        border: '1px solid #444746',
        boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
    },
    title: {
        fontSize: '2rem',
        textAlign: 'center',
        color: '#8ab4f8',
        fontWeight: 'bold',
        marginBottom: '10px',
    },
    subtitle: {
        color: '#c4c7c5',
        textAlign: 'center',
        marginBottom: '25px',
        fontSize: '1.1rem',
    },

    // --- TABS ---
    tabContainer: {
        display: 'flex',
        marginBottom: '30px',
        borderBottom: '1px solid #444746',
    },
    activeTab: {
        flex: 1,
        padding: '12px',
        backgroundColor: 'transparent',
        color: '#8ab4f8',
        border: 'none',
        borderBottom: '2px solid #8ab4f8',
        cursor: 'pointer',
        fontWeight: 'bold',
    },
    inactiveTab: {
        flex: 1,
        padding: '12px',
        backgroundColor: 'transparent',
        color: '#c4c7c5',
        border: 'none',
        cursor: 'pointer',
    },

    // --- FORM ELEMENTS ---
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
    },
    inputGroup: {
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
    },
    label: {
        fontSize: '0.9rem',
        color: '#e3e3e3',
        marginLeft: '4px',
    },
    input: {
        padding: '14px 18px',
        borderRadius: '12px',
        border: '1px solid #444746',
        backgroundColor: '#131314',
        color: '#fff',
        fontSize: '1rem',
        outline: 'none',
    },
    loginBtn: {
        marginTop: '10px',
        padding: '14px',
        borderRadius: '25px',
        backgroundColor: '#8ab4f8',
        color: '#0b2245',
        border: 'none',
        fontWeight: 'bold',
        fontSize: '1rem',
        cursor: 'pointer',
        transition: 'background 0.2s',
    },

    // --- FEEDBACK & LINKS ---
    errorText: {
        color: '#f87171',
        fontSize: '0.9rem',
        textAlign: 'center',
        backgroundColor: 'rgba(248, 113, 113, 0.1)',
        padding: '10px',
        borderRadius: '8px',
    },
    successText: {
        color: '#10b981',
        fontSize: '0.9rem',
        textAlign: 'center',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        padding: '10px',
        borderRadius: '8px',
    },
    linkText: {
        color: '#8ab4f8',
        cursor: 'pointer',
        fontSize: '0.9rem',
        textDecoration: 'underline',
    }
};


export default Login;