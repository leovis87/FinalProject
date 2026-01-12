from src.models import (DebateRooms,
                        Participant,
                        Message, User)
from utils.auth import get_password_hash

# [USER 인증]
def create_user(db,
                user_id: str,
                email: str,
                nickname: str,
                password: str):
    """
    새 사용자 생성 (회원가입)
    
    비유: 회원가입 신청서 접수
    
    Args:
        password: 평문 비밀번호 (자동으로 암호화됨)
    """
    # 1. 중복 체크
    existing_user = db.query(User).filter(
        (User.user_id == user_id) | (User.email == email)
    ).first()
    
    if existing_user:
        if existing_user.user_id == user_id:
            raise Exception("이미 사용 중인 ID입니다")
        if existing_user.email == email:
            raise Exception("이미 사용 중인 이메일입니다")
    
    # 2. 비밀번호 암호화
    hashed_password = get_password_hash(password)
    
    # 3. 사용자 생성
    new_user = User(
        user_id=user_id,
        email=email,
        nickname=nickname,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


def get_user_by_id(db, user_id: str):
    """
    user_id로 사용자 찾기
    """
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_email(db, email: str):
    """
    이메일로 사용자 찾기
    """
    return db.query(User).filter(User.email == email).first()

# 기존 create_room, join_room 등은 그대로 유지


# [Create] 
def create_room(db,
                created_by: str,
                title: str,
                topic: str,
                room_type: str,
                max_participants: int = 4):
    """
    토론방 생성
        - user_id: 토론방 생성자 ID
        - title: 토론방 제목
        - topic: 토론 주제
    """
    make_room = DebateRooms(
        title = title,
        topic = topic,
        room_type = room_type,
        max_participants = max_participants,
        current_participants = 0,
        created_by = created_by,
        status = "대기 중"
    )
    db.add(make_room)
    db.commit()
    db.refresh(make_room)
    
    return make_room


def join_room(db,
              room_id: int,
              user_id: str,
              nickname: str,
              side: str,):
    """
    토론방 입장
        - room_id: 토론방 번호
        - user_id: 입장 ID
        - nickname: 표시될 이름
        - side: 찬성 / 반대
    """
    # 1. 해당 토론방에 있는지 체크
    existing = db.query(Participant).filter(
        Participant.room_id == room_id,
        Participant.user_id == user_id
    ).first()

    if existing:
        raise Exception("⚠️ 이미 방에 참가했습니다!")
    
    # 2 방이 꽉 찼는지 체크
    room = db.query(DebateRooms).filter(
        DebateRooms.id == room_id
    ).first()

    if not room:
        raise Exception("⚠️ 존재하지 않는 방입니다.")
    
    if room.current_participants >= room.max_participants:
        raise Exception("⚠️ 방이 꽉 찼습니다.")
    
    # 3. 참가자 추가
    participant = Participant(
        room_id = room_id,
        user_id = user_id,
        nickname = nickname,
        side = side
    )
    db.add(participant)

    # 4. 현재 참가자 수 증가
    room.current_participants += 1

    db.commit()
    db.refresh(participant)

    return participant


def save_message(db,
                 room_id: int,
                 sender_type: str,
                 sender_id: str,
                 content: str,
                 side: str = None
    ):
    """
    message를 DB에 저장
    """
    message = Message(
        room_id = room_id,
        sender_type = sender_type,
        sender_id = sender_id,
        side = side,
        content = content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return message

# [GET]
def get_user_side(db,
                  room_id: int,
                  user_id: str
                  ):
    """
    사용자의 side (찬성 / 반대) 불러오기
    """
    participant = db.query(Participant).filter(
        Participant.room_id == room_id,
        Participant.user_id == user_id
    ).first()

    return participant.side if participant else None


def get_room_messages(db,
                      room_id: int,
                      side: str = None
                      ):
    """
    토론방 message 불러오기
    """
    query = db.query(Message).filter(
        Message.room_id == room_id
    )

    if side:
        query = query.filter(
            Message.side == side
        )

    return query.order_by(Message.created_at).all()


def get_rooms(db):
    """
    전체 토론방 목록 가져오기
        - 최신순으로 정렬
    """

    return db.query(DebateRooms)\
            .order_by(DebateRooms.created_at.desc())\
            .all()


def get_room_info(db,
                  room_id: int):
    """
    특정 토론방 정보 가져오기
    """
    get_room_info = db.query(DebateRooms).filter(
        DebateRooms.id == room_id
    ).first()

    return get_room_info


def get_participants(db,
                     room_id: int):
    """
    특정 토론방의 참가자 목록 가져오기
    """
    get_participants_list = db.query(Participant).filter(
        Participant.room_id == room_id
    ).all()

    return get_participants_list