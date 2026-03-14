import { useNavigate } from 'react-router-dom';

function PlanSelector() {
  const navigate = useNavigate();
  
  const selectPlan = (planName) => {
    localStorage.setItem('selectedPlan', planName);
    navigate('/student-dashboard');
  };

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Select Your Learning Plan</h1>
      <button onClick={() => selectPlan('Board Prep')}>Board Exam Focus</button>
      <button onClick={() => selectPlan('Concept Clarity')}>Basic Concept Clarity</button>
    </div>
  );
}
export default PlanSelector;