# For FrontEnd

# JSON Body (필요 항목)
# {
#   "input": {
#     "topic": "사용자가 입력한 주제 (예: 2026년 AI 트렌드)"
#   }
# }


# For BackEnd

# 1. 필요한 모듈 install
# pip install "langserve[all]"

# 2. 하기로 간단하게 구현 가능
# from fastapi import FastAPI
# from langserve import add_routes           # <- 이게 있어야 사용 가능 함
# from deep_research import light_storm_app  # <- deep_research graph

# "/light-storm/stream" 등의 AI 전용 주소가 자동으로 생성 됨.
# add_routes(
#     app,
#     light_storm_app,
#     path="/light-storm",
# )

# add_routes로 생성되는 endpoints
# POST /light-storm/invoke: [invoke] 결과 한 번에 받기
# POST /light-storm/stream: [streming] 타자 치듯 실시간 받기
# GET /light-storm/playground: 웹에서 바로 테스트해보는 채팅창