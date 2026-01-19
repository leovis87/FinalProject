'''
⭐ Agent, Chain 구분해서 사용하기

description:
    - Agent (에이전트):
        -> "도구(Tool)를 써야 하거나", "스스로 생각하고 행동(Reasoning Loop)해야 할 때" 씁니다. (예: 사회자의 Fact-Check, 검색)
        -> 입력값: Dict

    - Chain (체인):
        -> "주어진 텍스트를 읽고 답변만 하면 될 때" 씁니다.
        -> 입력값: str
    
    💡 루프(Loop) 필요 == Agent
        -> Loop: [검색 요청] -> [검색 실행] -> [결과 읽기] -> [최종 답변]
'''
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
from typing import (Literal)
from .schemas import (
    DebateState,
    TopicBriefing, RefereeDecision,
    ModeratorReport, PersonalCoachingReport
)
from .config import (GEMINI_MODELS,
                    TEMPERATURE, MAX_TOKENS,
                    TAVILY_SEARCH,
                    llm_g_real_non_harm,
                    get_search_tool,
                    create_run_config)
from core.config import settings 

# LangChain Core
from langchain_core.messages import HumanMessage, AIMessage # 수동 기억장치 (history)
from langchain_core.messages import SystemMessage # ✅ Prompt Caching 활성화
from langchain_core.runnables import (ConfigurableField, # ✅ LLM에 유연성 부여
                                      RunnableConfig)    # IDE 자동 완성 / 설정 관리

# LangChain Agent & Tools
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory

# LangGraph
from langgraph.prebuilt import create_react_agent

load_dotenv()

# ============================================
# logging 설정
# ============================================
logger = logging.getLogger('nodes')


# ============================================
# 🏗️ 내부 공통 함수 & 헬퍼 함수
# ============================================
def _generate_team_feedback(state: DebateState,
                            config: RunnableConfig,
                            target_team: str) -> dict:
    '''
    description:
        - 💎 [Premium] 개인별 심층 피드백 생성
        - Agent(검색/분석) -> Structure LLM(Pydantic) pipeline
        - ⭐ Topic Analysis(전략 데이터)를 참고하여 비교 분석 수행

    Args:
        - target_team(str): 'pro' 또는 'con'

    Return:
        - dict: {user_id: feedback_text}
    '''
    # ---------------------------------------------------------
    # 1. 대상 팀 리스트 가져오기
    # ---------------------------------------------------------
    if target_team == 'pro':
        users = state.get('pro_users', [])
        team_name_kr = '찬성 팀'
        team_recs = state['topic_analysis'].pro_args if state.get('topic_analysis') else []
    
    else:
        users = state.get('con_users', [])
        team_name_kr = '반대 팀'
        team_recs = state['topic_analysis'].con_args if state.get('topic_analysis') else []

    # ---------------------------------------------------------
    # ⚡ 2. [핵심] 유료 사용자 필터링 (골라내기)
    # ---------------------------------------------------------
    # "is_premium이 True인 사람만 남겨라"
    # (키가 없으면 기본값 False 처리로 안전하게)

    premium_users = [u for u in users if u.get('is_premium', False)]

    # 유료 유저가 한 명도 없으면? -> 바로 종료 (비용 0원)
    if not premium_users:
        logger.info(f"🚫 [{team_name_kr}] 프리미엄 유저가 없습니다. 피드백 생성을 건너뜁니다.")
        return {}

    logger.info(f"[{team_name_kr}] 프리미엄 유저 {len(premium_users)}명 분석 시작...")
    
    # ============================================
    # 🏗️ Config 재설정 & Callback 재조립
    # ============================================
    run_config = create_run_config(config, is_structured_mode = True)
    enable_streaming = run_config.get('configurable', {}) if config else {}.get('is_stream', False)

    # ============================================
    # 🕵️ 1. 분석가 Agent 준비 (검색 능력 탑재)
    # ============================================
    search_tool = get_search_tool(use_tavily = True)
    tools = [search_tool]

    agent = create_react_agent(llm_g_real_non_harm, tools)

    # ============================================
    # 🏗️ 2-1. 구조화 LLM 준비 (포맷팅)
    # ============================================
    structuring_llm = llm_g_real_non_harm.bind(
        model = GEMINI_MODELS['flash'],
        temperature = 0.0,
        max_output_tokens = 8192
    ).with_structured_output(PersonalCoachingReport)

    # ============================================
    # 📚 3. Context 구성 (전략 데이터 주입)
    # ============================================
    full_context = '\n'.join([
        f"[{msg.get('user_name')}] {msg.get('content')}" 
        for msg in state['messages']
    ])
    
    # 전략 가이드 텍스트 변환
    strategy_guide = "없음"
    if team_recs:
        strategy_guide = "\n".join([f"- {rec}" for rec in team_recs])

    feedbacks = {}

    # ============================================
    # 🔄 4. 필터링된 유저(premium_users)만 반복문 돌리기
    # ============================================
    for user in premium_users:
        # 💸 유료 유저 체크 (state에 is_premium 플래그가 있다고 가정)
        user_id = user['user_id']
        user_name = user['user_name']

        logger.info(f"👤 {user_name} ({team_name_kr}) 분석 중...")

        # 해당 유저 발언만 추출
        user_messages = [msg for msg in state['messages'] if msg.get('user_id') == user_id]

        if not user_messages:
            feedbacks[user_id] = "발언 기록이 없어 피드백을 생성할 수 없습니다."
            continue

        user_content_str = '\n'.join([f"- {msg['content']}" for msg in user_messages])

        # ---------------------------------------------------------
        # (A) Agent 실행: 심층 분석 & 팩트체크용 prompt
        # ---------------------------------------------------------
        system_prompt = f"""
[Role]
너는 대한민국 최고의 토론 교육 전문가야.
사용자의 발언 논리, 근거의 적절성, 태도 등을 분석해서
도움이 되는 '개인 맞춤 피드백'을 따뜻하고 구체적인 어조로 작성해줘.

[Comparison Criteria]
전문가가 분석한 이번 토론의 [{team_name_kr} 필승 전략]은 다음과 같아:
{strategy_guide}

[Task]
사용자가 위 전략을 잘 활용했는지, 혹은 놓쳤는지도 분석에 포함해.
통계나 수치를 언급했다면 반드시 검색 도구로 사실 여부를 검증해.
"""

        user_prompt = f"""
주제:
'{state.get('topic')}'

전체 흐름:
{full_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 분석 대상:
{user_name} ({team_name_kr})

발언 내용:
{user_content_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

위 참가자에 대한 심층 코칭 리포트를 작성해줘.
1. 강점과 약점 분석
2. 발언별 구체적 교정 (비논리적 부분, 표현 개선)
3. 추천 학습 키워드
"""
        
        # System_prompt + User_prompt
        # LLM입력을 위해 [system + user] 순서로 전달
        sys_msg = SystemMessage(content = system_prompt)
        user_msg = HumanMessage(content = user_prompt)

        # System + User 결합
        msg_list = [sys_msg, user_msg]

        # Agent용 dict로 변환
        agent_inputs = {
            'messages': msg_list
        }

        try:
            # 1. Agent 실행
            agent_result = agent.invoke(
                agent_inputs,
                config = run_config
            )

            raw_content = agent_result['messages'][-1].content
            analysis_text = _parse_agent_output(raw_content)
            
            # ---------------------------------------------------------
            # (B) Structure 실행: JSON 변환
            # ---------------------------------------------------------
            # ============================================
            # 💉 2-2. 구조화 LLM system_promt 주입 
            # ============================================
            formatting_system_prompt = """
[Task]
입력된 분석 텍스트를 바탕으로 완벽한 JSON 데이터를 생성해.

[Rules]
1. 'detailed_points' 리스트를 절대 비워지마.
2. 각 point의 'critique'(비평)와 'suggestion'(제안) 필드는 필수야.
3. 만약 원문에서 비평할 내용이 명시되어 있지 않다면, 문맥을 추론해서 채워 넣어.
4. 절대 null이나 빈 문자열("")을 반환하지 마.
"""

            formatting_messages = [
                SystemMessage(content = formatting_system_prompt),
                HumanMessage(content = analysis_text)
            ]
            
            # 2. 분석된 내용을 PersonalCoachingReport 객체로 변환
            final_report: PersonalCoachingReport = structuring_llm.invoke(formatting_messages)
            
            # user_id 주입
            final_report.user_id = user_id

            # 결과 저장
            feedbacks[user_id] = final_report

            # 스트리밍이 아닐 경우 출력 확인
            if not enable_streaming:
                logger.info(f"✅ {user_name} 개인 피드백 리포트 생성 완료")

        except Exception as e:
            logger.error(f"⚠️ {user_name} 피드백 실패: {e}")
            feedbacks[user_id] = "분석 중 오류 발생"

    return feedbacks

def _run_debater_logic(
        state: DebateState,
        config: RunnableConfig,
        role_name: str,           # 예: '찬성', '반대'
        my_tag: str,              # 예: '[찬성]', '[반대]'
        opponent_tag: str,        # 예: '[반대]', '[찬성]'
        state_key_overwrite: str  # 예: 'latest_pro_message'
) -> dict:
    '''
    description:
        - 찬성/반대 AI 노드를 위한 공통 로직 함수
        - ⭐ 업그레이드: analyze_topic_node에서 생성한 데이터 참조
    '''
    logger.info(f"[🤖 {role_name} 측 AI - {state['current_turn']}턴]")

    # ============================================
    # 🏗️ 1. Config 재설정 & Callback 재조립
    # ============================================
    run_config = create_run_config(config)
    
    # 모델 설정 강제
    if 'configurable' not in run_config:
        run_config['configurable'] = {}

    run_config['configurable']['model'] = GEMINI_MODELS['flash']
    run_config['configurable']['temp'] = 0.7
    
    # ============================================
    # 🏗️ 2. History 변환 (Role Mapping)
    # ============================================
    history_messages = []
    
    for msg in state['messages']:
        content = msg.get('content', '')
        
        # 상대방의 말 -> HumanMessage (들어야 할 대상)
        if opponent_tag in content:
            clean_content = content.replace(opponent_tag, "").strip()
            history_messages.append(HumanMessage(content = clean_content))
            
        # 내 과거 발언 -> AIMessage (내가 했던 말)
        # ⚠️ [수정] ["태그"] 리스트가 아니라 "[태그]" 문자열로 비교해야 함!
        elif my_tag in content:
            clean_content = content.replace(my_tag, "").strip()
            history_messages.append(AIMessage(content = clean_content))

    # ============================================
    # 🧠 3. 전략 데이터(Topic Analysis) 로드
    # ============================================
    # analyze_topic_node가 만들어둔 분석 결과 가져오기
    analysis_data = state.get('topic_analysis')

    strategy_guide = ''

    if analysis_data:
        # (1) 배경 지식 추가
        strategy_guide += f"\n[Background Info]\n{analysis_data.description}"

        # (2) 내 역할에 맞는 추천 입론 가져오기
        recommendations = []
        if role_name == '찬성':
            recommendations = analysis_data.pro_args
        
        elif role_name == '반대':
            recommendations = analysis_data.con_args
        
        # (3) 프롬프트에 넣을 텍스트로 변환
        if recommendations:
            rec_text = '\n'.join([f"- {rec}" for rec in recommendations])
            strategy_guide += F"\n[Recommended Strategy]\n우리 측 승리를 위한 핵심 논거:\n{rec_text}\n\n위 논거들을 적절히 활용하여 주장을 강화해."

    # ============================================
    # 🤖 4. 프롬프트 & LLM 실행
    # ============================================
    system_prompt = f"""
    [Role]
    너는 토론의 [{role_name}] 측 토론자야.
    주제: {state['topic']}

    {strategy_guide}
    
    [Instructions]
    1. 상대방(HumanMessage)의 의견을 논리적으로 반박해.
    2. 위 [Recommended Strategy]에 있는 논거를 적극적으로 활용해.
    3. 말투는 정중하지만 단호하게.
    4. 너무 길어지지 않게 핵심 위주로 발언해.
    """
    
    messages_to_send = [SystemMessage(content = system_prompt)] + history_messages
    
    result = llm_g_real_non_harm.invoke(
        messages_to_send, 
        config = run_config
    )
    
    final_content = result.content
    logging(f"🗣️ {role_name} AI: {final_content}")
    
    # ============================================
    # 💾 5. State 업데이트
    # ============================================
    new_message = {
        'turn': state['current_turn'],
        'role': 'ai',
        'user_name': f'{role_name}_AI',
        'content': f'{my_tag} {final_content}' # 태그 붙여서 저장
    }
    
    return {
        'messages': [new_message],
        state_key_overwrite: final_content
    }


def _parse_agent_output(agent_result_content) -> str:
    """
    Gemini/LangChain의 Agent 결과(content)가 String이 아니라 
    List[Dict] 또는 Dict 형태로 나올 경우 순수 텍스트만 추출
    """
    # 1. 그냥 문자열이면 바로 리턴
    if isinstance(agent_result_content, str):
        return agent_result_content
    
    # 2. 리스트인 경우 (멀티모달 파트가 나뉠 때)
    # 예: [{'type': 'text', 'text': '...'}]
    if isinstance(agent_result_content, list):
        return "".join([
            item.get('text', '') 
            for item in agent_result_content 
            if isinstance(item, dict) and item.get('type') == 'text'
        ])
    
    # 3. 딕셔너린 경우 (에러가 난 상황)
    # 예: {'type': 'text', 'text': '...'}
    if isinstance(agent_result_content, dict):
        if agent_result_content.get('type') == 'text':
            return agent_result_content.get('text', '')
            
    # 그 외의 경우 (강제 형변환)
    return str(agent_result_content)

# ============================================
# 🧰 Node 함수
# ============================================
# Start Node (Topic 요약 + 각 측 입론 추천)
def analyze_topic_node(state: DebateState,
                       config: RunnableConfig) -> DebateState:
    '''
    description:
        - [START Node] 토론 시작 직후 실행
        - state['topic']을 분석하여 설명 및 추천 입론 생성
        - 결과를 state에 저장
        - 💡 Agent 사용
            -> Structuring LLM 이 output 정리 (pydantic 전용)
    '''
    current_topic = state.get('topic', '')
    logger.info(f"[🚀 토론 분석 시작] 주제: {current_topic}")

    # ============================================
    # 🏗️ Config 재설정 & Callback 재조립
    # ============================================
    # 1. Config 재설정 (Helper 사용)
    run_config = create_run_config(config, is_structured_mode = True)

    # 스트리밍 여부 확인 (run_config에서 안전하게 추출)
    enable_streaming = run_config.get('configurable', {}).get('is_stream', False)
    logging.info(f">>스트리밍 모드: {enable_streaming}")
    
    # 모델 설정 강제
    if 'configurable' not in run_config:
        run_config['configurable'] = {}

    run_config['configurable']['model'] = GEMINI_MODELS['flash']
    run_config['configurable']['temp'] = 0.7
    run_config['configurable']['token'] = MAX_TOKENS['high']

    # ============================================
    # 🏗️ 로직 설정
    # ============================================
    # 1. 🔎 Search Tool 실행 (최신 정보 수집)
    search_tool = get_search_tool(use_tavily = True)
    tools = [search_tool]

    # 2-1. 🤖 Agent 생성 (LLM + Search tool)
    agent = create_react_agent(llm_g_real_non_harm, tools)

    # 2-2. 👨‍⚖️ output 구조화 LLM (pydantic 적용)
        #   -> 이 LLM은 정리만하는 간단한 Chain LLM => flash모델로
    structuring_llm = llm_g_real_non_harm.bind(
        model = GEMINI_MODELS['flash'],
        temperature = 0.0
    ).with_structured_output(TopicBriefing)

    # 3. 🧾 System prompt (분석가 페르소나)
    system_prompt = f"""
[Role]
너는 토론 주제 분석 전문가야.
주어지는 주제에 대해 [배경 지식]과 [쟁점]을 명확하게 파악하고, 양측의 입론 전략을 세워줘.

오늘 날짜:
{datetime.now().strftime('%Y년 %m월 %d일')}

[Task]
1. 주제에 대한 배경 설명 (필요 시, 검색을 통해 최신 이슈 반영)
2. [찬성] 측 추천 입론 2가지 (논리적 근거 포함)
3. [반대] 측 추천 입론 2가지 (논리적 근거 포함)

[중요]
1. 검색 tool 사용 시, 오늘 날짜 기준 최신 내용으로 확인할 것.

[출력 형식]
## 1. 주제 배경 및 현황
(내용...)

## 2. 찬성 측 추천 입론
1. (핵심 주장): (설명...)
2. (핵심 주장): (설명...)

## 3. 반대 측 추천 입론
1. (핵심 주장): (설명...)
2. (핵심 주장): (설명...)
"""

    # 4. 🧾 User prompt
    user_prompt = f"""
분석할 주제:
'{current_topic}'

위 주제를 심층 분석해줘.
"""
    
    # 5-1. LLM입력을 위해 [system + user] 순서로 전달
    sys_msg = SystemMessage(content = system_prompt)
    user_msg = HumanMessage(content = user_prompt)

    # 5-2. System + User 결합
    msg_list = [sys_msg, user_msg]

    # 5-3. Agent 입력 형식으로 변환
    #   ⚠️ Agent 입력 == Dict
    agent_inputs = {
        "messages": msg_list
    }
    
    try:
        logger.info("Agent 실행 중... (검색 포함)")
        # Agent가 "검색 -> 생각 -> 답변" 루프를 돔
        result = agent.invoke(agent_inputs,
                              config = run_config)
        
        # 6. 📝 결과 텍스트 추출
        #   -> text로 출력
        raw_content = result['messages'][-1].content

        logger.info(f"\nAgent Raw Output:\n{raw_content[:200]}...")

        text_output = _parse_agent_output(raw_content)

        # 7. 🏗️ 구조화 (Formatting)
        logger.info("구조화(Formatting) 진행 중...")

        final_obj: TopicBriefing = structuring_llm.invoke(text_output)

        logger.info(f"구조화 완료 객체: {final_obj}")

        if final_obj:
            logger.info("\n✅ [분석 결과 생성 성공]")
            logger.info(f"📄 배경: {final_obj.description[:50]}...")
            logger.info(f"👍 찬성 추천: {len(final_obj.pro_args)}개")
            logger.info(f"👎 반대 추천: {len(final_obj.con_args)}개")

        # 스트리밍 아닐 때만 출력
        if not enable_streaming:
            logger.info(final_obj)

        # 8. 💾 State 업데이트 (분석 결과 저장)
        #    -> 보통 이 결과는 나중에 UI에 보여주거나, 토론자 AI들에게 system prompt로 주입할 수도 있음
        return {
            'topic_analysis': final_obj
        }
        
    except Exception as e:
        logger.error(f"⚠️ 주제 분석 실패: {str(e)}")
        return {} # 에러 시 빈 딕셔너리 리턴 (Workflow 안 멈추게)

# 찬성 측 유져 노드 함수
def pro_turn_node_user(state: DebateState) -> DebateState:
    '''
    description:
        - 찬성 팀 user 발언 Node (사용자 input)
    '''
    logger.info(f"🔵 [찬성 팀 턴] 시작 - Turn {state['current_turn']}")

    # 찬성 팀 순서 (턴에 따라 돌아가며)
    user_index = (state['current_turn'] -1) % len(state['pro_users'])
    current_user = state['pro_users'][user_index]

    # 서버값 가져오기
    user_input = state.get('user_input', '')
    
    # 빈 값 체크
    if not user_input:
        logger.warning(f"⚠️ User input is empty for {current_user['user_name']}")
    
    logger.info(f"👤 {current_user['user_name']}: {user_input}")

    # messages에 추가
    new_message = {
        'turn': state["current_turn"],
        'role': "pro",
        'user_id': current_user["user_id"],
        'user_name': current_user["user_name"],
        'content': user_input
    }

    return {
        'messages': [new_message],
        'latest_pro_message': user_input # 덮어쓰기(Overwrite) 필드는 그냥 리턴하기
    }

# 반대 측 유져 노드 함수
def con_turn_node_user(state: DebateState) -> DebateState:
    '''
    description:
        - 반대 팀 user 발언 Node (사용자 input)
    '''
    logger.info(f"🔴 [반대 팀 턴] 시작 - Turn {state['current_turn']}")

    # 반대 팀 순서 (턴에 따라 돌아가며)
    user_index = (state['current_turn'] - 1) % len(state['con_users'])
    current_user = state['con_users'][user_index]

    # 출력 예시: 🎙️ {current_user["user_name"]}님 차례입니다.'
    print(f"🎙️ {current_user["user_name"]}")

    # 사용자 입력
    # Local test시:
    user_input = input('💬 반대 의견: ')

    # 서버값 가져오기
    # user_input = state.get('user_input', '')

    # 빈 값 체크
    if not user_input:
        logger.warning(f"⚠️ User input is empty for {current_user['user_name']}")
    
    logger.info(f"👤 {current_user['user_name']}: {user_input}")

    # messages에 추가
    new_message = {
            'turn': state['current_turn'],
            'role': "con",
            'user_id': current_user["user_id"],
            'user_name': current_user["user_name"],
            'content': user_input
    }

    return {
        'messages': [new_message],
        'latest_con_message': user_input # 덮어쓰기(Overwrite) 필드는 그냥 리턴하기
    }

# AI vs AI용 [찬성] 측 AI 노드 함수
def pro_turn_node_ai(state: DebateState,
                     config: RunnableConfig) -> DebateState:
    """
    description:
        - 반대 팀 ai 발언 Node (이전 대화 참고)
        - ⭐ state['messages'] => 저장은 pro 가 human ==>> con 은 ai
    """
    return _run_debater_logic(
        state = state,
        config = config,
        role_name = '찬성',         # Role 이름
        my_tag = '[찬성]',          # 구분용 `내` 태그
        opponent_tag = '[반대]',    # 구분용 `상대` 태그
        state_key_overwrite = 'latest_pro_message'  # 갱신할 state 키
    )

# AI vs AI용 [반대] 측 AI 노드 함수
def con_turn_node_ai(state: DebateState,
                     config: RunnableConfig) -> DebateState:
    """
    description:
        - 반대 팀 ai 발언 Node
        - Config & Callback 재조립 + History 포맷팅(Human/AI 변환) + LLM 실행
        - ⭐ state['messages'] => 저장은 pro 가 human ==>> con 은 ai
    """
    return _run_debater_logic(
        state = state,
        config = config,
        role_name = '반대',         # Role 이름
        my_tag = '[반대]',          # 구분용 `내` 태그
        opponent_tag = '[찬성]',    # 구분용 `상대` 태그
        state_key_overwrite = 'latest_con_message'  # 갱신할 state 키
    )

# 요약 및 턴 증가 노드 함수
def summary_node(state: DebateState,
                 config: RunnableConfig) -> DebateState:
    '''
    description:
        - 요약 Node: 턴 완료 후 카운트 증가
    '''
    logger.info(f"[📝 턴 {state['current_turn']} 요약 및 정리 중...]")

    current_turn = state['current_turn']
    # ============================================
    # 🏗️ Config 재설정 & Callback 재조립
    # ============================================
    run_config = create_run_config(config)

    # 모델 설정 강제
    if 'configurable' not in run_config:
        run_config['configurable'] = {}
    run_config['configurable']['model'] = GEMINI_MODELS['flash']
    run_config['configurable']['temp'] = 0.0
    run_config['configurable']['token'] = MAX_TOKENS['mid']

    # ============================================
    # 🏗️ 데이터 추출 (Reverse Search)
    # ============================================
    # 1. Prompt용 변수 설정
    messages = state.get('messages', [])

    # 2. Error 방지용 초기화
    pro_msgs = []
    con_msgs = []

    # 3. 전체 메시지 순회
    for msg in reversed(messages):
        # 해당 메시지가 '현재 턴'인지 확인
        if msg.get('turn') == state['current_turn']:

            # 찬성 측 발언 수집
            if msg.get('role') == 'pro':
                # "발언자: 내용" 형태로 저장하여 AI가 해당 발언자도 기억하게 추가 수정
                pro_msgs.append(f"{msg.get('user_name')}: {msg.get('content')}")

            # 반대 측 발언 수집
            elif msg.get('role') == 'cone':
                # "발언자: 내용" 형태로 저장하여 AI가 해당 발언자도 기억하게 추가 수정
                con_msgs.append(f"{msg.get('user_name')}: {msg.get('content')}")

    # 4. 리스트를 하나의 문자열로 합치기 (발언이 없으면 "발언 없음" 처리)
    # join 사용
    last_pro_msg = "\n".join(pro_msgs) if pro_msgs else "발언 없음"
    last_con_msg = "\n".join(con_msgs) if con_msgs else "발언 없음"

    # ============================================
    # 🏗️ Prompt 구성 (압축 요약 유도)
    # ============================================
    system_prompt = f"""
[Role]
너는 토론 기록관이야.

[Task]
이번 턴에서 오간 '찬성'과 '반대' 측의 주장을 분석해서, 각각 **핵심 논거 한 문장**으로 요약해.
장황한 설명은 빼고, 논리적인 뼈대만 남겨.

[Output Format]
[Turn {current_turn}]
🔵 찬성: (핵심 주장 요약)
🔴 반대: (핵심 주장 요약)
"""

    user_prompt = f"""
[Turn {current_turn} Data]
- 찬성 팀 발언: {last_pro_msg}
- 반대 팀 발언: {last_con_msg}

위 내용을 포맷에 맞춰 요약해줘.
"""

    # ============================================
    # 🏗️ LLM 실행
    # ============================================
    # 4-1. LLM입력을 위해 [system + user] 순서로 전달
    sys_msg = SystemMessage(content = system_prompt)
    user_msg = HumanMessage(content = user_prompt)

    # 4-2. System + User 결합
    msg_list = [sys_msg, user_msg]

    try:
        # 5. LLM 요약 생성
        response = llm_g_real_non_harm.invoke(msg_list,
                                              config = run_config)
        
        summary_result = _parse_agent_output(response.content)
        logger.info(f"\n📄 [요약 완료]\n{summary_result}")
    
    except Exception as e:
        logger.error(f"⚠️ 요약 생성 실패: {e}")
        summary_result = f"[Turn {current_turn}] 요약 실패 (Error Occurred)"
        logger.error(f"[Turn {current_turn}] 요약 실패 (Error Occurred)")
    
    # ============================================
    # 🏗️ State 업데이트 (핵심!)
    # ============================================
    return {
        # 1. 리스트에 추가
        'summary_history': [summary_result], 
        
        # 2. 턴 증가
        'current_turn': current_turn + 1
    }

# 비속어, 비방, 논점 이탈 감지 Chain LLM 노드 함수
def referee_node_ai(state: DebateState,
                    config: RunnableConfig) -> DebateState:
    '''
    description:
        - 실시간 중재 Node: 가장 최근 발언 체크
        - 각 팀의 발언이 끝날 때 마다 실시간으로 최근 발언 체크
            -> 비속어, 비방, 논점 이탈 시 실시간으로 발언.
        - Pydantic 적용: RefereeDecision
    '''
    logger.info(f"[👨‍⚖️ Referee 검토 중...]")

    # ============================================
    # 🏗️ Config 재설정 & Callback 재조립
    # ============================================
    run_config = create_run_config(config, is_structured_mode = True)

    # 모델 설정 강제
    if 'configurable' not in run_config:
        run_config['configurable'] = {}
    
    run_config['configurable']['model'] = GEMINI_MODELS['flash']
    run_config['configurable']['temp'] = 0.0
    run_config['configurable']['token'] = MAX_TOKENS['low']

    # ============================================
    # 🏗️ 로직 설정
    # ============================================
    # 1. Messages state 확인
    if not state['messages']:
        return {}
    
    # 2. 마지막 발언 추출
    last_message = state['messages'][-1]
    user_name = last_message.get('user_name', '참가자')
    content = last_message.get('content', '')
    topic = state.get('topic', '')

    logger.info(f'\n[REFEREE_AI] "{last_message["user_name"]}" 발언 체크 중...')

    # ============================================
    # 🤖 LLM 구성하기
    # ============================================
    # 1. 구조화 (.with_structured_output)
    #   ⭐ pydantic 적용 -> .invoke 시, 'RefereeDecision' 객체를 반환
    referee_llm = llm_g_real_non_harm.with_structured_output(RefereeDecision)

    # 4. Prompt 구성 (pydantic 적용)
    system_prompt = f"""
[Role]
너는 엄격한 토론 심판이야.
사용자의 발언을 분석하여, 다음 기준에 따라 위반 여부를 판단해줘.

[위반 기준]
1. profanity: 욕설, 비속어 사용
2. personal_attack: 상대방 인격 모독, 비난
3. off_topic: 토론 주제와 전혀 상관없는 잡담 등

"""
    
    user_prompt = f"""
토론 주제:
{topic}

발언 내용:
{content}

위 발언을 분석, 판단해줘.
"""
    
    # 4-1. LLM입력을 위해 [system + user] 순서로 전달
    sys_msg = SystemMessage(content = system_prompt)
    user_msg = HumanMessage(content = user_prompt)

    # 4-2. System + User 결합
    msg_list = [sys_msg, user_msg]

    # 5. LLM 실행
    try:
        result: RefereeDecision = referee_llm.invoke(
            msg_list,
            config = run_config
        )

        # 6. 결과 처리 (객체의 속성처럼 접근 가능: result.has_issue)
        if result.has_issue:
            logger.info(f"⚠️ [REFEREE 경고] {result.message}")

            new_warning = {
                'turn': state.get('current_turn'),
                'user_name': user_name,
                'type': result.issue_type,
                'message': result.message
            }

            return {
                'referee_warnings': [new_warning]
            }

        else:
            logger.info("✅ 심판 판정: 문제 없음")

            return {}
    
    except Exception as e:
        # 혹시라도 모델이 schema를 못 맞추거나 API 에러가 날 경우 대비
        logger.error(f"⚠️ Referee 구조화 출력 에러: {str(e)}")

        return {}

def moderator_shared_node(state: DebateState,
                          config: RunnableConfig) -> DebateState:
    '''
    description:
        - 사회자 노드: [검색/분석 Agent] -> [구조화 LLM] pipeline
          (공통 노드: 유/무료 상관없이 '전체 요약 및 채점' 수행)
        - 채점 + fact-check (Agent + search tool)
        - DB 저장을 위해 Pydantic(ModeratorReport)으로 출력 강제
    '''
    logger.info(f"[🤖 AI Moderator 전체 토론 분석 및 채점, 데이터 구조화 중...]")

    # ============================================
    # 🏗️ Config 재설정 & Callback 재조립
    # ============================================
    run_config = create_run_config(config, is_structured_mode = True)
    enable_streaming = run_config.get('configurable', {}).get('is_stream', False)

    # 모델 설정 강제
    if 'configurable' not in run_config:
        run_config['configurable'] = {}

    run_config['configurable']['model'] = GEMINI_MODELS['pro']
    run_config['configurable']['temp'] = 0.0
    run_config['configurable']['token'] = 8192

    # ============================================
    # 🏗️ 로직 설정
    #   1단계: 분석 및 fact-check (Agent)
    #       -> text 내용 생성
    # ============================================
    # 1. 🔎 Search Tool 설정
    search_tool = get_search_tool(use_tavily = True)
    tools = [search_tool]

    # 2. 🏗️ 모델 준비
    moderator_llm = llm_g_real_non_harm
    
    # 3-1. 🤖 Agent 생성 (LLM + search tool)
    #   -> 내부적으로 LLM + Tools loop가 형성됨
    agent = create_react_agent(moderator_llm, tools)

    # 💉 safety_setting 재주입
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    # 3-2. 👨‍⚖️ Output 제한용 LLM .bind 형식이 아닌 새로 생성
    #   -> 정리만 함. 가벼운 flash 모델로.
    moderator_structuring_llm = ChatGoogleGenerativeAI(
        model = GEMINI_MODELS['flash'],
        google_api_key = settings.GEMINI_API_KEY,
        temperature = 0.0,
        max_output_tokens = 8192,           # 토큰 확보
        safety_settings = safety_settings,  # 직접 주입
    )

    structuring_llm = moderator_structuring_llm.with_structured_output(ModeratorReport)

    # ---------------------------------------------------------
    # 1. 👥 참가자 명단 문자열 생성 (Prompt 주입용)
    # ---------------------------------------------------------
    # LLM이 "누가 user_A인지" 알아야 정확한 Key를 생성함.
    pro_info = "\n".join([f"- {u['user_name']} (ID: {u['user_id']})" for u in state['pro_users']])
    con_info = "\n".join([f"- {u['user_name']} (ID: {u['user_id']})" for u in state['con_users']])

    # ---------------------------------------------------------
    # 2. 📝 Prompt 구성
    # ---------------------------------------------------------
    # 🧾 System prompt 설정 (동적, 정적) + 정적 prompt caching 추가
    system_content = [
        # 👟 동적 prompt
        {
            'type': 'text',
            'text': f"""
[참가자 level]
{state['level']}

[Role]
너는 10년 이상 경력의 {state['level']} 토론 코치야.

[찬성 팀]
{pro_info}

[반대 팀]
{con_info}

[오늘 날짜]
{datetime.now().strftime('%Y년 %m월 %d일')}
"""
        },

        # 🧘 정적 prompt
        {
            'type': 'text',
            'text': f"""
[Task]
1. 전체 토론 요약
2. 각 팀별 채점 (학생 논술 평가 기준)
3. 주요 주장 fact-check (검색 필수)
4. 검색 툴 사용 시, 꼭 {datetime.now().strftime('%Y년 %m월 %d일')}을 기준으로 검색할 것.
5. 구체적 근거와 출처 제시

'채점항목'
아래 4가지 항목에 대해 각 팀별로 점수를 매겨줘.
1. 주장 명확성 (25점 만점)
   - 수준 5(25점): 입장이 명확하며 처음부터 끝까지 유지됨
   - 수준 4(20점): 입장은 분명하나 일부 발언에서 흔들림
   - 수준 3(15점): 입장은 있으나 표현이 모호함
   - 수준 2(10점): 입장이 불분명하거나 질문에 따라 변함
   - 수준 1(5점): 자신의 입장을 제시하지 못함

2. 근거 적합성 (30점 만점)
   - 수준 5(30점): 근거가 주장과 직접 연결되고 설명 가능
   - 수준 4(24점): 관련 근거 제시, 설명 일부 부족
   - 수준 3(18점): 근거는 있으나 주장과 연결 약함
   - 수준 2(12점): 예시는 있으나 근거 역할 미흡
   - 수준 1(6점): 근거 없이 의견만 제시
   * 이 항목은 fact-check 필수! 통계/수치 검색으로 검증!

3. 상호작용·반응 (25점 만점)
   - 수준 5(25점): 상대 주장 요지를 정확히 받아 반응
   - 수준 4(20점): 상대 발언을 언급하며 의견 제시
   - 수준 3(15점): 반응 시도는 있으나 핵심 빗나감
   - 수준 2(10점): 형식적 반응("동의/비동의")만 있음
   - 수준 1(5점): 상대 발언 무시

4. 토론 태도 (20점 만점)
   - 수준 5(20점): 경청, 차례 준수, 상대 존중 모두 완벽
   - 수준 4(16점): 1회 미흡하나 즉시 수정
   - 수준 3(12점): 반복적으로 주의 필요
   - 수준 2(8점): 감정적 표현이 다수 섞임
   - 수준 1(4점): 규칙 지속 위반

출력 형식:
[찬성 팀]
총점: XX/100점

1. 주장 명확성: XX점 (수준 X)
   근거: ...

2. 근거 적합성: XX점 (수준 X)
   근거: ...
   📌 Fact-check: ...

3. 상호작용·반응: XX점 (수준 X)
   근거: ...

4. 토론 태도: XX점 (수준 X)
   근거: ...

[반대 팀]
총점: XX/100점
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 총평
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[출력 제외]
**개개인에 대한 피드백은 작성하지 마. 오직 팀 단위 평가만 수행해.
""",
            # 📂 Claude 전용 Caching
            'cache_control': {
                'type': 'ephemeral'
            }
        }
    ]

    # 전체 대화 내용 취합
    debate_content = '\n\n'.join([
        f"턴 {msg.get('turn', '?')} - [{msg.get('user_name', 'Unknown')}({msg.get('role', 'Unknown')})]:\n{msg.get('content', '')}"
        for msg in state['messages']
    ])

    # User prompt 설정
    user_prompt = f"""
주제:
'{state['topic']}'

전체 토론 내용:
{debate_content}

위 토론을 분석하고 채점해줘.
통계나 수치가 포함된 주장은 반드시 검색 도구를 사용하여 Fact-check을 수행하고 결과를 반영해줘.
"""
    
    # 7-1. System prompt를 SystemMessage로 인스턴스화
    sys_msg = SystemMessage(content = system_content)
    user_msg = HumanMessage(content = user_prompt)

    # 7-2. System + User 결합
    msg_list = [sys_msg, user_msg]

    # 7-3. Agent 입력 형식으로 변환
    agent_inputs = {
            'messages': msg_list
    }

    try:
        # 8. 💉 Agent에 Config, 메시지 주입
        #   ⚠️ 중요: Agent 그래프는 {"messages": [ ... ]} 형태의 dict로 입력받음.
        result = agent.invoke(agent_inputs,
                              config = run_config)
        
        # 9. 🎯 결과 추출
        #   Agent 결과의 'messages' 리스트 중, 가장 마지막 메시지 == 최종 답변
        raw_content = result['messages'][-1].content
        text_output = _parse_agent_output(raw_content)

        # ============================================
        # 🏗️ 로직 설정
        #   2단계: 데이터 구조화 (Structuring LLM)
        #       -> text -> JSON formatting
        # ============================================
        # 💉 구조화 LLM system_promt 주입 
        # ============================================
        formatting_system_prompt = f"""
[Task]
입력된 분석 텍스트를 바탕으로 'ModeratorReport' JSON을 완성하시오.

[Critical Rules]
1. 다음 3가지 필드를 **반드시** 포함해야 한다.
   - "general_summary": 전체 총평
   - "pro_eval": 찬성 팀 평가 객체
   - "con_eval": 반대 팀 평가 객체
   
2. **'pro_individual_feedbacks'와 'con_individual_feedbacks'는 작성하지 마시오.** (스키마에 없음)

3. **[중요] 'feedback_text' 필드 작성 규칙:**
   - 절대 한 문단으로 요약하지 마시오.
   - Agent가 분석한 **[주장 명확성], [근거 적합성], [상호작용], [태도]**의 상세 내용과 점수 근거를 모두 포함하시오.
   - 가독성을 위해 줄바꿈(\\n)과 글머리 기호(-, •)를 사용하여 마크다운 줄글 형태로 작성하시오.

4. JSON 객체를 중간에 닫지 말고("}}") 모든 필드를 채울 때까지 계속 생성하시오.

[참가자 ID 정보]
{pro_info}
{con_info}
"""

        formatting_messages = [
            SystemMessage(content = formatting_system_prompt),
            HumanMessage(content = text_output)
        ]

        final_obj: ModeratorReport = structuring_llm.invoke(formatting_messages)

        if not enable_streaming:
            logger.info(f"\n📊 [찬성 점수]: {final_obj.pro_eval.total_score}점")
            logger.info(f"📊 [반대 점수]: {final_obj.con_eval.total_score}점")
            logger.info(f"📝 [총평]: {final_obj.general_summary[:50]}...")

        return {
            # State에 Str -> 'Dict 객체'로 
            'moderator_report': final_obj
        }
    
    except Exception as e:
        logger.error(f"⚠️ 분석 실패: {str(e)}")

        return {
            'moderator_summary': '분석 중 오류가 발생했습니다.'
        }

# Search tool + Chain [찬성] 측 개개인 fact-check AI 노드 함수
def pro_feedback_node(state: DebateState,
                      config: RunnableConfig) -> DebateState:
    '''
    description:
        - 찬성 팀 개인별 피드백 (💸 유료 전용)
        - 헬퍼 함수 호출 (target = 'pro')
    '''
    feedbacks = _generate_team_feedback(state, config, 'pro')
    logger.info(f"✅ [찬성 팀] 피드백 생성 완료: {len(feedbacks)}명")

    
    return{
        'premium_feedbacks': feedbacks  # 변경 부분만 리턴

    } 

# Search tool + Agent [반대] 측 개개인 fact-check AI 노드 함수
def con_feedback_node(state: DebateState,
                      config: RunnableConfig) -> DebateState:
    '''
    description:
        - 찬성 팀 개인별 피드백 (💸 유료 전용)
        - 헬퍼 함수 호출 (target = 'pro')
    '''
    feedbacks = _generate_team_feedback(state, config, 'con')
    logger.info(f"✅ [찬성 팀] 피드백 생성 완료: {len(feedbacks)}명")
    
    return{
        'premium_feedbacks': feedbacks  # 변경 부분만 리턴
    } 


# ============================================
# 🗺️ 라우터 함수
#   - 📌 분기 처리
# ============================================
# 🛠️ 토론 시작 전 Topic 추천을 진행하는 라우터 함수
def route_topic_check(state: DebateState) -> Literal['valid', 'invalid']:
    '''
    description:
        - 라우터: 추천을 할지 안할지 판단
    '''
    if state.get('is_topic_valid'):
        return 'valid'
    
    else:
        return 'invalid'

# 최대 턴을 확인하여 Loop를 끝내는 라우터 노드 함수
def should_continue_debate(state: DebateState) -> Literal['continue', 'end']:
    '''
    description:
        - 라우터: 계속할지 종료할지 판단

    Returns:
        - 'continu': 다시 찬성 Node로 (Loop)
        - 'end': 종료
    '''
    if state['current_turn'] <= state['max_turns']:
        logger.info(f'\n[라우터] -> 계속 진행! (현재: {state["current_turn"]}, 최대: {state["max_turns"]})')
        return 'continue'

    else:
        logger.info(f'\n[라우터] -> 종료! (최대 턴 도달)')    
        return 'end'

# 📌 설명:
# current_turn <= max_turns → "continue" 반환
#   → Conditional Edge가 "continue"를 받으면
#   → 다시 pro_node_ai로 돌아감! (Loop!)
# 
# current_turn > max_turns → "end" 반환
#   → END로 이동 (종료)

# 공통 분석 후, 각 팀 개개인 fact-check feedback 분기 함수
def router_for_feedback(state: DebateState) -> DebateState:
    '''
    description:
        - 공통 분석 후, 각 팀 개개인의 피드백을 생성할지 분기
    '''
    # 1. 전체 참가자 리스트
    all_users = state.get('pro_users', []) + state.get('con_users', [])
    
    # 2. 유료 회원(is_premium=True)이 한 명이라도 있는지 체크
    has_premium_user = any(u.get('is_premium', False) for u in all_users)
    
    if has_premium_user:
        logger.info("💎 프리미엄 유저 감지 -> 심층 피드백 생성(병렬) 시작")
        # 찬성/반대 피드백 노드를 동시에 실행 (List 리턴)
        return ["pro_feedback", "con_feedback"]
        
    else:
        logger.info("🏁 프리미엄 유저 없음 -> 토론 종료")
        return "debate_end"

# 토론 종료 라우터 노드 함수
def debate_end_node(state: DebateState) -> DebateState:
    '''
    description:
        - 토론 종료 노드 (분기만)
    '''
    logger.info(f"[토론 종료!]")

    return state