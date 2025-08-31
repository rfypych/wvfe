import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:5001';
const axiosInstance = axios.create({
    baseURL: API_URL,
    withCredentials: true
});

function ScanDetailPage() {
    const [scan, setScan] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { id } = useParams(); // Get the scan ID from the URL

    useEffect(() => {
        const fetchScanDetails = async () => {
            try {
                setLoading(true);
                const response = await axiosInstance.get(`/api/scans/${id}`);
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

    if (loading) {
        return <div>Loading scan details...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    if (!scan) {
        return <div>Scan not found.</div>;
    }

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
        </div>
    );
}

export default ScanDetailPage;
