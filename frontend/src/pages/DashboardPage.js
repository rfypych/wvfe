import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api';

function DashboardPage({ onLogout }) {
    const [scans, setScans] = useState([]);
    const [targetUrl, setTargetUrl] = useState('');
    const [message, setMessage] = useState('');

    const fetchScans = useCallback(async () => {
        try {
            const response = await apiClient.get('/api/scans');
            setScans(response.data);
        } catch (error) {
            setMessage('Could not load scan history.');
        }
    }, []);

    useEffect(() => {
        fetchScans();
        // Set up polling to refresh the scan list every 5 seconds
        const interval = setInterval(fetchScans, 5000);
        // Clean up the interval on component unmount
        return () => clearInterval(interval);
    }, [fetchScans]);

    const handleNewScan = async (e) => {
        e.preventDefault();
        if (!targetUrl) {
            setMessage('Please enter a target URL.');
            return;
        }
        setMessage('Starting new scan...');
        try {
            const response = await apiClient.post('/api/scans', { target_url: targetUrl });
            setMessage(response.data.message);
            setTargetUrl(''); // Clear the input field
            fetchScans(); // Refresh the list immediately
        } catch (error) {
            setMessage(error.response?.data?.message || 'Failed to start scan.');
        }
    };

    return (
        <div>
            <h2>Dashboard</h2>
            <button onClick={onLogout} style={{ position: 'absolute', top: 10, right: 10 }}>Logout</button>

            <div style={{ padding: '10px', margin: '10px 0', border: '1px solid red', backgroundColor: '#ffdddd', color: 'red' }}>
                <strong>Peringatan (Disclaimer):</strong> Alat ini hanya boleh digunakan pada situs web yang Anda miliki atau memiliki izin eksplisit untuk diuji. Penggunaan tanpa izin adalah ilegal.
            </div>

            <div className="new-scan-form">
                <h3>Start a New Scan</h3>
                <form onSubmit={handleNewScan}>
                    <input
                        type="text"
                        value={targetUrl}
                        onChange={(e) => setTargetUrl(e.target.value)}
                        placeholder="https://example.com"
                        style={{ width: '300px', marginRight: '10px' }}
                    />
                    <button type="submit">Scan</button>
                </form>
                {message && <p>{message}</p>}
            </div>

            <div className="scan-history">
                <h3>Scan History</h3>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr>
                            <th style={{ border: '1px solid #ddd', padding: '8px' }}>ID</th>
                            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Target URL</th>
                            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Status</th>
                            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Date</th>
                            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {scans.length > 0 ? scans.map(scan => (
                            <tr key={scan.id}>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{scan.id}</td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{scan.target_url}</td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{scan.status}</td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{new Date(scan.created_at).toLocaleString()}</td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                                    <Link to={`/scans/${scan.id}`}>View Details</Link>
                                </td>
                            </tr>
                        )) : (
                            <tr>
                                <td colSpan="5" style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'center' }}>No scans found.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default DashboardPage;
