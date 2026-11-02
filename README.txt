FREQUENCY — ITERATIVE STUDIO / MacBook Neo

실행: START_WEBSITE.command (또는 터미널에서 bash START_WEBSITE.command)
초안: ACE-Step이 10초/4스텝 AI 오디오를 만들고 30초로 반복 확장합니다.
수정: 음색/저음/음량 변경은 Python에서 기존 오디오를 처리하고 새 버전으로 저장합니다.
기타 수정: 악기/멜로디/장르 변경은 '요청 반영해 AI 재생성'을 사용합니다.
고품질: 30초/8스텝 생성 모드도 선택할 수 있지만 느립니다.
모든 WAV 파일은 ~/Library/Application Support/FREQUENCY/tracks/ 에 저장됩니다.

주의:
- 빠른 초안은 기기 성능에 따라 수 분 이상 걸릴 수 있습니다. 즉시 AI 생성은 보장하지 않습니다.
- 짧은 AI 음악을 30초로 반복하면 음악적 다양성이 제한되고 경계가 완벽하지 않을 수 있습니다.
- ACE-Step 서버 API와 모델 버전이 다를 경우 API 호환성 수정이 필요할 수 있습니다.
- 서버 주소 http://127.0.0.1:8001/docs 는 API 서버 확인에 사용합니다.
- 이 버전은 전문 오디오 엔지니어링/마스터링 툴을 대체하지 않습니다.
