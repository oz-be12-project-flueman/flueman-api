# 🤖 Flueman API – 디지털 휴먼 AI 가상비서 서비스

## 📌 프로젝트 소개
Flueman(플루맨, Fluent Human) API는 **디지털 휴먼 AI 가상비서 서비스**를 위한  
**AI 모델 배포용 API 서버**입니다.

- **목표**: 사용자 요청을 빠르고 안전하게 처리, AI 예측 결과 효율적 제공  
- **특징**: FastAPI 기반, MySQL + S3 데이터 관리, JWT 인증/보안, AWS 클라우드 네이티브 아키텍처  

---

## ⚙️ 주요 기능
1. **데이터베이스 설계**  
   - 사용자, 모델, 요청/응답, 피드백 관리  
   - MySQL 기반 스키마 설계  

2. **API 서버 (FastAPI)**  
   - RESTful API, JWT 인증  
   - 요청 검증 및 오류 처리  

3. **데이터 전처리 파이프라인**  
   - 정규화, 중복 제거, 토큰화, 결측값 처리  
   - 다양한 데이터 소스 통합  

4. **AI 모델 배포 및 모니터링**  
   - AWS ECS/Fargate 또는 EC2 배포  
   - CloudWatch + OpenTelemetry 모니터링  
   - 로그/장애 추적  

---

## 🏗 프로젝트 구조

### 🔑 기술 스택
- **FastAPI** (Uvicorn/Gunicorn)  
- **MySQL (RDS)** – 사용자/모델/요청/피드백 관리  
- **S3** – 학습/추론 아티팩트 저장  
- **Redis (옵션)** – 세션, 레이트리밋, 잡 큐  
- **모델 서버 (옵션)** – GPU 인스턴스 분리 배치  
- **CI/CD** – GitHub Actions → ECR → ECS  
- **Observability** – CloudWatch, OpenTelemetry  
- **보안** – JWT, AWS Secrets Manager, TLS, IAM 최소권한  

### 📂 디렉터리 구조
```bash
flueman-api/
 ├─ app/
 │  ├─ core/              # 전역 설정/보안/DB/로깅
 │  ├─ shared/            # 재사용 유틸/인터페이스
 │  ├─ features/          # 기능별 모듈
 │  │   ├─ auth/          # 인증/로그인
 │  │   ├─ users/         # 사용자 관리
 │  │   ├─ models_registry/ # 모델 메타 관리
 │  │   ├─ inference/     # 추론 API
 │  │   ├─ datasets/      # 데이터 업로드/전처리
 │  │   ├─ feedback/      # 피드백 관리
 │  │   ├─ monitoring/    # 모니터링/로그 조회
 │  │   └─ health/        # 헬스체크
 │  ├─ main.py            # FastAPI 엔트리포인트
 │  └─ middleware.py      # CORS, 로깅, 에러핸들러
 ├─ migrations/           # Alembic 마이그레이션
 ├─ tests/                # 기능별 테스트
 ├─ docker/               # Dockerfile, compose 등
 ├─ pyproject.toml
 └─ README.md
```
---
### 📂 데이터베이스 개요

- **users** : 사용자/권한
- **api_keys** : 외부 접근용 API Key (옵션)
- **sessions** : 세션/토큰 블랙리스트 관리
- **models** : 모델 버전/경로(S3)/태그
- **requests** : API 요청 로그 (요청/응답 메타)
- **predictions** : 예측 결과 (출력/스코어)
- **feedback** : 사용자 피드백 (정답/평가)
- **datasets** : 원천/전처리 데이터 메타 정보
- **preproc_jobs** : 데이터 전처리 잡 이력
- **audit_logs** : 보안/중요 이벤트 감사 로그
---
### 🌿 브랜치

- **main**  
  - 운영 배포용  
  - 직접 푸시 금지, Pull Request만 허용  
  - 필수 체크: 테스트, 린트, 빌드  
  - 병합 시 태그(`vX.Y.Z`) 생성 → 프로덕션 배포  

- **dev**  
  - 개발 통합 브랜치 (스테이징)  
  - 기능 브랜치 → dev 병합  
  - 기본 체크: 테스트, 린트  

- **release/***  
  - 릴리스 준비 브랜치  
  - 버그 수정만 허용  
  - 검증 완료 후 main/dev에 병합  

---
#### 네이밍 규칙
- 기능: `feature/<영역>/<세부>`  
- 버그픽스: `fix/<영역>/<이슈>`  
- 릴리스: `release/x.y.z`  
- 핫픽스: `hotfix/x.y.z` 
