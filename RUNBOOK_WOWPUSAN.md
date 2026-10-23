# wow_pusan 운영 메모 (Buffer 채널 6adb11ab778b240e2f9a3f54)
- 콘셉트: 부산 외국인 관광객용 영어+한국어 가이드(맛집·명소·길찾기·불편 해결·재미난 이야기·롯데 자이언츠).
- 주 3회 예약(KST): 수 19:30 / 금 12:30 / 일 20:30. 예약 한도 10건(채널별 적용 확인됨).
- 제작: `tools/busan_posts.py`(스펙, 사실은 출처 확인된 것만) → Actions `busan-assets`(cands: 사진 후보, build: 카드) → Buffer 예약.
- 사진: Pixabay(상업 이용 가능). 후보 시트를 직접 보고 `tools/busan_photos.json`에 ID 기록.
- 사실 확인 원칙: 길·시간·가격은 출처 확인된 것만 쓰고 카드에 "Naver Map 재확인" 문구를 넣는다. 미확인 항목(해운대, 흰여울, BIFF광장, 송도 케이블카, 사직 최근접역 출구 등)은 추가 조사 후 사용.
- 1차 배치 9건: 10/25 지도앱, 10/28 감천, 10/30 음식, 11/1 자이언츠, 11/4 용궁사, 11/6 재미난 이야기, 11/8 광안리, 11/13 교통카드 외 자갈치(11/11).
- 롯데 소식: 2026 7위(64-77-3), 마무리캠프 11/4 미야자키, 2027 일정 미발표(발표되면 일정 게시물 추가).

## 주간 제작·예약 절차 (매주 토요일 자동 작업)
1. Buffer wow_pusan 채널의 예약 큐를 확인하고 마지막 예약일 +1부터, 수 19:30 / 금 12:30 / 일 20:30 슬롯에 최대 (10 - 현재 예약 건수)개, 보통 3개를 채운다.
2. 아래 주제 백로그에서 3개를 고른다(롯데 자이언츠 소식·일정은 시즌 중에는 주 1회 우선, 비시즌에는 2주 1회). 주제마다 WebSearch/WebFetch(조사 에이전트 병렬 사용)로 공식 출처(Visit Busan, VisitKorea, 부산시 영문 사이트, 구단 공식)를 확인하고, 출처가 확인된 사실만 쓴다. 길·가격이 미확인이면 빼고 "Naver Map 재확인" 문구를 유지한다.
3. `tools/busan_posts.py`에 새 항목을 추가(기존 slug 번호 이어서) → `python3 tools/busan_posts.py` → 커밋·푸시 → Actions `busan-assets` mode=cands → pull 후 `busan/cands/<slug>.jpg`를 직접 보고 장소에 맞는 사진 선택(사람 얼굴 크게 나온 사진·로고·장소와 무관한 사진 제외) → `tools/busan_photos.json`에 ID 추가 → mode=build → pull 후 카드 이미지를 직접 확인(글자 잘림·사진 불일치 시 수정).
4. 카드 확인 후 Buffer create_post(채널 6adb11ab778b240e2f9a3f54, assets=raw URL 이미지들, instagram {type:"post", shouldShareToFeed:true}, customScheduled, schedulingType automatic, caption=busan/<slug>/caption.txt). 예약 후 list_posts로 확인.
5. 사용 스킬: social-media-skills의 hook-writer(표지 문구), carousel-writer(구성), hashtag-strategy, instagram-seo.
6. 비밀번호·API 키는 어디에도 쓰지 않는다.

## 주제 백로그 (사용 후 줄 긋기)
- 해운대해수욕장·블루라인파크(가는 법 조사 필요), 흰여울문화마을, BIFF 광장·국제시장, 태종대, 송도해상케이블카·구름산책로, 부산역 KTX 도착 후 이동, 보수동 책방골목, 동래온천·동래파전, 서면 먹자골목, 오륙도 스카이워크
- 외국인 불편 해결 시리즈: 현금·카드·ATM, 짐 보관·배송, 영어 메뉴판·주문 팁, 날씨·계절별 옷차림, 심야 교통, 와이파이·eSIM
- 이야기: 피란수도 유적, 부산 사투리 몇 마디, 부산국제영화제 소식, 불꽃축제 일정(공식 발표 확인 후)
- 롯데 자이언츠: 2027 일정 발표 시 일정 게시물, 마무리캠프·감독 인선 소식, 사직구장 먹거리·응원 팁
