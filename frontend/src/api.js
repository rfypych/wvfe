import axios from 'axios';

// Define the base URL for the backend API
const API_URL = 'http://127.0.0.1:5001';

// Create a single, pre-configured instance of axios
const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true, // This is crucial for sending session cookies
});

export default apiClient;
