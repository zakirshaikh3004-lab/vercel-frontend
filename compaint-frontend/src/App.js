import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'https://your-backend.onrender.com';

function App() {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState('login');
  const [complaints, setComplaints] = useState([]);
  const [departments, setDepartments] = useState([]);

  // Login/Register Form
  const [form, setForm] = useState({ email: '', password: '', name: '', role: 'student' });
  // Complaint Form
  const [complaintForm, setComplaintForm] = useState({ 
    title: '', description: '', department_id: 1, priority: 'medium', anonymous: false 
  });
  // Anonymous Check
  const [anonymousId, setAnonymousId] = useState('');

  useEffect(() => {
    if (user) {
      loadComplaints();
      loadDepartments();
    }
  }, [user]);

  const loadComplaints = async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/complaints`, {
      headers: { 'Authorization': token }
    });
    const data = await response.json();
    setComplaints(data);
  };

  const loadDepartments = async () => {
    const response = await fetch(`${API_URL}/departments`);
    const data = await response.json();
    setDepartments(data);
  };

  const handleAuth = async (isLogin) => {
    const url = isLogin ? '/login' : '/register';
    const response = await fetch(API_URL + url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      setUser(data.user);
      setPage('dashboard');
    } else {
      alert('Error: ' + (await response.json()).detail);
    }
  };

  const submitComplaint = async () => {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_URL}/complaints`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': token
      },
      body: JSON.stringify(complaintForm)
    });
    
    if (response.ok) {
      alert('Complaint submitted!');
      setComplaintForm({ title: '', description: '', department_id: 1, priority: 'medium', anonymous: false });
      loadComplaints();
    }
  };

  const checkAnonymous = async () => {
    const response = await fetch(`${API_URL}/complaints/anonymous/${anonymousId}`);
    if (response.ok) {
      const complaint = await response.json();
      setComplaints([complaint]);
    } else {
      alert('Complaint not found');
    }
  };

  const updateStatus = async (complaintId, status) => {
    const token = localStorage.getItem('token');
    await fetch(`${API_URL}/complaints/${complaintId}`, {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': token
      },
      body: JSON.stringify({ status })
    });
    loadComplaints();
  };

  if (!user) {
    return (
      <div className="app">
        <h1>College Complaint System</h1>
        <div className="auth-form">
          <h2>{page === 'login' ? 'Login' : 'Register'}</h2>
          
          {page !== 'login' && (
            <>
              <input type="text" placeholder="Full Name" 
                value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
              <select value={form.role} onChange={e => setForm({...form, role: e.target.value})}>
                <option value="student">Student</option>
                <option value="admin">Admin</option>
              </select>
            </>
          )}
          
          <input type="email" placeholder="Email" 
            value={form.email} onChange={e => setForm({...form, email: e.target.value})} />
          <input type="password" placeholder="Password" 
            value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
          
          <button onClick={() => handleAuth(page === 'login')}>
            {page === 'login' ? 'Login' : 'Register'}
          </button>
          
          <p>
            {page === 'login' ? "Don't have an account? " : "Already have an account? "}
            <span className="link" onClick={() => setPage(page === 'login' ? 'register' : 'login')}>
              {page === 'login' ? 'Register' : 'Login'}
            </span>
          </p>

          <div className="demo-info">
            <p><strong>Demo Admin:</strong> admin@college.edu / admin123</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <h1>Welcome, {user.name} ({user.role})</h1>
        <button onClick={() => {
          localStorage.clear();
          setUser(null);
          setPage('login');
        }}>Logout</button>
      </header>

      {user.role === 'student' && (
        <div className="student-view">
          <div className="section">
            <h2>Submit Complaint</h2>
            <input type="text" placeholder="Title" 
              value={complaintForm.title} 
              onChange={e => setComplaintForm({...complaintForm, title: e.target.value})} />
            <textarea placeholder="Description" 
              value={complaintForm.description}
              onChange={e => setComplaintForm({...complaintForm, description: e.target.value})} />
            <select value={complaintForm.department_id} 
              onChange={e => setComplaintForm({...complaintForm, department_id: parseInt(e.target.value)})}>
              {departments.map(dept => (
                <option key={dept.id} value={dept.id}>{dept.name}</option>
              ))}
            </select>
            <select value={complaintForm.priority}
              onChange={e => setComplaintForm({...complaintForm, priority: e.target.value})}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <label>
              <input type="checkbox" 
                checked={complaintForm.anonymous}
                onChange={e => setComplaintForm({...complaintForm, anonymous: e.target.checked})} />
              Submit Anonymously
            </label>
            <button onClick={submitComplaint}>Submit</button>
          </div>

          <div className="section">
            <h2>Check Anonymous Complaint</h2>
            <input type="text" placeholder="Complaint ID" 
              value={anonymousId} onChange={e => setAnonymousId(e.target.value)} />
            <button onClick={checkAnonymous}>Check Status</button>
          </div>

          <div className="section">
            <h2>My Complaints</h2>
            {complaints.map(comp => (
              <div key={comp.id} className="complaint">
                <h3>{comp.title}</h3>
                <p>{comp.description}</p>
                <span className={`status ${comp.status}`}>{comp.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {user.role === 'admin' && (
        <div className="admin-view">
          <h2>All Complaints</h2>
          {complaints.map(comp => (
            <div key={comp.id} className="complaint">
              <h3>{comp.title} - {comp.department_name}</h3>
              <p>{comp.description}</p>
              <select value={comp.status} onChange={e => updateStatus(comp.id, e.target.value)}>
                <option value="open">Open</option>
                <option value="in-progress">In Progress</option>
                <option value="closed">Closed</option>
              </select>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
