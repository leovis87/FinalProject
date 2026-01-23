import axiosClient from "./axiosClient";

export const debateApi = {
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
    }
};