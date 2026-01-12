-- [ PostgreSQL (superuser: 관리자 계정) ]

-- Password: GKwlak1332!
-- Retype password: GKwlak1332!
-- Port: 5432

-- 일반 계정:
-- ID: jinu
-- PASSWORD: jw1234


-- [ PostgreSQL에서 새로운 사용자/DB 만들기 ]
-- 1. 관리자 계정 접속
-- psql -U postgres
-- pass: GKwlak1332!
-- port: 5432


-- 사용자 계정 생성 (없으면 새로 생성)
DO $$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'jinu'
   ) THEN
      CREATE ROLE jinu LOGIN PASSWORD 'jw1234';
   END IF;
END
$$;

-- 데이터베이스 생성 (없으면 새로 생성)
CREATE DATABASE mydb OWNER jinu;

-- DB 접속 후 테이블 생성
\c mydb

CREATE TABLE IF NOT EXISTS debate_rooms (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,            -- 방 제목
    topic TEXT NOT NULL,                    -- 토론 주제
    room_type VARCHAR(20) NOT NULL,         -- 학생/비즈니스/일반
    status VARCHAR(20) DEFAULT '대기중',    -- 대기중/진행중/종료
    max_participants INT DEFAULT 4,         -- 최대 인원
    current_participants INT DEFAULT 0,     -- 현재 인원
    max_turns INT DEFAULT 10,               -- 최대 턴
    current_turn INT DEFAULT 0,             -- 현재 턴
    created_by VARCHAR(50),                 -- 방장
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(50) REFERENCES debate_rooms(id),
    user_id VARCHAR(50) NOT NULL,
    nickname VARCHAR(50) NOT NULL,          -- 표시될 이름
    side VARCHAR(10) NOT NULL,              -- 찬성/반대
    is_online BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(room_id, user_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(50) REFERENCES debate_rooms(id),
    sender_type VARCHAR(20) NOT NULL,       -- user / ai_moderator
    sender_id VARCHAR(50),
    side VARCHAR(10),                       -- 찬성/반대/NULL
    content TEXT NOT NULL,
    turn_number INT,
    created_at TIMESTAMP DEFAULT NOW()
);