# Eval report - `20260505T112824Z-1d2d73`

- Started: 2026-05-05T11:51:28.180164+00:00
- Questions: 30
- Agents: rag, graph, pageindex, router
- Source: `/Users/emilesilvis/Dropbox/30 - 39 Projects/llms-on-graphs/graph-rag-graph-agent/eval_runs/20260505T112824Z-1d2d73.json`

## Accuracy by category

Scores are mean judge grades (correct=1, partial=0.5, wrong=0); `n` is sample size in that cell.

| Category | rag | graph | pageindex | router |
| --- | --- | --- | --- | --- |
| aggregation_count | 0.12 (n=4) | 0.38 (n=4) | 0.62 (n=4) | 0.75 (n=4) |
| dependency_chain | 0.88 (n=4) | 1.00 (n=4) | 0.75 (n=4) | 0.75 (n=4) |
| multi_hop_2 | 0.10 (n=5) | 0.90 (n=5) | 0.20 (n=5) | 0.90 (n=5) |
| multi_hop_3 | 0.25 (n=4) | 0.75 (n=4) | 0.50 (n=4) | 0.75 (n=4) |
| negation | 0.38 (n=4) | 0.38 (n=4) | 0.50 (n=4) | 0.62 (n=4) |
| one_hop | 0.80 (n=5) | 0.80 (n=5) | 0.90 (n=5) | 0.70 (n=5) |
| shared_neighbor | 0.88 (n=4) | 0.75 (n=4) | 0.88 (n=4) | 0.75 (n=4) |
| **overall** | **0.48** (n=30) | **0.72** (n=30) | **0.62** (n=30) | **0.75** (n=30) |

## Latency

| Agent | mean (s) | p95 (s) | n |
| --- | --- | --- | --- |
| rag | 9.00 | 17.24 | 30 |
| graph | 7.96 | 18.69 | 30 |
| pageindex | 10.88 | 22.45 | 30 |
| router | 14.03 | 37.10 | 30 |

## Tool-call counts

Mean tool calls per question, per category. Higher = the agent needed more retrieval or refinement steps to answer.

| Category | rag | graph | pageindex | router |
| --- | --- | --- | --- | --- |
| aggregation_count | 5.2 (n=4) | 5.2 (n=4) | 6.2 (n=4) | 1.2 (n=4) |
| dependency_chain | 6.5 (n=4) | 4.2 (n=4) | 4.8 (n=4) | 1.0 (n=4) |
| multi_hop_2 | 7.8 (n=5) | 3.2 (n=5) | 6.8 (n=5) | 1.0 (n=5) |
| multi_hop_3 | 8.5 (n=4) | 4.5 (n=4) | 5.2 (n=4) | 1.8 (n=4) |
| negation | 10.8 (n=4) | 9.2 (n=4) | 7.5 (n=4) | 1.0 (n=4) |
| one_hop | 1.0 (n=5) | 1.6 (n=5) | 2.6 (n=5) | 1.0 (n=5) |
| shared_neighbor | 3.0 (n=4) | 4.2 (n=4) | 3.0 (n=4) | 1.0 (n=4) |

## Failure attribution

Per category and agent, how each row was attributed by the oracle Cypher. `extraction_miss` = the gold answer is not reachable from the extracted graph (graph paradigm only); `agent_miss` = reachable but the agent answered wrong / partial; `agent_ok` = reachable and the agent answered correctly; `no_oracle` = the question has no seed_cypher (answer lives only in the markdown).

### rag

| Category | agent_ok | agent_miss | extraction_miss | no_oracle |
| --- | --- | --- | --- | --- |
| aggregation_count | 0 | 4 | 0 | 0 |
| dependency_chain | 3 | 1 | 0 | 0 |
| multi_hop_2 | 0 | 5 | 0 | 0 |
| multi_hop_3 | 1 | 3 | 0 | 0 |
| negation | 0 | 4 | 0 | 0 |
| one_hop | 4 | 1 | 0 | 0 |
| shared_neighbor | 3 | 1 | 0 | 0 |
| **total** | **11** | **19** | **0** | **0** |

### graph

| Category | agent_ok | agent_miss | extraction_miss | no_oracle |
| --- | --- | --- | --- | --- |
| aggregation_count | 1 | 3 | 0 | 0 |
| dependency_chain | 4 | 0 | 0 | 0 |
| multi_hop_2 | 4 | 1 | 0 | 0 |
| multi_hop_3 | 3 | 1 | 0 | 0 |
| negation | 1 | 3 | 0 | 0 |
| one_hop | 4 | 0 | 1 | 0 |
| shared_neighbor | 3 | 1 | 0 | 0 |
| **total** | **20** | **9** | **1** | **0** |

### pageindex

| Category | agent_ok | agent_miss | extraction_miss | no_oracle |
| --- | --- | --- | --- | --- |
| aggregation_count | 2 | 2 | 0 | 0 |
| dependency_chain | 2 | 2 | 0 | 0 |
| multi_hop_2 | 1 | 4 | 0 | 0 |
| multi_hop_3 | 2 | 2 | 0 | 0 |
| negation | 0 | 4 | 0 | 0 |
| one_hop | 4 | 1 | 0 | 0 |
| shared_neighbor | 3 | 1 | 0 | 0 |
| **total** | **14** | **16** | **0** | **0** |

### router

| Category | agent_ok | agent_miss | extraction_miss | no_oracle |
| --- | --- | --- | --- | --- |
| aggregation_count | 3 | 1 | 0 | 0 |
| dependency_chain | 3 | 1 | 0 | 0 |
| multi_hop_2 | 4 | 1 | 0 | 0 |
| multi_hop_3 | 3 | 1 | 0 | 0 |
| negation | 2 | 2 | 0 | 0 |
| one_hop | 3 | 2 | 0 | 0 |
| shared_neighbor | 3 | 1 | 0 | 0 |
| **total** | **21** | **9** | **0** | **0** |

## `set_difference` adoption (graph agent, v6)

Number of `set_difference(candidate_cypher, exclude_cypher)` tool invocations that produced a populated diff (rather than an error). Quantifies how often v6's lever 1 (negation guard rail) actually fired - paradigm-symmetric to v5's alias-folded calls and v3's `find_rel_types_like` coverage.

Total `set_difference` calls across all questions: **10** (touched 7 of 30 graph rows).

| Question | Category | set_difference calls |
| --- | --- | --- |
| `gold-008` | negation | 1 |
| `gold-021` | dependency_chain | 3 |
| `gold-024` | shared_neighbor | 1 |
| `gold-025` | aggregation_count | 2 |
| `gold-028` | negation | 1 |
| `gold-029` | negation | 1 |
| `gold-030` | negation | 1 |

## `get_section_content` adoption (pageindex agent, v7)

Number of `get_section_content(node_id)` tool invocations per question. Quantifies how many tree nodes the PageIndex agent navigated to before answering - paradigm-symmetric to v6's `set_difference` adoption section and v5's alias-folded calls.

Total `get_section_content` calls across all questions: **124** (touched 30 of 30 pageindex rows).

| Question | Category | section calls |
| --- | --- | --- |
| `gold-001` | one_hop | 2 |
| `gold-002` | one_hop | 1 |
| `gold-003` | one_hop | 2 |
| `gold-004` | multi_hop_2 | 1 |
| `gold-005` | multi_hop_2 | 10 |
| `gold-006` | shared_neighbor | 2 |
| `gold-007` | aggregation_count | 3 |
| `gold-008` | negation | 4 |
| `gold-009` | multi_hop_3 | 2 |
| `gold-010` | dependency_chain | 4 |
| `gold-011` | one_hop | 2 |
| `gold-012` | one_hop | 1 |
| `gold-013` | multi_hop_2 | 7 |
| `gold-014` | multi_hop_2 | 9 |
| `gold-015` | multi_hop_2 | 2 |
| `gold-016` | multi_hop_3 | 3 |
| `gold-017` | multi_hop_3 | 10 |
| `gold-018` | multi_hop_3 | 2 |
| `gold-019` | dependency_chain | 4 |
| `gold-020` | dependency_chain | 4 |
| `gold-021` | dependency_chain | 3 |
| `gold-022` | shared_neighbor | 2 |
| `gold-023` | shared_neighbor | 2 |
| `gold-024` | shared_neighbor | 2 |
| `gold-025` | aggregation_count | 3 |
| `gold-026` | aggregation_count | 6 |
| `gold-027` | aggregation_count | 9 |
| `gold-028` | negation | 10 |
| `gold-029` | negation | 6 |
| `gold-030` | negation | 6 |

## Router paradigm selection (v8)

Which sub-agent paradigm the router (`ask_rag` / `ask_graph` / `ask_pageindex`) consulted per question. `primary` is the first paradigm called on that question; the per-paradigm columns count how many times each was invoked (the router may consult more than one). Paradigm-symmetric to v6's `set_difference` adoption section and v7's `get_section_content` adoption section.

Primary paradigm picks across 30 router rows: **rag=0, graph=26, pageindex=4**.

| Question | Category | Primary | rag | graph | pageindex |
| --- | --- | --- | --- | --- | --- |
| `gold-001` | one_hop | graph | 0 | 1 | 0 |
| `gold-002` | one_hop | graph | 0 | 1 | 0 |
| `gold-003` | one_hop | pageindex | 0 | 0 | 1 |
| `gold-004` | multi_hop_2 | graph | 0 | 1 | 0 |
| `gold-005` | multi_hop_2 | graph | 0 | 1 | 0 |
| `gold-006` | shared_neighbor | graph | 0 | 1 | 0 |
| `gold-007` | aggregation_count | pageindex | 0 | 0 | 1 |
| `gold-008` | negation | graph | 0 | 1 | 0 |
| `gold-009` | multi_hop_3 | graph | 0 | 1 | 0 |
| `gold-010` | dependency_chain | graph | 0 | 1 | 0 |
| `gold-011` | one_hop | pageindex | 0 | 0 | 1 |
| `gold-012` | one_hop | graph | 0 | 1 | 0 |
| `gold-013` | multi_hop_2 | graph | 0 | 1 | 0 |
| `gold-014` | multi_hop_2 | graph | 0 | 1 | 0 |
| `gold-015` | multi_hop_2 | graph | 0 | 1 | 0 |
| `gold-016` | multi_hop_3 | graph | 0 | 2 | 1 |
| `gold-017` | multi_hop_3 | graph | 0 | 1 | 0 |
| `gold-018` | multi_hop_3 | graph | 0 | 1 | 1 |
| `gold-019` | dependency_chain | graph | 0 | 1 | 0 |
| `gold-020` | dependency_chain | graph | 0 | 1 | 0 |
| `gold-021` | dependency_chain | graph | 0 | 1 | 0 |
| `gold-022` | shared_neighbor | graph | 0 | 1 | 0 |
| `gold-023` | shared_neighbor | graph | 0 | 1 | 0 |
| `gold-024` | shared_neighbor | graph | 0 | 1 | 0 |
| `gold-025` | aggregation_count | pageindex | 0 | 0 | 1 |
| `gold-026` | aggregation_count | graph | 0 | 1 | 0 |
| `gold-027` | aggregation_count | graph | 0 | 2 | 0 |
| `gold-028` | negation | graph | 0 | 1 | 0 |
| `gold-029` | negation | graph | 0 | 1 | 0 |
| `gold-030` | negation | graph | 0 | 1 | 0 |

## Alias-folded tool calls (graph agent, v5)

Number of `reach` / `neighbourhood` / `resolve_entity` calls where two or more node-name spellings (alias siblings, e.g. `Auth Service` + `Authentication Service`) were unioned in the result. Quantifies how often v5's lever 1 (tool-level alias resolution) actually fired.

Total alias-folded tool calls across all questions: **50** (touched 24 of 30 graph rows).

| Question | Category | alias-folded calls |
| --- | --- | --- |
| `gold-001` | one_hop | 1 |
| `gold-002` | one_hop | 2 |
| `gold-004` | multi_hop_2 | 3 |
| `gold-006` | shared_neighbor | 2 |
| `gold-007` | aggregation_count | 2 |
| `gold-008` | negation | 2 |
| `gold-009` | multi_hop_3 | 2 |
| `gold-010` | dependency_chain | 3 |
| `gold-011` | one_hop | 2 |
| `gold-012` | one_hop | 1 |
| `gold-013` | multi_hop_2 | 3 |
| `gold-014` | multi_hop_2 | 1 |
| `gold-016` | multi_hop_3 | 5 |
| `gold-017` | multi_hop_3 | 1 |
| `gold-018` | multi_hop_3 | 2 |
| `gold-019` | dependency_chain | 1 |
| `gold-020` | dependency_chain | 2 |
| `gold-022` | shared_neighbor | 4 |
| `gold-023` | shared_neighbor | 4 |
| `gold-025` | aggregation_count | 1 |
| `gold-026` | aggregation_count | 3 |
| `gold-027` | aggregation_count | 1 |
| `gold-028` | negation | 1 |
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

- **rag** [OK correct, 2.7s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The Auth Service is managed by the **Platform Team** (source: [service-auth-service.md](service-auth-service.md)).
- **graph** [OK correct, 2.6s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The team that manages the Auth Service is the **Platform Team**.
- **pageindex** [OK correct, 7.3s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The **Auth Service** is managed by the **Platform Team**. The Platform Team is responsible for building, operating, and maintaining essential backend services, including the Auth Service, which handles user authentication and ensures secure access across applications (node_ids: 0172, 0347).
- **router** [OK correct, 3.6s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Platform Team'.
    > The team that manages the Auth Service is the **Platform Team**.

### `gold-002` - *one_hop*

**Question:** What programming language is the Payments Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** (no oracle for this question)

- **rag** [X wrong, 2.0s] (1 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java** (source: team-product.md).
- **graph** [X wrong, 3.2s] (2 tool calls, extraction_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java**. This information was retrieved from the relationship `[:IMPLEMENTED_IN]` in the graph.
- **pageindex** [OK correct, 3.6s] (2 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Payments Service is implemented in **Python**. This choice is made for its simplicity and robust libraries, which are beneficial for handling payment transactions efficiently (source: node_id 0235).
- **router** [X wrong, 6.1s] (1 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java** (retrieved from the graph).

### `gold-003` - *one_hop*

**Question:** What does Istio facilitate in the ShopFlow platform?

**Expected:** Istio facilitates service-to-service communication.
**Key entities:** service-to-service communication

**Oracle Cypher rows:** 1

- **rag** [OK correct, 2.9s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities, including 'service-to-service communication'.
    > Istio facilitates efficient service-to-service communication within the ShopFlow platform by providing a uniform way to secure, connect, and observe microservices. This service mesh is integral to the platform's microservices architecture, allowing for smooth management of complex distributed systems. Key microservices, including the Shopflow App, operate on this robust Istio infrastructure (sourc...
- **graph** [OK correct, 3.6s] (2 tool calls, agent_ok) - The agent's answer includes the expected entity and accurately states the same facts as the expected answer.
    > Istio facilitates service-to-service communication in the ShopFlow platform. Additionally, it provides security, observability, and traffic management, and is part of the microservices architecture and API ecosystem. It also integrates with Kubernetes and supports canary releases.   This information was gathered from the relationships connected to the entity "Istio".
- **pageindex** [~ partial, 6.7s] (3 tool calls, agent_miss) - The agent's answer mentions service-to-service communication but includes additional details not required by the expected answer.
    > In the ShopFlow platform, Istio facilitates several key functionalities:  1. **Service Communication**: It provides a uniform way to secure, connect, and observe microservices, enhancing service-to-service communication.  2. **Traffic Management**: Istio enables sophisticated traffic steering, including load balancing, traffic shaping, and the implementation of retries and timeouts to ensure resil...
- **router** [~ partial, 11.7s] (1 tool calls, agent_miss) - The answer is on the right track but does not explicitly mention 'service-to-service communication'.
    > Istio facilitates several key functionalities in the ShopFlow platform, including:  1. **Traffic Management**: Intelligent load balancing, traffic shaping, and management of retries and timeouts. 2. **Security**: Automates secure communications using Mutual TLS (mTLS) and implements Role-Based Access Control (RBAC). 3. **Observability**: Enhances metrics, distributed tracing, and logging for bette...

### `gold-004` - *multi_hop_2*

**Question:** Which infrastructure does the service managed by the Platform Team for authentication use?

**Expected:** It uses AWS, Kubernetes EKS, and Kafka.
**Key entities:** AWS, Kubernetes EKS, Kafka

**Oracle Cypher rows:** 3

- **rag** [X wrong, 4.8s] (2 tool calls, agent_miss) - The agent's answer does not mention AWS, Kubernetes EKS, or Kafka, which are the expected entities.
    > The Auth Service managed by the Platform Team uses a scalable infrastructure built with Python. It integrates with Redis to cache session data and authentication tokens, which helps reduce database load by serving token validation requests directly from the cache (source: [service-auth-service.md]).
- **graph** [OK correct, 9.7s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: AWS, Kubernetes EKS, and Kafka.
    > The service managed by the Platform Team for authentication, known as the Auth Service, uses the following infrastructure:  1. **Kafka** 2. **Kubernetes EKS** 3. **AWS**  These infrastructures are utilized for various functionalities within the Auth Service (from the neighbourhood of the Auth Service).
- **pageindex** [OK correct, 9.4s] (2 tool calls, agent_ok) - The agent's answer includes all expected entities: AWS, Kubernetes EKS, and Kafka.
    > The service managed by the Platform Team for authentication, known as the **Auth Service**, uses the following infrastructure:  - **AWS**: For scalability and reliability. - **Kubernetes EKS**: For managing containerized applications. - **Kafka**: For message brokering.  Additionally, it utilizes **Redis** for caching session data and user credentials (source: node_id 0172).
- **router** [OK correct, 14.7s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: AWS, Kubernetes EKS, and Kafka.
    > The service managed by the Platform Team for authentication, known as the Auth Service, uses the following infrastructure: Kafka, Kubernetes EKS, and AWS. (Source: graph query)

### `gold-005` - *multi_hop_2*

**Question:** Who authored the ADR about the QuickCart acquisition, and what is their role?

**Expected:** Bob Martinez, who is a Staff SRE, authored it.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 15.7s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the author or their role, missing all key entities.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 10.0s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities accurately.
    > The ADR about the QuickCart acquisition was authored by Bob Martinez, who holds the role of Staff SRE.
- **pageindex** [X wrong, 20.6s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the author or their role.
    > Sorry, need more steps to process this request.
- **router** [OK correct, 9.1s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The ADR about the QuickCart acquisition was authored by Bob Martinez, who is a Staff SRE.

### `gold-006` - *shared_neighbor*

**Question:** Which programming language is used by both the Auth Service and the PII Service?

**Expected:** Python is used by both.
**Key entities:** Python

**Oracle Cypher rows:** 4

- **rag** [OK correct, 3.8s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service are developed using **Python**.   - Auth Service: Built with Python (source: service-auth-service.md). - PII Service: Developed in Python (source: service-pii-service.md).
- **graph** [OK correct, 4.1s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities, specifically Python.
    > Both the Auth Service and the PII Service use Python as their programming language.   This was determined from the outgoing relationships of each service: - The Auth Service is built with Python. - The PII Service is developed in Python.   Thus, Python is the common programming language used by both services.
- **pageindex** [OK correct, 6.1s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > Both the Auth Service and the PII Service use **Python** as their programming language.  - **Auth Service**: Built with Python (node_id: 0172). - **PII Service**: Developed in Python (node_id: 0248).
- **router** [OK correct, 5.5s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service use Python as their programming language. This was confirmed through their respective service details in the graph.

### `gold-007` - *aggregation_count*

**Question:** How many services does the Platform Team manage?

**Expected:** The Platform Team manages 3 services (Auth Service, GraphQL Service, PII Service).
**Key entities:** 3, Auth Service, GraphQL Service, PII Service

**Oracle Cypher rows:** 1
**Oracle enumeration (3):** Auth Service, GraphQL Service, PII Service

- **rag** [X wrong, 17.2s] (10 tool calls, agent_miss) - The agent's answer lists incorrect services and misses expected entities like GraphQL Service and PII Service.
    > The Platform Team manages 3 services: Auth Service, Data Lineage Service, and Payments Service.
- **graph** [OK correct, 5.2s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages 3 services: PII Service, GraphQL Service, and Auth Service.
- **pageindex** [OK correct, 14.5s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages **three services**:  1. **Auth Service** - Handles user authentication and ensures secure access across applications. 2. **PII Service** - Manages Personally Identifiable Information (PII) to ensure compliance with data protection laws. 3. **GraphQL Service** - Enables flexible data querying and efficient communication between client and server.  These services are design...
- **router** [OK correct, 14.1s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages **three services**:   1. **Auth Service** 2. **PII Service** 3. **GraphQL Service**  These services are essential for scalability, security, and efficiency within the organization (node_ids: 0347, 0352, 0351).

### `gold-008` - *negation*

**Question:** Among the services managed by the Platform Team, which ones do NOT depend on the Data Lineage Service?

**Expected:** The GraphQL Service and the PII Service do not depend on the Data Lineage Service.
**Key entities:** GraphQL Service, PII Service

**Oracle Cypher rows:** 2

- **rag** [~ partial, 19.1s] (13 tool calls, agent_miss) - The agent's answer mentions the PII Service but omits the GraphQL Service, which is also expected.
    > The service managed by the Platform Team that does NOT depend on the Data Lineage Service is the **PII Service**.   This conclusion is based on the dependencies of the other services:  - **Auth Service**, **Payments Service**, and **Shopflow App** all depend on the Data Lineage Service (from the search results).   Thus, the only service that does not have this dependency is the PII Service (from t...
- **graph** [OK correct, 6.8s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > Among the services managed by the Platform Team, the ones that do NOT depend on the Data Lineage Service are:  1. PII Service 2. GraphQL Service  This was determined by identifying the services managed by the Platform Team and excluding those that depend on the Data Lineage Service.
- **pageindex** [~ partial, 22.4s] (5 tool calls, agent_miss) - The agent correctly identifies the GraphQL Service but incorrectly states that the PII Service depends on the Data Lineage Service.
    > Among the services managed by the Platform Team, the following do NOT depend on the Data Lineage Service:  1. **Mobile Backend-for-Frontend (BFF) Service** 2. **Payments Service** 3. **GraphQL Service**  The **Auth Service** and **PII Service** are the only services that explicitly depend on the Data Lineage Service (from the content of the Data Lineage Service section).   This information was der...
- **router** [OK correct, 37.1s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The services managed by the Platform Team that do NOT depend on the Data Lineage Service are:  1. PII Service 2. GraphQL Service  (This information was retrieved using the graph agent.)

### `gold-009` - *multi_hop_3*

**Question:** What database does the service authored (developed) by Bob Martinez use for caching?

**Expected:** The Auth Service, developed by Bob Martinez, uses Redis for caching.
**Key entities:** Auth Service, Redis

**Oracle Cypher rows:** 1

- **rag** [X wrong, 21.8s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information about the expected entities or the database used for caching.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 7.3s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Redis.
    > The service authored by Bob Martinez, known as the Auth Service, uses **Redis** for caching. This was determined by examining the relationships of the Auth Service, which indicates it utilizes Redis as its database.
- **pageindex** [OK correct, 23.3s] (3 tool calls, agent_ok) - The agent's answer correctly identifies Redis and the Auth Service, matching the expected entities and facts.
    > The service developed by Bob Martinez uses **Redis** for caching. Redis is employed to cache session data and user credentials, which helps reduce load on the primary database and improve response times for frequent requests (from sections on the Auth Service and Payments Service).   Specifically, Redis is used in: - **Auth Service**: Caches session data and user credentials for faster authenticat...
- **router** [OK correct, 8.2s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Redis.
    > The service authored by Bob Martinez, known as the Auth Service, uses **Redis** for caching. This information was retrieved from the graph database.

### `gold-010` - *dependency_chain*

**Question:** Which services depend on the Data Lineage Service, directly or transitively?

**Expected:** The Auth Service and the Payments Service depend on the Data Lineage Service.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 3

- **rag** [OK correct, 14.6s] (11 tool calls, agent_ok) - The agent's answer includes both the Auth Service and Payments Service, matching the expected entities.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service**    - Transitive dependencies:       - **Shopflow App**      - **Fraud Detection Service** 3. **Shopflow App**    - Transitive dependencies:      - **Recommendation Service**      - **Mobile BFF Service**  In summary, the complete list of services is: Auth Service...
- **graph** [OK correct, 7.8s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service**  Both services have a direct dependency on the Data Lineage Service (hops=1).   This information was gathered using the `reach` tool to find dependencies and then confirmed through the `neighbourhood` tool for each service.
- **pageindex** [~ partial, 10.2s] (5 tool calls, agent_miss) - The answer includes expected entities but adds an unsupported entity, Shopflow App, which is not in the expected answer.
    > The services that depend on the **Data Lineage Service**, either directly or transitively, are:  1. **Auth Service** - It relies on the Data Lineage Service for tracking and handling user authentication data flow. 2. **Payments Service** - This service utilizes the Data Lineage Service to track payment information flow, ensuring end-to-end traceability. 3. **Shopflow App** - It has a direct depend...
- **router** [OK correct, 11.4s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service**  This information was retrieved using the graph agent, which identified the dependencies through the `DEPENDS_ON` relationship.

### `gold-011` - *one_hop*

**Question:** What programming language is the Data Lineage Service implemented in?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 2.2s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in **Python** (source: service-data-lineage-service.md).
- **graph** [OK correct, 3.4s] (2 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in Python. This information was retrieved from the relationship `IS_IMPLEMENTED_IN` in the graph.
- **pageindex** [OK correct, 10.3s] (3 tool calls, agent_ok) - The agent's answer states the implementation language as Python and includes additional relevant details.
    > The Data Lineage Service is implemented in **Python**. This service is a core component of the microservices architecture, designed to track data flow and maintain data integrity across various services (node_id: 0200).
- **router** [OK correct, 8.4s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in **Python**.

### `gold-012` - *one_hop*

**Question:** Which cache does the Auth Service use for storing session data?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 2.6s] (1 tool calls, agent_ok) - The agent's answer correctly states that the Auth Service uses Redis for caching session data.
    > The Auth Service uses Redis to cache session data and authentication tokens. This helps reduce the load on the primary database by serving token validation requests directly from the cache (source: technology-redis-cache.md).
- **graph** [OK correct, 2.1s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Redis'.
    > The Auth Service uses Redis for storing session data.
- **pageindex** [OK correct, 5.2s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > The Auth Service uses **Redis** for storing session data. It caches both session information and user credentials to reduce the load on the primary database and facilitate faster authentication checks (source: service-auth-service).
- **router** [OK correct, 3.4s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Redis'.
    > The Auth Service uses Redis for storing session data.

### `gold-013` - *multi_hop_2*

**Question:** Who leads the team that operates the QuickCart Orders Service?

**Expected:** Bob Martinez leads the Orders Team, which operates the QuickCart Orders Service.
**Key entities:** Bob Martinez, Orders Team

**Oracle Cypher rows:** 1

- **rag** [X wrong, 14.6s] (11 tool calls, hit step cap, agent_miss) - The answer does not mention any expected entities and states it cannot provide the information.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 4.1s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The team that operates the QuickCart Orders Service is led by Bob Martinez.
- **pageindex** [X wrong, 24.7s] (8 tool calls, agent_miss) - The agent's answer incorrectly names Dan Okafor instead of Bob Martinez as the team leader.
    > The team that operates the QuickCart Orders Service is the **Orders Team**, which consists of **25 members**. The team is led by **Dan Okafor**, who is a Backend Engineer and was involved in the creation of the service. The Orders Team is responsible for managing order processing, ensuring service reliability, and optimizing the system for performance and scalability (node_ids: 0340, 0258).
- **router** [OK correct, 7.3s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The team that operates the QuickCart Orders Service is led by Bob Martinez.

### `gold-014` - *multi_hop_2*

**Question:** What programming language is the service developed by Bob Martinez built with?

**Expected:** Python - the Auth Service, which Bob Martinez developed, is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 10.8s] (9 tool calls, agent_miss) - The agent's answer does not mention the Auth Service or specify Python for it, missing key expected entities.
    > The services developed by Bob Martinez and their respective programming languages are as follows:  1. **Mobile Backend-for-Frontend (BFF) Service** - JavaScript 2. **Recommendation Service** - Python 3. **Fraud Detection Service** - Python 4. **QuickCart Orders Service** - (Programming language not specified in the retrieved data) 5. **GraphQL Service** - JavaScript  Thus, the services developed b...
- **graph** [OK correct, 4.0s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: 'Auth Service' and 'Python'.
    > The service developed by Bob Martinez, known as the Auth Service, is built with Python.
- **pageindex** [X wrong, 17.7s] (10 tool calls, agent_miss) - The agent's answer mentions JavaScript and GraphQL, missing the expected entities 'Auth Service' and 'Python'.
    > The service developed by Bob Martinez is built with **JavaScript**. This is specifically for the **GraphQL Federation Layer** that he is involved with (as noted in the section about the GraphQL service implementation).   If you need information about other services or their programming languages, please let me know!
- **router** [OK correct, 11.6s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: 'Auth Service' and 'Python'.
    > The service developed by Bob Martinez, known as the Auth Service, is built with Python.

### `gold-015` - *multi_hop_2*

**Question:** Who authored the ADR about GDPR compliance, and what team do they lead?

**Expected:** Alice Chen authored the ADR and leads the SRE Team.
**Key entities:** Alice Chen, SRE Team

**Oracle Cypher rows:** 1

- **rag** [~ partial, 9.8s] (6 tool calls, agent_miss) - The answer correctly identifies Alice Chen but fails to mention the SRE Team, instead mentioning an unconfirmed Engineering Team.
    > The ADR about GDPR compliance was authored by **Alice Chen**, who is a **Senior Architect**. However, the specific team that she leads is not explicitly mentioned in the retrieved documents. The Engineering Team is referenced, but it is not confirmed that Alice Chen leads this team (source: [adr-gdpr-compliance-2020.md](adr-gdpr-compliance-2020.md)).
- **graph** [~ partial, 4.9s] (3 tool calls, agent_miss) - The agent correctly identifies Alice Chen as the author but incorrectly states the team she leads.
    > Alice Chen authored the ADR about GDPR compliance and leads the Customer Experience Team.
- **pageindex** [X wrong, 6.6s] (3 tool calls, agent_miss) - The agent's answer contradicts the expected answer regarding the team Alice Chen leads.
    > The ADR about GDPR compliance was authored by **Alice Chen**, who is a **Senior Architect**. She leads the **Platform Team** responsible for the implementation of the PII Service and Data Lineage Tracking Service to ensure GDPR compliance (sections from `adr-gdpr-compliance-2020` and `team-engineering`).
- **router** [~ partial, 6.2s] (1 tool calls, agent_miss) - The agent correctly identifies Alice Chen but incorrectly states the team as Customer Experience instead of SRE.
    > Alice Chen authored the ADR about GDPR compliance and leads the Customer Experience Team.

### `gold-016` - *multi_hop_3*

**Question:** Which programming language is used by the service that is managed by the Platform Team and depends on the Data Lineage Service?

**Expected:** Python - the Auth Service is managed by the Platform Team, depends on the Data Lineage Service, and is built with Python.
**Key entities:** Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 8.3s] (5 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Python.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Auth Service**, which is implemented in **Python**.
- **graph** [X wrong, 10.8s] (6 tool calls, agent_miss) - The agent's answer mentions incorrect entities and programming language, contradicting the expected answer.
    > The service that is managed by the Platform Team and depends on the Data Lineage Service is the **Payments Service**, which is implemented in **Java**.   This was determined by first identifying the Payments Service as the middle entity that depends on the Data Lineage Service, and then checking its programming language through its relationships.   Key Cypher patterns used: 1. `MATCH (Platform Tea...
- **pageindex** [OK correct, 12.0s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Python.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Auth Service**. This service is implemented in **Python**.   The Auth Service is responsible for handling user authentication and relies on the Data Lineage Service for tracking data flow related to user authentication data.   Thus, the programming language used is **Python**.   This information is derived f...
- **router** [OK correct, 59.9s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Python.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Auth Service**, which uses **Python** as its programming language. This information was gathered from the graph and pageindex tools.

### `gold-017` - *multi_hop_3*

**Question:** What programming language is used by the service developed by the person who authored 'ADR: QuickCart Acquisition and Integration'?

**Expected:** Python - Bob Martinez authored the ADR and developed the Auth Service, which is built with Python.
**Key entities:** Bob Martinez, Auth Service, Python

**Oracle Cypher rows:** 1

- **rag** [X wrong, 15.1s] (11 tool calls, hit step cap, agent_miss) - The answer is a refusal and does not mention any expected entities or facts.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 6.6s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The service developed by Bob Martinez, who authored 'ADR: QuickCart Acquisition and Integration', is the **Auth Service**, which is built using **Python**.   This information was gathered through the relationships connecting Bob Martinez to the Auth Service and the programming language used for its development.
- **pageindex** [X wrong, 19.1s] (11 tool calls, hit step cap, agent_miss) - The answer does not provide any information or mention any expected entities.
    > Sorry, need more steps to process this request.
- **router** [OK correct, 16.6s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The service developed by Bob Martinez, who authored 'ADR: QuickCart Acquisition and Integration', is the Auth Service, which is built using Python.

### `gold-018` - *multi_hop_3*

**Question:** What role does the person who developed the authentication service managed by the Platform Team have?

**Expected:** Staff SRE - Bob Martinez, who developed the Auth Service (managed by the Platform Team), is a Staff SRE.
**Key entities:** Bob Martinez, Staff SRE

**Oracle Cypher rows:** 1

- **rag** [X wrong, 10.4s] (7 tool calls, agent_miss) - The agent's answer contradicts the expected answer by naming different entities and roles.
    > The person who developed the authentication service managed by the Platform Team is **Chloe Park**, and her role is **Engineering Manager** (source: [adr-engineering-reorganization-2017.md](adr-engineering-reorganization-2017.md), [team-engineering.md](team-engineering.md)).
- **graph** [OK correct, 4.9s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Bob Martinez and Staff SRE.
    > The person who developed the Authentication Service is Bob Martinez, and his role is Staff SRE (Site Reliability Engineer).
- **pageindex** [X wrong, 8.3s] (3 tool calls, agent_miss) - The answer does not mention Bob Martinez or the role of Staff SRE, missing key entities.
    > The person who developed the authentication service managed by the Platform Team has the role of a member of the **Platform Team**. This team is responsible for building, operating, and maintaining essential backend services, including the Auth Service, which handles user authentication and ensures secure access across applications (source: node_id 0172 and 0347).
- **router** [X wrong, 61.9s] (2 tool calls, agent_miss) - The agent's answer does not mention Bob Martinez or the role of Staff SRE, missing key entities.
    > The person who developed the authentication service managed by the Platform Team has the role of a developer or engineer within that team (source: service-auth-service, team-platform).

### `gold-019` - *dependency_chain*

**Question:** Which services rely on the Payments Service, directly or transitively?

**Expected:** The Fraud Detection Service relies on the Payments Service.
**Key entities:** Fraud Detection Service

**Oracle Cypher rows:** 1

- **rag** [OK correct, 15.8s] (10 tool calls, agent_ok) - The agent's answer includes the expected entity 'Fraud Detection Service' and aligns with the expected answer.
    > The services that rely on the Payments Service, either directly or transitively, are:  1. **ShopFlow App** 2. **Data Lineage Service**    - Depends on: **Auth Service** 3. **Fraud Detection Service**    - Depends on: **Recommendation Service**  Thus, the complete list of services is: - ShopFlow App - Data Lineage Service - Auth Service (transitive dependency) - Fraud Detection Service - Recommenda...
- **graph** [OK correct, 3.1s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Fraud Detection Service'.
    > The service that relies on the Payments Service, directly or transitively, is the **Fraud Detection Service**.
- **pageindex** [OK correct, 8.2s] (5 tool calls, agent_ok) - The agent's answer includes the expected entity 'Fraud Detection Service' and aligns with the expected answer.
    > The services that rely on the Payments Service, either directly or transitively, are:  1. **Fraud Detection Service** - Directly relies on the Payments Service to monitor transaction data continuously. 2. **Data Lineage Service** - Utilizes the Payments Service to track payment information flow, ensuring end-to-end traceability. 3. **ShopFlow App** - Integrates with the Payments Service for seamle...
- **router** [OK correct, 15.1s] (1 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity.
    > The service that relies on the Payments Service, either directly or transitively, is the **Fraud Detection Service**. This was identified through a direct dependency relationship.

### `gold-020` - *dependency_chain*

**Question:** Which service, directly or transitively, depends on the ShopFlow application?

**Expected:** The Recommendation Service depends on the ShopFlow application.
**Key entities:** Recommendation Service

**Oracle Cypher rows:** 1

- **rag** [~ partial, 6.3s] (3 tool calls, agent_miss) - The answer includes the expected entity but adds unrelated services, making it partially correct.
    > The services that directly or transitively depend on the ShopFlow application are:  1. **Payments Service**: Integrates with ShopFlow for transaction workflows and is a dependency for the Fraud Detection Service. 2. **Fraud Detection Service**: Relies on the Payments Service, which in turn depends on ShopFlow. 3. **Recommendation Service**: Directly depends on ShopFlow to access user interaction d...
- **graph** [OK correct, 5.1s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Recommendation Service'.
    > The service that directly depends on the ShopFlow application is the **Recommendation Service**. This was determined through a direct relationship identified in the graph.
- **pageindex** [~ partial, 8.6s] (5 tool calls, agent_miss) - The answer mentions the Recommendation Service but includes additional, unnecessary services.
    > The services that directly or transitively depend on the ShopFlow application are:  1. **Payments Service** - Integrates with the ShopFlow App to facilitate seamless transaction workflows. 2. **QuickCart Orders Service** - Integrates with the ShopFlow application for order processing. 3. **Recommendation Service** - Utilizes the ShopFlow App for generating user-specific recommendations. 4. **Data ...
- **router** [OK correct, 6.8s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Recommendation Service'.
    > The service that directly or transitively depends on the ShopFlow application is the **Recommendation Service**. This information was retrieved using the graph agent.

### `gold-021` - *dependency_chain*

**Question:** Which services use Redis for caching or session storage? Consider all relationship types that express use/employ/cache.

**Expected:** The Auth Service and the Payments Service both use Redis for caching.
**Key entities:** Auth Service, Payments Service

**Oracle Cypher rows:** 2

- **rag** [OK correct, 4.6s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that use Redis for caching or session storage are:  1. **Auth Service**    - Uses Redis for caching session data and user credentials.     2. **Payments Service**    - Employs Redis for caching transaction histories and managing session data.  Both services utilize Redis to enhance performance and reduce load on their primary databases (from multiple sources including "technology-redi...
- **graph** [OK correct, 18.7s] (9 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that use Redis for caching or session storage are:  1. **Payments Service** 2. **Auth Service**  These services utilize Redis as indicated by the relationships `IS_USED_BY` and `USES_DATABASE`.
- **pageindex** [OK correct, 5.6s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that use Redis for caching or session storage are:  1. **Auth Service**    - Uses Redis to cache session data and authentication tokens, reducing the load on the primary database.  2. **Payments Service**    - Caches transaction histories and recent payment details to enhance transaction lookup speed and improve user experience.  These services leverage Redis to streamline data retrie...
- **router** [X wrong, 24.1s] (1 tool calls, agent_miss) - The agent's answer contradicts the expected answer and misses both key entities: Auth Service and Payments Service.
    > No services were found that use Redis for caching or session storage based on the relationships in the graph.

### `gold-022` - *shared_neighbor*

**Question:** Which cache database is used by both the Auth Service and the Payments Service?

**Expected:** Redis.
**Key entities:** Redis

**Oracle Cypher rows:** 1

- **rag** [OK correct, 3.4s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the Auth Service and the Payments Service use **Redis** as their cache database. Redis is utilized to cache session data and authentication tokens for the Auth Service, and to cache transaction histories and recent payment details for the Payments Service (source: technology-redis-cache.md).
- **graph** [OK correct, 5.3s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the **Auth Service** and the **Payments Service** use **Redis** as their cache database.   - The **Auth Service** has an outgoing relationship indicating it **uses** Redis. - The **Payments Service** also has an outgoing relationship indicating it **employs** Redis.  This information was gathered from the neighbourhoods of both services, where Redis was identified as a common cache database.
- **pageindex** [OK correct, 5.8s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the Auth Service and the Payments Service use **Redis** as their caching database.   - The **Auth Service** utilizes Redis for caching session data and user credentials to enhance performance and reduce load on the primary database. - The **Payments Service** employs Redis to cache transaction validations and manage session data efficiently, improving response rates for frequent requests.  Th...
- **router** [OK correct, 8.7s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Redis'.
    > The cache database used by both the Auth Service and the Payments Service is **Redis**. This was determined through a graph query that identified Redis as a common resource for both services.

### `gold-023` - *shared_neighbor*

**Question:** Which programming language is used by both the Fraud Detection Service and the Recommendation Service?

**Expected:** Python.
**Key entities:** Python

**Oracle Cypher rows:** 1

- **rag** [OK correct, 4.0s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service are implemented in **Python**.   - The Fraud Detection Service is designed to identify and prevent fraudulent activities and is implemented in Python (source: service-fraud-detection-service.md). - The Recommendation Service offers tailored recommendations and is also built using Python (source: service-recommendation-service.md).
- **graph** [OK correct, 6.0s] (4 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service use **Python** as their programming language.   - The Fraud Detection Service is implemented in Python. - The Recommendation Service is built using Python.  This information was gathered from the neighbourhoods of both services, specifically looking for the programming language relationships.
- **pageindex** [OK correct, 5.9s] (3 tool calls, agent_ok) - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the **Fraud Detection Service** and the **Recommendation Service** are implemented using **Python** as their programming language.  - **Fraud Detection Service**: Programming Language: Python (Node ID: 0225) - **Recommendation Service**: Programming Language: Python (Node ID: 0270)  Thus, the programming language used by both services is Python.
- **router** [OK correct, 7.2s] (1 tool calls, agent_ok) - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service use **Python** as their programming language. This was determined through a graph query examining their relationships.

### `gold-024` - *shared_neighbor*

**Question:** Which services integrate with both the GraphQL Federation Layer and the Monolithic Django App?

**Expected:** The BFF Service and the Recommendation Service integrate with both.
**Key entities:** BFF Service, Recommendation Service

**Oracle Cypher rows:** 2

- **rag** [~ partial, 6.5s] (6 tool calls, agent_miss) - The answer includes the expected entities but adds incorrect ones, making it partially correct.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **BFF Service** 2. **Recommendation Service** 3. **Fraud Detection Service** 4. **Quickcart Orders Service**  These services are part of the architecture that connects the GraphQL Federation Layer and the Monolithic Django App (sources: service-graphql-service.md, service-shopflow-app.md).
- **graph** [X wrong, 11.0s] (7 tool calls, agent_miss) - The agent's answer mentions incorrect services and misses the expected entities: BFF Service and Recommendation Service.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **Fraud Detection Service** 2. **Quickcart Orders**  These were identified by comparing the integration relationships of both services.
- **pageindex** [~ partial, 5.2s] (3 tool calls, agent_miss) - The agent's answer includes the expected entities but adds an incorrect entity, the Fraud Detection Service.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App (Shopflow App) are:  1. **Backend for Frontend (BFF) Service** 2. **Recommendation Service** 3. **Fraud Detection Service**  These services interact with the GraphQL Federation Layer and also have dependencies on the Monolithic Django App (Shopflow App) (from node_ids 0058 and 0279).
- **router** [X wrong, 11.1s] (1 tool calls, agent_miss) - The agent's answer mentions different services and misses the expected entities: BFF Service and Recommendation Service.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. Fraud Detection Service 2. Quickcart Orders  This information was retrieved using the graph agent by analyzing the integration relationships.

### `gold-025` - *aggregation_count*

**Question:** How many teams does the ShopFlow platform have?

**Expected:** ShopFlow has 9 teams - Catalog, Customer Experience, Data, Engineering, Logistics, Orders, Platform, Product, and the Site Reliability Engineering (SRE) Team.
**Key entities:** 9, Catalog Team, Customer Experience Team, Data Team, Engineering Team, Logistics Team, Orders Team, Platform Team, Product Team, Site Reliability Engineering (SRE) Team

**Oracle Cypher rows:** 1
**Oracle enumeration (9):** Catalog Team, Customer Experience Team, Data Team, Engineering Team, Logistics Team, Orders Team, Platform Team, Product Team, Site Reliability Engineering (SRE) Team

- **rag** [X wrong, 5.4s] (4 tool calls, agent_miss) - The answer does not mention the number of teams or any expected entities, contradicting the expected answer.
    > The ShopFlow platform has approximately 1,500 dedicated professionals organized into several specialized teams (source: company-shopflow.md). However, the exact number of distinct teams is not specified.
- **graph** [X wrong, 8.9s] (6 tool calls, agent_miss) - The agent's answer lists only 2 teams, missing 7 expected teams and the total count of 9.
    > The ShopFlow platform has 2 teams: **Platform Team** and **Site Reliability Engineering (SRE) Team**.   This was determined by querying the teams associated with the ShopFlow platform and excluding those that are not directly linked.
- **pageindex** [OK correct, 6.6s] (4 tool calls, agent_ok) - The agent's answer lists all 9 expected teams and matches the expected answer.
    > The ShopFlow platform has **nine teams**. They are:  1. Engineering Team 2. Platform Team 3. Product Team 4. Data Team 5. Catalog Team 6. Orders Team 7. Logistics Team 8. Customer Experience Team 9. Site Reliability Engineering (SRE) Team  This information was gathered from the sections on the ShopFlow team overview (node_id: 0112) and the engineering team overview (node_id: 0320).
- **router** [OK correct, 7.5s] (1 tool calls, agent_ok) - The agent's answer lists all 9 expected teams and matches the expected answer.
    > The ShopFlow platform has **nine teams**:  1. Engineering Team 2. Platform Team 3. Product Team 4. Data Team 5. Catalog Team 6. Orders Team 7. Logistics Team 8. Customer Experience Team 9. Site Reliability Engineering (SRE) Team  This information was retrieved from the page index.

### `gold-026` - *aggregation_count*

**Question:** How many distinct services or components have their code implemented in Python?

**Expected:** 6 - the Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, and the Monolithic Django App.
**Key entities:** 6, Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 1
**Oracle enumeration (6):** Auth Service, Data Lineage Service, Fraud Detection Service, Monolithic Django App, PII Service, Recommendation Service

- **rag** [~ partial, 6.5s] (3 tool calls, agent_miss) - The agent's answer mentions 5 services but omits the Data Lineage Service and states an incorrect total number.
    > There are 5 distinct services implemented in Python: Auth Service, PII Service, Fraud Detection Service, Recommendation Service, and Monolithic Django App.
- **graph** [X wrong, 19.7s] (11 tool calls, agent_miss) - The agent's answer includes incorrect entities like PostgreSQL and Snowflake, missing Auth Service and Recommendation Service.
    > There are 6 distinct services or components that have their code implemented in Python:  1. Data Lineage Service 2. Fraud Detection Service 3. Monolithic Django App 4. PII Service 5. PostgreSQL 6. Snowflake  This information was gathered using the `reach` tool to find entities that are implemented in Python.
- **pageindex** [~ partial, 6.3s] (7 tool calls, agent_miss) - The agent's answer includes 5 expected entities but incorrectly adds 'Payments Service' instead of 'Data Lineage Service'.
    > There are **six distinct services** that have their code implemented in Python:  1. **Auth Service** 2. **Fraud Detection Service** 3. **Payments Service** 4. **PII Service** 5. **Recommendation Service** 6. **Shopflow App** (Monolithic Django App)  These services leverage Python for various functionalities, including authentication, fraud detection, payment processing, data privacy compliance, an...
- **router** [X wrong, 5.8s] (1 tool calls, agent_miss) - The agent's answer lists only 2 services, missing 4 expected entities and the total count of 6.
    > There are 2 distinct services implemented in Python: **Fraud Detection Service** and **Data Lineage Service** (from the graph agent).

### `gold-027` - *aggregation_count*

**Question:** How many entities does the Fraud Detection Service directly integrate with (via INTEGRATES_WITH edges)?

**Expected:** 3 - Elasticsearch, Kibana, and QuickCart.
**Key entities:** 3, Elasticsearch, Kibana, QuickCart

**Oracle Cypher rows:** 1
**Oracle enumeration (3):** Elasticsearch, Kibana, QuickCart

- **rag** [X wrong, 5.0s] (4 tool calls, agent_miss) - The answer lists incorrect entities and misses Elasticsearch and Kibana, contradicting the expected answer.
    > The Fraud Detection Service directly integrates with 2 entities: Payments Service and QuickCart.
- **graph** [~ partial, 3.2s] (2 tool calls, agent_miss) - The answer mentions the number of entities but omits their names: Elasticsearch, Kibana, and QuickCart.
    > The Fraud Detection Service directly integrates with 3 entities via INTEGRATES_WITH edges.
- **pageindex** [X wrong, 16.2s] (10 tool calls, agent_miss) - The agent's answer lists incorrect entities and an incorrect count, missing Elasticsearch and Kibana.
    > The **Fraud Detection Service** directly integrates with **two entities**:  1. **QuickCart** - for fraud prevention in e-commerce transactions. 2. **GraphQL Service** - for providing API endpoints necessary for fraud analytics.  Thus, the count of entities is **2** (QuickCart, GraphQL Service). This information was derived from the sections on the Fraud Detection Service (node_id: 0220) and its in...
- **router** [OK correct, 10.5s] (2 tool calls, agent_ok) - The agent's answer states the same facts and mentions all expected entities.
    > The Fraud Detection Service directly integrates with 3 entities: Kibana, Elasticsearch, and QuickCart. (Source: graph query)

### `gold-028` - *negation*

**Question:** Among the services managed by the Platform Team, which ones are NOT implemented in Python?

**Expected:** The GraphQL Service is not documented as being implemented in Python (the Auth Service and PII Service both are).
**Key entities:** GraphQL Service

**Oracle Cypher rows:** 1

- **rag** [X wrong, 12.8s] (11 tool calls, agent_miss) - The agent's answer contradicts the expected answer by stating all services are implemented in Python, missing the GraphQL Service entity.
    > The services managed by the Platform Team that are NOT implemented in Python are: **None**. All identified services (Auth Service, PII Service, Fraud Detection Service, and Shopflow App) are implemented in Python.
- **graph** [X wrong, 44.7s] (26 tool calls, hit step cap, agent_miss) - The agent's answer is a refusal and does not mention any expected entities.
    > Sorry, need more steps to process this request.
- **pageindex** [~ partial, 10.3s] (11 tool calls, agent_miss) - The answer correctly identifies the GraphQL Service but includes additional services not mentioned in the expected answer.
    > The services managed by the Platform Team that are **NOT** implemented in Python are:  1. **GraphQL Service** - Implemented in JavaScript. 2. **Mobile Backend-for-Frontend (BFF) Service** - Implemented in JavaScript. 3. **QuickCart Orders Service** - Uses Amazon SQS for messaging but does not specify a programming language in the retrieved content.  The following services are implemented in Python...
- **router** [OK correct, 6.4s] (1 tool calls, agent_ok) - The agent's answer correctly identifies the GraphQL Service as not implemented in Python, matching the expected answer and entity.
    > The service managed by the Platform Team that is NOT implemented in Python is the **GraphQL Service**. This information was retrieved from the graph database.

### `gold-029` - *negation*

**Question:** Among the services that depend on the Data Lineage Service, which are NOT managed by the Platform Team?

**Expected:** The Payments Service and the Monolithic Django App depend on the Data Lineage Service but are not managed by the Platform Team.
**Key entities:** Payments Service, Monolithic Django App

**Oracle Cypher rows:** 2

- **rag** [~ partial, 10.5s] (9 tool calls, agent_miss) - The agent mentions the Payments Service but incorrectly includes the Shopflow App instead of the Monolithic Django App.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. Payments Service 2. Shopflow App
- **graph** [X wrong, 6.3s] (4 tool calls, agent_miss) - The agent's answer lists incorrect services and misses the expected entities entirely.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. PII Service 2. GraphQL Service  The Auth Service is managed by the Platform Team.
- **pageindex** [~ partial, 9.8s] (7 tool calls, agent_miss) - The agent correctly identifies the Payments Service but incorrectly includes other services not in the expected answer.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. **Payments Service** 2. **Auth Service** 3. **ShopFlow App**  These services are managed by different teams, specifically the Engineering Team and the Data Team, rather than the Platform Team, which manages the Auth Service, PII Service, and GraphQL Service (from the content of node_ids 0199, 005...
- **router** [X wrong, 13.3s] (1 tool calls, agent_miss) - The agent's answer includes an incorrect entity, 'Auth Service', not in the expected answer.
    > The services that depend on the Data Lineage Service and are NOT managed by the Platform Team are:  1. Payments Service 2. Monolithic Django App 3. Auth Service  (This information was retrieved using the graph agent.)

### `gold-030` - *negation*

**Question:** Among the services implemented in Python, which ones are NOT managed by the Platform Team?

**Expected:** The Data Lineage Service, the Fraud Detection Service, the Recommendation Service, and the Monolithic Django App are implemented in Python but not managed by the Platform Team.
**Key entities:** Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

**Oracle Cypher rows:** 4

- **rag** [~ partial, 10.8s] (10 tool calls, agent_miss) - The agent's answer mentions the Recommendation Service but misses other expected entities and incorrectly states the Fraud Detection Service is managed by the Platform Team.
    > The services implemented in Python that are **NOT** managed by the Platform Team are:  1. **Recommendation Service** 2. **Shopflow App**  The following services are managed by the Platform Team: - **Auth Service** - **PII Service** - **Fraud Detection Service**   (References: service-auth-service.md, service-pii-service.md, service-fraud-detection-service.md, service-recommendation-service.md, ser...
- **graph** [~ partial, 5.7s] (4 tool calls, agent_miss) - The agent's answer mentions some expected entities but is incomplete.
    > The services implemented in Python that are NOT managed by the Platform Team are:  1. Fraud Detection Service 2. Data Lineage Service  These results were derived from checking the services implemented in Python and excluding those managed by the Platform Team.
- **pageindex** [~ partial, 9.7s] (7 tool calls, agent_miss) - The agent correctly mentions the Recommendation Service but misses other expected entities and includes incorrect ones.
    > The services implemented in Python that are **NOT** managed by the Platform Team are:  1. **Mobile Backend-for-Frontend (BFF) Service** 2. **Payments Service** 3. **Recommendation Service**  These services are managed by different teams, such as the Product Team and the Engineering Team, rather than the Platform Team (from sections on services and team responsibilities).   The Platform Team manage...
- **router** [~ partial, 7.7s] (1 tool calls, agent_miss) - The answer mentions some expected entities but is incomplete, missing the Recommendation Service and Monolithic Django App.
    > The services implemented in Python that are NOT managed by the Platform Team are:  1. Fraud Detection Service 2. Data Lineage Service  (This information was retrieved using the graph agent.)
