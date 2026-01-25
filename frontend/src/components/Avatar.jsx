const BASE_URL = "https://api.dicebear.com/9.x/micah/svg";

/**
 * @param {string} seed - 생성할 아바타의 시드 (회원 닉네임)
 * @param {object} options - 아바타 꾸미기 옵션 (예: { glasses: 'variant1', hair: 'variant2' })
 * @param {string} className
 */

function Avatar({ seed, className, options = {} }) {
    // 기본 옵션 설정
    const finalOptions = {
        mouth: "laughing",
        ...options
    };

    // 쿼리 스트링 변환
    const queryString = Object.entries(finalOptions)
        .map(([key, value]) => {
            return `${key}=${encodeURIComponent(value)}`;
        })
        .join('&');

    const imageUrl = `${BASE_URL}?seed=${encodeURIComponent(seed || 'Guest')}&${queryString}`;

    return (
        <img
            src={imageUrl}
            alt={`${seed}님의 아바타`}
            className={className}
        />
    );
}
export default Avatar