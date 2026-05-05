# Eval report - `20260503T103231Z-c5145a`

- Started: 2026-05-03T10:42:13.951285+00:00
- Questions: 30
- Agents: rag, graph
- Source: `/Users/emilesilvis/Dropbox/30 - 39 Projects/llms-on-graphs/graph-rag-graph-agent/eval_runs/20260503T103231Z-c5145a.json`

## Accuracy by category

Scores are mean judge grades (correct=1, partial=0.5, wrong=0); `n` is sample size in that cell.

| Category | rag | graph |
| --- | --- | --- |
| aggregation_count | 0.00 (n=4) | 0.50 (n=4) |
| dependency_chain | 0.75 (n=4) | 1.00 (n=4) |
| multi_hop_2 | 0.00 (n=5) | 0.60 (n=5) |
| multi_hop_3 | 0.25 (n=4) | 0.75 (n=4) |
| negation | 0.25 (n=4) | 0.25 (n=4) |
| one_hop | 0.80 (n=5) | 0.80 (n=5) |
| shared_neighbor | 0.75 (n=4) | 1.00 (n=4) |
| **overall** | **0.40** (n=30) | **0.70** (n=30) |

## Latency

| Agent | mean (s) | p95 (s) | n |
| --- | --- | --- | --- |
| rag | 8.90 | 17.66 | 30 |
| graph | 8.49 | 19.61 | 30 |

## Tool-call counts

Mean tool calls per question, per category. Higher = the agent needed more retrieval or refinement steps to answer.

| Category | rag | graph |
| --- | --- | --- |
| aggregation_count | 4.5 (n=4) | 4.5 (n=4) |
| dependency_chain | 8.5 (n=4) | 4.0 (n=4) |
| multi_hop_2 | 5.8 (n=5) | 3.6 (n=5) |
| multi_hop_3 | 6.8 (n=4) | 2.5 (n=4) |
| negation | 7.8 (n=4) | 8.5 (n=4) |
| one_hop | 1.0 (n=5) | 1.4 (n=5) |
| shared_neighbor | 4.0 (n=4) | 5.0 (n=4) |

## Failure attribution

Per category and agent, how each row was attributed by the oracle Cypher. `extraction_miss` = the gold answer is not reachable from the extracted graph (graph paradigm only); `agent_miss` = reachable but the agent answered wrong / partial; `agent_ok` = reachable and the agent answered correctly; `no_oracle` = the question has no seed_cypher (answer lives only in the markdown).

### rag

| Category | agent_ok | agent_miss | extraction_miss | no_oracle |
| --- | --- | --- | --- | --- |
| aggregation_count | 0 | 4 | 0 | 0 |
| dependency_chain | 2 | 2 | 0 | 0 |
| multi_hop_2 | 0 | 5 | 0 | 0 |
| multi_hop_3 | 1 | 3 | 0 | 0 |
| negation | 0 | 4 | 0 | 0 |
| one_hop | 4 | 1 | 0 | 0 |
| shared_neighbor | 3 | 1 | 0 | 0 |
| **total** | **10** | **20** | **0** | **0** |

### graph

| Category | agent_ok | agent_miss | extraction_miss | no_oracle |
| --- | --- | --- | --- | --- |
| aggregation_count | 1 | 3 | 0 | 0 |
| dependency_chain | 4 | 0 | 0 | 0 |
| multi_hop_2 | 3 | 2 | 0 | 0 |
| multi_hop_3 | 3 | 1 | 0 | 0 |
| negation | 0 | 4 | 0 | 0 |
| one_hop | 4 | 0 | 1 | 0 |
| shared_neighbor | 4 | 0 | 0 | 0 |
| **total** | **19** | **10** | **1** | **0** |

## Alias-folded tool calls (graph agent, v5)

Number of `reach` / `neighbourhood` / `resolve_entity` calls where two or more node-name spellings (alias siblings, e.g. `Auth Service` + `Authentication Service`) were unioned in the result. Quantifies how often v5's lever 1 (tool-level alias resolution) actually fired.

Total alias-folded tool calls across all questions: **52** (touched 22 of 30 graph rows).

| Question | Category | alias-folded calls |
| --- | --- | --- |
| `gold-001` | one_hop | 1 |
| `gold-002` | one_hop | 2 |
| `gold-005` | multi_hop_2 | 1 |
| `gold-006` | shared_neighbor | 4 |
| `gold-007` | aggregation_count | 2 |
| `gold-009` | multi_hop_3 | 1 |
| `gold-010` | dependency_chain | 3 |
| `gold-011` | one_hop | 1 |
| `gold-012` | one_hop | 1 |
| `gold-013` | multi_hop_2 | 3 |
| `gold-014` | multi_hop_2 | 1 |
| `gold-017` | multi_hop_3 | 1 |
| `gold-018` | multi_hop_3 | 2 |
| `gold-019` | dependency_chain | 1 |
| `gold-020` | dependency_chain | 2 |
| `gold-022` | shared_neighbor | 4 |
| `gold-023` | shared_neighbor | 4 |
| `gold-025` | aggregation_count | 5 |
| `gold-027` | aggregation_count | 1 |
| `gold-028` | negation | 4 |
| `gold-029` | negation | 4 |
| `gold-030` | negation | 4 |

## `find_rel_types_like` coverage (graph agent)

For each gold question that flagged concepts requiring rel-type unioning, did the graph agent invoke `find_rel_types_like` for each concept? A concept is matched fuzzily by token / stem overlap with the tool's `concept` arg.

| Question | Concept | Probed? |
| --- | --- | --- |
| `gold-001` | manages | no |
| `gold-002` | implemented in | no |
| `gold-003` | facilitates | no |
| `gold-004` | manages | no |
| `gold-004` | uses infrastructure | no |
| `gold-005` | authored | yes |
| `gold-005` | role | no |
| `gold-006` | implemented in | no |
| `gold-007` | manages | no |
| `gold-008` | manages | no |
| `gold-008` | depends on | no |
| `gold-009` | developed by | no |
| `gold-009` | uses for caching | no |
| `gold-010` | depends on | no |
| `gold-011` | implemented in | no |
| `gold-012` | uses cache | no |
| `gold-013` | operates | no |
| `gold-013` | leads | no |
| `gold-014` | developed by | no |
| `gold-014` | built with | no |
| `gold-015` | authored | no |
| `gold-015` | leads | no |
| `gold-016` | managed by | no |
| `gold-016` | depends on | no |
| `gold-016` | built with | no |
| `gold-017` | authored | no |
| `gold-017` | developed by | no |
| `gold-017` | built with | no |
| `gold-018` | managed by | no |
| `gold-018` | developed by | no |
| `gold-018` | role | no |
| `gold-019` | depends on | no |
| `gold-020` | depends on | no |
| `gold-021` | uses for caching | no |
| `gold-022` | uses cache | no |
| `gold-023` | implemented in | no |
| `gold-024` | integrates with | no |
| `gold-025` | has team | no |
| `gold-026` | implemented in | no |
| `gold-027` | integrates with | no |
| `gold-028` | managed by | no |
| `gold-028` | implemented in | no |
| `gold-029` | depends on | no |
| `gold-029` | managed by | no |
| `gold-030` | implemented in | no |
| `gold-030` | managed by | no |

## Per-question detail

### `gold-001` - *one_hop*

**Question:** Which team manages the Auth Service?

**Expected:** The Platform Team manages the Auth Service.
**Key entities:** Platform Team

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.1s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The Auth Service is managed by the **Platform Team** (source: [service-auth-service.md]).
- **graph** [OK correct, 9.4s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The team that manages the Auth Service is the **Platform Team**. This information was retrieved from the relationships associated with the Auth Service.

### `gold-002` - *one_hop*

**Question:** What programming language is the Payments Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** (no oracle for this question)

- **rag** [X wrong, 3.1s] (1 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java** (source: team-product.md).
- **graph** [X wrong, 5.7s] (2 tool calls, extraction_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java**. This information was retrieved from the relationship `[:IMPLEMENTED_IN]` in the graph.

### `gold-003` - *one_hop*

**Question:** What does Istio facilitate in the ShopFlow platform?

**Expected:** Istio facilitates service-to-service communication.
**Key entities:** service-to-service communication

**Oracle Cypher rows:** 1

- **rag** [OK correct, 5.3s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'service-to-service communication'.
    > Istio facilitates efficient service-to-service communication within the ShopFlow platform by providing a uniform way to secure, connect, and observe microservices. This service mesh is integral to the platform's microservices architecture, allowing for smooth management of complex distributed systems. Key microservices, including the Shopflow App, operate on this robust Istio infrastructure (sourc...
- **graph** [OK correct, 4.7s] (2 tool calls, agent_ok) - The agent's answer includes the expected entity and accurately describes Istio's role in the platform.
    > Istio facilitates service-to-service communication in the ShopFlow platform. Additionally, it provides security, observability, and traffic management, and is part of the microservices architecture and API ecosystem. It also supports canary releases (from the neighbourhood of Istio).

### `gold-004` - *multi_hop_2*

**Question:** Which infrastructure does the service managed by the Platform Team for authentication use?

**Expected:** It uses AWS, Kubernetes EKS, and Kafka.
**Key entities:** AWS, Kubernetes EKS, Kafka

**Oracle Cypher rows:** 3

- **rag** [X wrong, 5.6s] (2 tool calls, agent_miss) - The agent's answer does not mention AWS, Kubernetes EKS, or Kafka, which are the expected entities.
    > The Auth Service managed by the Platform Team uses a scalable infrastructure built with Python. It integrates with Redis to cache session data and authentication tokens, which helps reduce database load by serving token validation requests directly from the cache (source: [service-auth-service.md]).
- **graph** [X wrong, 1.9s] (agent_miss) - The agent's answer is an error message and does not address the question or mention any expected entities.
    > (agent error: RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}})

### `gold-005` - *multi_hop_2*

**Question:** Who authored the ADR about the QuickCart acquisition, and what is their role?

**Expected:** Bob Martinez, who is a Staff SRE, authored it.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 10.8s] (agent_miss) - The agent's answer is an error message and does not address the question or mention any expected entities.
    > (agent error: RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}})
- **graph** [OK correct, 30.8s] (12 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Bob Martinez and Staff SRE.
    > The ADR about the QuickCart acquisition, titled "ADR: QuickCart Acquisition and Integration," was authored by Bob Martinez, who holds the role of Staff SRE.   This information was gathered using the relationships from the entities "ADR: QuickCart Acquisition and Integration" and "Bob Martinez."

### `gold-006` - *shared_neighbor*

**Question:** Which programming language is used by both the Auth Service and the PII Service?

**Expected:** Python is used by both.
**Key entities:** Python

**Oracle Cypher rows:** 4

- **rag** [OK correct, 3.3s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service are developed using **Python**.   - Auth Service: Built with Python (source: service-auth-service.md). - PII Service: Developed in Python (source: service-pii-service.md).
- **graph** [OK correct, 8.5s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service use **Python** as their programming language.   - The Auth Service is built with Python. - The PII Service is developed in Python.  This information was gathered from the neighbourhoods of both services, specifically looking at the relationships that indicate the programming languages used.

### `gold-007` - *aggregation_count*

**Question:** How many services does the Platform Team manage?

**Expected:** The Platform Team manages 3 services (Auth Service, GraphQL Service, PII Service).
**Key entities:** 3, Auth Service, GraphQL Service, PII Service

**Oracle Cypher rows:** 1

- **rag** [X wrong, 8.6s] (6 tool calls, agent_miss) - The agent's answer lists only 2 services and omits the GraphQL Service, contradicting the expected answer.
    > The Platform Team manages **two services**:  1. **Auth Service** - Responsible for user authentication and secure access across applications. 2. **PII Service** - Focuses on user data protection, including continuous delivery, monitoring, and security protocols.  Thus, the count of services managed by the Platform Team is **2** (source: [service-auth-service.md](service-auth-service.md), [service-...
- **graph** [OK correct, 7.0s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages 3 services: PII Service, GraphQL Service, and Auth Service.

### `gold-008` - *negation*

**Question:** Among the services managed by the Platform Team, which ones do NOT depend on the Data Lineage Service?

**Expected:** The GraphQL Service and the PII Service do not depend on the Data Lineage Service.
**Key entities:** GraphQL Service, PII Service

**Oracle Cypher rows:** 2

- **rag** [~ partial, 9.4s] (7 tool calls, agent_miss) - The agent mentions the PII Service but omits the GraphQL Service, which is expected.
    > The services managed by the Platform Team that do NOT depend on the Data Lineage Service are:  1. PII Service  The Auth Service and Payments Service do depend on the Data Lineage Service (from the notes retrieved).
- **graph** [X wrong, 8.6s] (agent_miss) - The agent's answer is an error message and does not address the question or mention any expected entities.
    > (agent error: RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}})

### `gold-009` - *multi_hop_3*

**Question:** What database does the service authored (developed) by Bob Martinez use for caching?

**Expected:** The Auth Service, developed by Bob Martinez, uses Redis for caching.
**Key entities:** Auth Service, Redis

**Oracle Cypher rows:** 1

- **rag** [X wrong, 2.9s] (agent_miss) - The agent's answer is an error message and does not address the question or mention any expected entities.
    > (agent error: RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}})
- **graph** [OK correct, 4.9s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The service authored by Bob Martinez, known as the Auth Service, uses **Redis** for caching.   This information was gathered from the relationships associated with the Auth Service, specifically the `USES_DATABASE` relationship.

### `gold-010` - *dependency_chain*

**Question:** Which services depend on the Data Lineage Service, directly or transitively?

**Expected:** The Auth Service and the Payments Service depend on the Data Lineage Service.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 3

- **rag** [~ partial, 17.7s] (10 tool calls, agent_miss) - The answer includes expected entities but adds extra services not in the expected answer.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service**    - Transitive dependency: **Fraud Detection Service** 3. **Shopflow App**    - Transitive dependencies: **Recommendation Service**, **Mobile BFF Service**  Thus, the complete list of services is: - Auth Service - Payments Service - Fraud Detection Service - Sho...
- **graph** [OK correct, 6.7s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** (directly) 2. **Payments Service** (directly)  Both services have a direct dependency on the Data Lineage Service. The relationships were identified using the `DEPENDS_ON` and `RELIES_ON` relationship types.

### `gold-011` - *one_hop*

**Question:** What programming language is the Data Lineage Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 2.3s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in **Python** (source: service-data-lineage-service.md).
- **graph** [OK correct, 2.0s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in Python.

### `gold-012` - *one_hop*

**Question:** Which cache does the Auth Service use for storing session data?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.6s] (1 tool calls, agent_ok) - The agent's answer correctly states that the Auth Service uses Redis for caching session data.
    > The Auth Service uses Redis to cache session data and authentication tokens. This helps reduce the load on the primary database by serving token validation requests directly from the cache (source: technology-redis-cache.md).
- **graph** [OK correct, 2.6s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity, Redis.
    > The Auth Service uses Redis for storing session data. This was determined from the outgoing relationship indicating that it "uses database" Redis.

### `gold-013` - *multi_hop_2*

**Question:** Who leads the team that operates the QuickCart Orders Service?

**Expected:** Bob Martinez leads the Orders Team, which operates the QuickCart Orders Service.
**Key entities:** Bob Martinez, Orders Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 14.0s] (11 tool calls, hit step cap, agent_miss) - The answer does not mention any expected entities and states it needs more information.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 3.8s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The team that operates the QuickCart Orders Service is led by Bob Martinez.

### `gold-014` - *multi_hop_2*

**Question:** What programming language is the service developed by Bob Martinez built with?

**Expected:** Python - the Auth Service, which Bob Martinez developed, is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 11.1s] (5 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating JavaScript instead of Python and misses the 'Auth Service' entity.
    > The service developed by Bob Martinez is built with JavaScript.
- **graph** [OK correct, 6.7s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: 'Auth Service' and 'Python'.
    > The service developed by Bob Martinez, known as the Auth Service, is built with Python.

### `gold-015` - *multi_hop_2*

**Question:** Who authored the ADR about GDPR compliance, and what team do they lead?

**Expected:** Alice Chen authored the ADR and leads the SRE Team.
**Key entities:** Alice Chen, SRE Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 19.6s] (11 tool calls, hit step cap, agent_miss) - The answer is a refusal and does not mention any expected entities.
    > Sorry, need more steps to process this request.
- **graph** [X wrong, 5.0s] (agent_miss) - judge error: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}
    > (agent error: RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}})

### `gold-016` - *multi_hop_3*

**Question:** Which programming language is used by the service that is managed by the Platform Team and depends on the Data Lineage Service?

**Expected:** Python - the Auth Service is managed by the Platform Team, depends on the Data Lineage Service, and is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 7.4s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Python.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Auth Service**, which is implemented in **Python**.
- **graph** [X wrong, 3.7s] (agent_miss) - The agent's answer is an error message and does not address the question or mention any expected entities.
    > (agent error: RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}})

### `gold-017` - *multi_hop_3*

**Question:** What programming language is used by the service developed by the person who authored 'ADR: QuickCart Acquisition and Integration'?

**Expected:** Python - Bob Martinez authored the ADR and developed the Auth Service, which is built with Python.
**Key entities:** Bob Martinez, Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 18.1s] (11 tool calls, hit step cap, agent_miss) - The answer is a refusal and does not mention any expected entities or facts.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 7.3s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The programming language used by the service developed by Bob Martinez, who authored 'ADR: QuickCart Acquisition and Integration', is Python.   This was determined through the relationships found in the graph, specifically that the "Auth Service" is built with Python and is developed by Bob Martinez.

### `gold-018` - *multi_hop_3*

**Question:** What role does the person who developed the authentication service managed by the Platform Team have?

**Expected:** Staff SRE - Bob Martinez, who developed the Auth Service (managed by the Platform Team), is a Staff SRE.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 13.0s] (11 tool calls, hit step cap, agent_miss) - The agent's answer is a refusal and does not mention any expected entities.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 7.2s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Bob Martinez and Staff SRE.
    > Bob Martinez, who developed the Authentication Service managed by the Platform Team, has the role of Staff SRE (Site Reliability Engineer).   This information was gathered from the relationships associated with both the Authentication Service and Bob Martinez.

### `gold-019` - *dependency_chain*

**Question:** Which services rely on the Payments Service, directly or transitively?

**Expected:** The Fraud Detection Service relies on the Payments Service.
**Key entities:** Fraud Detection Service

**Oracle Cypher rows:** 1

- **rag** [OK correct, 13.5s] (10 tool calls, agent_ok) - The agent's answer includes the expected entity 'Fraud Detection Service' and provides additional relevant information.
    > The services that rely on the Payments Service, either directly or transitively, are:  1. **ShopFlow App** 2. **Data Lineage Service** 3. **Fraud Detection Service** 4. **Recommendation Service** (via ShopFlow App) 5. **Auth Service** (via Data Lineage Service)  Thus, the complete list of services is: ShopFlow App, Data Lineage Service, Fraud Detection Service, Recommendation Service, and Auth Ser...
- **graph** [OK correct, 3.6s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity.
    > The service that relies on the Payments Service, directly or transitively, is the **Fraud Detection Service**.

### `gold-020` - *dependency_chain*

**Question:** Which service, directly or transitively, depends on the ShopFlow application?

**Expected:** The Recommendation Service depends on the ShopFlow application.
**Key entities:** Recommendation Service

**Oracle Cypher rows:** 1

- **rag** [~ partial, 13.9s] (12 tool calls, agent_miss) - The answer mentions the Recommendation Service but includes additional, unnecessary services.
    > The services that directly or transitively depend on the ShopFlow application are:  1. **Payments Service** 2. **Recommendation Service** 3. **Data Lineage Service** 4. **Auth Service** 5. **Fraud Detection Service**  The Fraud Detection Service does not have any further dependencies.   These findings are based on the interdependencies outlined in the retrieved documents.
- **graph** [OK correct, 9.0s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The service that directly or transitively depends on the ShopFlow application is the **Recommendation Service**. This service relies on ShopFlow directly.   The key Cypher patterns used were `reach` to find dependencies and `neighbourhood` to explore the connections of the Recommendation Service.

### `gold-021` - *dependency_chain*

**Question:** Which services use Redis for caching or session storage? Consider all relationship types that express use/employ/cache.

**Expected:** The Auth Service and the Payments Service both use Redis for caching.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 2

- **rag** [OK correct, 5.7s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that use Redis for caching or session storage are:  1. **Auth Service**    - Uses Redis for caching session data and user credentials.  2. **Payments Service**    - Employs Redis for caching transaction histories and managing session data.  Both services utilize Redis to enhance performance and reduce load on their primary databases (from multiple sources including "technology-redis-c...
- **graph** [OK correct, 11.5s] (7 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The services that use Redis for caching or session storage are:  1. **Payments Service** 2. **Auth Service**  These services utilize Redis through the relationships: `IS_USED_BY`, `USES_DATABASE`, and `TO_BE_USED_FOR`.

### `gold-022` - *shared_neighbor*

**Question:** Which cache database is used by both the Auth Service and the Payments Service?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 4.4s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the Auth Service and the Payments Service use **Redis** as their cache database. Redis is utilized to cache session data and authentication tokens for the Auth Service, and to cache transaction histories and recent payment details for the Payments Service (source: technology-redis-cache.md).
- **graph** [OK correct, 4.6s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities, including Redis.
    > Both the **Auth Service** and the **Payments Service** use **Redis** as their cache database.   - The **Auth Service** has an outgoing relationship indicating it **uses** Redis. - The **Payments Service** also has an outgoing relationship indicating it **employs** Redis.  This information was gathered from the neighbourhoods of both services, where Redis was identified as a common cache database.

### `gold-023` - *shared_neighbor*

**Question:** Which programming language is used by both the Fraud Detection Service and the Recommendation Service?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.2s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service are implemented in **Python**.   - The Fraud Detection Service is designed to identify and prevent fraudulent activities and is implemented in Python (source: service-fraud-detection-service.md). - The Recommendation Service offers tailored recommendations and is also built using Python (source: service-recommendation-service.md).
- **graph** [OK correct, 8.9s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service use **Python** as their programming language.   This was determined by checking the outgoing relationships for each service:  - The Fraud Detection Service is implemented in Python. - The Recommendation Service is built using Python.   Thus, Python is the common programming language used by both services.

### `gold-024` - *shared_neighbor*

**Question:** Which services integrate with both the GraphQL Federation Layer and the Monolithic Django App?

**Expected:** The BFF Service and the Recommendation Service integrate with both.
**Key entities:** BFF Service, Recommendation Service

**Oracle Cypher rows:** 2

- **rag** [X wrong, 13.4s] (10 tool calls, agent_miss) - The agent's answer includes additional services not in the expected answer, contradicting the expected entities.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **BFF Service** 2. **Recommendation Service** 3. **Fraud Detection Service** 4. **Quickcart Orders Service**  These services are mentioned as key integrations for both the GraphQL Federation Layer and the Monolithic Django App (source: [service-graphql-service.md](service-graphql-service.md) a...
- **graph** [OK correct, 9.6s] (8 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **Recommendation Service** 2. **BFF Service**  These services were found in the outgoing relationships of both the GraphQL Federation Layer and the Monolithic Django App.

### `gold-025` - *aggregation_count*

**Question:** How many teams does the ShopFlow platform have?

**Expected:** ShopFlow has 9 teams - Catalog, Customer Experience, Data, Engineering, Logistics, Orders, Platform, Product, and the Site Reliability Engineering (SRE) Team.
**Key entities:** 9, Catalog Team, Customer Experience Team, Data Team, Engineering Team, Logistics Team, Orders Team, Platform Team, Product Team, Site Reliability Engineering (SRE) Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 8.8s] (5 tool calls, agent_miss) - The answer does not mention any of the expected teams or the number of teams, and provides irrelevant information.
    > The ShopFlow platform has approximately 1,500 dedicated professionals organized into several specialized teams (source: company-shopflow.md).
- **graph** [~ partial, 14.2s] (9 tool calls, agent_miss) - The agent's answer mentions 5 out of the 9 expected teams, missing 4 key entities.
    > The ShopFlow platform has 5 teams: Platform Team, Engineering Team, Logistics Team, SRE Team, and Product Team.

### `gold-026` - *aggregation_count*

**Question:** How many distinct services or components have their code implemented in Python?

**Expected:** 6 - the Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, and the Monolithic Django App.
**Key entities:** 6, Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 1

- **rag** [X wrong, 6.3s] (3 tool calls, agent_miss) - The agent's answer lists 5 services and misses key entities like Data Lineage Service and Monolithic Django App.
    > There are 5 distinct services implemented in Python: Auth Service, PII Service, Fraud Detection Service, Recommendation Service, and Shopflow App.
- **graph** [X wrong, 8.7s] (3 tool calls, agent_miss) - The agent's answer lists only 2 services, missing 4 expected entities and the total count of 6.
    > There are 2 distinct services implemented in Python: **Data Lineage Service** and **Fraud Detection Service**.

### `gold-027` - *aggregation_count*

**Question:** How many entities does the Fraud Detection Service directly integrate with (via INTEGRATES_WITH edges)?

**Expected:** 3 - Elasticsearch, Kibana, and QuickCart.
**Key entities:** 3, Elasticsearch, Kibana, QuickCart

**Oracle Cypher rows:** 1

- **rag** [X wrong, 6.1s] (4 tool calls, agent_miss) - The answer lists incorrect entities and misses Elasticsearch and Kibana, contradicting the expected answer.
    > The Fraud Detection Service directly integrates with 2 entities: Payments Service and QuickCart.
- **graph** [~ partial, 4.7s] (2 tool calls, agent_miss) - The answer states the correct number but lacks the specific entities: Elasticsearch, Kibana, and QuickCart.
    > The Fraud Detection Service directly integrates with 3 entities via INTEGRATES_WITH edges.

### `gold-028` - *negation*

**Question:** Among the services managed by the Platform Team, which ones are NOT implemented in Python?

**Expected:** The GraphQL Service is not documented as being implemented in Python (the Auth Service and PII Service both are).
**Key entities:** GraphQL Service

**Oracle Cypher rows:** 1

- **rag** [X wrong, 12.0s] (7 tool calls, agent_miss) - The agent's answer incorrectly identifies the Payments Service instead of the GraphQL Service as not implemented in Python.
    > The services managed by the Platform Team that are NOT implemented in Python are:  1. **Payments Service** - Implemented in Java.  Thus, the only service not implemented in Python is the Payments Service.   (Cited from: service-payments-service.md)
- **graph** [~ partial, 21.4s] (17 tool calls, agent_miss) - The answer correctly identifies the GraphQL Service but incorrectly includes the Auth Service as not implemented in Python.
    > The services managed by the Platform Team are: 1. PII Service 2. GraphQL Service 3. Auth Service  Among these, the only service that has been confirmed to be implemented in Python is the GDPR compliance, which is related to the PII Service. However, there is no information available regarding the implementation languages for the GraphQL Service and Auth Service.  Thus, the services managed by the ...

### `gold-029` - *negation*

**Question:** Among the services that depend on the Data Lineage Service, which are NOT managed by the Platform Team?

**Expected:** The Payments Service and the Monolithic Django App depend on the Data Lineage Service but are not managed by the Platform Team.
**Key entities:** Payments Service, Monolithic Django App

**Oracle Cypher rows:** 2

- **rag** [X wrong, 10.5s] (8 tool calls, agent_miss) - The agent's answer does not mention the expected entities and incorrectly identifies the Shopflow App.
    > The services that depend on the Data Lineage Service but are NOT managed by the Platform Team are:  - Shopflow App  This is based on the dependencies found (Auth Service, Payments Service, Shopflow App) and the management details (Auth Service and Payments Service are managed by the Platform Team).
- **graph** [~ partial, 12.4s] (8 tool calls, agent_miss) - The agent correctly identifies Payments Service but misses Monolithic Django App and incorrectly mentions Auth Service.
    > Among the services that depend on the Data Lineage Service, the one that is NOT managed by the Platform Team is **Payments Service**.   This was determined by checking the management relationships of both services that depend on the Data Lineage Service: Auth Service and Payments Service. Auth Service is managed by the Platform Team, while Payments Service is operated by the Product Team.

### `gold-030` - *negation*

**Question:** Among the services implemented in Python, which ones are NOT managed by the Platform Team?

**Expected:** The Data Lineage Service, the Fraud Detection Service, the Recommendation Service, and the Monolithic Django App are implemented in Python but not managed by the Platform Team.
**Key entities:** Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 4

- **rag** [~ partial, 10.6s] (9 tool calls, agent_miss) - The agent's answer mentions some expected entities but misses 'Data Lineage Service' and 'Monolithic Django App'.
    > The services implemented in Python that are **not** managed by the Platform Team are:  1. **Fraud Detection Service** 2. **Recommendation Service** 3. **Shopflow App**  The **Auth Service** and **PII Service** are managed by the Platform Team (source: service-auth-service.md, service-pii-service.md).
- **graph** [X wrong, 19.6s] (9 tool calls, agent_miss) - The agent's answer does not mention any of the expected entities and provides incorrect information.
    > The services implemented in Python that are **not** managed by the Platform Team are:  1. **Auth Service** - No implementation found. 2. **GraphQL Service** - No implementation found. 3. **PII Service** - Implemented in **PostgreSQL** and **Python**.  Thus, the only service that is not managed by the Platform Team and has a Python implementation is the **PII Service**.   The key Cypher patterns us...
