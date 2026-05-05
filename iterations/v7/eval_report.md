# Eval report - `20260505T095819Z-6f3566`

- Started: 2026-05-05T10:16:23.786958+00:00
- Questions: 30
- Agents: rag, graph, pageindex
- Source: `/Users/emilesilvis/Dropbox/30 - 39 Projects/llms-on-graphs/graph-rag-graph-agent/eval_runs/20260505T095819Z-6f3566.json`

## Accuracy by category

Scores are mean judge grades (correct=1, partial=0.5, wrong=0); `n` is sample size in that cell.

| Category | rag | graph | pageindex |
| --- | --- | --- | --- |
| aggregation_count | 0.12 (n=4) | 0.38 (n=4) | 0.62 (n=4) |
| dependency_chain | 0.75 (n=4) | 0.88 (n=4) | 0.88 (n=4) |
| multi_hop_2 | 0.00 (n=5) | 0.90 (n=5) | 0.20 (n=5) |
| multi_hop_3 | 0.25 (n=4) | 0.50 (n=4) | 0.50 (n=4) |
| negation | 0.50 (n=4) | 0.38 (n=4) | 0.38 (n=4) |
| one_hop | 0.80 (n=5) | 0.80 (n=5) | 0.90 (n=5) |
| shared_neighbor | 0.88 (n=4) | 0.75 (n=4) | 0.88 (n=4) |
| **overall** | **0.47** (n=30) | **0.67** (n=30) | **0.62** (n=30) |

## Latency

| Agent | mean (s) | p95 (s) | n |
| --- | --- | --- | --- |
| rag | 9.43 | 18.07 | 30 |
| graph | 9.06 | 16.25 | 30 |
| pageindex | 13.83 | 26.22 | 30 |

## Tool-call counts

Mean tool calls per question, per category. Higher = the agent needed more retrieval or refinement steps to answer.

| Category | rag | graph | pageindex |
| --- | --- | --- | --- |
| aggregation_count | 6.5 (n=4) | 3.8 (n=4) | 6.2 (n=4) |
| dependency_chain | 6.5 (n=4) | 3.8 (n=4) | 4.8 (n=4) |
| multi_hop_2 | 7.0 (n=5) | 3.6 (n=5) | 7.0 (n=5) |
| multi_hop_3 | 9.2 (n=4) | 9.8 (n=4) | 5.2 (n=4) |
| negation | 8.2 (n=4) | 6.2 (n=4) | 8.0 (n=4) |
| one_hop | 1.0 (n=5) | 1.4 (n=5) | 3.2 (n=5) |
| shared_neighbor | 4.0 (n=4) | 4.2 (n=4) | 3.2 (n=4) |

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
| one_hop | 4 | 0 | 1 | 0 |
| shared_neighbor | 3 | 1 | 0 | 0 |
| **total** | **18** | **11** | **1** | **0** |

### pageindex

| Category | agent_ok | agent_miss | extraction_miss | no_oracle |
| --- | --- | --- | --- | --- |
| aggregation_count | 2 | 2 | 0 | 0 |
| dependency_chain | 3 | 1 | 0 | 0 |
| multi_hop_2 | 1 | 4 | 0 | 0 |
| multi_hop_3 | 2 | 2 | 0 | 0 |
| negation | 0 | 4 | 0 | 0 |
| one_hop | 4 | 1 | 0 | 0 |
| shared_neighbor | 3 | 1 | 0 | 0 |
| **total** | **15** | **15** | **0** | **0** |

## `set_difference` adoption (graph agent, v6)

Number of `set_difference(candidate_cypher, exclude_cypher)` tool invocations that produced a populated diff (rather than an error). Quantifies how often v6's lever 1 (negation guard rail) actually fired - paradigm-symmetric to v5's alias-folded calls and v3's `find_rel_types_like` coverage.

Total `set_difference` calls across all questions: **12** (touched 8 of 30 graph rows).

| Question | Category | set_difference calls |
| --- | --- | --- |
| `gold-008` | negation | 1 |
| `gold-021` | dependency_chain | 2 |
| `gold-024` | shared_neighbor | 1 |
| `gold-025` | aggregation_count | 2 |
| `gold-026` | aggregation_count | 1 |
| `gold-028` | negation | 3 |
| `gold-029` | negation | 1 |
| `gold-030` | negation | 1 |

## `get_section_content` adoption (pageindex agent, v7)

Number of `get_section_content(node_id)` tool invocations per question. Quantifies how many tree nodes the PageIndex agent navigated to before answering - paradigm-symmetric to v6's `set_difference` adoption section and v5's alias-folded calls.

Total `get_section_content` calls across all questions: **129** (touched 30 of 30 pageindex rows).

| Question | Category | section calls |
| --- | --- | --- |
| `gold-001` | one_hop | 3 |
| `gold-002` | one_hop | 1 |
| `gold-003` | one_hop | 4 |
| `gold-004` | multi_hop_2 | 1 |
| `gold-005` | multi_hop_2 | 10 |
| `gold-006` | shared_neighbor | 2 |
| `gold-007` | aggregation_count | 3 |
| `gold-008` | negation | 4 |
| `gold-009` | multi_hop_3 | 2 |
| `gold-010` | dependency_chain | 5 |
| `gold-011` | one_hop | 2 |
| `gold-012` | one_hop | 1 |
| `gold-013` | multi_hop_2 | 8 |
| `gold-014` | multi_hop_2 | 10 |
| `gold-015` | multi_hop_2 | 1 |
| `gold-016` | multi_hop_3 | 3 |
| `gold-017` | multi_hop_3 | 10 |
| `gold-018` | multi_hop_3 | 2 |
| `gold-019` | dependency_chain | 3 |
| `gold-020` | dependency_chain | 4 |
| `gold-021` | dependency_chain | 3 |
| `gold-022` | shared_neighbor | 3 |
| `gold-023` | shared_neighbor | 2 |
| `gold-024` | shared_neighbor | 2 |
| `gold-025` | aggregation_count | 1 |
| `gold-026` | aggregation_count | 6 |
| `gold-027` | aggregation_count | 9 |
| `gold-028` | negation | 10 |
| `gold-029` | negation | 7 |
| `gold-030` | negation | 7 |

## Alias-folded tool calls (graph agent, v5)

Number of `reach` / `neighbourhood` / `resolve_entity` calls where two or more node-name spellings (alias siblings, e.g. `Auth Service` + `Authentication Service`) were unioned in the result. Quantifies how often v5's lever 1 (tool-level alias resolution) actually fired.

Total alias-folded tool calls across all questions: **58** (touched 23 of 30 graph rows).

| Question | Category | alias-folded calls |
| --- | --- | --- |
| `gold-001` | one_hop | 1 |
| `gold-002` | one_hop | 2 |
| `gold-004` | multi_hop_2 | 3 |
| `gold-006` | shared_neighbor | 4 |
| `gold-007` | aggregation_count | 2 |
| `gold-008` | negation | 3 |
| `gold-009` | multi_hop_3 | 2 |
| `gold-010` | dependency_chain | 3 |
| `gold-011` | one_hop | 1 |
| `gold-012` | one_hop | 1 |
| `gold-013` | multi_hop_2 | 3 |
| `gold-014` | multi_hop_2 | 1 |
| `gold-016` | multi_hop_3 | 10 |
| `gold-017` | multi_hop_3 | 1 |
| `gold-018` | multi_hop_3 | 2 |
| `gold-019` | dependency_chain | 1 |
| `gold-020` | dependency_chain | 2 |
| `gold-022` | shared_neighbor | 4 |
| `gold-023` | shared_neighbor | 4 |
| `gold-025` | aggregation_count | 2 |
| `gold-027` | aggregation_count | 1 |
| `gold-028` | negation | 4 |
| `gold-029` | negation | 1 |

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
| `gold-018` | developed by | yes |
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

- **rag** [OK correct, 2.9s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The Auth Service is managed by the **Platform Team** (source: [service-auth-service.md](service-auth-service.md)).
- **graph** [OK correct, 3.1s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The team that manages the Auth Service is the **Platform Team**. This information was retrieved from the relationships associated with the Auth Service.
- **pageindex** [OK correct, 8.0s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The **Auth Service** is managed by the **Platform Team**. This team is responsible for the operation and maintenance of the Auth Service, ensuring secure and reliable access management across the platform (node_id: 0172).   The Platform Team focuses on scalability, security, and efficiency in managing services like the Auth Service (node_id: 0351).

### `gold-002` - *one_hop*

**Question:** What programming language is the Payments Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** (no oracle for this question)

- **rag** [X wrong, 3.2s] (1 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java** (source: team-product.md).
- **graph** [X wrong, 6.9s] (2 tool calls, extraction_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java**. This information was retrieved from the relationship `[:IMPLEMENTED_IN]` in the graph.
- **pageindex** [OK correct, 5.4s] (2 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Payments Service is implemented in **Python**. This choice is made for its simplicity and robust libraries, which are beneficial for handling payment transactions efficiently (source: node_id 0235).

### `gold-003` - *one_hop*

**Question:** What does Istio facilitate in the ShopFlow platform?

**Expected:** Istio facilitates service-to-service communication.
**Key entities:** service-to-service communication

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.2s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities, including 'service-to-service communication'.
    > Istio facilitates efficient service-to-service communication within the ShopFlow platform by providing a uniform way to secure, connect, and observe microservices. This service mesh is integral to the platform's microservices architecture, allowing for smooth management of complex distributed systems. Key microservices, including the Shopflow App, operate on this robust Istio infrastructure (sourc...
- **graph** [OK correct, 3.5s] (2 tool calls, agent_ok) - The agent's answer includes the expected entity and accurately describes Istio's role in the platform.
    > Istio facilitates service-to-service communication in the ShopFlow platform. Additionally, it provides security, observability, and traffic management, and is part of the microservices architecture and API ecosystem. It also supports canary releases (from the neighbourhood of Istio).
- **pageindex** [~ partial, 15.9s] (5 tool calls, agent_miss) - The agent's answer mentions service communication but adds extra details not in the expected answer.
    > In the ShopFlow platform, Istio facilitates improved service communication and management by providing advanced capabilities such as service discovery, load balancing, and monitoring. This integration enhances the resilience of the microservices architecture, allowing for seamless traffic management and quicker issue detection. Additionally, it supports scalability by simplifying interactions betw...

### `gold-004` - *multi_hop_2*

**Question:** Which infrastructure does the service managed by the Platform Team for authentication use?

**Expected:** It uses AWS, Kubernetes EKS, and Kafka.
**Key entities:** AWS, Kubernetes EKS, Kafka

**Oracle Cypher rows:** 3

- **rag** [X wrong, 4.2s] (2 tool calls, agent_miss) - The agent's answer does not mention AWS, Kubernetes EKS, or Kafka, and instead discusses unrelated technologies.
    > The Auth Service managed by the Platform Team uses a scalable infrastructure built with Python. It integrates with Redis to cache session data and authentication tokens, which helps reduce database load by serving token validation requests directly from the cache (source: [service-auth-service.md]).
- **graph** [OK correct, 11.5s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: AWS, Kubernetes EKS, and Kafka.
    > The service managed by the Platform Team for authentication, known as the Auth Service, uses the following infrastructure:  1. **Kafka** 2. **Kubernetes EKS** 3. **AWS**  These infrastructures are utilized for various functions including managing authentication requests and ensuring smoother interactions.   This information was gathered from the neighbourhood of the Auth Service, specifically look...
- **pageindex** [OK correct, 14.3s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: AWS, Kubernetes EKS, and Kafka.
    > The service managed by the Platform Team for authentication, known as the **Auth Service**, uses the following infrastructure:  1. **AWS** - for scalability and reliability. 2. **Kubernetes EKS** - for managing containerized applications. 3. **Kafka** - for message brokering.  This information was retrieved from the section on the Auth Service (node_id: 0172).

### `gold-005` - *multi_hop_2*

**Question:** Who authored the ADR about the QuickCart acquisition, and what is their role?

**Expected:** Bob Martinez, who is a Staff SRE, authored it.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 18.1s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the author or their role, missing all key entities.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 7.5s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The ADR about the QuickCart acquisition was authored by Bob Martinez, who holds the role of Staff SRE. This information was gathered from the relationships associated with both the ADR and the author.
- **pageindex** [X wrong, 24.5s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the author or their role, missing key entities.
    > Sorry, need more steps to process this request.

### `gold-006` - *shared_neighbor*

**Question:** Which programming language is used by both the Auth Service and the PII Service?

**Expected:** Python is used by both.
**Key entities:** Python

**Oracle Cypher rows:** 4

- **rag** [OK correct, 4.5s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service are developed using **Python**.   - Auth Service: Built with Python (source: service-auth-service.md). - PII Service: Developed in Python (source: service-pii-service.md).
- **graph** [OK correct, 5.5s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > Both the Auth Service and the PII Service use **Python** as their programming language.   - The Auth Service is built with Python. - The PII Service is developed in Python.  This information was gathered from the neighbourhoods of both services, specifically looking for the programming language used.
- **pageindex** [OK correct, 6.5s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service use **Python** as their programming language.  - **Auth Service**: Built with Python. - **PII Service**: Also developed in Python.  This information was retrieved from the sections on the Auth Service (node_id: 0172) and the PII Service (node_id: 0248).

### `gold-007` - *aggregation_count*

**Question:** How many services does the Platform Team manage?

**Expected:** The Platform Team manages 3 services (Auth Service, GraphQL Service, PII Service).
**Key entities:** 3, Auth Service, GraphQL Service, PII Service

**Oracle Cypher rows:** 1
**Oracle enumeration (3):** Auth Service, GraphQL Service, PII Service

- **rag** [X wrong, 14.9s] (10 tool calls, agent_miss) - The agent's answer lists incorrect services and misses expected entities like GraphQL Service and PII Service.
    > The Platform Team manages 3 services: Auth Service, Data Lineage Service, and Payments Service (from the notes in the scratchpad).
- **graph** [OK correct, 3.5s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages 3 services: PII Service, GraphQL Service, and Auth Service.
- **pageindex** [OK correct, 26.2s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages **three services**:  1. **Auth Service** - Handles user authentication and ensures secure access across applications. 2. **PII Service** - Manages Personally Identifiable Information (PII) to ensure compliance with data protection laws. 3. **GraphQL Service** - Enables flexible data querying and efficient communication between client and server.  These services are design...

### `gold-008` - *negation*

**Question:** Among the services managed by the Platform Team, which ones do NOT depend on the Data Lineage Service?

**Expected:** The GraphQL Service and the PII Service do not depend on the Data Lineage Service.
**Key entities:** GraphQL Service, PII Service

**Oracle Cypher rows:** 2

- **rag** [~ partial, 16.7s] (11 tool calls, agent_miss) - The agent mentions the PII Service but omits the GraphQL Service, which is also expected.
    > Among the services managed by the Platform Team, the one that does NOT depend on the Data Lineage Service is the **PII Service**.   The other services, namely the **Auth Service**, **Payments Service**, and **Shopflow App**, all have dependencies on the Data Lineage Service (source: service-auth-service.md, service-payments-service.md, service-shopflow-app.md).
- **graph** [OK correct, 13.5s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: GraphQL Service and PII Service.
    > Among the services managed by the Platform Team, the ones that do NOT depend on the Data Lineage Service are:  1. PII Service 2. GraphQL Service  This was determined by identifying the services managed by the Platform Team and excluding those that depend on the Data Lineage Service. The relevant Cypher patterns used were for managing services and checking dependencies.
- **pageindex** [X wrong, 27.3s] (5 tool calls, agent_miss) - The agent's answer incorrectly includes the Auth Service, which contradicts the expected answer.
    > Among the services managed by the Platform Team, the following do NOT depend on the Data Lineage Service:  1. **GraphQL Service** 2. **PII Service** 3. **Auth Service**  The Auth Service explicitly depends on the Data Lineage Service, while the GraphQL and PII Services do not have any stated dependencies on it (source: sections on the Platform Team, Auth Service, and Data Lineage Service).

### `gold-009` - *multi_hop_3*

**Question:** What database does the service authored (developed) by Bob Martinez use for caching?

**Expected:** The Auth Service, developed by Bob Martinez, uses Redis for caching.
**Key entities:** Auth Service, Redis

**Oracle Cypher rows:** 1

- **rag** [X wrong, 22.0s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the Auth Service or Redis.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 8.9s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Redis.
    > The service authored by Bob Martinez, known as the Auth Service, uses **Redis** for caching. This was determined by examining the relationships of the Auth Service, which indicates it utilizes Redis as its database for caching purposes.
- **pageindex** [OK correct, 15.9s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Redis.
    > The service authored by Bob Martinez, the **Auth Service**, uses **Redis** for caching session data and user credentials. This caching mechanism helps reduce the load on the primary database by storing temporary session information and allows for faster authentication checks.  Additionally, the **Payments Service**, which is also relevant, employs Redis as a caching layer to improve response rates...

### `gold-010` - *dependency_chain*

**Question:** Which services depend on the Data Lineage Service, directly or transitively?

**Expected:** The Auth Service and the Payments Service depend on the Data Lineage Service.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 3

- **rag** [~ partial, 16.3s] (10 tool calls, agent_miss) - The answer includes the expected entities but adds extra services not mentioned in the expected answer.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service**    - Transitive dependency: **Fraud Detection Service** 3. **Shopflow App**    - Transitive dependencies: **Recommendation Service**, **Mobile BFF Service**  Thus, the complete list of services is: - Auth Service - Payments Service - Fraud Detection Service - Sho...
- **graph** [OK correct, 12.9s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service**  Both services have a direct dependency on the Data Lineage Service (hops=1).   This information was gathered using the `reach` tool to find dependencies and then further explored using `neighbourhood` to confirm the relationships.
- **pageindex** [~ partial, 14.5s] (6 tool calls, agent_miss) - The answer includes the expected entities but adds extra services not mentioned in the expected answer.
    > The services that depend on the **Data Lineage Service**, either directly or transitively, are:  1. **Auth Service** - It relies on the Data Lineage Service for tracking and handling user authentication data flow. 2. **Payments Service** - This service utilizes the Data Lineage Service to track payment information flow, ensuring end-to-end traceability. 3. **Shopflow App** - It has a direct depend...

### `gold-011` - *one_hop*

**Question:** What programming language is the Data Lineage Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 2.4s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in **Python** (source: service-data-lineage-service.md).
- **graph** [OK correct, 2.6s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in Python. This information was retrieved from the relationship `IS_IMPLEMENTED_IN` in the graph.
- **pageindex** [OK correct, 13.8s] (3 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in **Python**. This service is a core component of the microservices architecture, designed to track data flow and maintain data integrity across various services (node_id: 0200).

### `gold-012` - *one_hop*

**Question:** Which cache does the Auth Service use for storing session data?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.7s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > The Auth Service uses **Redis** for storing session data. This caching mechanism helps reduce the load on the primary database by serving session information directly from the cache (source: technology-redis-cache.md, service-auth-service.md).
- **graph** [OK correct, 2.1s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Redis'.
    > The Auth Service uses Redis for storing session data.
- **pageindex** [OK correct, 8.5s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > The Auth Service uses **Redis** for storing session data. It caches both session information and user credentials to reduce the load on the primary database and facilitate faster authentication checks (source: node_id 0172).

### `gold-013` - *multi_hop_2*

**Question:** Who leads the team that operates the QuickCart Orders Service?

**Expected:** Bob Martinez leads the Orders Team, which operates the QuickCart Orders Service.
**Key entities:** Bob Martinez, Orders Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 18.9s] (11 tool calls, hit step cap, agent_miss) - The answer does not mention any expected entities or provide relevant information.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 7.7s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The team that operates the QuickCart Orders Service is led by Bob Martinez.
- **pageindex** [X wrong, 30.5s] (9 tool calls, agent_miss) - The agent's answer incorrectly names Dan Okafor instead of Bob Martinez as the team leader.
    > The team that operates the QuickCart Orders Service is the **Orders Team**, which consists of **25 members**. The team is led by **Dan Okafor**, who is a Backend Engineer and was involved in the creation of the service. The Orders Team is responsible for managing customer orders efficiently, ensuring service reliability, and optimizing the order processing system (source: node_ids 0340, 0258).

### `gold-014` - *multi_hop_2*

**Question:** What programming language is the service developed by Bob Martinez built with?

**Expected:** Python - the Auth Service, which Bob Martinez developed, is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 6.8s] (5 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating JavaScript instead of Python.
    > The service developed by Bob Martinez is built with JavaScript.
- **graph** [OK correct, 8.4s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The service developed by Bob Martinez, known as the Auth Service, is built with Python.
- **pageindex** [X wrong, 19.6s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the programming language or the service developed by Bob Martinez.
    > Sorry, need more steps to process this request.

### `gold-015` - *multi_hop_2*

**Question:** Who authored the ADR about GDPR compliance, and what team do they lead?

**Expected:** Alice Chen authored the ADR and leads the SRE Team.
**Key entities:** Alice Chen, SRE Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 9.8s] (6 tool calls, agent_miss) - The answer incorrectly states Alice Chen's role and team, missing 'SRE Team' and contradicting the expected answer.
    > The ADR about GDPR compliance was authored by **Alice Chen**, who is a **Senior Architect**. She is part of the **Engineering Team**, which consists of 150 engineers (source: [adr-gdpr-compliance-2020.md](adr-gdpr-compliance-2020.md) and [team-engineering.md](team-engineering.md)).
- **graph** [~ partial, 6.1s] (3 tool calls, agent_miss) - The agent correctly identifies Alice Chen as the author but incorrectly states the team she leads.
    > Alice Chen authored the ADR about GDPR compliance and leads the Customer Experience Team.
- **pageindex** [X wrong, 6.7s] (2 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating Alice Chen leads the Platform Team, not the SRE Team.
    > The ADR about GDPR compliance was authored by **Alice Chen**, who is a **Senior Architect**. She leads the implementation of the GDPR compliance services, specifically the PII Service and Data Lineage Tracking Service, which are managed by the **Platform Team** (as indicated in the context of the ADR).   This information was retrieved from the section on GDPR compliance (node_id: 0044).

### `gold-016` - *multi_hop_3*

**Question:** Which programming language is used by the service that is managed by the Platform Team and depends on the Data Lineage Service?

**Expected:** Python - the Auth Service is managed by the Platform Team, depends on the Data Lineage Service, and is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 6.7s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Auth Service**. It is built using the **Python** programming language.   Sources:  - Auth Service overview (service-auth-service.md) - Data Lineage Service dependencies (service-data-lineage-service.md)
- **graph** [X wrong, 16.3s] (11 tool calls, agent_miss) - The agent's answer mentions incorrect entities and contradicts the expected answer.
    > The service that is managed by the Platform Team and depends on the Data Lineage Service is the **Payments Service**, which is implemented in **Java**.   This information was gathered through a series of queries that identified the relationships between the Platform Team, the Payments Service, and the Data Lineage Service.
- **pageindex** [OK correct, 5.7s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Python.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Auth Service**. The programming language used for the Auth Service is **Python** (as indicated in the service details).   Thus, the answer is: - **Programming Language**: Python - **Service**: Auth Service  This information was retrieved from the sections on the Platform Team, Data Lineage Service, and Auth ...

### `gold-017` - *multi_hop_3*

**Question:** What programming language is used by the service developed by the person who authored 'ADR: QuickCart Acquisition and Integration'?

**Expected:** Python - Bob Martinez authored the ADR and developed the Auth Service, which is built with Python.
**Key entities:** Bob Martinez, Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 16.3s] (11 tool calls, hit step cap, agent_miss) - The answer is a refusal and does not mention any expected entities or facts.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 6.3s] (4 tool calls, agent_ok) - The agent's answer includes all expected entities and accurately reflects the expected answer.
    > The service developed by Bob Martinez, who authored 'ADR: QuickCart Acquisition and Integration', is the **Auth Service**, which is built using **Python**.   This information was gathered through the relationships connecting Bob Martinez to the Auth Service and the programming language used for its development.
- **pageindex** [X wrong, 16.1s] (11 tool calls, hit step cap, agent_miss) - The answer is a refusal and does not mention any expected entities or facts.
    > Sorry, need more steps to process this request.

### `gold-018` - *multi_hop_3*

**Question:** What role does the person who developed the authentication service managed by the Platform Team have?

**Expected:** Staff SRE - Bob Martinez, who developed the Auth Service (managed by the Platform Team), is a Staff SRE.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 14.8s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about Bob Martinez or the Staff SRE role.
    > Sorry, need more steps to process this request.
- **graph** [X wrong, 39.0s] (19 tool calls, hit step cap, agent_miss) - The agent's answer is a refusal and does not mention any expected entities or facts.
    > Sorry, need more steps to process this request.
- **pageindex** [X wrong, 6.4s] (3 tool calls, agent_miss) - The answer does not mention Bob Martinez or the role of Staff SRE, missing key entities.
    > The person who developed the authentication service managed by the Platform Team has the role of a developer, specifically working on the **Auth Service**. This service is responsible for handling user authentication requests and is managed by the Platform Team, which focuses on building and maintaining essential backend services.   The Auth Service is built using Python and operates on AWS infras...

### `gold-019` - *dependency_chain*

**Question:** Which services rely on the Payments Service, directly or transitively?

**Expected:** The Fraud Detection Service relies on the Payments Service.
**Key entities:** Fraud Detection Service

**Oracle Cypher rows:** 1

- **rag** [OK correct, 14.1s] (10 tool calls, agent_ok) - The agent's answer includes the expected entity 'Fraud Detection Service' and aligns with the expected answer.
    > The services that rely on the Payments Service, either directly or transitively, are:  1. **ShopFlow App** 2. **Data Lineage Service** 3. **Fraud Detection Service** 4. **Recommendation Service** (depends on ShopFlow App) 5. **Auth Service** (depends on Data Lineage Service)  Thus, the complete list of services is: ShopFlow App, Data Lineage Service, Fraud Detection Service, Recommendation Service...
- **graph** [OK correct, 2.8s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Fraud Detection Service'.
    > The service that relies on the Payments Service, directly or transitively, is the **Fraud Detection Service**.
- **pageindex** [OK correct, 19.6s] (4 tool calls, agent_ok) - The agent's answer includes the expected entity 'Fraud Detection Service' and aligns with the expected answer.
    > The services that rely on the Payments Service, either directly or transitively, are:  1. **Fraud Detection Service** - Directly relies on the Payments Service to monitor transaction data continuously. 2. **Data Lineage Service** - Utilizes the Payments Service to track payment information flow, ensuring end-to-end traceability. 3. **ShopFlow App** - Integrates with the Payments Service for seamle...

### `gold-020` - *dependency_chain*

**Question:** Which service, directly or transitively, depends on the ShopFlow application?

**Expected:** The Recommendation Service depends on the ShopFlow application.
**Key entities:** Recommendation Service

**Oracle Cypher rows:** 1

- **rag** [~ partial, 8.0s] (4 tool calls, agent_miss) - The agent's answer includes the expected entity but adds unrelated services, making it incomplete and slightly off-track.
    > The services that depend directly or transitively on the ShopFlow application are:  1. **Payments Service**: Integrates with ShopFlow for transaction workflows and is a dependency for the Fraud Detection Service. 2. **Recommendation Service**: Depends on ShopFlow to access user interaction data for generating recommendations. 3. **Data Lineage Service**: Directly depends on ShopFlow for tracking d...
- **graph** [OK correct, 5.2s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The service that directly depends on the ShopFlow application is the **Recommendation Service**. This service relies on ShopFlow for its operations.   The findings were based on the relationship types `DEPENDS_ON` and `RELIES_ON` observed in the graph.
- **pageindex** [OK correct, 15.8s] (5 tool calls, agent_ok) - The agent's answer includes the Recommendation Service, which is the expected entity, along with additional relevant details.
    > The services that directly or transitively depend on the ShopFlow application include:  1. **Payments Service** - Integrates with the ShopFlow App to facilitate seamless transaction workflows. 2. **Data Lineage Service** - Ensures all data transformations and usages are tracked accurately, relying on the ShopFlow App for data consistency. 3. **Recommendation Service** - Utilizes the ShopFlow App t...

### `gold-021` - *dependency_chain*

**Question:** Which services use Redis for caching or session storage? Consider all relationship types that express use/employ/cache.

**Expected:** The Auth Service and the Payments Service both use Redis for caching.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 2

- **rag** [OK correct, 5.1s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that use Redis for caching or session storage are:  1. **Auth Service**    - Uses Redis for caching session data and user credentials.  2. **Payments Service**    - Employs Redis for caching transaction histories and managing session data.  Both services utilize Redis to enhance performance by reducing load on the primary database and improving response times (sources: technology-redi...
- **graph** [~ partial, 10.2s] (6 tool calls, agent_miss) - The agent mentions the Auth Service but incorrectly states the Payments Service's use of Redis.
    > The services that use Redis for caching or session storage are:  1. **Auth Service** (via the relationship `USES_DATABASE`).  The Payments Service employs Redis but does not use it for caching or session storage based on the relationships identified.
- **pageindex** [OK correct, 5.8s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that use Redis for caching or session storage are:  1. **Auth Service**    - Uses Redis to cache session data and authentication tokens, reducing load on the primary database.  2. **Payments Service**    - Caches transaction histories and recent payment details to enhance transaction lookup speed.  In total, there are **2 services** that utilize Redis for caching or session storage. T...

### `gold-022` - *shared_neighbor*

**Question:** Which cache database is used by both the Auth Service and the Payments Service?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.6s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the Auth Service and the Payments Service use **Redis** as their cache database. Redis is utilized to cache session data and authentication tokens for the Auth Service, and to cache transaction histories and recent payment details for the Payments Service (source: technology-redis-cache.md).
- **graph** [OK correct, 6.6s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the **Auth Service** and the **Payments Service** use **Redis** as their cache database.   - The **Auth Service** has an outgoing relationship indicating it **uses** Redis. - The **Payments Service** also has an outgoing relationship indicating it **employs** Redis.  This information was gathered from the neighbourhoods of both services, where Redis was identified as a common cache database.
- **pageindex** [OK correct, 5.7s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the Auth Service and the Payments Service use **Redis** as their caching database.   - The **Auth Service** utilizes Redis for caching session data and user credentials to enhance performance and reduce load on the primary database. - The **Payments Service** employs Redis to cache transaction histories and recent payment details, improving transaction lookup speed.  This information was retr...

### `gold-023` - *shared_neighbor*

**Question:** Which programming language is used by both the Fraud Detection Service and the Recommendation Service?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.8s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service are implemented in **Python**.   - The Fraud Detection Service is designed to identify and prevent fraudulent activities and is implemented in Python (source: service-fraud-detection-service.md). - The Recommendation Service offers tailored recommendations and is also built using Python (source: service-recommendation-service.md).
- **graph** [OK correct, 6.2s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service are built using **Python**.   - The Fraud Detection Service is implemented in Python. - The Recommendation Service is built using Python.  This information was gathered from the neighbourhoods of both services, where the relevant relationships were identified.
- **pageindex** [OK correct, 4.8s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the **Fraud Detection Service** and the **Recommendation Service** use **Python** as their programming language.  - **Fraud Detection Service**: Implemented in Python (node_id: 0225). - **Recommendation Service**: Also built using Python (node_id: 0270).   Thus, the programming language used by both services is Python.

### `gold-024` - *shared_neighbor*

**Question:** Which services integrate with both the GraphQL Federation Layer and the Monolithic Django App?

**Expected:** The BFF Service and the Recommendation Service integrate with both.
**Key entities:** BFF Service, Recommendation Service

**Oracle Cypher rows:** 2

- **rag** [~ partial, 9.3s] (10 tool calls, agent_miss) - The agent's answer includes the expected entities but adds extra, unsupported services.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **BFF Service** 2. **Recommendation Service** 3. **Fraud Detection Service** 4. **Quickcart Orders Service**  These services are mentioned as key integrations for both the GraphQL Federation Layer and the Monolithic Django App (source: [service-graphql-service.md](service-graphql-service.md) a...
- **graph** [X wrong, 11.6s] (5 tool calls, agent_miss) - The answer includes incorrect entities not in the expected answer, such as Fraud Detection Service and Quickcart Orders.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. BFF Service 2. Recommendation Service 3. Fraud Detection Service 4. Quickcart Orders  This was determined by identifying the services that the GraphQL Federation Layer integrates with and then checking which of those also integrate with the Monolithic Django App, using the relationship types r...
- **pageindex** [~ partial, 5.2s] (3 tool calls, agent_miss) - The agent's answer includes the expected entities but adds an incorrect entity, the Fraud Detection Service.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App (Shopflow App) are:  1. **Backend for Frontend (BFF) Service** 2. **Recommendation Service** 3. **Fraud Detection Service**  These services interact with the GraphQL Federation Layer and also have dependencies or integrations with the Monolithic Django App (Shopflow App) (from node_ids 0058 and 0279).

### `gold-025` - *aggregation_count*

**Question:** How many teams does the ShopFlow platform have?

**Expected:** ShopFlow has 9 teams - Catalog, Customer Experience, Data, Engineering, Logistics, Orders, Platform, Product, and the Site Reliability Engineering (SRE) Team.
**Key entities:** 9, Catalog Team, Customer Experience Team, Data Team, Engineering Team, Logistics Team, Orders Team, Platform Team, Product Team, Site Reliability Engineering (SRE) Team

**Oracle Cypher rows:** 1
**Oracle enumeration (9):** Catalog Team, Customer Experience Team, Data Team, Engineering Team, Logistics Team, Orders Team, Platform Team, Product Team, Site Reliability Engineering (SRE) Team

- **rag** [X wrong, 6.5s] (4 tool calls, agent_miss) - The answer does not mention the number of teams or any expected entities, and states it lacks information.
    > The ShopFlow platform has approximately 1,500 dedicated professionals organized into several specialized teams. However, the exact number of teams is not specified in the retrieved information (source: company-shopflow.md).
- **graph** [X wrong, 12.9s] (9 tool calls, agent_miss) - The agent's answer lists only 3 teams, missing key entities and contradicting the expected total of 9 teams.
    > The ShopFlow platform has 3 teams: Platform Team, Catalog Team, and Engineering Team.
- **pageindex** [OK correct, 7.6s] (4 tool calls, agent_ok) - The agent's answer lists all 9 teams and matches the expected entities.
    > The ShopFlow platform has 9 teams:  1. Engineering Team 2. Platform Team 3. Product Team 4. Data Team 5. Catalog Team 6. Orders Team 7. Logistics Team 8. Customer Experience Team 9. Site Reliability Engineering (SRE) Team  This information was retrieved from the "company-shopflow" section.

### `gold-026` - *aggregation_count*

**Question:** How many distinct services or components have their code implemented in Python?

**Expected:** 6 - the Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, and the Monolithic Django App.
**Key entities:** 6, Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 1
**Oracle enumeration (6):** Auth Service, Data Lineage Service, Fraud Detection Service, Monolithic Django App, PII Service, Recommendation Service

- **rag** [~ partial, 11.3s] (8 tool calls, agent_miss) - The agent's answer includes 5 correct entities but incorrectly adds QuickCart Orders Service instead of Data Lineage Service.
    > There are **6 distinct services** implemented in Python:  1. Auth Service 2. PII Service 3. Fraud Detection Service 4. Recommendation Service 5. Monolithic Django App 6. QuickCart Orders Service (from the final scratchpad note).
- **graph** [X wrong, 9.6s] (2 tool calls, agent_miss) - The agent's answer contradicts the expected answer and misses all key entities.
    > There are no distinct services or components that have their code implemented in Python. The candidates found were also excluded, indicating that they do not meet the criteria.
- **pageindex** [~ partial, 19.5s] (7 tool calls, agent_miss) - The agent's answer includes 6 services but incorrectly lists 'Payments Service' instead of 'Data Lineage Service'.
    > There are **six distinct services** with their code implemented in Python:  1. **Auth Service** 2. **Fraud Detection Service** 3. **Payments Service** 4. **PII Service** 5. **Recommendation Service** 6. **Shopflow App** (Monolithic Django App)  These services leverage Python for various functionalities, including authentication, fraud detection, payment processing, data privacy compliance, and per...

### `gold-027` - *aggregation_count*

**Question:** How many entities does the Fraud Detection Service directly integrate with (via INTEGRATES_WITH edges)?

**Expected:** 3 - Elasticsearch, Kibana, and QuickCart.
**Key entities:** 3, Elasticsearch, Kibana, QuickCart

**Oracle Cypher rows:** 1
**Oracle enumeration (3):** Elasticsearch, Kibana, QuickCart

- **rag** [X wrong, 4.8s] (4 tool calls, agent_miss) - The answer lists incorrect entities and an incorrect number of integrations, missing Elasticsearch and Kibana.
    > The Fraud Detection Service directly integrates with 2 entities: Payments Service and QuickCart.
- **graph** [~ partial, 4.3s] (2 tool calls, agent_miss) - The answer mentions the correct number but lacks the specific entities: Elasticsearch, Kibana, and QuickCart.
    > The Fraud Detection Service directly integrates with 3 entities via INTEGRATES_WITH edges.
- **pageindex** [X wrong, 15.2s] (10 tool calls, agent_miss) - The answer lists incorrect entities and misses Elasticsearch and Kibana, contradicting the expected answer.
    > The Fraud Detection Service directly integrates with **three** entities via INTEGRATES_WITH edges:  1. **Payments Service** 2. **QuickCart** 3. **GraphQL Service**  These integrations facilitate fraud detection and prevention in various transaction contexts (node IDs: 0210, 0218, 0219).

### `gold-028` - *negation*

**Question:** Among the services managed by the Platform Team, which ones are NOT implemented in Python?

**Expected:** The GraphQL Service is not documented as being implemented in Python (the Auth Service and PII Service both are).
**Key entities:** GraphQL Service

**Oracle Cypher rows:** 1

- **rag** [~ partial, 9.6s] (7 tool calls, agent_miss) - The agent correctly identifies the GraphQL Service but adds an unsupported Payments Service, which is not in the expected answer.
    > The services managed by the Platform Team that are NOT implemented in Python are:  1. **GraphQL Service** - Implemented in JavaScript. 2. **Payments Service** - Implemented in Java.  The other services, such as the Data Lineage Service, PII Service, and Fraud Detection Service, are implemented in Python.
- **graph** [X wrong, 18.7s] (12 tool calls, agent_miss) - The agent's answer incorrectly states the PII Service is not implemented in Python and lacks clarity on the GraphQL Service.
    > The services managed by the Platform Team that are NOT implemented in Python are:  - **PII Service** (implemented in PostgreSQL) - **GraphQL Service** (no implementation found) - **Auth Service** (no implementation found)  Thus, the only service with a known implementation that is not Python is the PII Service, which is implemented in PostgreSQL. The other two services do not have any recorded imp...
- **pageindex** [~ partial, 16.4s] (11 tool calls, agent_miss) - The agent correctly identifies the GraphQL Service but adds an unsupported service, QuickCart Orders Service.
    > The services managed by the Platform Team that are **NOT** implemented in Python are:  1. **GraphQL Service** - Implemented in JavaScript. 2. **QuickCart Orders Service** - The documentation does not specify the programming language, but it is integrated with Amazon SQS for messaging.  The following services managed by the Platform Team are implemented in Python: - Auth Service - PII Service - Rec...

### `gold-029` - *negation*

**Question:** Among the services that depend on the Data Lineage Service, which are NOT managed by the Platform Team?

**Expected:** The Payments Service and the Monolithic Django App depend on the Data Lineage Service but are not managed by the Platform Team.
**Key entities:** Payments Service, Monolithic Django App

**Oracle Cypher rows:** 2

- **rag** [~ partial, 10.9s] (6 tool calls, agent_miss) - The agent correctly identifies the Payments Service but incorrectly includes the Shopflow App instead of the Monolithic Django App.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. **Payments Service** - Managed by the Product Team. 2. **Shopflow App** - Managed by the Engineering Team.  Thus, the answer is: - Payments Service - Shopflow App  These findings are based on the dependencies of the Data Lineage Service (from the service-data-lineage-service.md) and the managemen...
- **graph** [X wrong, 10.0s] (4 tool calls, agent_miss) - The agent's answer lists incorrect services and misses the expected entities entirely.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. PII Service 2. GraphQL Service  The Auth Service is managed by the Platform Team.
- **pageindex** [~ partial, 18.9s] (8 tool calls, agent_miss) - The agent correctly identifies the Payments Service but incorrectly includes the Shopflow App instead of the Monolithic Django App.
    > The services that depend on the **Data Lineage Service** and are NOT managed by the **Platform Team** are:  1. **Auth Service** - Managed by the Platform Team. 2. **Payments Service** - Managed by the Product Team. 3. **Shopflow App** - Managed by the Engineering Team.  Thus, the services that depend on the Data Lineage Service but are not managed by the Platform Team include the **Payments Servic...

### `gold-030` - *negation*

**Question:** Among the services implemented in Python, which ones are NOT managed by the Platform Team?

**Expected:** The Data Lineage Service, the Fraud Detection Service, the Recommendation Service, and the Monolithic Django App are implemented in Python but not managed by the Platform Team.
**Key entities:** Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 4

- **rag** [~ partial, 10.7s] (9 tool calls, agent_miss) - The agent's answer mentions some expected entities but includes incorrect ones and misses others.
    > The services implemented in Python that are **not** managed by the Platform Team are:  1. **Fraud Detection Service** 2. **Recommendation Service** 3. **Shopflow App** 4. **QuickCart Orders Service**  The **Auth Service** and **PII Service** are managed by the Platform Team (source: service-auth-service.md, service-pii-service.md).
- **graph** [~ partial, 8.5s] (4 tool calls, agent_miss) - The answer mentions some expected entities but is incomplete, missing the Recommendation Service and Monolithic Django App.
    > The services implemented in Python that are NOT managed by the Platform Team are:  1. Fraud Detection Service 2. Data Lineage Service  These results were obtained by identifying services implemented in Python and excluding those managed by the Platform Team. The relevant Cypher patterns used were for identifying services implemented in Python and for excluding those managed by the Platform Team.
- **pageindex** [~ partial, 14.8s] (8 tool calls, agent_miss) - The agent's answer mentions two expected entities but includes incorrect ones and misses others.
    > The services implemented in Python that are **NOT** managed by the Platform Team are:  1. **Recommendation Service** 2. **Fraud Detection Service** 3. **Payments Service** 4. **Mobile Backend-for-Frontend (BFF) Service**  The Platform Team manages the Auth Service, PII Service, and GraphQL Service, but the services listed above are operated by other teams (e.g., Engineering Team, Product Team) (so...
