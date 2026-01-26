import axiosClient from "./axiosClient";

export const debateApi = {
    // 방 목록 조회
    getDebateRooms: () => {
        return axiosClient.get('/debates/');
    },

    // 방 정보 조회
    getRoomInfo: (roomId) => {
        return axiosClient.get(`/debates/${roomId}`);
    },

    // 방 생성
    createRoom: (roomData) => {
        return axiosClient.post('/debates/', roomData);
    },

    // AI 주제 추천
    getAiRecommendations: (params) => {
        return axiosClient.post('/rag/topics/generate', params);
    },

    // 내 토론 기록 조회
    getHistory: () => {
        return axiosClient.get('/debates/history');
    },

    // 인기 판결문 조회
    getPopularVerdicts: (limit = 8) => {
        return axiosClient.get('/debates/verdicts/popular', {
            params: { limit }
        });
    },

    // 판결문 상세 조회
    getDebateVerdict: (roomId) => {
        return axiosClient.get(`/debates/${roomId}/verdict`);
    }
};