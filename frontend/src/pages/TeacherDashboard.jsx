import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function TeacherDashboard() {
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [view, setView] = useState('overview');
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedClass, setSelectedClass] = useState("All");

    useEffect(() => {
        const token = localStorage.getItem('token');
        axios.get(`http://localhost:9010/teacher/analytics`, {
            headers: { Authorization: `Bearer ${token}` }
        })
            .then(res => setData(res.data))
            .catch(err => console.error("Error loading analytics", err));
    }, []);

    if (!data) return (
        <div style={{ ...styles.dashboard, justifyContent: 'center', alignItems: 'center' }}>
            <h2 style={{ color: '#38bdf8' }}>Loading Teacher Analytics...</h2>
        </div>
    );

    const handleStudentClick = (student) => {
        setSelectedStudent(student);
        setView('performance');
    };

    // Filter Logic: Search by Name and Filter by Class
    const filteredStudents = data.students.filter(s => {
        const matchesSearch = s.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesClass = selectedClass === "All" || s.class === selectedClass;
        return matchesSearch && matchesClass;
    });

    // Get unique classes for the dropdown filter
    const classes = ["All", ...new Set(data.students.map(s => s.class).filter(Boolean))];

    return (
        <div style={styles.dashboard}>
            {/* Sidebar */}
            <nav style={styles.sidebar}>
                <h2 style={styles.logo}>CORE<span style={{ color: '#fff' }}>AI</span></h2>
                <ul style={styles.navList}>
                    <li style={view === 'overview' ? styles.activeNavItem : styles.navItem} onClick={() => setView('overview')}>📊 Class Overview</li>
                    <li style={view === 'list' ? styles.activeNavItem : styles.navItem} onClick={() => setView('list')}>👥 Student List</li>
                    <li style={styles.navItem} onClick={() => navigate('/chat')}>💬 AI Assistant</li>
                </ul>
                <button onClick={() => { localStorage.clear(); window.location.href = '/'; }} style={styles.logoutBtn}>Logout</button>
            </nav>

            {/* Main Content */}
            <main style={styles.mainContent}>
                <header style={styles.header}>
                    <h1 style={{ color: '#fff' }}>Teacher Analytics <span style={{ color: '#38bdf8' }}>Control Panel</span></h1>
                </header>

                {/* OVERVIEW */}
                {view === 'overview' && (
                    <>
                        <div style={styles.topRow}>
                            <div style={styles.statCard}>
                                <h3 style={styles.cardTitle}>TOTAL STUDENTS</h3>
                                <p style={styles.statValue}>{data.total_students}</p>
                            </div>
                            <div style={styles.statCard}>
                                <h3 style={styles.cardTitle}>CLASS AVG ACCURACY</h3>
                                <p style={styles.statValue}>{data.average_accuracy}%</p>
                                <div style={styles.miniBar}><div style={{ ...styles.miniFill, width: `${data.average_accuracy}%` }}></div></div>
                            </div>
                        </div>

                        <div style={styles.sectionCard}>
                            <div style={styles.filterBar}>
                                <h3 style={{ color: '#38bdf8' }}>Performance Roster</h3>
                                <div style={{ display: 'flex', gap: '10px' }}>
                                    <input
                                        style={styles.input}
                                        placeholder="Search name..."
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                    />
                                    <select
                                        style={styles.select}
                                        value={selectedClass}
                                        onChange={(e) => setSelectedClass(e.target.value)}
                                    >
                                        {classes.map(c => <option key={c} value={c}>Class {c}</option>)}
                                    </select>
                                </div>
                            </div>

                            <table style={styles.table}>
                                <thead>
                                    <tr style={styles.tableHeader}>
                                        <th style={styles.th}>Name</th>
                                        <th style={styles.th}>Class</th>
                                        <th style={styles.th}>Accuracy</th>
                                        <th style={styles.th}>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredStudents.map((student) => (
                                        <tr key={student.id} style={styles.tr}>
                                            <td style={{ ...styles.td, color: '#38bdf8', cursor: 'pointer', fontWeight: 'bold' }} onClick={() => handleStudentClick(student)}>
                                                {student.name}
                                            </td>
                                            <td style={styles.td}>{student.class || "N/A"}</td>
                                            <td style={styles.td}>{student.accuracy}%</td>
                                            <td style={styles.td}>
                                                <span style={{
                                                    ...styles.statusBadge,
                                                    backgroundColor: student.accuracy < 50 ? '#7f1d1d' : '#064e3b',
                                                    color: student.accuracy < 50 ? '#f87171' : '#34d399'
                                                }}>
                                                    {student.accuracy < 50 ? 'Low' : 'On Track'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                )}

                {/* VIEW 2: LIST  */}
                {view === 'list' && (
                    <div style={styles.sectionCard}>
                        <h3 style={{ marginBottom: '20px', color: '#38bdf8' }}>Student Directory</h3>
                        <table style={styles.table}>
                            <thead>
                                <tr style={styles.tableHeader}>
                                    <th style={styles.th}>Name</th>
                                    <th style={styles.th}>Email</th>
                                    <th style={styles.th}>Class Level</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.students.map((student) => (
                                    <tr key={student.id} style={styles.tr}>
                                        <td style={styles.td}>{student.name}</td>
                                        <td style={styles.td}>{student.email}</td>
                                        <td style={styles.td}>Grade {student.class || "Not Set"}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/*PERFORMANCE */}
                {view === 'performance' && selectedStudent && (
                    <div style={styles.sectionCard}>
                        <button onClick={() => setView('overview')} style={styles.backBtn}>← Back</button>
                        <h2 style={{ color: '#fff' }}>Report: <span style={{ color: '#38bdf8' }}>{selectedStudent.name}</span></h2>
                        <div style={styles.topRow}>
                            <div style={styles.statCard}><h3 style={styles.cardTitle}>ACCURACY</h3><p style={styles.statValue}>{selectedStudent.accuracy}%</p></div>
                            <div style={styles.statCard}><h3 style={styles.cardTitle}>PROGRESS</h3><p style={styles.statValue}>{selectedStudent.chapters} Ch.</p></div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

const styles = {
    dashboard: { display: 'flex', minHeight: '100vh', backgroundColor: '#131314', color: '#e3e3e3', fontFamily: "'Google Sans', sans-serif" },
    sidebar: { width: '300px', backgroundColor: '#1e1f20', padding: '2rem 1.5rem', display: 'flex', flexDirection: 'column', borderRight: '1px solid #444746' },
    logo: { fontSize: '1.8rem', fontWeight: 'bold', marginBottom: '2rem', color: '#8ab4f8', letterSpacing: '1px' },
    navList: { listStyle: 'none', padding: 0, flex: 1 },
    navItem: { padding: '12px 16px', borderRadius: '12px', cursor: 'pointer', marginBottom: '8px', color: '#c4c7c5', transition: '0.2s' },
    activeNavItem: { padding: '12px 16px', borderRadius: '12px', cursor: 'pointer', marginBottom: '8px', backgroundColor: '#004a77', color: '#c2e7ff', fontWeight: 'bold' },
    mainContent: { flex: 1, padding: '40px', overflowY: 'auto' },
    header: { marginBottom: '30px' },
    topRow: { display: 'flex', gap: '20px', marginBottom: '30px' },
    statCard: { flex: 1, backgroundColor: '#1e1f20', padding: '25px', borderRadius: '20px', border: '1px solid #444746' },
    cardTitle: { fontSize: '0.8rem', color: '#c4c7c5', margin: 0, letterSpacing: '1px' },
    statValue: { fontSize: '2.5rem', fontWeight: 'bold', margin: '10px 0', color: '#fff' },
    miniBar: { height: '6px', backgroundColor: '#334155', borderRadius: '3px', marginTop: '10px' },
    miniFill: { height: '100%', backgroundColor: '#8ab4f8', borderRadius: '3px' },
    sectionCard: { backgroundColor: '#1e1f20', padding: '25px', borderRadius: '20px', border: '1px solid #444746' },
    filterBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
    input: { backgroundColor: '#1e1f20', border: '1px solid #444746', borderRadius: '25px', padding: '12px 18px', color: '#fff', outline: 'none' },
    select: { backgroundColor: '#1e1f20', border: '1px solid #444746', borderRadius: '8px', padding: '10px', color: '#fff' },
    table: { width: '100%', borderCollapse: 'collapse' },
    tableHeader: { textAlign: 'left', borderBottom: '1px solid #444746' },
    th: { padding: '15px', color: '#c4c7c5', fontSize: '0.85rem' },
    tr: { borderBottom: '1px solid #131314' },
    td: { padding: '15px', color: '#e3e3e3' },
    statusBadge: { padding: '4px 10px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 'bold' },
    logoutBtn: { backgroundColor: 'transparent', color: '#c4c7c5', border: '1px solid #444746', padding: '12px', borderRadius: '10px', cursor: 'pointer', marginTop: '20px' },
    backBtn: { backgroundColor: 'transparent', color: '#8ab4f8', border: 'none', cursor: 'pointer', marginBottom: '10px', fontWeight: 'bold' }
};

export default TeacherDashboard;