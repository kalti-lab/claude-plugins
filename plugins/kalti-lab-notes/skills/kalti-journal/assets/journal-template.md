---
id:        # 타입약어-슬러그 (예: exp-sampler-detail). 재사용 금지. 약어: exp/invest/build/read/meet/decide/retro
title:     # 무슨 작업인지 한 줄
date:      # YYYY-MM-DD
author:    # 본인 (journals/ 바로 아래 작성자 폴더 이름. 그 아래 프로젝트 하위폴더 이름이 아님)
type:      # experiment | investigation | build | reading | meeting | decision | retro
tags: []   # 허용 목록에서만 (SKILL.md 참고)
project: "[[종목 노트 이름]]"   # 예: "[[이미지생성-파이프라인]]"
# tests: "[[가설 노트 이름]]"   # 가설을 검증하는 experiment일 때만 이 줄을 살린다
---

# (title과 같은 제목)

## 질문 / 목적
무엇을, 왜.

## 배경
이어지는 맥락. 관련 일지가 있으면 [[파일 이름]]으로 링크.

## 한 일 (방법)
어떻게·왜 그 방법이었는지 서술. 결과를 좌우하는 고정값/변수·수치·버전은 그대로.
코드 내부 이름(함수·필드·플래그)은 뜻으로 풀어 쓰고, 한 줄에 한 메시지로.
(커밋 해시·단계 번호·diff/라인 수치·임시 스크립트 경로는 넣지 않는다 — SKILL.md 참고.)

## 결과 / 관찰
나온 그대로. 실패·이상치도 빼지 말 것.

## 해석 / 막힌 점·해결
관찰에서 무엇을 읽었나. 가설·발견이 떠오르면 여기 적어둔다(온톨로지 정제는 운영자 몫).

## 결정
무엇을, 왜.

## 다음 액션
