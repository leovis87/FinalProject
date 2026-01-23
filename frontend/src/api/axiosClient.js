import axios from 'axios';

const axiosClient = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
    // timeout: 5000,
});

// 요청 인터셉터
axiosClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// 응답 인터셉터
axiosClient.interceptors.response.use(
    (response) => response.data,
    (error) => {
        return Promise.reject(error);
    }
);

export default axiosClient;