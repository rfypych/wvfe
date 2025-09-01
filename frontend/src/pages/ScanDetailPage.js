import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiClient from '../api';

function ScanDetailPage() {
    const [scan, setScan] = useState(null);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { id } = useParams();
    const logContainerRef = useRef(null);

    useEffect(() => {
        const fetchScanDetails = async () => {
            try {
                setLoading(true);
                const response = await apiClient.get(`/api/scans/${id}`);
                setScan(response.data);
                setError('');
            } catch (err) {
                setError(err.response?.data?.message || 'Failed to fetch scan details.');
            } finally {
                setLoading(false);
            }
        };
        fetchScanDetails();
    }, [id]);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const response = await apiClient.get(`/api/scans/${id}/logs`);
                setLogs(response.data);
            } catch (err) {
                // Don't overwrite main page error, just log this one
                console.error("Failed to fetch logs");
            }
        };

        fetchLogs(); // Initial fetch

        // If the scan is running, poll for updates
        if (scan?.status === 'running' || scan?.status === 'pending') {
            const interval = setInterval(() => {
                fetchLogs();
                // Also refresh scan details to check if status has changed to 'completed'
                const fetchScanStatus = async () => {
                    const res = await apiClient.get(`/api/scans/${id}`);
                    setScan(res.data);
                }
                fetchScanStatus();
            }, 3000); // Poll every 3 seconds

            // Clean up the interval when the component unmounts or scan completes
            return () => clearInterval(interval);
        }
    }, [id, scan?.status]);

    // Auto-scroll to the bottom of the log container
    useEffect(() => {
        if (logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [logs]);

    if (loading) return <div>Loading scan details...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!scan) return <div>Scan not found.</div>;

    return (
        <div>
            <Link to="/dashboard">Back to Dashboard</Link>
            <h2>Scan Details for ID: {scan.id}</h2>
            <p><strong>Target URL:</strong> {scan.target_url}</p>
            <p><strong>Status:</strong> {scan.status}</p>
            <p><strong>Scan Started:</strong> {new Date(scan.created_at).toLocaleString()}</p>

            <h3>Vulnerabilities Found ({scan.vulnerabilities.length})</h3>
            {scan.vulnerabilities.length > 0 ? (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr>
                            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Type</th>
                            <th style={{ border: '1px solid #ddd', padding: '8px' }}>URL</th>
                            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Payload</th>
                            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {scan.vulnerabilities.map(vuln => (
                            <tr key={vuln.id}>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{vuln.type}</td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{vuln.url}</td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}><code>{vuln.payload}</code></td>
                                <td style={{ border: '1px solid #ddd', padding: '8px' }}>{vuln.details}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : (
                <p>No vulnerabilities found for this scan.</p>
            )}

            <h3>Scan Log</h3>
            <pre ref={logContainerRef} style={{ backgroundColor: '#f4f4f4', border: '1px solid #ddd', padding: '10px', maxHeight: '400px', overflowY: 'scroll', whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                {logs.length > 0 ? logs.map(log => `[${new Date(log.timestamp).toLocaleTimeString()}] ${log.message}`).join('\n') : 'No logs yet...'}
            </pre>
        </div>
    );
}

export default ScanDetailPage;
