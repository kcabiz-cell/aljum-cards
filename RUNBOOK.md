# 알아줌 인스타 자동 게시 런북 (매주 화요일 21시 실행)

목표: Buffer(arajum_saju, 채널 ID 6ad8b0df778b240e2f7a3254, 조직 ID 6ad8b005fa2ac3e803d63a8d)에 다음 7일치 카드뉴스를 예약한다.
무료 플랜 한도: 예약 10건 이하. 게시 시각은 한국시간 매일 07:30 (dueAt 예: 2026-10-29T07:30:00+09:00, schedulingType=automatic, mode=customScheduled).
톤 원칙(절대 규칙): 따뜻함·위로·편안함. 공포·불안 조성 금지. 본문(일진 풀이)·카드·댓글/답글은 항상 긍정적이고 다정한 표현만 쓴다.
금지 표현 예: 흉, 불길, 재앙, 조심하라, 나쁜 날, 어긋남, 충돌, 사고, 이별 위험 등. 부담되는 관계(충·해·파)도 '새 바람/따뜻한 한마디/작은 정돈' 같은 긍정 표현으로 쓴다.
문체·내용 규칙: 해요체만 사용. 바넘 문장(누구에게나 들어맞는 모호한 단정, 읽는 사람의 성격·감정·사건을 짐작해 말하는 문장) 금지. '~일 거예요' 식 예언 대신 구체적이고 부담 없는 행동 제안('~해 보세요')으로 쓴다. 읽고 조금이라도 불쾌하거나 불안할 수 있는 표현은 절대 쓰지 않는다. 항상 위로와 응원의 톤.
팔로워 댓글에 답할 때도 늘 감사·공감·응원의 말투(존댓말)로, 부정적 예언이나 단정은 하지 않는다.
이미지 경로는 갱신 시 캐시를 피하려면 cards/YYYY-MM-DD/v2/ 처럼 새 폴더에 올린다.

## 절차
1. Buffer `list_posts`(status=scheduled)로 마지막 예약일 확인. 시작일 = 마지막 예약일 +1 (예약이 없으면 내일). 총 예약이 10건을 넘지 않게 7일치만 추가.
2. 이 저장소 `tools/`에서 `python3 -I tools/gen_content.py YYYY-MM-DD ...` 실행 → `tools/content_YYYY-MM-DD.json` 생성. (그룹은 2026-10-21=쥐~뱀을 기준으로 하루씩 번갈아 자동 결정)
3. 문구 품질을 직접 검토하고 어색하거나 겁주는 표현은 JSON에서 고친다. 반복이 심하면 문구를 새로 쓴다.
4. 각 날짜마다 `python3 -I tools/make_cards.py tools/content_YYYY-MM-DD.json` → `tools/out/YYYY-MM-DD/*.png`(8장). 두 장 이상 열어 글자 겹침/잘림 확인.
5. 이미지를 `cards/YYYY-MM-DD/01.png ~ 08.png`로 복사(정렬 순서대로), `tools/out`·`content_*.json`은 커밋하지 않아도 된다. main에 커밋·푸시.
6. 푸시 후 `https://raw.githubusercontent.com/kcabiz-cell/aljum-cards/main/cards/YYYY-MM-DD/01.png`가 200인지 확인.
7. 날짜별로 Buffer `create_post`: text = JSON의 `caption` 그대로, assets = 위 URL 8개(image만, 순서대로), metadata.instagram = {type: "post", shouldShareToFeed: true}. (firstComment는 유료 기능이라 사용 금지)
8. `list_posts`로 7건이 정상 예약됐는지 확인하고 사용자에게 한국어 존댓말로 결과를 짧게 보고한다.

## 메모
- 이미지는 반드시 공개 저장소 raw URL이어야 한다.
- Buffer 연결: claude.ai 커넥터(OAuth). 연결이 없으면 중단하고 사용자에게 재연결을 요청한다.
- 디자인은 1번 시안(v1, 플랫 색 구분)으로 확정. make_cards.py를 바꾸지 말 것.
