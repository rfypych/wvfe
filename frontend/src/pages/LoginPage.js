import React, { useState } from 'react';
import apiClient from '../api';

function LoginPage({ onLoginSuccess }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setMessage('Logging in...');
        try {
            const response = await apiClient.post(`/api/auth/login`, {
                username,
                password
            });
            setMessage(response.data.message);
            if (response.data.status === 'success') {
                onLoginSuccess();
            }
        } catch (error) {
            if (error.response) {
                setMessage(`Error: ${error.response.data.message}`);
            } else {
                setMessage('Error: Could not connect to the server.');
            }
        }
    };

    return (
        <div>
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
                <div>
                    <label>Username:</label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label>Password:</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button type="submit">Login</button>
            </form>
            {message && <p>{message}</p>}
        </div>
    );
}

export default LoginPage;
