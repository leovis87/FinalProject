import axiosClient from "./axiosClient";

export const userApi = {
    // 내 정보 조회
    getMe: () => {
        return axiosClient.get('/users/me');
    },

    // 테스트 유저 목록 조회
    getTestUsers: () => {
        return axiosClient.get('/users/test-users');
    },

    // 테스트 로그인
    loginTestUser: (email) => {
        return axiosClient.post('/users/login/test', { email });
    }
};