# Eval report - `20260503T110821Z-1e6867`

- Started: 2026-05-03T11:20:01.517778+00:00
- Questions: 30
- Agents: rag, graph
- Source: `/Users/emilesilvis/Dropbox/30 - 39 Projects/llms-on-graphs/graph-rag-graph-agent/eval_runs/20260503T110821Z-1e6867.json`

## Accuracy by category

Scores are mean judge grades (correct=1, partial=0.5, wrong=0); `n` is sample size in that cell.

| Category | rag | graph |
| --- | --- | --- |
| aggregation_count | 0.00 (n=4) | 0.38 (n=4) |
| dependency_chain | 0.75 (n=4) | 0.75 (n=4) |
| multi_hop_2 | 0.00 (n=5) | 0.90 (n=5) |
| multi_hop_3 | 0.25 (n=4) | 0.50 (n=4) |
| negation | 0.25 (n=4) | 0.38 (n=4) |
| one_hop | 0.80 (n=5) | 0.60 (n=5) |
| shared_neighbor | 0.75 (n=4) | 1.00 (n=4) |
| **overall** | **0.40** (n=30) | **0.65** (n=30) |

## Latency

| Agent | mean (s) | p95 (s) | n |
| --- | --- | --- | --- |
| rag | 9.84 | 16.71 | 30 |
| graph | 11.87 | 27.95 | 30 |

## Tool-call counts

Mean tool calls per question, per category. Higher = the agent needed more retrieval or refinement steps to answer.

| Category | rag | graph |
| --- | --- | --- |
| aggregation_count | 5.2 (n=4) | 4.2 (n=4) |
| dependency_chain | 6.0 (n=4) | 4.2 (n=4) |
| multi_hop_2 | 8.0 (n=5) | 3.6 (n=5) |
| multi_hop_3 | 9.8 (n=4) | 12.8 (n=4) |
| negation | 8.8 (n=4) | 11.0 (n=4) |
| one_hop | 1.0 (n=5) | 1.8 (n=5) |
| shared_neighbor | 4.0 (n=4) | 7.5 (n=4) |

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
| dependency_chain | 3 | 1 | 0 | 0 |
| multi_hop_2 | 4 | 1 | 0 | 0 |
| multi_hop_3 | 2 | 2 | 0 | 0 |
| negation | 1 | 3 | 0 | 0 |
| one_hop | 3 | 1 | 1 | 0 |
| shared_neighbor | 4 | 0 | 0 | 0 |
| **total** | **18** | **11** | **1** | **0** |

## `set_difference` adoption (graph agent, v6)

Number of `set_difference(candidate_cypher, exclude_cypher)` tool invocations that produced a populated diff (rather than an error). Quantifies how often v6's lever 1 (negation guard rail) actually fired - paradigm-symmetric to v5's alias-folded calls and v3's `find_rel_types_like` coverage.

Total `set_difference` calls across all questions: **16** (touched 8 of 30 graph rows).

| Question | Category | set_difference calls |
| --- | --- | --- |
| `gold-008` | negation | 1 |
| `gold-021` | dependency_chain | 2 |
| `gold-024` | shared_neighbor | 2 |
| `gold-025` | aggregation_count | 3 |
| `gold-026` | aggregation_count | 1 |
| `gold-028` | negation | 3 |
| `gold-029` | negation | 1 |
| `gold-030` | negation | 3 |

## Alias-folded tool calls (graph agent, v5)

Number of `reach` / `neighbourhood` / `resolve_entity` calls where two or more node-name spellings (alias siblings, e.g. `Auth Service` + `Authentication Service`) were unioned in the result. Quantifies how often v5's lever 1 (tool-level alias resolution) actually fired.

Total alias-folded tool calls across all questions: **72** (touched 25 of 30 graph rows).

| Question | Category | alias-folded calls |
| --- | --- | --- |
| `gold-002` | one_hop | 2 |
| `gold-004` | multi_hop_2 | 3 |
| `gold-006` | shared_neighbor | 6 |
| `gold-007` | aggregation_count | 2 |
| `gold-008` | negation | 3 |
| `gold-009` | multi_hop_3 | 5 |
| `gold-010` | dependency_chain | 3 |
| `gold-011` | one_hop | 2 |
| `gold-012` | one_hop | 1 |
| `gold-013` | multi_hop_2 | 3 |
| `gold-014` | multi_hop_2 | 1 |
| `gold-016` | multi_hop_3 | 10 |
| `gold-017` | multi_hop_3 | 1 |
| `gold-018` | multi_hop_3 | 2 |
| `gold-019` | dependency_chain | 1 |
| `gold-020` | dependency_chain | 2 |
| `gold-021` | dependency_chain | 2 |
| `gold-022` | shared_neighbor | 4 |
| `gold-023` | shared_neighbor | 4 |
| `gold-024` | shared_neighbor | 6 |
| `gold-025` | aggregation_count | 2 |
| `gold-027` | aggregation_count | 1 |
| `gold-028` | negation | 4 |
| `gold-029` | negation | 1 |
| `gold-030` | negation | 1 |

## `find_rel_types_like` coverage (graph agent)

For each gold question that flagged concepts requiring rel-type unioning, did the graph agent invoke `find_rel_types_like` for each concept? A concept is matched fuzzily by token / stem overlap with the tool's `concept` arg.

| Question | Concept | Probed? |
| --- | --- | --- |
| `gold-001` | manages | no |
| `gold-002` | implemented in | no |
| `gold-003` | facilitates | no |
| `gold-004` | manages | no |
| `gold-004` | uses infrastructure | no |
| `gold-005` | authored | no |
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
| `gold-025` | has team | yes |
| `gold-026` | implemented in | yes |
| `gold-027` | integrates with | no |
| `gold-028` | managed by | no |
| `gold-028` | implemented in | yes |
| `gold-029` | depends on | no |
| `gold-029` | managed by | yes |
| `gold-030` | implemented in | yes |
| `gold-030` | managed by | yes |

## Per-question detail

### `gold-001` - *one_hop*

**Question:** Which team manages the Auth Service?

**Expected:** The Platform Team manages the Auth Service.
**Key entities:** Platform Team

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.0s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The Auth Service is managed by the **Platform Team** (source: [service-auth-service.md](service-auth-service.md)).
- **graph** [OK correct, 2.4s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The team that manages the Auth Service is the Platform Team.

### `gold-002` - *one_hop*

**Question:** What programming language is the Payments Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** (no oracle for this question)

- **rag** [X wrong, 2.9s] (1 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java** (source: team-product.md).
- **graph** [X wrong, 4.2s] (2 tool calls, extraction_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java**. This information was retrieved from the relationship `[:IMPLEMENTED_IN]` in the graph.

### `gold-003` - *one_hop*

**Question:** What does Istio facilitate in the ShopFlow platform?

**Expected:** Istio facilitates service-to-service communication.
**Key entities:** service-to-service communication

**Oracle Cypher rows:** 1

- **rag** [OK correct, 2.9s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'service-to-service communication'.
    > Istio facilitates efficient service-to-service communication within the ShopFlow platform by providing a uniform way to secure, connect, and observe microservices. This service mesh is integral to the platform's microservices architecture, allowing for smooth management of complex distributed systems. Key microservices, including the Shopflow App, operate on this robust Istio infrastructure (sourc...
- **graph** [OK correct, 3.4s] (2 tool calls, agent_ok) - The agent's answer includes the expected entity and accurately describes Istio's role in the platform.
    > Istio facilitates service-to-service communication in the ShopFlow platform. Additionally, it provides security, observability, and traffic management, and is part of the microservices architecture and API ecosystem. It also supports canary releases (from the neighbourhood of Istio).

### `gold-004` - *multi_hop_2*

**Question:** Which infrastructure does the service managed by the Platform Team for authentication use?

**Expected:** It uses AWS, Kubernetes EKS, and Kafka.
**Key entities:** AWS, Kubernetes EKS, Kafka

**Oracle Cypher rows:** 3

- **rag** [X wrong, 5.0s] (2 tool calls, agent_miss) - The agent's answer does not mention AWS, Kubernetes EKS, or Kafka, which are the expected entities.
    > The Auth Service managed by the Platform Team uses a scalable infrastructure built with Python. It integrates with Redis to cache session data and authentication tokens, which helps reduce database load by serving token validation requests directly from the cache (source: [service-auth-service.md]).
- **graph** [OK correct, 5.9s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: AWS, Kubernetes EKS, and Kafka.
    > The service managed by the Platform Team for authentication, known as the Auth Service, uses the following infrastructure:  1. **Kafka** 2. **Kubernetes EKS** 3. **AWS**  These infrastructures are utilized for various functionalities within the Auth Service (from the neighbourhood of the Auth Service).

### `gold-005` - *multi_hop_2*

**Question:** Who authored the ADR about the QuickCart acquisition, and what is their role?

**Expected:** Bob Martinez, who is a Staff SRE, authored it.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 15.4s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the author or their role.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 7.7s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The ADR about the QuickCart acquisition was authored by Bob Martinez, who holds the role of Staff SRE. This information was gathered from the relationships associated with both the ADR and the author.

### `gold-006` - *shared_neighbor*

**Question:** Which programming language is used by both the Auth Service and the PII Service?

**Expected:** Python is used by both.
**Key entities:** Python

**Oracle Cypher rows:** 4

- **rag** [OK correct, 3.7s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity, Python.
    > Both the Auth Service and the PII Service are developed using **Python**.   - Auth Service: Built with Python (source: service-auth-service.md). - PII Service: Developed in Python (source: service-pii-service.md).
- **graph** [OK correct, 13.6s] (8 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the **Auth Service** and the **PII Service** are built using **Python**.   - The Auth Service is confirmed to be built with Python. - The PII Service is also developed in Python.  This information was gathered through the relationships indicating the programming languages used by each service.

### `gold-007` - *aggregation_count*

**Question:** How many services does the Platform Team manage?

**Expected:** The Platform Team manages 3 services (Auth Service, GraphQL Service, PII Service).
**Key entities:** 3, Auth Service, GraphQL Service, PII Service

**Oracle Cypher rows:** 1
**Oracle enumeration (3):** Auth Service, GraphQL Service, PII Service

- **rag** [X wrong, 16.7s] (10 tool calls, agent_miss) - The agent's answer lists incorrect services and misses expected entities like GraphQL Service and PII Service.
    > The Platform Team manages 3 services: Auth Service, Data Lineage Service, and Payments Service.
- **graph** [OK correct, 4.8s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages 3 services: PII Service, GraphQL Service, and Auth Service.

### `gold-008` - *negation*

**Question:** Among the services managed by the Platform Team, which ones do NOT depend on the Data Lineage Service?

**Expected:** The GraphQL Service and the PII Service do not depend on the Data Lineage Service.
**Key entities:** GraphQL Service, PII Service

**Oracle Cypher rows:** 2

- **rag** [~ partial, 13.9s] (7 tool calls, agent_miss) - The agent's answer mentions the PII Service but omits the GraphQL Service.
    > The services managed by the Platform Team that do NOT depend on the Data Lineage Service are:  1. PII Service  Thus, the only service that does not depend on the Data Lineage Service is the PII Service.   (Cited from: "platform_team_services" and "data_lineage_dependencies" in scratchpad)
- **graph** [OK correct, 11.1s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > Among the services managed by the Platform Team, the ones that do NOT depend on the Data Lineage Service are:  1. PII Service 2. GraphQL Service  This was determined by identifying the services managed by the Platform Team and excluding those that depend on the Data Lineage Service. The relevant Cypher patterns used were for managing services and checking dependencies.

### `gold-009` - *multi_hop_3*

**Question:** What database does the service authored (developed) by Bob Martinez use for caching?

**Expected:** The Auth Service, developed by Bob Martinez, uses Redis for caching.
**Key entities:** Auth Service, Redis

**Oracle Cypher rows:** 1

- **rag** [X wrong, 19.4s] (13 tool calls, agent_miss) - The agent's answer incorrectly identifies the service as 'Payments Service' instead of 'Auth Service'.
    > The service authored by Bob Martinez that uses a caching database is the **Payments Service**, which employs **Redis** for caching purposes. This caching layer helps reduce load time and improve response rates for frequent requests, particularly for transaction validations and session data management (from the "Payments Service" documentation).  In summary, the Payments Service developed by Bob Ma...
- **graph** [OK correct, 17.3s] (17 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Redis.
    > The service authored by Bob Martinez that uses caching is the **Auth Service**, which utilizes **Redis** as its database for caching.   This information was gathered through the relationships involving Bob Martinez and the Auth Service, specifically looking at the outgoing relationships from the Auth Service that indicate it uses Redis for caching.

### `gold-010` - *dependency_chain*

**Question:** Which services depend on the Data Lineage Service, directly or transitively?

**Expected:** The Auth Service and the Payments Service depend on the Data Lineage Service.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 3

- **rag** [~ partial, 16.4s] (8 tool calls, agent_miss) - The answer includes expected entities but adds extra services not in the expected answer.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** (direct dependency) 2. **Payments Service** (direct dependency) 3. **Shopflow App** (direct dependency) 4. **Recommendation Service** (transitive dependency via Shopflow App) 5. **Mobile BFF Service** (transitive dependency via Shopflow App)  These dependencies illustrate the interconne...
- **graph** [OK correct, 6.1s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service**  Both services have a direct dependency on the Data Lineage Service. The relationships were identified using the `DEPENDS_ON` and `RELIES_ON` relationship types.

### `gold-011` - *one_hop*

**Question:** What programming language is the Data Lineage Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.6s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in **Python** (source: [service-data-lineage-service.md :: Data Lineage Service > Overview]).
- **graph** [OK correct, 7.0s] (2 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in Python. This information was retrieved from the relationship `IS_IMPLEMENTED_IN` in the graph.

### `gold-012` - *one_hop*

**Question:** Which cache does the Auth Service use for storing session data?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 4.1s] (1 tool calls, agent_ok) - The agent's answer correctly states that the Auth Service uses Redis for caching session data.
    > The Auth Service uses Redis to cache session data and authentication tokens. This helps reduce the load on the primary database by serving token validation requests directly from the cache (source: technology-redis-cache.md).
- **graph** [X wrong, 5.6s] (2 tool calls, agent_miss) - The answer does not mention Redis and instead lists unrelated information about caches and relationships.
    > The Auth Service uses the following caches for storing session data:  1. authentication tokens 2. session data  These were identified through the relationship `CACHES` in the graph.

### `gold-013` - *multi_hop_2*

**Question:** Who leads the team that operates the QuickCart Orders Service?

**Expected:** Bob Martinez leads the Orders Team, which operates the QuickCart Orders Service.
**Key entities:** Bob Martinez, Orders Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 16.4s] (11 tool calls, hit step cap, agent_miss) - The answer does not mention any expected entities and indicates a lack of information.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 4.7s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The team that operates the QuickCart Orders Service is led by Bob Martinez.

### `gold-014` - *multi_hop_2*

**Question:** What programming language is the service developed by Bob Martinez built with?

**Expected:** Python - the Auth Service, which Bob Martinez developed, is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 6.9s] (5 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating JavaScript instead of Python and misses the 'Auth Service' entity.
    > The service developed by Bob Martinez is built with JavaScript.
- **graph** [OK correct, 4.6s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: 'Auth Service' and 'Python'.
    > The service developed by Bob Martinez, known as the Auth Service, is built with Python.

### `gold-015` - *multi_hop_2*

**Question:** Who authored the ADR about GDPR compliance, and what team do they lead?

**Expected:** Alice Chen authored the ADR and leads the SRE Team.
**Key entities:** Alice Chen, SRE Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 15.3s] (11 tool calls, hit step cap, agent_miss) - The answer is a refusal and does not mention any expected entities.
    > Sorry, need more steps to process this request.
- **graph** [~ partial, 3.6s] (3 tool calls, agent_miss) - The agent correctly identifies Alice Chen but incorrectly states the team she leads.
    > Alice Chen authored the ADR about GDPR compliance and leads the Customer Experience Team.

### `gold-016` - *multi_hop_3*

**Question:** Which programming language is used by the service that is managed by the Platform Team and depends on the Data Lineage Service?

**Expected:** Python - the Auth Service is managed by the Platform Team, depends on the Data Lineage Service, and is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 7.5s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Auth Service**. It is built using the **Python** programming language.   Sources:  - Auth Service overview (service-auth-service.md) - Data Lineage Service dependencies (service-data-lineage-service.md)
- **graph** [X wrong, 18.1s] (11 tool calls, agent_miss) - The agent's answer mentions 'Payments Service' and 'Java', which contradicts the expected 'Auth Service' and 'Python'.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Payments Service**, which is implemented in **Java**.   This was determined by first identifying the Payments Service as the middle entity that the Platform Team manages and which depends on the Data Lineage Service. The programming language used by the Payments Service was found to be Java through its outgo...

### `gold-017` - *multi_hop_3*

**Question:** What programming language is used by the service developed by the person who authored 'ADR: QuickCart Acquisition and Integration'?

**Expected:** Python - Bob Martinez authored the ADR and developed the Auth Service, which is built with Python.
**Key entities:** Bob Martinez, Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 15.8s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the expected entities or the programming language used.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 9.2s] (4 tool calls, agent_ok) - The agent's answer includes all expected entities and accurately states the same facts as the expected answer.
    > The programming language used by the service developed by Bob Martinez, who authored 'ADR: QuickCart Acquisition and Integration', is Python. This was determined from the relationship indicating that the Auth Service, which he developed, is built with Python.   Key Cypher patterns used: 1. `MATCH (s:Entity {name: 'ADR: QuickCart Acquisition and Integration'})<-[:AUTHOR_OF]-(a:Entity) RETURN a.name...

### `gold-018` - *multi_hop_3*

**Question:** What role does the person who developed the authentication service managed by the Platform Team have?

**Expected:** Staff SRE - Bob Martinez, who developed the Auth Service (managed by the Platform Team), is a Staff SRE.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 15.8s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about Bob Martinez or the role of Staff SRE.
    > Sorry, need more steps to process this request.
- **graph** [X wrong, 51.3s] (19 tool calls, hit step cap, agent_miss) - The agent's answer is a refusal and does not mention any expected entities.
    > Sorry, need more steps to process this request.

### `gold-019` - *dependency_chain*

**Question:** Which services rely on the Payments Service, directly or transitively?

**Expected:** The Fraud Detection Service relies on the Payments Service.
**Key entities:** Fraud Detection Service

**Oracle Cypher rows:** 1

- **rag** [OK correct, 18.3s] (10 tool calls, agent_ok) - The agent's answer includes the expected entity 'Fraud Detection Service' and aligns with the expected answer.
    > The services that rely on the Payments Service, either directly or transitively, are:  1. **ShopFlow App** 2. **Data Lineage Service**    - Depends on: **Auth Service** 3. **Fraud Detection Service**    - Depends on: **Recommendation Service**  Thus, the complete list of services is: - ShopFlow App - Data Lineage Service - Auth Service (transitive) - Fraud Detection Service - Recommendation Servic...
- **graph** [OK correct, 2.9s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity.
    > The service that relies on the Payments Service, directly or transitively, is the **Fraud Detection Service**.

### `gold-020` - *dependency_chain*

**Question:** Which service, directly or transitively, depends on the ShopFlow application?

**Expected:** The Recommendation Service depends on the ShopFlow application.
**Key entities:** Recommendation Service

**Oracle Cypher rows:** 1

- **rag** [~ partial, 11.7s] (4 tool calls, agent_miss) - The agent's answer includes the Recommendation Service but adds unrelated services, making it partially correct.
    > The services that directly or transitively depend on the ShopFlow application are:  1. **Payments Service**: Integrates with the ShopFlow App for transaction workflows. 2. **Recommendation Service**: Depends on the ShopFlow App to access user interaction data for generating recommendations. 3. **Data Lineage Service**: Directly depends on the ShopFlow App for tracking data flow as part of the shop...
- **graph** [OK correct, 10.8s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Recommendation Service'.
    > The service that directly depends on the ShopFlow application is the **Recommendation Service**. This was determined through a direct relationship identified in the graph.

### `gold-021` - *dependency_chain*

**Question:** Which services use Redis for caching or session storage? Consider all relationship types that express use/employ/cache.

**Expected:** The Auth Service and the Payments Service both use Redis for caching.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 2

- **rag** [OK correct, 5.0s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The services that use Redis for caching or session storage are:  1. **Auth Service**    - Uses Redis to cache session data and user credentials.  2. **Payments Service**    - Employs Redis for caching transaction histories and managing session data.  Both services utilize Redis to enhance performance by reducing load on the primary database and improving response times (sources: technology-redis-c...
- **graph** [X wrong, 20.9s] (8 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating no services use Redis for caching.
    > No services were found that use Redis for caching or session storage. The attempts to find services using various relationship types related to "use" and "caching" returned no matches. Specifically, both the Payments Service and Auth Service were identified as using Redis, but they do not have any outgoing relationships indicating they use Redis for caching or session storage.   Key Cypher pattern...

### `gold-022` - *shared_neighbor*

**Question:** Which cache database is used by both the Auth Service and the Payments Service?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 4.4s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the Auth Service and the Payments Service use **Redis** as their cache database. Redis is utilized to cache session data and authentication tokens for the Auth Service, and to cache transaction histories and recent payment details for the Payments Service (source: technology-redis-cache.md).
- **graph** [OK correct, 14.9s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity, Redis.
    > Both the **Auth Service** and the **Payments Service** use **Redis** as their cache database.   - The **Auth Service** has an outgoing relationship indicating it **uses** Redis. - The **Payments Service** also has an outgoing relationship indicating it **employs** Redis.  This information was gathered from the neighbourhoods of both services, where Redis was identified as a common cache database.

### `gold-023` - *shared_neighbor*

**Question:** Which programming language is used by both the Fraud Detection Service and the Recommendation Service?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 4.6s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service are implemented in **Python**.   - The Fraud Detection Service is designed to identify and prevent fraudulent activities and is implemented in Python (source: service-fraud-detection-service.md). - The Recommendation Service offers tailored recommendations and is also built using Python (source: service-recommendation-service.md).
- **graph** [OK correct, 7.9s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service use **Python** as their programming language.   - The Fraud Detection Service is implemented in Python. - The Recommendation Service is built using Python.  This information was gathered from the neighbourhoods of both services, specifically looking for the relationship types that indicate the programming language used.

### `gold-024` - *shared_neighbor*

**Question:** Which services integrate with both the GraphQL Federation Layer and the Monolithic Django App?

**Expected:** The BFF Service and the Recommendation Service integrate with both.
**Key entities:** BFF Service, Recommendation Service

**Oracle Cypher rows:** 2

- **rag** [X wrong, 11.0s] (10 tool calls, agent_miss) - The answer includes additional services not in the expected answer, contradicting the expected entities.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **BFF Service** 2. **Recommendation Service** 3. **Fraud Detection Service** 4. **Quickcart Orders Service**  These services are mentioned as key integrations for both the GraphQL Federation Layer and the Monolithic Django App (source: [service-graphql-service.md](service-graphql-service.md) a...
- **graph** [OK correct, 16.6s] (14 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **BFF Service** 2. **Recommendation Service**  These services were found to integrate with both applications based on their relationships in the graph. The Cypher patterns used involved checking for integration relationships with both entities.

### `gold-025` - *aggregation_count*

**Question:** How many teams does the ShopFlow platform have?

**Expected:** ShopFlow has 9 teams - Catalog, Customer Experience, Data, Engineering, Logistics, Orders, Platform, Product, and the Site Reliability Engineering (SRE) Team.
**Key entities:** 9, Catalog Team, Customer Experience Team, Data Team, Engineering Team, Logistics Team, Orders Team, Platform Team, Product Team, Site Reliability Engineering (SRE) Team

**Oracle Cypher rows:** 1
**Oracle enumeration (9):** Catalog Team, Customer Experience Team, Data Team, Engineering Team, Logistics Team, Orders Team, Platform Team, Product Team, Site Reliability Engineering (SRE) Team

- **rag** [X wrong, 5.5s] (4 tool calls, agent_miss) - The answer does not mention any of the expected teams or the number of teams, and states it lacks information.
    > The ShopFlow platform has about 1,500 dedicated professionals organized into several specialized teams. However, the exact number of teams is not specified in the retrieved information (source: company-shopflow.md).
- **graph** [X wrong, 17.7s] (11 tool calls, agent_miss) - The agent's answer states 8 teams, contradicting the expected 9, and fails to mention all expected entities.
    > The ShopFlow platform has 8 teams associated with it, which include the Platform Team, Catalog Team, Engineering Team, and others. The specific teams are not fully enumerated in the data retrieved, but the total count is confirmed to be 8.   This information was gathered from the relationships of the ShopFlow entity, specifically the `HAS_TEAM` relationship.

### `gold-026` - *aggregation_count*

**Question:** How many distinct services or components have their code implemented in Python?

**Expected:** 6 - the Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, and the Monolithic Django App.
**Key entities:** 6, Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 1
**Oracle enumeration (6):** Auth Service, Data Lineage Service, Fraud Detection Service, Monolithic Django App, PII Service, Recommendation Service

- **rag** [X wrong, 4.3s] (3 tool calls, agent_miss) - The agent's answer lists 5 services and misses key entities like Data Lineage Service and Monolithic Django App.
    > There are 5 distinct services implemented in Python: Auth Service, PII Service, Fraud Detection Service, Recommendation Service, and Shopflow App.
- **graph** [X wrong, 5.5s] (2 tool calls, agent_miss) - The agent's answer contradicts the expected answer and mentions none of the expected entities.
    > There are no distinct services or components that have their code implemented in Python. The candidates found were also excluded, indicating that all relevant entities are accounted for in the exclusion criteria.

### `gold-027` - *aggregation_count*

**Question:** How many entities does the Fraud Detection Service directly integrate with (via INTEGRATES_WITH edges)?

**Expected:** 3 - Elasticsearch, Kibana, and QuickCart.
**Key entities:** 3, Elasticsearch, Kibana, QuickCart

**Oracle Cypher rows:** 1
**Oracle enumeration (3):** Elasticsearch, Kibana, QuickCart

- **rag** [X wrong, 5.6s] (4 tool calls, agent_miss) - The answer lists incorrect entities and misses Elasticsearch and Kibana, contradicting the expected answer.
    > The Fraud Detection Service directly integrates with 2 entities: Payments Service and QuickCart.
- **graph** [~ partial, 4.2s] (2 tool calls, agent_miss) - The answer states the correct number but does not mention any of the expected entities.
    > The Fraud Detection Service directly integrates with 3 entities via INTEGRATES_WITH edges.

### `gold-028` - *negation*

**Question:** Among the services managed by the Platform Team, which ones are NOT implemented in Python?

**Expected:** The GraphQL Service is not documented as being implemented in Python (the Auth Service and PII Service both are).
**Key entities:** GraphQL Service

**Oracle Cypher rows:** 1

- **rag** [X wrong, 14.2s] (9 tool calls, agent_miss) - The agent's answer does not mention the GraphQL Service, which is the expected entity not implemented in Python.
    > The services managed by the Platform Team that are NOT implemented in Python are:  1. **Payments Service** - Implemented in Java. 2. **BFF Service** - Implemented in JavaScript. 3. **Fraud Detection Service** - Implementation details not specified, but not mentioned as Python.  The services implemented in Python are the **Auth Service** and **PII Service** (both confirmed to be in Python).   Thus,...
- **graph** [X wrong, 38.8s] (22 tool calls, agent_miss) - The agent incorrectly states that the PII and Auth Services are not implemented in Python, contradicting the expected answer.
    > The services managed by the Platform Team that are NOT implemented in Python are:  - **PII Service** - **GraphQL Service** - **Auth Service**  However, I could not find any information indicating that any of these services are implemented in Python, as all queries returned no results for their implementation language. Thus, they are all considered as not implemented in Python.   This conclusion is...

### `gold-029` - *negation*

**Question:** Among the services that depend on the Data Lineage Service, which are NOT managed by the Platform Team?

**Expected:** The Payments Service and the Monolithic Django App depend on the Data Lineage Service but are not managed by the Platform Team.
**Key entities:** Payments Service, Monolithic Django App

**Oracle Cypher rows:** 2

- **rag** [~ partial, 12.8s] (10 tool calls, agent_miss) - The agent correctly mentions the Payments Service but incorrectly includes the Shopflow App instead of the Monolithic Django App.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. **Payments Service** (managed by the Product Team) 2. **Shopflow App** (managed by the Engineering Team)   The **Auth Service** is managed by the Platform Team.
- **graph** [X wrong, 7.2s] (4 tool calls, agent_miss) - The agent's answer lists incorrect services and misses the expected entities entirely.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. PII Service 2. GraphQL Service  The Auth Service is managed by the Platform Team.

### `gold-030` - *negation*

**Question:** Among the services implemented in Python, which ones are NOT managed by the Platform Team?

**Expected:** The Data Lineage Service, the Fraud Detection Service, the Recommendation Service, and the Monolithic Django App are implemented in Python but not managed by the Platform Team.
**Key entities:** Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 4

- **rag** [X wrong, 13.3s] (9 tool calls, agent_miss) - The answer misses key entities and incorrectly states management details, contradicting the expected answer.
    > The services implemented in Python that are **not** managed by the Platform Team are:  1. **Fraud Detection Service** - Managed by the Engineering Team. 2. **Recommendation Service** - Managed by the Platform Team but also involves collaboration with the Data Team. 3. **Shopflow App** - Operated by the Engineering Team. 4. **QuickCart Orders Service** - Operated by the Orders Team.  The **PII Serv...
- **graph** [~ partial, 27.9s] (13 tool calls, agent_miss) - The agent's answer mentions some expected entities but is incomplete.
    > The services implemented in Python that are NOT managed by the Platform Team are: 1. Data Lineage Service 2. Fraud Detection Service  These results were derived from comparing the services implemented in Python with those managed by the Platform Team.
