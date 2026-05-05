# Eval report - `20260502T135653Z-3202a9`

- Started: 2026-05-02T14:07:19.860454+00:00
- Questions: 30
- Agents: rag, graph
- Source: `/Users/emilesilvis/Dropbox/30 - 39 Projects/llms-on-graphs/graph-rag-graph-agent/eval_runs/20260502T135653Z-3202a9.json`

## Accuracy by category

Scores are mean judge grades (correct=1, partial=0.5, wrong=0); `n` is sample size in that cell.

| Category | rag | graph |
| --- | --- | --- |
| aggregation_count | 0.00 (n=4) | 0.50 (n=4) |
| dependency_chain | 0.75 (n=4) | 0.38 (n=4) |
| multi_hop_2 | 0.10 (n=5) | 0.90 (n=5) |
| multi_hop_3 | 0.25 (n=4) | 0.75 (n=4) |
| negation | 0.38 (n=4) | 0.50 (n=4) |
| one_hop | 0.80 (n=5) | 0.80 (n=5) |
| shared_neighbor | 0.88 (n=4) | 1.00 (n=4) |
| **overall** | **0.45** (n=30) | **0.70** (n=30) |

## Latency

| Agent | mean (s) | p95 (s) | n |
| --- | --- | --- | --- |
| rag | 9.57 | 20.11 | 30 |
| graph | 9.64 | 19.63 | 30 |

## Tool-call counts

Mean tool calls per question, per category. Higher = the agent needed more retrieval or refinement steps to answer.

| Category | rag | graph |
| --- | --- | --- |
| aggregation_count | 4.8 (n=4) | 3.2 (n=4) |
| dependency_chain | 7.0 (n=4) | 4.8 (n=4) |
| multi_hop_2 | 7.2 (n=5) | 4.6 (n=5) |
| multi_hop_3 | 9.5 (n=4) | 8.2 (n=4) |
| negation | 9.0 (n=4) | 10.0 (n=4) |
| one_hop | 1.0 (n=5) | 5.0 (n=5) |
| shared_neighbor | 4.0 (n=4) | 4.8 (n=4) |

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
| multi_hop_3 | 3 | 1 | 0 | 0 |
| negation | 2 | 2 | 0 | 0 |
| one_hop | 4 | 0 | 1 | 0 |
| shared_neighbor | 4 | 0 | 0 | 0 |
| **total** | **20** | **9** | **1** | **0** |

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
| `gold-024` | integrates with | yes |
| `gold-025` | has team | no |
| `gold-026` | implemented in | yes |
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

- **rag** [OK correct, 2.9s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The Auth Service is managed by the **Platform Team** (source: [service-auth-service.md](service-auth-service.md)).
- **graph** [OK correct, 2.2s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The team that manages the Auth Service is the **Platform Team**. This information was retrieved from the relationships associated with the Auth Service.

### `gold-002` - *one_hop*

**Question:** What programming language is the Payments Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** (no oracle for this question)

- **rag** [X wrong, 1.9s] (1 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java** (source: team-product.md).
- **graph** [X wrong, 28.5s] (19 tool calls, hit step cap, extraction_miss) - The agent's answer does not mention Python or provide any relevant information.
    > Sorry, need more steps to process this request.

### `gold-003` - *one_hop*

**Question:** What does Istio facilitate in the ShopFlow platform?

**Expected:** Istio facilitates service-to-service communication.
**Key entities:** service-to-service communication

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.6s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities, including service-to-service communication.
    > Istio facilitates efficient service-to-service communication within the ShopFlow platform by providing a uniform way to secure, connect, and observe microservices. This service mesh is integral to the platform's microservices architecture, allowing for smooth management of complex distributed systems. Key microservices, including the Shopflow App, operate on this robust Istio infrastructure (sourc...
- **graph** [OK correct, 9.5s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities, with additional relevant details.
    > Istio facilitates service-to-service communication in the ShopFlow platform. Additionally, it provides security, observability, and traffic management, and is part of the microservices architecture and API ecosystem. It also supports canary releases (from the neighbourhood of Istio).   This information was gathered from the neighbourhood of the "Istio" entity.

### `gold-004` - *multi_hop_2*

**Question:** Which infrastructure does the service managed by the Platform Team for authentication use?

**Expected:** It uses AWS, Kubernetes EKS, and Kafka.
**Key entities:** AWS, Kubernetes EKS, Kafka

**Oracle Cypher rows:** 3

- **rag** [X wrong, 3.6s] (2 tool calls, agent_miss) - The answer does not mention AWS, Kubernetes EKS, or Kafka, and instead discusses unrelated technologies like Python and Redis.
    > The Auth Service managed by the Platform Team uses a scalable infrastructure built with Python. It integrates with Redis to cache session data and authentication tokens, which helps reduce database load by serving token validation requests directly from the cache (source: [service-auth-service.md]).
- **graph** [OK correct, 12.1s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: AWS, Kubernetes EKS, and Kafka.
    > The service managed by the Platform Team for authentication, known as the Auth Service, uses the following infrastructure:  - **Kafka** - **Kubernetes EKS** - **AWS**  This information was gathered from the neighbourhood of the Auth Service, which shows its dependencies and infrastructure usage.

### `gold-005` - *multi_hop_2*

**Question:** Who authored the ADR about the QuickCart acquisition, and what is their role?

**Expected:** Bob Martinez, who is a Staff SRE, authored it.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 22.9s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the author or their role.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 14.4s] (11 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Bob Martinez and Staff SRE.
    > The ADR about the QuickCart acquisition, titled "ADR: QuickCart Acquisition and Integration," was authored by **Bob Martinez**, who holds the role of **Staff SRE**.   This information was gathered using the relationships from the entities "ADR: QuickCart Acquisition and Integration" and "Bob Martinez."

### `gold-006` - *shared_neighbor*

**Question:** Which programming language is used by both the Auth Service and the PII Service?

**Expected:** Python is used by both.
**Key entities:** Python

**Oracle Cypher rows:** 4

- **rag** [OK correct, 3.0s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity, Python.
    > Both the Auth Service and the PII Service are developed using **Python**.   - Auth Service: Built with Python (source: service-auth-service.md). - PII Service: Developed in Python (source: service-pii-service.md).
- **graph** [OK correct, 3.0s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service use the programming language **Python**.   This was determined from the neighbourhoods of both services, where: - The Auth Service is built with Python. - The PII Service is developed in Python.   These findings were retrieved from the relationships associated with each service.

### `gold-007` - *aggregation_count*

**Question:** How many services does the Platform Team manage?

**Expected:** The Platform Team manages 3 services (Auth Service, GraphQL Service, PII Service).
**Key entities:** 3, Auth Service, GraphQL Service, PII Service

**Oracle Cypher rows:** 1

- **rag** [X wrong, 12.6s] (9 tool calls, agent_miss) - The agent's answer lists incorrect services and misses expected entities like GraphQL Service and PII Service.
    > The Platform Team manages **three services**:  1. Auth Service 2. Data Lineage Service 3. Payments Service  These services are essential for backend operations and support various functionalities within the organization (source: team-platform.md, service-auth-service.md, service-data-lineage-service.md, service-payments-service.md).
- **graph** [OK correct, 2.7s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages 3 services: PII Service, GraphQL Service, and Auth Service.

### `gold-008` - *negation*

**Question:** Among the services managed by the Platform Team, which ones do NOT depend on the Data Lineage Service?

**Expected:** The GraphQL Service and the PII Service do not depend on the Data Lineage Service.
**Key entities:** GraphQL Service, PII Service

**Oracle Cypher rows:** 2

- **rag** [~ partial, 12.2s] (8 tool calls, agent_miss) - The agent correctly identifies the PII Service but incorrectly includes API Gateway and omits GraphQL Service.
    > The Platform Team manages the following services:  1. **Auth Service** - Depends on the Data Lineage Service. 2. **PII Service** - No dependencies on the Data Lineage Service found. 3. **Payments Service** - Depends on the Data Lineage Service. 4. **API Gateway** - No dependencies on the Data Lineage Service found.  Thus, the services managed by the Platform Team that do NOT depend on the Data Lin...
- **graph** [OK correct, 11.8s] (8 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The services managed by the Platform Team that do NOT depend on the Data Lineage Service are:  1. PII Service 2. GraphQL Service  The only service that depends on the Data Lineage Service is the Auth Service.   This was determined by identifying the services managed by the Platform Team and then checking which of those depend on the Data Lineage Service.

### `gold-009` - *multi_hop_3*

**Question:** What database does the service authored (developed) by Bob Martinez use for caching?

**Expected:** The Auth Service, developed by Bob Martinez, uses Redis for caching.
**Key entities:** Auth Service, Redis

**Oracle Cypher rows:** 1

- **rag** [X wrong, 13.7s] (11 tool calls, hit step cap, agent_miss) - The agent's answer is a refusal and does not mention any expected entities.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 3.5s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Redis.
    > The service authored (developed) by Bob Martinez, known as the Auth Service, uses **Redis** for caching.

### `gold-010` - *dependency_chain*

**Question:** Which services depend on the Data Lineage Service, directly or transitively?

**Expected:** The Auth Service and the Payments Service depend on the Data Lineage Service.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 3

- **rag** [~ partial, 10.9s] (8 tool calls, agent_miss) - The answer includes expected entities but adds extra, unsupported services.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service** 3. **Shopflow App** 4. **Fraud Detection Service** 5. **Recommendation Service**  These dependencies were identified through the service interdependencies documented in the relevant sections (service-data-lineage-service.md, service-auth-service.md, service-payme...
- **graph** [~ partial, 3.0s] (1 tool calls, agent_miss) - The agent's answer includes the expected entities but adds an extra entity not in the expected answer.
    > The services that depend on the Data Lineage Service, directly or transitively, are: 1. Auth Service 2. Monolithic Django App 3. Payments Service  These results were obtained using the `reach` function with the relationship concepts "depends on" and "relies on".

### `gold-011` - *one_hop*

**Question:** What programming language is the Data Lineage Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 2.8s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in **Python** (source: service-data-lineage-service.md).
- **graph** [OK correct, 3.9s] (2 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in Python. This was determined from the outgoing relationship `IS_IMPLEMENTED_IN` that connects it to the programming language Python.

### `gold-012` - *one_hop*

**Question:** Which cache does the Auth Service use for storing session data?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 2.9s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > The Auth Service uses Redis to cache session data and authentication tokens. This helps reduce the load on the primary database by serving token validation requests directly from the cache (source: technology-redis-cache.md).
- **graph** [OK correct, 3.3s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity, Redis.
    > The Auth Service uses Redis for storing session data. This was determined from the outgoing relationship indicating that it "uses database" Redis.

### `gold-013` - *multi_hop_2*

**Question:** Who leads the team that operates the QuickCart Orders Service?

**Expected:** Bob Martinez leads the Orders Team, which operates the QuickCart Orders Service.
**Key entities:** Bob Martinez, Orders Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 19.4s] (11 tool calls, hit step cap, agent_miss) - The agent's answer does not mention any expected entities or provide relevant information.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 3.9s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Bob Martinez and Orders Team.
    > The team that operates the QuickCart Orders Service is led by Bob Martinez.

### `gold-014` - *multi_hop_2*

**Question:** What programming language is the service developed by Bob Martinez built with?

**Expected:** Python - the Auth Service, which Bob Martinez developed, is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 8.4s] (5 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating JavaScript instead of Python.
    > The service developed by Bob Martinez is built with JavaScript.
- **graph** [OK correct, 9.3s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The service developed by Bob Martinez, known as the Auth Service, is built with Python.

### `gold-015` - *multi_hop_2*

**Question:** Who authored the ADR about GDPR compliance, and what team do they lead?

**Expected:** Alice Chen authored the ADR and leads the SRE Team.
**Key entities:** Alice Chen, SRE Team

**Oracle Cypher rows:** 1

- **rag** [~ partial, 11.4s] (7 tool calls, agent_miss) - The answer correctly identifies Alice Chen but fails to mention the SRE Team, providing incomplete information about her leadership role.
    > The ADR about GDPR compliance was authored by **Alice Chen**, who is a **Senior Architect**. However, the specific team that Alice Chen leads is not explicitly mentioned in the retrieved documents. The Engineering Team is noted to consist of 150 individuals, but it is unclear if Alice Chen leads this team or is part of it (source: [adr-gdpr-compliance-2020.md](adr-gdpr-compliance-2020.md), [team-e...
- **graph** [~ partial, 3.7s] (3 tool calls, agent_miss) - The agent correctly identifies Alice Chen as the author but incorrectly states the team she leads.
    > Alice Chen authored the ADR about GDPR compliance and leads the Customer Experience Team.

### `gold-016` - *multi_hop_3*

**Question:** Which programming language is used by the service that is managed by the Platform Team and depends on the Data Lineage Service?

**Expected:** Python - the Auth Service is managed by the Platform Team, depends on the Data Lineage Service, and is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 8.0s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Python.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Auth Service**, which is implemented in **Python**.
- **graph** [X wrong, 45.3s] (21 tool calls, hit step cap, agent_miss) - The agent's answer is a refusal and does not mention any expected entities or facts.
    > Sorry, need more steps to process this request.

### `gold-017` - *multi_hop_3*

**Question:** What programming language is used by the service developed by the person who authored 'ADR: QuickCart Acquisition and Integration'?

**Expected:** Python - Bob Martinez authored the ADR and developed the Auth Service, which is built with Python.
**Key entities:** Bob Martinez, Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 20.1s] (11 tool calls, hit step cap, agent_miss) - The answer is a refusal and does not mention any expected entities or facts.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 5.3s] (4 tool calls, agent_ok) - The agent's answer includes all expected entities and matches the expected answer's facts.
    > The service developed by Bob Martinez, who authored 'ADR: QuickCart Acquisition and Integration', is the Auth Service, which is built using Python.   Key Cypher patterns used: 1. Resolved the entity for 'ADR: QuickCart Acquisition and Integration' to find the author. 2. Queried Bob Martinez's neighbourhood to find the service he developed. 3. Queried the Auth Service's neighbourhood to determine t...

### `gold-018` - *multi_hop_3*

**Question:** What role does the person who developed the authentication service managed by the Platform Team have?

**Expected:** Staff SRE - Bob Martinez, who developed the Auth Service (managed by the Platform Team), is a Staff SRE.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 14.2s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about Bob Martinez or the role of Staff SRE.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 13.0s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Bob Martinez and Staff SRE.
    > The person who developed the Authentication Service, Bob Martinez, has the role of Staff SRE (Site Reliability Engineer).   This information was gathered through the relationships connecting Bob Martinez to the Auth Service and his role as indicated in the graph.

### `gold-019` - *dependency_chain*

**Question:** Which services rely on the Payments Service, directly or transitively?

**Expected:** The Fraud Detection Service relies on the Payments Service.
**Key entities:** Fraud Detection Service

**Oracle Cypher rows:** 1

- **rag** [OK correct, 21.8s] (12 tool calls, agent_ok) - The agent's answer includes the Fraud Detection Service, matching the expected entities.
    > The services that rely on the Payments Service, either directly or transitively, are:  1. **ShopFlow App** 2. **Data Lineage Service** 3. **Fraud Detection Service** 4. **Recommendation Service** (depends on ShopFlow App) 5. **Auth Service** (depends on Data Lineage Service)  Thus, the complete list of services is: - ShopFlow App - Data Lineage Service - Fraud Detection Service - Recommendation Se...
- **graph** [X wrong, 17.8s] (12 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating no services rely on the Payments Service.
    > No services were found that rely on the Payments Service, either directly or transitively. I explored various relationship types such as "relies on," "depends on," and "supports," but there were no matches in the graph.

### `gold-020` - *dependency_chain*

**Question:** Which service, directly or transitively, depends on the ShopFlow application?

**Expected:** The Recommendation Service depends on the ShopFlow application.
**Key entities:** Recommendation Service

**Oracle Cypher rows:** 1

- **rag** [~ partial, 8.6s] (6 tool calls, agent_miss) - The agent's answer includes the expected entity but adds extra, unverified services.
    > The services that depend on the ShopFlow application, either directly or transitively, are:  1. **Payments Service** (depends directly on ShopFlow) 2. **Recommendation Service** (depends directly on ShopFlow) 3. **Fraud Detection Service** (depends transitively on ShopFlow via Payments Service)  Thus, the complete list is: Payments Service, Recommendation Service, and Fraud Detection Service.
- **graph** [OK correct, 2.4s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Recommendation Service'.
    > The service that directly or transitively depends on the ShopFlow application is the **Recommendation Service**.

### `gold-021` - *dependency_chain*

**Question:** Which services use Redis for caching or session storage? Consider all relationship types that express use/employ/cache.

**Expected:** The Auth Service and the Payments Service both use Redis for caching.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 2

- **rag** [OK correct, 4.6s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that use Redis for caching or session storage are:  1. **Auth Service**    - Uses Redis for caching session data and user credentials.  2. **Payments Service**    - Employs Redis for caching transaction histories and managing session data.  Both services utilize Redis to enhance performance by reducing load on primary databases and improving response times (from multiple sources inclu...
- **graph** [X wrong, 7.1s] (5 tool calls, agent_miss) - The agent's answer mentions none of the expected entities and lists unrelated services instead.
    > The services that use Redis for caching or session storage are:  1. **Logistics Team** 2. **Data Lineage Tracking Service** 3. **SRE Team**  These services are connected to Redis via various relationship types that express usage.

### `gold-022` - *shared_neighbor*

**Question:** Which cache database is used by both the Auth Service and the Payments Service?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.8s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the Auth Service and the Payments Service use **Redis** as their cache database. Redis is utilized to cache session data and authentication tokens for the Auth Service, and to cache transaction histories and recent payment details for the Payments Service (source: technology-redis-cache.md).
- **graph** [OK correct, 4.7s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity, Redis.
    > Both the Auth Service and the Payments Service use **Redis** as their cache database.   - The Auth Service has an outgoing relationship indicating it **uses** Redis. - The Payments Service also has an outgoing relationship indicating it **employs** Redis.   This information was gathered from the neighbourhoods of both services.

### `gold-023` - *shared_neighbor*

**Question:** Which programming language is used by both the Fraud Detection Service and the Recommendation Service?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.6s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service are implemented in **Python**.   - The Fraud Detection Service is designed to identify and prevent fraudulent activities and is implemented in Python (source: service-fraud-detection-service.md). - The Recommendation Service offers tailored recommendations and is also built using Python (source: service-recommendation-service.md).
- **graph** [OK correct, 5.1s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service use **Python** as their programming language.   This was determined by checking the neighbourhoods of both services: - The Fraud Detection Service is implemented in Python. - The Recommendation Service is built using Python.   Thus, Python is the common programming language used by both services.

### `gold-024` - *shared_neighbor*

**Question:** Which services integrate with both the GraphQL Federation Layer and the Monolithic Django App?

**Expected:** The BFF Service and the Recommendation Service integrate with both.
**Key entities:** BFF Service, Recommendation Service

**Oracle Cypher rows:** 2

- **rag** [~ partial, 14.1s] (10 tool calls, agent_miss) - The answer includes the expected entities but adds extra, unsupported services.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **BFF Service** 2. **Recommendation Service** 3. **Fraud Detection Service** 4. **Quickcart Orders Service**  These services are mentioned as key integrations for both the GraphQL Federation Layer and the Monolithic Django App (source: [service-graphql-service.md](service-graphql-service.md) a...
- **graph** [OK correct, 19.6s] (9 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: BFF Service and Recommendation Service.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **BFF Service** 2. **Recommendation Service**  These services are connected to both the GraphQL Federation Layer and the Monolithic Django App via the `INTEGRATES_WITH` relationship.   The Cypher patterns used were: - `MATCH (s:Entity)-[:INTEGRATES_WITH]->(t:Entity) WHERE t.name IN [...] RETUR...

### `gold-025` - *aggregation_count*

**Question:** How many teams does the ShopFlow platform have?

**Expected:** ShopFlow has 9 teams - Catalog, Customer Experience, Data, Engineering, Logistics, Orders, Platform, Product, and the Site Reliability Engineering (SRE) Team.
**Key entities:** 9, Catalog Team, Customer Experience Team, Data Team, Engineering Team, Logistics Team, Orders Team, Platform Team, Product Team, Site Reliability Engineering (SRE) Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 7.2s] (4 tool calls, agent_miss) - The answer does not mention the number of teams or any expected entities, contradicting the expected answer.
    > The ShopFlow platform has about 1,500 dedicated professionals organized into several specialized teams, but the exact number of teams is not specified (source: company-shopflow.md).
- **graph** [X wrong, 8.0s] (6 tool calls, agent_miss) - The agent's answer lists incorrect teams and misses key expected entities.
    > The ShopFlow platform has 6 teams: Platform Team, Catalog Team, Engineering Team, SRE Team, Payments Service, and Mobile Backend-for-Frontend (BFF) Service.

### `gold-026` - *aggregation_count*

**Question:** How many distinct services or components have their code implemented in Python?

**Expected:** 6 - the Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, and the Monolithic Django App.
**Key entities:** 6, Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 1

- **rag** [X wrong, 5.0s] (3 tool calls, agent_miss) - The agent's answer lists 5 services and misses the Data Lineage Service and Monolithic Django App.
    > There are 5 distinct services implemented in Python: Auth Service, PII Service, Fraud Detection Service, Recommendation Service, and Shopflow App.
- **graph** [X wrong, 4.2s] (2 tool calls, agent_miss) - The agent's answer includes incorrect entities like PostgreSQL and Snowflake, missing expected ones like Auth and Recommendation Services.
    > There are 6 distinct services or components implemented in Python:  1. Data Lineage Service 2. Fraud Detection Service 3. Monolithic Django App 4. PII Service 5. PostgreSQL 6. Snowflake  This information was retrieved using the `reach` function to find entities that are implemented in Python.

### `gold-027` - *aggregation_count*

**Question:** How many entities does the Fraud Detection Service directly integrate with (via INTEGRATES_WITH edges)?

**Expected:** 3 - Elasticsearch, Kibana, and QuickCart.
**Key entities:** 3, Elasticsearch, Kibana, QuickCart

**Oracle Cypher rows:** 1

- **rag** [X wrong, 4.4s] (3 tool calls, agent_miss) - The answer lists incorrect entities and misses Elasticsearch and Kibana, contradicting the expected answer.
    > The Fraud Detection Service directly integrates with 2 entities: Payments Service and QuickCart.
- **graph** [OK correct, 4.7s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Fraud Detection Service directly integrates with 3 entities: Kibana, Elasticsearch, and QuickCart.

### `gold-028` - *negation*

**Question:** Among the services managed by the Platform Team, which ones are NOT implemented in Python?

**Expected:** The GraphQL Service is not documented as being implemented in Python (the Auth Service and PII Service both are).
**Key entities:** GraphQL Service

**Oracle Cypher rows:** 1

- **rag** [X wrong, 14.1s] (9 tool calls, agent_miss) - The agent's answer incorrectly identifies the Payments Service instead of the GraphQL Service as not implemented in Python.
    > The service managed by the Platform Team that is NOT implemented in Python is the **Payments Service**. The other services, including the Auth Service, PII Service, Fraud Detection Service, and Recommendation Service, are all implemented in Python (source: retrieved chunks from the search).
- **graph** [X wrong, 8.7s] (5 tool calls, agent_miss) - The agent's answer incorrectly states that all services are implemented in Python, contradicting the expected answer.
    > The Platform Team manages three services: PII Service, GraphQL Service, and Auth Service. Among these, none are excluded from being implemented in Python:  1. **PII Service** - Implemented in Python. 2. **GraphQL Service** - No specific implementation language mentioned, but it does not explicitly state Python is not used. 3. **Auth Service** - Implemented in Python.  Thus, there are **no services...

### `gold-029` - *negation*

**Question:** Among the services that depend on the Data Lineage Service, which are NOT managed by the Platform Team?

**Expected:** The Payments Service and the Monolithic Django App depend on the Data Lineage Service but are not managed by the Platform Team.
**Key entities:** Payments Service, Monolithic Django App

**Oracle Cypher rows:** 2

- **rag** [~ partial, 13.8s] (9 tool calls, agent_miss) - The agent correctly mentions the Payments Service but incorrectly includes the Shopflow App instead of the Monolithic Django App.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. Payments Service 2. Shopflow App
- **graph** [OK correct, 12.4s] (8 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities accurately.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. Payments Service 2. Monolithic Django App  The only service managed by the Platform Team that depends on the Data Lineage Service is the Auth Service.   This conclusion is based on the relationships identified through the Cypher queries regarding dependencies and management.

### `gold-030` - *negation*

**Question:** Among the services implemented in Python, which ones are NOT managed by the Platform Team?

**Expected:** The Data Lineage Service, the Fraud Detection Service, the Recommendation Service, and the Monolithic Django App are implemented in Python but not managed by the Platform Team.
**Key entities:** Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 4

- **rag** [~ partial, 11.7s] (10 tool calls, agent_miss) - The agent correctly identifies the Recommendation Service but misses other expected entities and incorrectly includes the Shopflow App.
    > The services implemented in Python that are **not** managed by the Platform Team are:  1. **Recommendation Service** 2. **Shopflow App**  The following services are managed by the Platform Team: - **Auth Service** - **PII Service** - **Fraud Detection Service**   Thus, the services not managed by the Platform Team are the Recommendation Service and the Shopflow App (from the findings in the search...
- **graph** [X wrong, 16.2s] (19 tool calls, agent_miss) - The agent's answer includes incorrect services and misses expected entities like the Recommendation Service and Monolithic Django App.
    > The services implemented in Python that are NOT managed by the Platform Team are:  1. Authentication Service 2. BFF Service 3. Data Lineage Service 4. Data Lineage Tracking Service 5. Fraud Detection Service 6. Istio Service Mesh 7. Mobile Backend-for-Frontend (BFF) Service 8. Payments Service 9. QuickCart Orders Service  These findings were derived from analyzing the relationships of each service...
