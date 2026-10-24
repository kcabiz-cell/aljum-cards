# 알아줌 인스타 자동 게시 런북 (매주 화요일 21시 실행 + 매일 점검에서 큐 보충)

목표: 위로·보듬음·다독임의 따뜻한 한마디 계정. Buffer(arajum_saju, 채널 ID 6ad8b0df778b240e2f7a3254, 조직 ID 6ad8b005fa2ac3e803d63a8d)에 다음 7일치 카드뉴스를 예약한다.
무료 플랜 한도: 예약 10건 이하. 게시 시각은 한국시간 매일 07:30 (dueAt 예: 2026-10-29T07:30:00+09:00, schedulingType=automatic, mode=customScheduled).
톤 원칙(절대 규칙): 따뜻함·위로·편안함. 공포·불안 조성 금지. 본문(일진 풀이)·카드·댓글/답글은 항상 긍정적이고 다정한 표현만 쓴다.
금지 표현 예: 흉, 불길, 재앙, 조심하라, 나쁜 날, 어긋남, 충돌, 사고, 이별 위험 등. 부담되는 관계(충·해·파)도 '새 바람/따뜻한 한마디/작은 정돈' 같은 긍정 표현으로 쓴다.
문체·내용 규칙: 해요체만 사용. 바넘 문장(누구에게나 들어맞는 모호한 단정, 읽는 사람의 성격·감정·사건을 짐작해 말하는 문장) 금지. '~일 거예요' 식 예언 대신 구체적이고 부담 없는 행동 제안('~해 보세요')으로 쓴다. 읽고 조금이라도 불쾌하거나 불안할 수 있는 표현은 절대 쓰지 않는다. 항상 위로와 응원의 톤.
팔로워 댓글에 답할 때도 늘 감사·공감·응원의 말투(존댓말)로, 부정적 예언이나 단정은 하지 않는다.
이미지 경로는 갱신 시 캐시를 피하려면 cards/YYYY-MM-DD/v2/ 처럼 새 폴더에 올린다.

## 절차 (매일 2회 구성: 아침 12띠 카드 + 저녁 위로 게시물)
- 매일 07:30 = **12띠 한 장 카드**(이미지 1장, 모든 요일). 2026-10-24 사용자 결정: "글씨가 작아도 12띠 운세를 매일 한 번에".
- 매일 21:30 = 위로 릴스(월·수·금·토) / 위로 이미지(일). 화·목 저녁은 없음(예약 한도 때문). 위로 문구 중 아침용(t=am)은 쓰지 않는다. 모든 위로 게시물 post_time은 21:30.
위로 이미지·릴스는 GitHub Actions(`comfort-assets`, 매주 화요일 20:00 KST)가 `comfort/YYYY-MM-DD/`에 만든다(`01.jpg` 또는 `reel.mp4`, `caption.txt`, `meta.json`).
1. Buffer `list_posts`(status=scheduled)로 마지막 예약일 확인(아침/저녁 각각). 예약 총합 10건 이하로, 부족한 날부터 채운다.
2. `git pull` 후 필요한 날짜의 `comfort/DATE/meta.json` 확인. 없으면 `gh api -X POST repos/kcabiz-cell/aljum-cards/actions/workflows/comfort-assets.yml/dispatches -f ref=main -f 'inputs[start]=YYYY-MM-DD' -f 'inputs[days]=7'` 실행, `gh api repos/kcabiz-cell/aljum-cards/actions/runs?per_page=1`로 success까지 대기 후 pull.
3. 아침 12띠 카드: `python3 -I tools/gen_content.py DATE`(content12_DATE.json 생성) → `python3 -I tools/make_card12.py tools/content12_DATE.json cards/DATE/all12.png` → 커밋·푸시 → raw URL 200 확인 → `create_post`(text=content12_DATE.json의 caption, assets=[{image:{url:raw .../cards/DATE/all12.png}}], instagram {type:"post", shouldShareToFeed:true}, dueAt DATE 07:30+09:00).
   (동물 그림은 tools/animals/*.png, 투명 배경. 칸 문구는 gen_content.py의 SHORT 풀에서 일진과 띠 관계로 고른다. 문구는 모두 해요체 행동 제안.)
4. 저녁 일요일 이미지: `create_post` text=caption.txt, assets=[{image:{url:raw .../comfort/DATE/01.jpg}}], instagram {type:"post", shouldShareToFeed:true}, dueAt DATE 21:30+09:00.
5. 저녁 월·수·금·토 릴스: text=caption.txt, assets=[{video:{url:raw .../comfort/DATE/reel.mp4}}], instagram {type:"reel", shouldShareToFeed:true}, dueAt DATE 21:30+09:00.
6. 업로드 전에 사진 한두 장 확인(사람 얼굴·로고·어두움이면 해당 폴더 삭제 후 재생성).
7. `list_posts`로 정상 예약 확인 후 사용자에게 한국어 존댓말로 짧게 보고.
8. 옛 8장 캐러셀(make_cards.py, 띠 6개씩 격일)은 더 쓰지 않는다(파일은 보존).

## 보너스 릴스 (저녁 21:30, 예약 여유 건수만큼만)
- 계절 자연 사진(Pixabay) + 위로·용기 문구·명언(`tools/bonus_lines.json`)으로 `comfort/YYYY-MM-DD-b/`에 생성. 실행: Actions `comfort-assets`의 `bonus` 입력에 날짜(쉼표 구분) 입력.
- 업로드: reel.mp4 raw URL, instagram {type:"reel", shouldShareToFeed:true}, dueAt = 해당 날짜 21:30(+09:00). 예약 총합 10건 한도 확인.
- 명언은 출처가 확실한 공유 저작물·속담만 쓰고, 출처를 화면에 표기한다.

## 메모
- Pixabay API 키: 저장소 Settings의 Variables 또는 Secrets에 `PIXABAY_API_KEY`. (Secrets 권장, 워크플로우는 둘 다 읽음)
- 배경 규칙: 밝은 자연·바다·하늘·꽃 (`QUERIES`), 너무 어두운 사진은 자동 제외. 음악은 직접 합성(저작권 없음).
- 이미지는 반드시 공개 저장소 raw URL이어야 한다.
- Buffer 연결: claude.ai 커넥터(OAuth). 연결이 없으면 중단하고 사용자에게 재연결을 요청한다.
- 12띠 카드 디자인: tools/make_card12.py (make_cards.py의 폰트·색 함수를 가져다 쓰므로 make_cards.py는 바꾸지 말 것).
