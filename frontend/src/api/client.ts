import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL || '/api/v1';

export const apiClient = axios.create({
    baseURL,
    headers: {
        'Content-Type': 'application/json',
    },
});

apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('google_id_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});
