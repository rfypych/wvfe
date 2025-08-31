import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:5001';
const axiosInstance = axios.create({
    baseURL: API_URL,
    withCredentials: true
});

function DashboardPage({ onLogout }) {
    const [user, setUser] = useState(null);
    const [message, setMessage] = useState('Loading dashboard...');

    useEffect(() => {
        const fetchDashboard = async () => {
            try {
                const response = await axiosInstance.get('/api/dashboard');
                setUser(response.data.user);
                setMessage(response.data.message);
            } catch (error) {
                setMessage('Could not load dashboard data.');
            }
        };
        fetchDashboard();
    }, []);

    return (
        <div>
            <h2>Dashboard</h2>
            <p>{message}</p>
            {user && (
                <div>
                    <p>Username: {user.username}</p>
                    <p>User ID: {user.id}</p>
                </div>
            )}
            <button onClick={onLogout}>Logout</button>
        </div>
    );
}

export default DashboardPage;
