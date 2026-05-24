# Mini Git 설명자료 V1

## 1. 프로젝트 한 문장 정의

> 이 프로젝트는 Python으로 만든 작은 Git 스타일 인메모리 커밋 관리 프로그램입니다.
> 사용자는 `INIT`, `COMMIT`, `BRANCH`, `SWITCH`, `LOG`, `PATH`, `ANCESTORS`, `SEARCH` 같은 명령을 입력하고, 프로그램은 커밋 그래프와 브랜치 상태를 메모리에서 관리합니다.

중요한 기준은 “Git을 완전히 구현했다”가 아닙니다.
이 프로젝트는 실제 Git의 파일 추적, 저장소 영속성, 네트워크 기능을 복제하는 것이 아니라, Git의 핵심 아이디어를 자료구조와 알고리즘 학습용으로 작게 구현한 프로젝트입니다.

중심 질문:

> 커밋이 서로 부모-자식 관계를 가지는 저장소를 만들 때, 어떤 자료구조와 알고리즘을 조합하면 Git과 비슷한 핵심 동작을 만들 수 있을까?

---

## 2. “이 프로그램이 무엇을 하는지”를 빠르게 고정시키기 위한 코드 설명 전 짧은 실행 예시

```bash
cd codex-harness/tasks/mission3_2/submission
python3 main.py
```

예시 입력:

```text
INIT Alice
COMMIT "Initial commit"
BRANCH feature
SWITCH feature
COMMIT "Add login feature"
LOG
QUIT
```

예상 출력의 핵심 형태:

```text
mini-git> Initialized repository.
Current branch: main
Current user: Alice
mini-git> [main c000001] Initial commit
mini-git> Created branch: feature
mini-git> Switched to branch: feature
mini-git> [feature c000002] Add login feature
mini-git> commit c000001 (Alice, ...)
parents: -
Initial commit
commit c000002 (Alice, ...) [feature]
parents: c000001
Add login feature
mini-git> Bye.
```

예시 해석:

- `INIT Alice`는 메모리 안에 저장소를 만들고 현재 사용자를 `Alice`로 설정합니다.
- `COMMIT "Initial commit"`은 첫 번째 커밋을 만듭니다.
- `BRANCH feature`는 현재 커밋을 가리키는 새 브랜치를 만듭니다.
- `SWITCH feature`는 현재 작업 브랜치를 `feature`로 바꿉니다.
- 두 번째 `COMMIT`은 `feature` 브랜치 위에 새 커밋을 만듭니다.
- `LOG`는 커밋 목록을 부모가 자식보다 먼저 보이도록 출력합니다.

여기까지는 단순한 명령어 프로그램처럼 보입니다.
하지만 이 프로젝트의 핵심은 “커밋들이 어떻게 연결되어 있고, 그 연결을 어떻게 빠르게 탐색하느냐”입니다.

---

## 3. 단순 커밋 목록에서 생기는 다섯 가지 문제

내부 구조로 넘어가는 출발 질문:

> 커밋 메시지를 그냥 리스트에 쌓기만 하면 Git 같은 동작을 만들 수 있을까요?

이 프로젝트에서는 적어도 다섯 가지 문제가 생깁니다.

### 문제 1. commit hash로 커밋을 빠르게 찾아야 한다

`PATH c000002 c000003` 또는 `ANCESTORS c000003` 같은 명령은 특정 커밋 hash에서 시작합니다.
전체 커밋을 매번 처음부터 끝까지 찾으면 느립니다.

필요한 구조: `commits` 딕셔너리

```text
"c000001" -> Commit(...)
"c000002" -> Commit(...)
"c000003" -> Commit(...)
```

효과: hash를 알면 해당 커밋 객체를 바로 찾을 수 있습니다.

### 문제 2. 브랜치는 커밋을 가리키는 이름이어야 한다

브랜치는 커밋을 복사하는 것이 아닙니다.
브랜치 이름이 어떤 커밋 hash를 가리키는지 기억하면 됩니다.

필요한 구조: `branches`

```text
branches

"main"    -> c000003
"feature" -> c000002

current_branch = "main"
```

핵심: HEAD는 현재 브랜치를 통해 간접적으로 현재 커밋을 가리킵니다.

### 문제 3. 커밋은 부모 관계를 가진 그래프여야 한다

Git의 커밋은 단순 배열이 아니라 부모를 가리키는 노드입니다.
새 커밋은 현재 HEAD를 부모로 갖습니다.
merge commit은 부모를 두 개 가질 수 있습니다.

필요한 구조: `Commit.parents`

```text
c000001
  |
  v
c000002

merge commit:

c000002     c000003
    \       /
     v     v
     c000004
```

이 구조는 방향이 있는 비순환 그래프, 즉 DAG입니다.

### 문제 4. 검색은 매번 전체 커밋을 훑지 않아야 한다

`SEARCH login`을 할 때 모든 커밋 메시지를 매번 확인할 수도 있습니다.
하지만 과제의 핵심은 역색인을 사용해 후보 커밋을 빠르게 가져오는 것입니다.

필요한 구조:

```text
keyword_index

"login" -> [c000002]
"feature" -> [c000002, c000003]

author_index

"alice" -> [c000001, c000002, c000003]
```

핵심: 검색어에서 커밋으로 바로 가는 길을 미리 만들어 둡니다.

### 문제 5. 그래프에서는 경로와 조상을 탐색해야 한다

`PATH c000002 c000003`은 두 커밋 사이의 최단 경로를 찾습니다.
`ANCESTORS c000004`는 특정 커밋의 모든 조상을 찾습니다.

필요한 알고리즘:

- 최단 경로: BFS
- 모든 조상 탐색: DFS 또는 stack 기반 탐색
- tie-break 정렬: 직접 구현한 정렬

---

## 4. 전체 구조 지도

이 프로젝트는 `main.py`를 실행 진입점으로 두고, 내부 책임을 여러 모듈로 나눕니다.

```text
사용자 입력
   |
   v
main.py
   |
   +--> minigit/cli.py: parse_command(), execute(), repl()
   |
   +--> minigit/repository.py: MiniGit 저장소 상태와 핵심 기능 관리
   |
   +--> minigit/models.py: Commit 커밋 노드 데이터
   |
   +--> minigit/sorting.py: insertion_sort(), merge_sort_custom()
   |
   +--> minigit/text_index.py: 검색 토큰 정규화
   |
   +--> minigit/diff_utils.py: render_line_diff() 보너스 diff
```

더 짧게 보면:

```text
REPL -> execute -> MiniGit -> Commit graph / indexes / algorithms
```

지도 해석:

> 사용자는 REPL에 명령을 입력합니다.
> `execute()`는 문자열 명령을 해석해서 `MiniGit` 메서드로 연결합니다.
> `MiniGit`은 실제 커밋, 브랜치, 인덱스, 그래프 탐색 상태를 관리합니다.

---

## 5. 파일별 역할 요약

| 파일 | 역할 | 핵심 |
|---|---|---|
| `submission/main.py` | 실행 진입점 | `repl()` 호출, 기존 import 호환성 유지 |
| `submission/minigit/__init__.py` | 패키지 공개 진입점 | 주요 클래스와 함수 export |
| `submission/minigit/cli.py` | CLI 계층 | 입력 파싱, 명령 dispatch, REPL |
| `submission/minigit/repository.py` | 저장소 핵심 로직 | MiniGit, 브랜치, 커밋, 탐색, 검색, merge |
| `submission/minigit/models.py` | 데이터 모델 | Commit |
| `submission/minigit/sorting.py` | 직접 구현 정렬 | insertion sort, merge sort |
| `submission/minigit/text_index.py` | 검색 토큰 처리 | 정규화, 메시지 키워드 분리 |
| `submission/minigit/diff_utils.py` | 보너스 diff | LCS 기반 line diff |
| `submission/README.md` | 사용자 설명 문서 | 실행 방법, 명령어, 구현 제약, 보너스 설명 |
| `scripts/check.sh` | 전체 검증 진입점 | 필수 명령, 정적 검사, 보너스 기능 검증 |
| `scripts/smoke.sh` | 빠른 핵심 검증 | 실행 가능성과 주요 명령 최소 확인 |

핵심 흐름: `main.py -> minigit.cli.repl() -> minigit.cli.execute() -> MiniGit method`.

---

## 6. 첫 번째 축: 명령은 어떻게 흘러가는가

대표 명령 `COMMIT "Add login feature"`가 프로그램 안에서 흘러가는 경로입니다.

```text
COMMIT "Add login feature"
   |
   v
repl()
   |
   v
execute(repository, line)
   |
   v
parse_command()
   |
   v
["COMMIT", "Add login feature"]
   |
   v
command = "commit"
   |
   v
repository.commit("Add login feature")
   |
   v
Commit 객체 생성
   |
   v
commits, commit_order, children, branches, indexes 갱신
   |
   v
"[branch c000002] Add login feature" 출력
```

이 흐름의 핵심: 명령 해석과 저장소 로직의 분리.

`execute()`는 다음을 담당합니다.

- 명령어 대소문자 정규화
- 인자 개수 검사
- `--sort-by=`, `--author=` 같은 옵션 형식 처리
- 알맞은 `MiniGit` 메서드 호출
- 잘못된 입력에 `Invalid args` 반환

`MiniGit`은 다음을 담당합니다.

- 저장소 초기화
- 브랜치와 HEAD 관리
- 커밋 생성
- 커밋 그래프 연결
- 검색 인덱스 관리
- 로그, 경로, 조상 탐색
- 보너스 merge와 sort benchmark

책임 분리의 효과: 입력 문법을 읽는 부분과 그래프 알고리즘을 읽는 부분을 따로 볼 수 있습니다.

---

## 7. CLI: 입력 문자열을 내부 명령으로 바꾸는 계층

`parse_command()`는 사용자가 입력한 문자열을 리스트로 바꿉니다.

```text
입력: commit "Add login feature"
   |
   v
shlex.split()
   |
   v
["commit", "Add login feature"]
```

`shlex.split`을 사용하는 이유는 따옴표 안의 공백을 하나의 인자로 다루기 위해서입니다.

예를 들어:

```text
commit "Add login feature"
```

이 입력은 다음처럼 처리되어야 합니다.

```text
["commit", "Add login feature"]
```

단순히 공백으로만 나누면 `"Add`, `login`, `feature"`처럼 쪼개져서 커밋 메시지를 제대로 다룰 수 없습니다.

### CLI 관찰 포인트

- 명령어는 `.lower()`로 소문자 변환 후 비교합니다.
- `exit` 또는 `quit`은 REPL을 종료합니다.
- 지원하지 않는 명령은 `Invalid args`를 반환합니다.
- 옵션은 `LOG --sort-by=date`, `SEARCH --author=<name>` 형식으로 처리합니다.

### 핵심 문장

> CLI는 Git 저장소를 직접 구현하는 부분이 아니라, 사용자의 문장을 `MiniGit` 메서드 호출로 바꾸는 번역 계층입니다.

---

## 8. 두 번째 축: MiniGit은 왜 중심인가

`MiniGit` 클래스는 이 프로젝트의 핵심입니다.
저장소의 모든 현재 상태가 이 객체 안에 있습니다.

내부 상태:

```text
initialized    : 저장소 초기화 여부
author         : 현재 사용자
current_branch : 현재 브랜치 이름
branches       : branch name -> head commit hash
commits        : commit hash -> Commit 객체
commit_order   : 커밋 생성 순서
children       : parent hash -> child hash 집합
keyword_index  : keyword -> commit hash 목록
author_index   : author -> commit hash 목록
next_id        : 다음 커밋 hash 생성을 위한 카운터
```

네 묶음으로 보는 MiniGit 상태:

### 묶음 1. 현재 저장소 상태

```text
initialized
author
current_branch
branches
```

이 묶음은 “지금 사용자가 어느 저장소, 어느 브랜치에서 작업 중인가”를 나타냅니다.

### 묶음 2. 커밋 그래프

```text
commits
commit_order
children
```

`commits`는 hash로 커밋을 찾는 빠른 조회 구조입니다.
`commit_order`는 부모가 자식보다 먼저 만들어졌다는 순서를 보존합니다.
`children`은 부모에서 자식으로 가는 역방향 간선을 따로 기억합니다.

### 묶음 3. 검색 인덱스

```text
keyword_index
author_index
```

검색 명령에서 전체 커밋을 매번 순회하지 않고 후보를 가져오기 위한 역색인입니다.

### 묶음 4. 보조 기능

```text
next_id
```

`c000001`, `c000002` 같은 세션 내 유일 hash를 만들기 위한 카운터입니다.

---

## 9. `INIT`: 저장소 상태의 출발점

`INIT <user_name>`은 저장소를 초기화합니다.

내부 흐름:

```text
init(user_name)
   |
   v
initialized = True
   |
   v
author = user_name
   |
   v
current_branch = "main"
   |
   v
branches = {"main": None}
   |
   v
commits, indexes, graph 상태 비우기
   |
   v
next_id = 1
```

핵심 변화:

1. 저장소가 사용 가능한 상태가 됩니다.
2. 기본 브랜치 `main`이 생깁니다.
3. 아직 커밋이 없으므로 `main`은 `None`을 가리킵니다.
4. 현재 사용자가 설정됩니다.

핵심 문장:

> `INIT`은 첫 커밋을 만드는 명령이 아니라, 커밋 그래프를 담을 빈 저장소 상태를 준비하는 명령입니다.

---

## 10. `COMMIT`: 그래프와 인덱스가 함께 갱신되는 명령

`COMMIT`은 이 프로젝트에서 가장 중요한 명령입니다.
커밋 하나를 추가하는 순간 여러 구조가 같이 바뀝니다.

`COMMIT <message>`의 내부 흐름:

```text
commit(message)
   |
   v
현재 브랜치 HEAD 확인
   |
   v
부모 목록 결정
   |
   v
새 hash 생성: c000001, c000002, ...
   |
   v
Commit 객체 생성
   |
   v
commits[hash]에 저장
   |
   v
commit_order에 hash 추가
   |
   v
children에서 parent -> child 연결 추가
   |
   v
현재 브랜치가 새 commit hash를 가리키게 갱신
   |
   v
keyword_index와 author_index 갱신
   |
   v
branch label 새로 계산
```

핵심 문장:

> `COMMIT`은 단순히 메시지를 저장하는 명령이 아니라, 커밋 그래프, 브랜치 포인터, 검색 인덱스를 한 번에 일관되게 갱신하는 명령입니다.

커밋 생성 후 상태 예시:

```text
commits
"c000001" -> Commit(message="Initial commit", parents=[])
"c000002" -> Commit(message="Add login feature", parents=["c000001"])

branches
"main" -> c000001
"feature" -> c000002

keyword_index
"login" -> ["c000002"]
"feature" -> ["c000002"]

author_index
"alice" -> ["c000001", "c000002"]
```

---

## 11. Commit 객체: 그래프의 노드

`Commit`은 커밋 그래프의 노드입니다.

각 커밋은 다음 정보를 가집니다.

```text
hash
message
author
timestamp
parents
branches
```

### 필드별 의미

| 필드 | 의미 |
|---|---|
| `hash` | 커밋을 찾기 위한 고유 ID |
| `message` | 커밋 메시지 |
| `author` | 작성자 |
| `timestamp` | 생성 시각 |
| `parents` | 부모 커밋 hash 목록 |
| `branches` | 이 커밋을 현재 가리키는 브랜치 이름 목록 |

중요한 필드는 `parents`입니다.
이 필드 때문에 커밋들이 단순 목록이 아니라 그래프가 됩니다.

```text
c000001.parents = []
c000002.parents = ["c000001"]
c000003.parents = ["c000001"]
c000004.parents = ["c000002", "c000003"]
```

`c000004`처럼 부모가 두 개인 커밋은 merge commit입니다.

---

## 12. Branch와 HEAD: 이름이 커밋을 가리키는 방식

브랜치는 커밋을 담는 별도 저장소가 아닙니다.
브랜치 이름이 특정 commit hash를 가리키는 구조입니다.

```text
branches

main    -> c000003
feature -> c000002

current_branch = "main"
```

`BRANCH feature`의 의미:

```text
현재 main이 c000001을 가리킴
feature도 c000001을 가리키게 생성
```

```text
main    -> c000001
feature -> c000001
```

`SWITCH feature`의 의미:

```text
current_branch = "feature"
```

그 다음 `COMMIT`을 하면:

```text
feature -> c000002
main    -> c000001
```

핵심 문장:

> 브랜치 전환은 커밋 데이터를 복사하는 일이 아니라, “이제 어느 브랜치 포인터를 움직일 것인가”를 바꾸는 일입니다.

---

## 13. LOG: 부모가 자식보다 먼저 나오는 이유

이 과제의 `LOG`는 최신순이 아닙니다.
부모 커밋이 자식 커밋보다 먼저 출력되어야 합니다.

이 프로젝트는 `commit_order`를 사용합니다.

```text
commit_order = [c000001, c000002, c000003]
```

왜 이것으로 충분한가:

> 새 커밋은 이미 존재하는 커밋만 부모로 가질 수 있습니다.
> 따라서 생성 순서를 보존하면 부모는 항상 자식보다 먼저 만들어집니다.

예시:

```text
commit c000001
parents: -
Initial commit

commit c000002
parents: c000001
Add login feature
```

핵심 문장:

> `LOG`의 기본 출력은 Git의 최신순 로그를 흉내 내는 것이 아니라, 커밋 그래프를 학습하기 쉽게 부모-자식 방향으로 보여주는 출력입니다.

---

## 14. 직접 정렬: `sorted()` 없이 날짜와 작성자 기준으로 보기

과제 제약상 Python의 `sorted()`나 `list.sort()`를 사용하지 않습니다.
대신 직접 구현한 정렬 알고리즘을 사용합니다.

구현된 정렬:

```text
insertion_sort()
merge_sort_custom()
```

`LOG --sort-by=date`:

```text
key = (commit.timestamp, commit.hash)
```

`LOG --sort-by=author`:

```text
key = (author 소문자, commit.hash)
```

`insertion_sort` 흐름:

```text
앞쪽은 이미 정렬된 구간
현재 원소를 하나 꺼냄
앞쪽에서 들어갈 위치를 찾음
한 칸씩 밀고 삽입
```

`merge_sort_custom`은 보너스 성능 비교에 사용합니다.

```text
반으로 나눔
각각 정렬
두 정렬된 목록을 병합
```

핵심 문장:

> 이 프로젝트에서 정렬은 라이브러리 호출 결과를 쓰는 기능이 아니라, 정렬 알고리즘 자체를 직접 구현하고 적용하는 학습 대상입니다.

---

## 15. SEARCH와 역색인: 전체 순회 대신 후보로 바로 가기

`SEARCH <keyword>`는 커밋 메시지에서 단어를 찾습니다.
하지만 검색할 때마다 모든 커밋 메시지를 확인하지 않습니다.

커밋이 만들어질 때 미리 인덱스를 갱신합니다.

```text
COMMIT "Add login feature"
   |
   v
split_message_keywords()
   |
   v
["add", "login", "feature"]
   |
   v
keyword_index 갱신
```

인덱스 예시:

```text
keyword_index

"add"     -> [c000002, c000003]
"login"   -> [c000002]
"feature" -> [c000002, c000003]
```

`SEARCH login` 흐름:

```text
search_keyword("login")
   |
   v
keyword_index["login"] 조회
   |
   v
[c000002]
   |
   v
commit_order 기준으로 결과 출력
```

`SEARCH --author=Alice`도 같은 원리입니다.

```text
author_index

"alice" -> [c000001, c000002, c000003]
```

핵심 문장:

> 역색인은 “커밋을 훑어서 검색어를 찾는 구조”가 아니라, “검색어에서 커밋 후보로 바로 가는 구조”입니다.

---

## 16. PATH: 커밋 그래프에서 최단 경로 찾기

`PATH <commit1> <commit2>`는 두 커밋 사이의 최단 경로를 찾습니다.
여기서 부모-자식 연결은 무방향 간선처럼 다룹니다.

예시 그래프:

```text
      c000001
      /     \
  c000002  c000003
```

입력:

```text
PATH c000002 c000003
```

출력:

```text
Path: c000002 -> c000001 -> c000003
```

내부 흐름:

```text
path_between(start, target)
   |
   v
BFS level을 path 목록으로 관리
   |
   v
현재 path의 마지막 커밋 확인
   |
   v
parents + children을 이웃으로 사용
   |
   v
target에 도달한 path 후보 수집
   |
   v
같은 길이 후보가 여러 개면 문자열 사전순 최소 선택
```

왜 `children`이 필요한가:

커밋 객체는 부모만 알고 있습니다.
하지만 `PATH`는 부모 방향과 자식 방향을 모두 이동해야 합니다.

그래서 commit 생성 때 다음 구조도 갱신합니다.

```text
children

c000001 -> {c000002, c000003}
```

핵심 문장:

> `PATH`는 커밋 그래프를 무방향 그래프로 보고 BFS로 가장 짧은 길을 찾는 기능입니다.

---

## 17. ANCESTORS: 부모 방향으로 올라가기

`ANCESTORS <commit_hash>`는 특정 커밋의 모든 조상을 출력합니다.

예시:

```text
c000001
  |
c000002
  |
c000003
```

입력:

```text
ANCESTORS c000003
```

결과:

```text
Ancestors of c000003:
- c000001: ...
- c000002: ...
```

내부 흐름:

```text
ancestors(commit_hash)
   |
   v
stack에 부모들을 넣음
   |
   v
하나씩 꺼내 방문
   |
   v
방문한 커밋의 부모도 stack에 추가
   |
   v
중복 방문은 visited로 방지
   |
   v
결과 hash를 직접 정렬 후 출력
```

`PATH`와의 차이:

| 기능 | 이동 방향 | 목표 |
|---|---|---|
| `PATH` | 부모와 자식 양방향 | 두 커밋 사이 최단 경로 |
| `ANCESTORS` | 부모 방향만 | 특정 커밋의 모든 조상 |

---

## 18. MERGE: 부모가 두 개인 커밋

`merge <branch_name>`은 보너스 기능입니다.
하지만 커밋 그래프를 이해하는 데 좋은 예시입니다.

상황:

```text
main    -> c000003
feature -> c000002
```

현재 브랜치가 `main`일 때:

```text
merge feature
```

새 커밋:

```text
c000004.parents = [c000003, c000002]
main -> c000004
```

그림:

```text
c000001
  |    \
  |     c000002  feature
  |
c000003          main before merge
  \     /
   v   v
  c000004        main after merge
```

핵심 문장:

> merge commit은 커밋 그래프가 단순한 선형 목록이 아니라 DAG라는 점을 가장 잘 보여주는 기능입니다.

---

## 19. DIFF와 line diff: 파일 추적이 아니라 비교 기능

`diff <file1> <file2>`는 보너스 기능입니다.
주의할 점은 이 프로그램이 Git처럼 파일 내용을 저장소에 추적하지는 않는다는 점입니다.

`diff`는 현재 파일 시스템에 존재하는 두 텍스트 파일을 읽어 줄 단위로 비교합니다.

출력 형태:

```text
Diff:
  same line
- old line
+ new line
```

내부 아이디어:

```text
render_line_diff(left, right)
   |
   v
LCS table 생성
   |
   v
공통 줄, 삭제 줄, 추가 줄을 순서대로 출력
```

핵심 문장:

> 이 프로젝트의 `diff`는 저장소에 파일을 기록하는 Git diff가 아니라, 두 외부 텍스트 파일을 비교하는 보너스 알고리즘 기능입니다.

---

## 20. 핵심 명령별 설명 스크립트

실제로 말할 수 있는 문장형 요약입니다.

### INIT

> `INIT`은 저장소를 초기화하는 명령입니다.
> 현재 사용자를 저장하고, 기본 브랜치 `main`을 만들고, 아직 커밋이 없으므로 `main`은 `None`을 가리키게 합니다.
> 이후 브랜치, 커밋, 검색 인덱스, 그래프 상태는 모두 이 초기 상태 위에서 쌓입니다.

### COMMIT

> `COMMIT`은 새 커밋 노드를 만드는 명령입니다.
> 현재 브랜치가 가리키는 HEAD를 부모로 삼고, `c000001` 같은 세션 내 고유 hash를 만듭니다.
> 그런 다음 `commits`에 저장하고, 생성 순서를 `commit_order`에 추가하고, 부모에서 자식으로 가는 `children` 정보도 갱신합니다.
> 마지막으로 현재 브랜치 포인터를 새 커밋으로 이동시키고, 메시지 keyword와 author 역색인을 갱신합니다.

### BRANCH / SWITCH

> `BRANCH`는 현재 HEAD를 가리키는 새 브랜치 이름을 만듭니다.
> `SWITCH`는 현재 작업 브랜치 이름만 바꿉니다.
> 즉, 브랜치는 커밋 복사본이 아니라 commit hash를 가리키는 포인터입니다.

### LOG

> `LOG`는 커밋을 출력하는 명령입니다.
> 기본 로그는 최신순이 아니라 부모가 자식보다 먼저 나오도록 `commit_order`를 사용합니다.
> `LOG --sort-by=date`와 `LOG --sort-by=author`는 Python 내장 정렬 API가 아니라 직접 구현한 insertion sort로 정렬합니다.

### PATH

> `PATH`는 두 커밋 사이의 최단 경로를 찾는 명령입니다.
> 부모 관계를 무방향 간선처럼 보고 BFS로 level 단위 탐색을 합니다.
> 같은 길이의 경로가 여러 개면 `hash->hash` 문자열 기준 사전순으로 가장 작은 경로를 고릅니다.

### ANCESTORS

> `ANCESTORS`는 특정 커밋의 모든 조상을 찾는 명령입니다.
> 시작 커밋의 부모들을 stack에 넣고, 부모 방향으로 계속 올라가며 방문합니다.
> 이미 방문한 커밋은 `visited`로 중복을 막습니다.

### SEARCH

> `SEARCH`는 메시지 keyword 또는 author로 커밋을 찾는 명령입니다.
> 검색할 때 전체 커밋을 훑는 것이 아니라, commit 생성 시 미리 만들어 둔 역색인에서 후보 commit hash를 가져옵니다.

### MERGE

> `merge`는 현재 브랜치 HEAD와 대상 브랜치 HEAD를 부모로 갖는 커밋을 만듭니다.
> 이 기능은 커밋 그래프가 단순 연결 리스트가 아니라 부모를 여러 개 가질 수 있는 DAG라는 점을 보여줍니다.

---

## 21. 예상 질문과 답변


---

## 22. 짧은 비유

구조를 빠르게 잡기 위한 짧은 비유입니다.

### CLI

CLI는 접수 창구입니다.
사용자가 말한 문장을 받아서 내부 담당자인 `MiniGit`에게 넘깁니다.

### MiniGit

MiniGit은 저장소 관리자입니다.
브랜치가 어디를 가리키는지, 커밋들이 어떻게 연결되는지, 검색 인덱스가 어떻게 갱신되는지를 관리합니다.

### Commit

Commit은 사건 기록 카드입니다.
메시지, 작성자, 시각, 부모 커밋을 담고 있습니다.

### Branch

Branch는 책갈피입니다.
전체 커밋을 복사하는 것이 아니라 특정 커밋 hash를 가리킵니다.

### Commit graph

Commit graph는 족보입니다.
각 커밋은 부모를 알고 있고, merge commit은 부모가 둘일 수 있습니다.

### Inverted index

역색인은 찾아보기입니다.
검색어를 보면 어느 커밋들을 봐야 하는지 바로 알려줍니다.
