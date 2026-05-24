# Mini Git 평가 기준 Q&A

## Q1. `INIT <user_name>` 명령어와 초기화 로직은 어디에 구현되어 있나요?

`INIT <user_name>`은 `minigit/cli.py`의 `execute()`에서 처리합니다. 입력 명령을 소문자로 바꾼 뒤 `init`이면 인자 1개를 검사하고 `repository.init(args[0])`을 호출합니다.

실제 초기화 로직은 `minigit/repository.py`의 `MiniGit.init()`에 있습니다. 이 메서드는 저장소를 사용 가능 상태로 만들고, 현재 작성자 이름을 저장하며, 기본 브랜치를 `main`으로 설정합니다. 또한 커밋 저장소, 커밋 순서 목록, 자식 간선 목록, 키워드 인덱스, 작성자 인덱스, 다음 커밋 ID를 모두 초기 상태로 되돌립니다.

핵심 상태는 다음과 같습니다.

```python
self.initialized = True
self.author = user_name
self.current_branch = "main"
self.branch_heads_by_name = {"main": None}
self.commits_by_hash = {}
self.commit_order = []
self.children = {}
self.keyword_index = {}
self.author_index = {}
self.next_id = 1
```

따라서 `INIT`은 단순 출력 명령이 아니라, 이후 `COMMIT`, `BRANCH`, `SWITCH`, `LOG`, `PATH`, `ANCESTORS`, `SEARCH`가 사용할 저장소 상태 전체를 준비하는 명령입니다.

## Q2. `BRANCH`, `SWITCH`, `COMMIT` 명령어와 브랜치 전환 로직은 어떻게 구현되어 있나요?

세 명령어는 `minigit/cli.py`의 `execute()`에서 각각 `create_branch()`, `switch_branch()`, `commit()`으로 연결됩니다.

`BRANCH <branch_name>`은 `MiniGit.create_branch()`가 처리합니다. 새 브랜치는 커밋을 복사하지 않고, 현재 브랜치가 가리키는 HEAD 커밋 해시를 그대로 가리킵니다.

```python
self.branch_heads_by_name[name] = self.branch_heads_by_name[self.current_branch]
```

`SWITCH <branch_name>`은 `MiniGit.switch_branch()`가 처리합니다. 브랜치가 존재하는지 확인한 뒤 `self.current_branch`만 바꿉니다. 즉 HEAD는 직접 커밋을 들고 있는 값이 아니라, 현재 브랜치 이름을 통해 간접적으로 결정됩니다.

`COMMIT <message>`는 `MiniGit.commit()`이 처리합니다. 새 커밋의 부모는 현재 브랜치의 HEAD입니다. 현재 브랜치에 커밋이 없다면 부모 없는 첫 커밋이 됩니다. 커밋 생성 후에는 현재 브랜치의 HEAD가 새 커밋 해시로 갱신됩니다.

```python
current_head = self.branch_heads_by_name[self.current_branch]
parents = [] if current_head is None else [current_head]
self.branch_heads_by_name[self.current_branch] = commit_hash
```

이 구조 때문에 브랜치 전환 후 커밋을 만들면, 새 커밋은 전환된 브랜치의 HEAD 위에 생성됩니다.

## Q3. `LOG` 명령어와 부모-자식 출력 순서는 어떻게 보장하나요?

`LOG` 명령어는 `minigit/cli.py`에서 `repository.log()`로 dispatch됩니다. 실제 출력은 `MiniGit.log()`가 담당합니다.

기본 `LOG`는 `self.commit_order`에 저장된 커밋 생성 순서를 사용합니다. 이 프로젝트에서는 새 커밋이 만들어질 때 항상 기존 커밋을 부모로 참조합니다. 따라서 생성 순서는 자연스럽게 부모가 자식보다 먼저 등장하는 순서입니다.

```python
self.commit_order.append(commit_hash)
```

`MiniGit.get_ordered_commits()`는 이 해시 목록을 따라 커밋 객체를 다시 가져옵니다.

```python
for commit_hash in self.commit_order:
    ordered.append(self.commits_by_hash[commit_hash])
```

출력 시에는 커밋 해시, 작성자, 시간, 브랜치 라벨, 부모 해시, 메시지를 순서대로 보여줍니다. 부모가 없으면 `parents: -`로 표시합니다.

## Q4. `PATH` 명령어의 최단 경로 탐색은 어떻게 구현되어 있나요?

`PATH <commit1> <commit2>`는 `MiniGit.path_between()`에서 구현되어 있습니다. 이 메서드는 두 커밋 해시가 존재하는지 먼저 확인하고, 커밋 그래프를 무방향 그래프로 보고 BFS를 수행합니다.

BFS를 선택한 이유는 간선 가중치가 모두 같을 때 최단 간선 수 경로를 가장 직접적으로 보장하기 때문입니다. `level`에는 현재 깊이의 경로 목록이 들어가고, 한 깊이를 모두 탐색한 뒤 다음 깊이로 넘어갑니다. 목표 커밋에 도달한 경로가 발견되면 그 깊이의 경로가 최단 경로입니다.

동일 길이의 최단 경로가 여러 개면 `"->".join(path)` 문자열 기준으로 직접 구현한 `insertion_sort()`를 사용해 사전순으로 가장 작은 경로를 선택합니다.

## Q5. `ANCESTORS` 명령어의 조상 탐색은 어떻게 구현되어 있나요?

`ANCESTORS <commit_hash>`는 `MiniGit.ancestors()`에서 구현되어 있습니다. 입력 커밋이 존재하는지 확인한 뒤, 해당 커밋의 `parents`에서 시작해 stack 기반 탐색을 수행합니다.

탐색 방향은 자식에서 부모 방향입니다. `visited` 집합을 사용해 같은 조상을 중복 방문하지 않도록 하고, 발견된 조상 해시는 `output`에 저장합니다.

```python
stack = list(self.commits_by_hash[commit_hash].parents)
while stack:
    current = stack.pop()
    if current in visited:
        continue
    visited.add(current)
    output.append(current)
```

최종 출력은 커밋 해시 기준으로 정렬해 안정적인 결과를 제공합니다. 조상이 없으면 `No ancestors`를 반환합니다.

## Q6. `SEARCH`와 옵션 검색, 정렬 기능은 어떻게 구현되어 있나요?

`SEARCH <keyword>`와 `SEARCH --author=<name>`은 `minigit/cli.py`의 `execute()`에서 구분됩니다. `--author=`로 시작하면 `repository.search_author()`를 호출하고, 그 외에는 `repository.search_keyword()`를 호출합니다.

검색은 전체 커밋을 매번 훑는 방식이 아니라 역색인을 사용합니다.

- `keyword_index`: 커밋 메시지 키워드에서 커밋 해시 목록으로 가는 딕셔너리
- `author_index`: 작성자 이름에서 커밋 해시 목록으로 가는 딕셔너리

정렬 기능은 `LOG --sort-by=date`, `LOG --sort-by=author`로 제공됩니다. `MiniGit.log()`에서 `sort_by` 값에 따라 직접 구현한 `insertion_sort()`를 호출합니다.

```python
commits = insertion_sort(commits, lambda commit: (commit.timestamp, commit.hash))
commits = insertion_sort(commits, lambda commit: (normalize_token(commit.author), commit.hash))
```

검색 결과 출력은 `render_search_results()`에서 담당하며, 결과 커밋은 `commit_order`를 기준으로 다시 정렬되어 부모-자식 생성 순서와 일관된 방식으로 표시됩니다.

## Q7. 커밋 저장소, 브랜치, HEAD 구조와 책임은 어떻게 분리되어 있나요?

저장소의 핵심 상태는 `MiniGit` 클래스에 모여 있지만, 역할별 자료구조는 분리되어 있습니다.

- `commits_by_hash`: 커밋 해시를 키로 커밋 객체를 빠르게 조회하는 저장소
- `commit_order`: 커밋 생성 순서를 보존하는 목록
- `branch_heads_by_name`: 브랜치 이름이 어떤 커밋 해시를 가리키는지 저장하는 브랜치 테이블
- `current_branch`: 현재 선택된 브랜치 이름
- `children`: 부모에서 자식으로 가는 보조 간선 목록
- `keyword_index`, `author_index`: 검색용 역색인

HEAD는 별도 커밋 객체가 아니라 `current_branch`와 `branch_heads_by_name[current_branch]`의 조합으로 표현됩니다. 이 구조는 실제 Git의 “브랜치 이름이 커밋을 가리키고, HEAD가 현재 브랜치를 가리키는 방식”을 단순화한 것입니다.

## Q8. 해시 기반 빠른 조회와 충돌 방지 전략은 무엇인가요?

커밋은 `commits_by_hash` 딕셔너리에 저장됩니다.

```python
self.commits_by_hash: dict[str, Commit] = {}
```

따라서 `PATH`, `ANCESTORS`, `LOG`, `SEARCH` 등에서 커밋 해시를 알고 있으면 평균적으로 O(1)에 가까운 시간에 커밋 객체를 조회할 수 있습니다.

해시는 실제 암호학적 해시가 아니라 학습과 테스트에 적합한 세션 내 결정적 ID입니다.

```python
commit_hash = f"c{self.next_id:06d}"
self.next_id += 1
```

충돌 방지는 `generate_hash()`의 while 루프에서 수행됩니다. 새로 만든 해시가 이미 `commits_by_hash`에 있으면 다음 번호를 다시 생성합니다.

```python
if commit_hash not in self.commits_by_hash:
    return commit_hash
```

현재 생성 방식에서는 순차 번호를 사용하므로 일반 실행에서는 충돌이 거의 발생하지 않지만, 방어적으로 존재 여부를 확인하도록 설계했습니다.

## Q9. 커밋 추가 시 역색인은 언제, 어떻게 갱신되나요?

역색인은 새 커밋이 생성된 직후 `MiniGit.commit()` 안에서 갱신됩니다.

```python
self.index_commit(commit)
```

`index_commit()`은 먼저 작성자 이름을 정규화해 `author_index`에 커밋 해시를 추가합니다. 그 다음 커밋 메시지를 공백 기준으로 나누고 소문자 정규화한 키워드를 `keyword_index`에 추가합니다.

```python
author_key = normalize_token(commit.author)
self.author_index.setdefault(author_key, []).append(commit.hash)
for keyword in split_message_keywords(commit.message):
    self.keyword_index.setdefault(keyword, []).append(commit.hash)
```

메시지 하나 안에서 같은 키워드가 반복될 수 있으므로 `split_message_keywords()`는 `seen` 집합을 사용해 한 커밋이 같은 키워드에 중복 등록되지 않도록 합니다.

## Q10. 명령어 간 그래프 탐색 로직은 어떻게 재사용되나요?

그래프 관련 상태와 탐색 로직은 `MiniGit` 내부에 모여 있습니다. 특히 `PATH`는 `neighbors()`를 통해 부모와 자식을 모두 포함한 이웃 목록을 가져옵니다.

```python
linked = set(self.commits_by_hash[commit_hash].parents)
linked.update(self.children.get(commit_hash, set()))
```

이렇게 이웃 계산을 `neighbors()`로 분리했기 때문에 `path_between()`은 간선 구성 방식보다 BFS 흐름에 집중할 수 있습니다. `ANCESTORS`는 부모 방향만 사용하므로 `Commit.parents`를 직접 따라갑니다. 두 명령 모두 동일한 커밋 저장소인 `commits_by_hash`와 동일한 그래프 데이터인 `parents`, `children`을 기반으로 동작합니다.

또한 정렬이 필요한 부분은 `sorting.py`의 `insertion_sort()`를 재사용합니다. 경로 tie-break, 조상 출력 정렬, 이웃 정렬, 로그 정렬이 모두 같은 정렬 helper를 사용합니다.

## Q11. docstring과 주석 작성 기준은 무엇인가요?

각 모듈과 주요 함수에는 docstring을 작성했습니다. 예를 들어 `repository.py`는 저장소 상태와 그래프 연산을 담당한다고 모듈 docstring에 명시하고, `MiniGit` 클래스도 인메모리 저장소의 책임을 설명합니다.

함수 docstring은 “무엇을 하는 함수인지”를 짧게 설명하는 기준으로 작성했습니다.

- `MiniGit.init()`: 저장소 초기화 또는 재설정
- `MiniGit.commit()`: 커밋 생성, 브랜치 포인터와 역색인 갱신
- `MiniGit.path_between()`: 무방향 최단 경로 탐색
- `MiniGit.ancestors()`: 부모 링크를 통한 조상 탐색
- `insertion_sort()`: 안정 삽입 정렬
- `merge_sort_custom()`: 안정 병합 정렬

주석은 모든 줄에 붙이지 않고, 명령 분기나 merge 전용 선택 인자처럼 읽는 사람이 헷갈릴 수 있는 지점에만 제한적으로 사용했습니다.

## Q12. 커밋 그래프가 DAG인 이유와 사이클이 생기면 어떤 문제가 있나요?

이 프로젝트의 커밋 그래프는 방향이 있는 비순환 그래프, 즉 DAG입니다. 새 커밋은 항상 이미 존재하는 현재 HEAD를 부모로 참조합니다. merge 커밋도 현재 브랜치 HEAD와 대상 브랜치 HEAD라는 기존 커밋들을 부모로 가집니다.

즉 간선 방향은 “새 커밋 -> 과거 부모 커밋”입니다. 새 커밋이 미래 커밋을 부모로 참조하지 않기 때문에 정상 흐름에서는 사이클이 생기지 않습니다.

사이클이 생기면 문제가 커집니다.

- `ANCESTORS`가 끝없이 부모를 따라갈 수 있습니다.
- 부모-자식 순서 출력이라는 의미가 깨집니다.
- “과거 커밋을 기반으로 새 커밋을 만든다”는 Git의 시간적 모델이 깨집니다.
- 최단 경로 탐색에서 방문 처리를 잘못하면 무한 탐색이 발생할 수 있습니다.

현재 구현은 `visited`와 `path` 검사를 사용해 탐색 중 무한 반복을 막고 있지만, 설계상 커밋 생성 방향을 제한해 DAG를 유지하는 것이 더 근본적인 해결입니다.

## Q13. `LOG` 명령어의 위상 정렬 성격은 어떻게 만족하나요?

기본 `LOG`는 별도의 위상 정렬 알고리즘을 매번 실행하지 않습니다. 대신 커밋 생성 규칙을 이용합니다.

이 프로젝트에서 커밋은 생성 시점에 이미 존재하는 커밋만 부모로 가질 수 있습니다. 따라서 어떤 커밋의 부모는 항상 그 커밋보다 먼저 `commit_order`에 들어갑니다.

이 성질 때문에 `commit_order` 자체가 부모가 자식보다 먼저 나오는 위상 정렬 결과와 같은 역할을 합니다. merge 커밋도 두 부모가 모두 기존 커밋이므로, merge 커밋은 항상 두 부모보다 뒤에 추가됩니다.

단, `LOG --sort-by=date`나 `LOG --sort-by=author`는 사용자가 명시적으로 정렬 기준을 바꾼 것이므로 기본 부모-자식 출력 조건보다 요청된 정렬 기준을 우선합니다.

## Q14. `PATH`에서 BFS를 선택한 이유와 무방향 간선 정의는 무엇인가요?

`PATH`의 목적은 두 커밋 사이의 최단 연결 경로를 찾는 것입니다. 커밋 그래프의 간선에는 별도 가중치가 없으므로, BFS가 최단 간선 수 경로를 보장합니다.

`PATH`에서는 부모 방향만 보지 않고, 부모와 자식 관계를 모두 이동 가능한 간선으로 봅니다. 예를 들어 서로 다른 브랜치의 두 커밋은 공통 조상을 통해 연결될 수 있어야 합니다.

이를 위해 `neighbors()`는 다음 두 종류를 합칩니다.

- 현재 커밋의 부모들: `Commit.parents`
- 현재 커밋의 자식들: `self.children[commit_hash]`

이 정의 덕분에 `c000002 -> c000001 -> c000003`처럼 한 브랜치 끝에서 공통 부모로 올라간 뒤 다른 브랜치 쪽 자식으로 내려가는 경로를 찾을 수 있습니다.

## Q15. 사용된 정렬 알고리즘의 시간복잡도와 안정 정렬 여부는 무엇인가요?

프로젝트에는 직접 구현한 두 가지 정렬이 있습니다.

`insertion_sort()`는 안정 정렬입니다. 앞의 값이 현재 값보다 클 때만 이동시키고, 같은 키 값에서는 기존 순서를 유지합니다. 시간복잡도는 평균과 최악이 O(n²), 이미 거의 정렬된 입력에서는 O(n)에 가까워질 수 있습니다. 로그 정렬, 경로 tie-break, 조상 정렬처럼 데이터 규모가 작거나 안정적인 결과가 중요한 곳에 사용합니다.

`merge_sort_custom()`도 안정 정렬입니다. 병합 시 왼쪽과 오른쪽의 키가 같으면 왼쪽 원소를 먼저 넣습니다.

```python
if compare_values(key_func(left[left_index]), key_func(right[right_index])) <= 0:
    merged.append(left[left_index])
```

병합 정렬의 시간복잡도는 평균과 최악 모두 O(n log n)입니다. `bench-sort` 명령에서 삽입 정렬과 성능 차이를 비교하는 용도로 사용합니다.

## Q16. 역색인의 성능적 이점은 무엇인가요?

역색인이 없으면 `SEARCH login`을 실행할 때마다 모든 커밋 메시지를 순회해야 합니다. 커밋 수를 n, 메시지 평균 길이를 m이라고 하면 검색마다 O(n * m)에 가까운 비용이 듭니다.

현재 구조에서는 커밋 생성 시 미리 다음 형태의 딕셔너리를 만들어 둡니다.

```text
keyword -> [commit_hash, commit_hash, ...]
author  -> [commit_hash, commit_hash, ...]
```

검색 시에는 정규화된 키로 딕셔너리를 조회하므로 후보 목록 접근은 평균적으로 O(1)에 가깝습니다. 이후 결과를 출력하기 위해 후보 수 k와 전체 순서 보정 비용이 추가됩니다. 현재 구현은 출력 순서를 `commit_order`에 맞추기 위해 전체 커밋 순서를 한 번 훑으므로 O(n)입니다.

즉 역색인은 “검색어와 관련 없는 커밋의 메시지를 다시 파싱하지 않는다”는 점에서 큰 이점이 있습니다. 특히 같은 저장소에서 검색을 여러 번 수행할수록 커밋 시점에 인덱싱 비용을 한 번 지불하는 구조가 유리합니다.

## Q17. 데이터 증가 시 병목 지점과 개선 방향은 무엇인가요?

데이터가 커질 때 예상되는 병목은 다음과 같습니다.

첫째, `render_search_results()`는 후보 해시를 찾은 뒤 출력 순서를 맞추려고 `commit_order` 전체를 순회합니다. 검색 결과가 적어도 전체 커밋 수 n에 비례하는 비용이 듭니다. 개선하려면 인덱스에 커밋 생성 순서를 함께 저장하거나, 커밋 해시에서 생성 순번으로 가는 맵을 두고 후보만 정렬하는 방식으로 바꿀 수 있습니다.

둘째, `refresh_branch_labels()`는 브랜치 라벨을 갱신할 때 모든 커밋을 순회합니다. 커밋이 많아지면 브랜치 생성이나 커밋마다 비용이 커질 수 있습니다. 개선하려면 커밋 객체에 라벨을 저장하지 않고, 로그 출력 시 브랜치 HEAD 역매핑을 계산하거나 `head_hash -> branch_names` 맵을 별도로 유지할 수 있습니다.

셋째, `PATH`는 동일 깊이의 여러 경로를 리스트로 들고 있어 분기 수가 커지면 메모리를 많이 사용할 수 있습니다. 개선하려면 predecessor 맵을 사용해 BFS를 수행하고, tie-break가 필요할 때 부모 후보만 관리하는 방식으로 바꿀 수 있습니다.

넷째, `insertion_sort()`는 O(n²)이므로 대규모 로그 정렬에는 부담이 됩니다. 정렬 요구가 커지면 이미 구현된 `merge_sort_custom()`을 로그 정렬에도 적용하는 것이 좋습니다.

## Q18. 간선 정의가 바뀌면 결과와 구현은 어떻게 달라지나요?

현재 `PATH`는 간선을 무방향으로 정의합니다. 즉 부모로 올라가는 이동과 자식으로 내려가는 이동이 모두 가능합니다. 그래서 서로 다른 브랜치의 커밋도 공통 조상을 거쳐 연결 경로를 찾을 수 있습니다.

만약 간선을 부모 방향으로만 정의하면, 최신 커밋에서 과거 조상으로 가는 경로는 찾을 수 있지만 조상에서 다른 브랜치의 자식으로 내려가는 경로는 찾을 수 없습니다. 예를 들어 `c000002`와 `c000003`이 같은 부모 `c000001`에서 갈라진 형제 커밋이면, `c000002 -> c000001`까지는 가능하지만 `c000001 -> c000003` 이동이 막혀 전체 경로가 없다고 나올 수 있습니다.

반대로 자식 방향으로만 정의하면 과거 커밋에서 미래 커밋으로 내려가는 경로는 찾을 수 있지만, 최신 커밋에서 조상으로 올라가는 경로는 찾을 수 없습니다.

따라서 `PATH`가 “커밋 그래프상 연결 관계”를 보여주는 명령이라면 현재처럼 부모와 자식을 모두 이웃으로 보는 무방향 정의가 적합합니다. 구현상으로도 이 정의는 `neighbors()` 한 곳에 모여 있어 변경 시 영향 범위를 줄일 수 있습니다.

## Q19. 정렬 요구사항이 강화되면 어떻게 해결할 수 있나요?

현재 기본 정렬 요구는 직접 구현한 정렬 알고리즘을 사용하는 것입니다. 그래서 `LOG --sort-by=date`, `LOG --sort-by=author`, 경로 tie-break, 조상 정렬에 `insertion_sort()`를 사용합니다.

정렬 요구가 강화될 수 있는 예시는 다음과 같습니다.

- 대규모 커밋에서도 빠른 정렬이 필요하다.
- 여러 기준을 조합해야 한다.
- 같은 키에서 원래 생성 순서를 반드시 유지해야 한다.
- 내림차순 옵션이 필요하다.

이 경우 우선 `merge_sort_custom()`을 일반 로그 정렬에도 적용할 수 있습니다. 병합 정렬은 안정 정렬이고 O(n log n)이므로 대규모 데이터에 더 적합합니다.

여러 기준 정렬은 key function을 튜플로 구성해 해결할 수 있습니다.

```python
lambda commit: (normalize_token(commit.author), commit.timestamp, commit.hash)
```

내림차순이 필요하면 정렬 함수에 `reverse` 옵션을 직접 추가하거나, 비교 함수를 확장해 기준별 방향을 받을 수 있습니다. 중요한 점은 Python 내장 `sort()`에 의존하지 않고, 프로젝트의 직접 구현 정렬 정책을 유지하면서 확장하는 것입니다.

## Q20. 해시 생성 방식 변경은 테스트와 디버깅에 어떤 영향을 주나요?

현재 해시는 `c000001`, `c000002`처럼 순차적으로 생성됩니다. 이 방식은 테스트와 디버깅에 유리합니다.

- 테스트에서 예상 출력이 안정적입니다.
- 사용자가 예시 명령을 따라 했을 때 문서와 같은 해시가 나옵니다.
- `PATH c000002 c000003` 같은 시나리오를 재현하기 쉽습니다.
- 로그를 읽을 때 생성 순서를 직관적으로 파악할 수 있습니다.

만약 실제 Git처럼 콘텐츠 기반 해시나 랜덤 해시로 바꾸면 테스트는 더 복잡해집니다. 매 실행마다 해시가 달라질 수 있거나, 메시지와 시간에 따라 해시가 바뀌면 예상 출력에 고정 해시를 쓰기 어렵습니다. 이 경우 테스트는 전체 문자열 비교 대신 정규식, 패턴 매칭, 또는 반환된 해시를 캡처해 다음 명령에 사용하는 방식으로 바뀌어야 합니다.

디버깅 측면에서도 순차 해시는 작은 프로젝트에서 상태 추적이 쉽습니다. 반면 콘텐츠 기반 해시는 실제 Git과 더 비슷하지만, 시간이나 작성자 등 어떤 필드를 해시에 포함하느냐에 따라 재현성이 달라집니다. 따라서 이 프로젝트에서는 학습과 검증을 위해 결정적이고 읽기 쉬운 세션 로컬 해시를 선택했습니다.
