# Eval report - `20260430T192426Z-a63891`

- Started: 2026-04-30T19:34:40.764178+00:00
- Questions: 30
- Agents: rag, graph
- Source: `/Users/emilesilvis/Dropbox/30 - 39 Projects/llms-on-graphs/graph-rag-graph-agent/eval_runs/20260430T192426Z-a63891.json`

## Accuracy by category

Scores are mean judge grades (correct=1, partial=0.5, wrong=0); `n` is sample size in that cell.

| Category | rag | graph |
| --- | --- | --- |
| aggregation_count | 0.12 (n=4) | 0.50 (n=4) |
| dependency_chain | 0.75 (n=4) | 0.50 (n=4) |
| multi_hop_2 | 0.10 (n=5) | 0.80 (n=5) |
| multi_hop_3 | 0.25 (n=4) | 1.00 (n=4) |
| negation | 0.38 (n=4) | 0.50 (n=4) |
| one_hop | 0.80 (n=5) | 0.80 (n=5) |
| shared_neighbor | 0.88 (n=4) | 0.88 (n=4) |
| **overall** | **0.47** (n=30) | **0.72** (n=30) |

## Latency

| Agent | mean (s) | p95 (s) | n |
| --- | --- | --- | --- |
| rag | 10.24 | 18.42 | 30 |
| graph | 8.18 | 20.71 | 30 |

## Tool-call counts

Mean tool calls per question, per category. Higher = the agent needed more retrieval or refinement steps to answer.

| Category | rag | graph |
| --- | --- | --- |
| aggregation_count | 5.8 (n=4) | 4.0 (n=4) |
| dependency_chain | 6.2 (n=4) | 3.8 (n=4) |
| multi_hop_2 | 6.0 (n=5) | 3.0 (n=5) |
| multi_hop_3 | 9.2 (n=4) | 6.0 (n=4) |
| negation | 9.5 (n=4) | 8.2 (n=4) |
| one_hop | 1.0 (n=5) | 3.0 (n=5) |
| shared_neighbor | 3.0 (n=4) | 5.5 (n=4) |

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
| aggregation_count | 2 | 2 | 0 | 0 |
| dependency_chain | 1 | 3 | 0 | 0 |
| multi_hop_2 | 4 | 1 | 0 | 0 |
| multi_hop_3 | 4 | 0 | 0 | 0 |
| negation | 1 | 3 | 0 | 0 |
| one_hop | 4 | 0 | 1 | 0 |
| shared_neighbor | 3 | 1 | 0 | 0 |
| **total** | **19** | **10** | **1** | **0** |

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
| `gold-008` | depends on | yes |
| `gold-009` | developed by | no |
| `gold-009` | uses for caching | no |
| `gold-010` | depends on | yes |
| `gold-011` | implemented in | no |
| `gold-012` | uses cache | no |
| `gold-013` | operates | no |
| `gold-013` | leads | no |
| `gold-014` | developed by | no |
| `gold-014` | built with | no |
| `gold-015` | authored | no |
| `gold-015` | leads | no |
| `gold-016` | managed by | no |
| `gold-016` | depends on | yes |
| `gold-016` | built with | no |
| `gold-017` | authored | no |
| `gold-017` | developed by | no |
| `gold-017` | built with | no |
| `gold-018` | managed by | no |
| `gold-018` | developed by | no |
| `gold-018` | role | no |
| `gold-019` | depends on | yes |
| `gold-020` | depends on | yes |
| `gold-021` | uses for caching | yes |
| `gold-022` | uses cache | no |
| `gold-023` | implemented in | no |
| `gold-024` | integrates with | yes |
| `gold-025` | has team | no |
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

- **rag** [OK correct, 8.4s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The Auth Service is managed by the **Platform Team** (source: service-auth-service.md).
- **graph** [OK correct, 4.9s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The team that manages the Auth Service is the **Platform Team**. This information was retrieved from the relationships associated with the Auth Service entity.

### `gold-002` - *one_hop*

**Question:** What programming language is the Payments Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** (no oracle for this question)

- **rag** [X wrong, 2.2s] (1 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java** (source: team-product.md).
- **graph** [X wrong, 11.7s] (8 tool calls, extraction_miss) - The agent's answer does not mention Python and instead focuses on unrelated technologies and lacks the key entity.
    > The Payments Service is implemented in a programming language that is not explicitly mentioned in the retrieved data. However, it is associated with several technologies such as Redis, Kafka, and is hosted on Kubernetes and AWS, which are commonly used in various programming environments.   To find the specific programming language, I would need to look for additional documentation or details that...

### `gold-003` - *one_hop*

**Question:** What does Istio facilitate in the ShopFlow platform?

**Expected:** Istio facilitates service-to-service communication.
**Key entities:** service-to-service communication

**Oracle Cypher rows:** 1

- **rag** [OK correct, 4.4s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'service-to-service communication'.
    > Istio facilitates efficient service-to-service communication within the ShopFlow platform by providing a uniform way to secure, connect, and observe microservices. This service mesh is integral to the platform's microservices architecture, allowing for smooth management of complex distributed systems. Key microservices, including the Shopflow App, operate on this robust Istio infrastructure (sourc...
- **graph** [OK correct, 4.0s] (2 tool calls, agent_ok) - The agent's answer includes the expected fact and entity, and provides additional relevant details without contradiction.
    > Istio facilitates service-to-service communication in the ShopFlow platform. Additionally, it provides security, observability, and traffic management, and is part of the microservices architecture and API ecosystem. It also supports canary releases (from the neighbourhood of "Istio").   This information was gathered from the relationships connected to the "Istio" entity.

### `gold-004` - *multi_hop_2*

**Question:** Which infrastructure does the service managed by the Platform Team for authentication use?

**Expected:** It uses AWS, Kubernetes EKS, and Kafka.
**Key entities:** AWS, Kubernetes EKS, Kafka

**Oracle Cypher rows:** 3

- **rag** [X wrong, 5.2s] (2 tool calls, agent_miss) - The agent's answer does not mention AWS, Kubernetes EKS, or Kafka, which are the expected entities.
    > The Auth Service managed by the Platform Team uses a scalable infrastructure built with Python. It integrates with Redis to cache session data and authentication tokens, which helps reduce database load by serving token validation requests directly from the cache (source: [service-auth-service.md]).
- **graph** [OK correct, 5.8s] (3 tool calls, agent_ok) - The agent's answer includes all expected entities: AWS, Kubernetes EKS, and Kafka.
    > The service managed by the Platform Team for authentication, known as the Auth Service, uses the following infrastructure:  1. **Kafka** 2. **Kubernetes EKS** 3. **AWS**  Additionally, it utilizes **Redis** as its database.   This information was gathered from the relationships of the Auth Service with the infrastructure entities.

### `gold-005` - *multi_hop_2*

**Question:** Who authored the ADR about the QuickCart acquisition, and what is their role?

**Expected:** Bob Martinez, who is a Staff SRE, authored it.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 20.4s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the author or their role.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 6.7s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities accurately.
    > Bob Martinez authored the ADR about the QuickCart acquisition, and his role is Staff SRE (Site Reliability Engineer).

### `gold-006` - *shared_neighbor*

**Question:** Which programming language is used by both the Auth Service and the PII Service?

**Expected:** Python is used by both.
**Key entities:** Python

**Oracle Cypher rows:** 4

- **rag** [OK correct, 5.2s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service are developed using **Python**.   - Auth Service: Built with Python (source: service-auth-service.md). - PII Service: Developed in Python (source: service-pii-service.md).
- **graph** [OK correct, 7.1s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service use the programming language **Python**.   This was determined by checking the neighbourhoods of both services, where the Auth Service is built with Python and the PII Service is developed in Python.   Key Cypher patterns used: - `MATCH (s:Entity {name: 'Auth Service'})` and `MATCH (s:Entity {name: 'PII Service'})` to find their respective programming lang...

### `gold-007` - *aggregation_count*

**Question:** How many services does the Platform Team manage?

**Expected:** The Platform Team manages 3 services (Auth Service, GraphQL Service, PII Service).
**Key entities:** 3, Auth Service, GraphQL Service, PII Service

**Oracle Cypher rows:** 1

- **rag** [X wrong, 16.5s] (10 tool calls, agent_miss) - The agent's answer lists incorrect services and misses expected entities like GraphQL Service and PII Service.
    > The Platform Team manages 3 services: Auth Service, Data Lineage Service, and Payments Service.
- **graph** [OK correct, 11.8s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages 3 services: PII Service, GraphQL Service, and Auth Service.

### `gold-008` - *negation*

**Question:** Among the services managed by the Platform Team, which ones do NOT depend on the Data Lineage Service?

**Expected:** The GraphQL Service and the PII Service do not depend on the Data Lineage Service.
**Key entities:** GraphQL Service, PII Service

**Oracle Cypher rows:** 2

- **rag** [~ partial, 12.0s] (7 tool calls, agent_miss) - The agent mentions the PII Service but omits the GraphQL Service, which is also expected.
    > The services managed by the Platform Team that do NOT depend on the Data Lineage Service are:  - PII Service  The Auth Service and Payments Service do depend on the Data Lineage Service (from the notes retrieved).
- **graph** [OK correct, 20.7s] (9 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The services managed by the Platform Team that do NOT depend on the Data Lineage Service are:  1. PII Service 2. GraphQL Service  The services were identified using the relationships managed by the Platform Team and filtering out those that depend on the Data Lineage Service.

### `gold-009` - *multi_hop_3*

**Question:** What database does the service authored (developed) by Bob Martinez use for caching?

**Expected:** The Auth Service, developed by Bob Martinez, uses Redis for caching.
**Key entities:** Auth Service, Redis

**Oracle Cypher rows:** 1

- **rag** [X wrong, 18.4s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the expected entities or the database used for caching.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 5.1s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Redis.
    > The service authored by Bob Martinez, known as the Auth Service, uses **Redis** for caching.

### `gold-010` - *dependency_chain*

**Question:** Which services depend on the Data Lineage Service, directly or transitively?

**Expected:** The Auth Service and the Payments Service depend on the Data Lineage Service.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 3

- **rag** [~ partial, 16.2s] (9 tool calls, agent_miss) - The agent's answer includes the expected entities but adds extra services not mentioned in the expected answer.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service**    - **Fraud Detection Service** (depends on Payments Service) 3. **Shopflow App**    - **Recommendation Service** (depends on Shopflow App)    - **Mobile BFF Service** (depends on Shopflow App)  Thus, the complete list of services is: - Auth Service - Payments S...
- **graph** [~ partial, 4.4s] (2 tool calls, agent_miss) - The agent's answer includes the expected entities but adds an extra entity not in the expected answer.
    > The services that depend on the Data Lineage Service, either directly or transitively, are: 1. Payments Service 2. Monolithic Django App 3. Auth Service  This information was retrieved using a transitive query for the `DEPENDS_ON` relationship.

### `gold-011` - *one_hop*

**Question:** What programming language is the Data Lineage Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 2.2s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in **Python** (source: service-data-lineage-service.md).
- **graph** [OK correct, 3.2s] (2 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in Python. This information was retrieved from the relationship `IS_IMPLEMENTED_IN` in the graph.

### `gold-012` - *one_hop*

**Question:** Which cache does the Auth Service use for storing session data?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 2.9s] (1 tool calls, agent_ok) - The agent's answer correctly states that the Auth Service uses Redis for caching session data.
    > The Auth Service uses Redis to cache session data and authentication tokens. This helps reduce the load on the primary database by serving token validation requests directly from the cache (source: technology-redis-cache.md).
- **graph** [OK correct, 3.2s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity, Redis.
    > The Auth Service uses Redis for storing session data. This was determined from the outgoing relationship indicating that it "USES_DATABASE" Redis.

### `gold-013` - *multi_hop_2*

**Question:** Who leads the team that operates the QuickCart Orders Service?

**Expected:** Bob Martinez leads the Orders Team, which operates the QuickCart Orders Service.
**Key entities:** Bob Martinez, Orders Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 15.8s] (11 tool calls, hit step cap, agent_miss) - The agent's answer is a refusal and does not mention any expected entities.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 3.8s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The team that operates the QuickCart Orders Service is led by Bob Martinez.

### `gold-014` - *multi_hop_2*

**Question:** What programming language is the service developed by Bob Martinez built with?

**Expected:** Python - the Auth Service, which Bob Martinez developed, is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 1.9s] (1 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating JavaScript instead of Python and misses 'Auth Service'.
    > The service developed by Bob Martinez is built with JavaScript (source: service-bff-service.md).
- **graph** [OK correct, 3.7s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: 'Auth Service' and 'Python'.
    > The service developed by Bob Martinez, known as the Auth Service, is built with Python. This information was retrieved from the relationships associated with the Auth Service entity.

### `gold-015` - *multi_hop_2*

**Question:** Who authored the ADR about GDPR compliance, and what team do they lead?

**Expected:** Alice Chen authored the ADR and leads the SRE Team.
**Key entities:** Alice Chen, SRE Team

**Oracle Cypher rows:** 1

- **rag** [~ partial, 12.6s] (5 tool calls, agent_miss) - The answer correctly identifies Alice Chen as the author but fails to mention she leads the SRE Team.
    > The ADR about GDPR compliance was authored by **Alice Chen**, who is a **Senior Architect**. However, the specific team that she leads is not explicitly mentioned in the retrieved documents. The Engineering Team is led by **Chloe Park**, but it is unclear if Alice Chen is part of that team or leads a different one.   Thus, the answer is: - **Author**: Alice Chen - **Role**: Senior Architect - **Te...
- **graph** [X wrong, 4.2s] (3 tool calls, agent_miss) - The agent's answer incorrectly states the team Alice Chen leads, missing the expected 'SRE Team'.
    > Alice Chen authored the ADR about GDPR compliance and leads the Customer Experience Team. This information was gathered from the relationships in the knowledge graph, specifically the `IS_AUTHOR_OF` and `IS_LED_BY` relationships.

### `gold-016` - *multi_hop_3*

**Question:** Which programming language is used by the service that is managed by the Platform Team and depends on the Data Lineage Service?

**Expected:** Python - the Auth Service is managed by the Platform Team, depends on the Data Lineage Service, and is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 14.8s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Auth Service**, which is implemented in **Python**.   This information is derived from the following sources: - The Auth Service is managed by the Platform Team and depends on the Data Lineage Service (search results from "services managed by Platform Team" and "Data Lineage Service dependencies"). - The pro...
- **graph** [OK correct, 22.2s] (11 tool calls, agent_ok) - The agent's answer mentions the Auth Service and Python, matching the expected entities and facts.
    > The services managed by the Platform Team that depend on the Data Lineage Service are:  1. **Payments Service** - Written in Python. 2. **Monolithic Django App** - Written in Python. 3. **Auth Service** - Written in Python.  Thus, the programming language used by these services is **Python**.   This information was gathered through the relationships and attributes of the services in the graph, spe...

### `gold-017` - *multi_hop_3*

**Question:** What programming language is used by the service developed by the person who authored 'ADR: QuickCart Acquisition and Integration'?

**Expected:** Python - Bob Martinez authored the ADR and developed the Auth Service, which is built with Python.
**Key entities:** Bob Martinez, Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 17.3s] (11 tool calls, hit step cap, agent_miss) - The answer is a refusal and does not mention any expected entities or facts.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 6.3s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Bob Martinez, Auth Service, and Python.
    > The service developed by Bob Martinez, who authored 'ADR: QuickCart Acquisition and Integration', is built with Python.   This information was gathered through the relationships connecting Bob Martinez to the Auth Service, which is developed using Python.

### `gold-018` - *multi_hop_3*

**Question:** What role does the person who developed the authentication service managed by the Platform Team have?

**Expected:** Staff SRE - Bob Martinez, who developed the Auth Service (managed by the Platform Team), is a Staff SRE.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 14.3s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about Bob Martinez or the Staff SRE role.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 6.5s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Bob Martinez and Staff SRE.
    > The person who developed the Authentication Service, Bob Martinez, has the role of Staff SRE (Site Reliability Engineer).   This information was gathered through the relationships connected to the "Auth Service" and "Bob Martinez" entities.

### `gold-019` - *dependency_chain*

**Question:** Which services rely on the Payments Service, directly or transitively?

**Expected:** The Fraud Detection Service relies on the Payments Service.
**Key entities:** Fraud Detection Service

**Oracle Cypher rows:** 1

- **rag** [OK correct, 14.5s] (10 tool calls, agent_ok) - The agent's answer includes the expected entity 'Fraud Detection Service' and aligns with the expected answer.
    > The services that rely on the Payments Service, either directly or transitively, are:  1. **ShopFlow App** 2. **Data Lineage Service** 3. **Fraud Detection Service** 4. **Recommendation Service** (depends on ShopFlow App) 5. **Auth Service** (depends on Data Lineage Service)  Thus, the complete list of services is: ShopFlow App, Data Lineage Service, Fraud Detection Service, Recommendation Service...
- **graph** [X wrong, 7.3s] (5 tool calls, agent_miss) - The agent's answer does not mention the Fraud Detection Service, which is the key expected entity.
    > The services that rely on the Payments Service, directly or transitively, are:  1. Monolithic Django App 2. Logistics Team 3. Data Lineage Service  This was determined using the relationships `INTEGRATES_WITH` and `SUPPORTS` in a transitive query.

### `gold-020` - *dependency_chain*

**Question:** Which service, directly or transitively, depends on the ShopFlow application?

**Expected:** The Recommendation Service depends on the ShopFlow application.
**Key entities:** Recommendation Service

**Oracle Cypher rows:** 1

- **rag** [~ partial, 8.4s] (4 tool calls, agent_miss) - The answer mentions the Recommendation Service but includes additional services not in the expected answer.
    > The services that depend directly or transitively on the ShopFlow application are:  1. **Payments Service**: Integrates with ShopFlow for transaction workflows and is a dependency for the Fraud Detection Service. 2. **Recommendation Service**: Depends on ShopFlow to access user interaction data for generating recommendations. 3. **Data Lineage Service**: Directly depends on ShopFlow for tracking d...
- **graph** [OK correct, 3.9s] (2 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Recommendation Service'.
    > The service that directly or transitively depends on the ShopFlow application is the Recommendation Service.

### `gold-021` - *dependency_chain*

**Question:** Which services use Redis for caching or session storage? Consider all relationship types that express use/employ/cache.

**Expected:** The Auth Service and the Payments Service both use Redis for caching.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 2

- **rag** [OK correct, 4.3s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that use Redis for caching or session storage are:  1. **Auth Service**    - Uses Redis for caching session data and user credentials.  2. **Payments Service**    - Utilizes Redis for caching transaction histories and managing session data.  Both services leverage Redis to enhance performance and reduce load on primary databases (from multiple sources including `technology-redis-cache...
- **graph** [~ partial, 9.4s] (6 tool calls, agent_miss) - The agent mentions the Auth Service but omits the Payments Service, making the answer incomplete.
    > The services that use Redis for caching or session storage are:  1. Auth Service  This was determined by querying the relationships that express usage of Redis, including various types of "use" and "cache" relationships.

### `gold-022` - *shared_neighbor*

**Question:** Which cache database is used by both the Auth Service and the Payments Service?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 4.6s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the Auth Service and the Payments Service use **Redis** as their cache database. Redis is utilized to cache session data and authentication tokens for the Auth Service, and to cache transaction histories and recent payment details for the Payments Service (source: technology-redis-cache.md).
- **graph** [OK correct, 5.2s] (4 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Redis'.
    > The cache database used by both the Auth Service and the Payments Service is **Redis**.   This was determined by checking the outgoing relationships for both services, where the Auth Service uses Redis via the relationship `USES_DATABASE` and the Payments Service employs Redis via the relationship `EMPLOYS`.

### `gold-023` - *shared_neighbor*

**Question:** Which programming language is used by both the Fraud Detection Service and the Recommendation Service?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.9s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service are implemented in **Python**.   - Fraud Detection Service: Implemented in Python (source: service-fraud-detection-service.md). - Recommendation Service: Built using Python (source: service-recommendation-service.md).
- **graph** [OK correct, 5.0s] (4 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service use **Python** as their programming language.   This was determined by checking the neighbourhoods of both services:  - The Fraud Detection Service is implemented in Python. - The Recommendation Service is built using Python.   (Cypher patterns used: `neighbourhood('Fraud Detection Service')` and `neighbourhood('Recommendation Service...

### `gold-024` - *shared_neighbor*

**Question:** Which services integrate with both the GraphQL Federation Layer and the Monolithic Django App?

**Expected:** The BFF Service and the Recommendation Service integrate with both.
**Key entities:** BFF Service, Recommendation Service

**Oracle Cypher rows:** 2

- **rag** [~ partial, 6.9s] (6 tool calls, agent_miss) - The agent's answer includes the expected entities but adds extra services not mentioned in the expected answer.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **BFF Service** 2. **Recommendation Service** 3. **Fraud Detection Service** 4. **Quickcart Orders Service**  These services are mentioned as key integrations with the GraphQL Federation Layer and are part of the broader architecture that includes the Monolithic Django App (source: service-gra...
- **graph** [~ partial, 13.2s] (10 tool calls, agent_miss) - The answer includes the expected entities but adds an incorrect entity, the Fraud Detection Service.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. BFF Service 2. Recommendation Service 3. Fraud Detection Service  These services were identified through their integration relationships with both entities. The Cypher patterns used included checking the outgoing relationships for both the GraphQL Federation Layer and the Monolithic Django App...

### `gold-025` - *aggregation_count*

**Question:** How many teams does the ShopFlow platform have?

**Expected:** ShopFlow has 9 teams - Catalog, Customer Experience, Data, Engineering, Logistics, Orders, Platform, Product, and the Site Reliability Engineering (SRE) Team.
**Key entities:** 9, Catalog Team, Customer Experience Team, Data Team, Engineering Team, Logistics Team, Orders Team, Platform Team, Product Team, Site Reliability Engineering (SRE) Team

**Oracle Cypher rows:** 1

- **rag** [~ partial, 18.1s] (7 tool calls, agent_miss) - The answer mentions some expected teams but not the total number or all teams.
    > The ShopFlow platform has approximately 1,500 dedicated professionals organized into several specialized teams, including the Data Team, Product Team, and Engineering Team.
- **graph** [X wrong, 8.9s] (6 tool calls, agent_miss) - The agent's answer lists incorrect teams and misses key expected entities.
    > The ShopFlow platform has 6 teams: Platform Team, Catalog Team, Engineering Team, SRE Team, Payments Service, and Mobile Backend-for-Frontend (BFF) Service.

### `gold-026` - *aggregation_count*

**Question:** How many distinct services or components have their code implemented in Python?

**Expected:** 6 - the Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, and the Monolithic Django App.
**Key entities:** 6, Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 1

- **rag** [X wrong, 4.7s] (3 tool calls, agent_miss) - The agent's answer lists 5 services, missing 'Data Lineage Service' and 'Monolithic Django App', and includes 'Shopflow App' incorrectly.
    > There are 5 distinct services implemented in Python: Auth Service, PII Service, Fraud Detection Service, Recommendation Service, and Shopflow App.
- **graph** [X wrong, 3.2s] (2 tool calls, agent_miss) - The agent's answer lists only 2 services, missing 4 expected entities and the total count of 6.
    > There are 2 distinct services implemented in Python: Fraud Detection Service and Data Lineage Service.

### `gold-027` - *aggregation_count*

**Question:** How many entities does the Fraud Detection Service directly integrate with (via INTEGRATES_WITH edges)?

**Expected:** 3 - Elasticsearch, Kibana, and QuickCart.
**Key entities:** 3, Elasticsearch, Kibana, QuickCart

**Oracle Cypher rows:** 1

- **rag** [X wrong, 4.2s] (3 tool calls, agent_miss) - The answer lists incorrect entities and misses Elasticsearch and Kibana, contradicting the expected answer.
    > The Fraud Detection Service directly integrates with 2 entities: Payments Service and QuickCart.
- **graph** [OK correct, 4.5s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Fraud Detection Service directly integrates with 3 entities: Kibana, Elasticsearch, and QuickCart.

### `gold-028` - *negation*

**Question:** Among the services managed by the Platform Team, which ones are NOT implemented in Python?

**Expected:** The GraphQL Service is not documented as being implemented in Python (the Auth Service and PII Service both are).
**Key entities:** GraphQL Service

**Oracle Cypher rows:** 1

- **rag** [X wrong, 12.2s] (7 tool calls, agent_miss) - The agent's answer incorrectly identifies the Payments Service instead of the GraphQL Service as not implemented in Python.
    > The services managed by the Platform Team that are NOT implemented in Python are:  1. **Payments Service** (implemented in Java)  Thus, the only service not implemented in Python is the Payments Service.   This information is derived from the details about the services managed by the Platform Team and the specific implementation languages of those services (service-auth-service.md, service-pii-ser...
- **graph** [X wrong, 11.5s] (5 tool calls, agent_miss) - The agent's answer incorrectly states that none of the services are implemented in Python, contradicting the expected answer.
    > The Platform Team manages 3 services: PII Service, GraphQL Service, and Auth Service. None of these services are implemented in Python, as there are no services linked to Python in the graph.  Thus, all services managed by the Platform Team (PII Service, GraphQL Service, Auth Service) are NOT implemented in Python.   This was determined using the relationships `MANAGES` and `IS_IMPLEMENTED_IN`.

### `gold-029` - *negation*

**Question:** Among the services that depend on the Data Lineage Service, which are NOT managed by the Platform Team?

**Expected:** The Payments Service and the Monolithic Django App depend on the Data Lineage Service but are not managed by the Platform Team.
**Key entities:** Payments Service, Monolithic Django App

**Oracle Cypher rows:** 2

- **rag** [~ partial, 13.7s] (10 tool calls, agent_miss) - The agent correctly identifies the Payments Service but misses the Monolithic Django App and incorrectly includes the Shopflow App.
    > The services that depend on the Data Lineage Service are:  1. **Auth Service** 2. **Payments Service** 3. **Shopflow App**  Among these, the services that are **NOT managed by the Platform Team** are:  - **Payments Service** - **Shopflow App**  The Auth Service is managed by the Platform Team (source: [service-auth-service.md](service-auth-service.md)).
- **graph** [~ partial, 16.6s] (10 tool calls, agent_miss) - The agent's answer includes the expected entities but adds an incorrect entity, Auth Service.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. Payments Service 2. Monolithic Django App 3. Auth Service  None of these services are managed by the Platform Team, as confirmed by the absence of any management relationships for these services with the Platform Team.   Key Cypher patterns used: - `MATCH (s:Entity)<-[:DEPENDS_ON]-(d:Entity) WHER...

### `gold-030` - *negation*

**Question:** Among the services implemented in Python, which ones are NOT managed by the Platform Team?

**Expected:** The Data Lineage Service, the Fraud Detection Service, the Recommendation Service, and the Monolithic Django App are implemented in Python but not managed by the Platform Team.
**Key entities:** Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 4

- **rag** [~ partial, 20.7s] (14 tool calls, agent_miss) - The agent mentions some expected entities but misses 'Data Lineage Service' and 'Monolithic Django App', and incorrectly includes 'Shopflow App'.
    > The services implemented in Python that are **not** managed by the Platform Team are:  1. **Fraud Detection Service** 2. **Recommendation Service** 3. **Shopflow App**  These services are managed by other teams, such as the Engineering Team and the Product Team (e.g., the Shopflow App is operated by the Engineering Team) (source: various service management documentation).
- **graph** [~ partial, 21.2s] (9 tool calls, agent_miss) - The agent's answer includes all expected entities but adds an incorrect entity, the PII Service.
    > The services implemented in Python that are NOT managed by the Platform Team are:  1. Fraud Detection Service 2. Data Lineage Service 3. Monolithic Django App 4. Recommendation Service 5. PII Service  The only service managed by the Platform Team is the Auth Service.   This was determined by identifying all services implemented in Python and excluding those managed by the Platform Team.
