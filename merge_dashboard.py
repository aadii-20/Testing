import sys

filepath = "c:/Users/Aditya/Documents/RBAS Chatbot/AI-chatboat/frontend/src/pages/StudentDashboard.jsx"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
state = 'NORMAL'
head_lines = []
major_lines = []
conflict_idx = 0

quiz_score_block = """                {isQuizSubmitted && quizScore && (
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
"""

for line in lines:
    if line.startswith('<<<<<<< HEAD'):
        state = 'IN_HEAD'
        head_lines = []
        major_lines = []
    elif line.startswith('======='):
        state = 'IN_MAJOR'
    elif line.startswith('>>>>>>> origin/major'):
        state = 'NORMAL'
        
        if conflict_idx in [0, 1, 2, 4, 5, 6, 7, 8, 10]:
            out.extend(head_lines)
        elif conflict_idx in [9, 11]:
            out.extend(major_lines)
        elif conflict_idx == 3:
            # Insert quiz score block before logout button in head_lines
            for hl in head_lines:
                if 'Logout' in hl and 'button' in hl:
                    out.append(quiz_score_block)
                out.append(hl)
                
        conflict_idx += 1
    else:
        if state == 'NORMAL':
            out.append(line)
        elif state == 'IN_HEAD':
            head_lines.append(line)
        elif state == 'IN_MAJOR':
            major_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(out)

print(f"Resolved {conflict_idx} conflicts in StudentDashboard.jsx")
