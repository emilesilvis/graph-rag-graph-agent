# Eval report - `20260418T134710Z-9dc0ac`

- Started: 2026-04-18T13:50:08.528553+00:00
- Questions: 10
- Agents: rag, graph
- Source: `/Users/emilesilvis/Dropbox/30 - 39 Projects/llms-on-graphs/graph-rag-graph-agent/eval_runs/20260418T134710Z-9dc0ac.json`

## Accuracy by category

Scores are mean judge grades (correct=1, partial=0.5, wrong=0); `n` is sample size in that cell.

| Category | rag | graph |
| --- | --- | --- |
| aggregation_count | 0.00 (n=1) | 1.00 (n=1) |
| dependency_chain | 0.50 (n=1) | 0.50 (n=1) |
| multi_hop_2 | 0.00 (n=2) | 1.00 (n=2) |
| multi_hop_3 | 0.00 (n=1) | 0.00 (n=1) |
| negation | 0.50 (n=1) | 0.50 (n=1) |
| one_hop | 0.67 (n=3) | 0.67 (n=3) |
| shared_neighbor | 1.00 (n=1) | 1.00 (n=1) |
| **overall** | **0.40** (n=10) | **0.70** (n=10) |

## Latency

| Agent | mean (s) | p95 (s) | n |
| --- | --- | --- | --- |
| rag | 8.44 | 13.28 | 10 |
| graph | 7.67 | 12.88 | 10 |

## Per-question detail

### `gold-001` - *one_hop*

**Question:** Which team manages the Auth Service?

**Expected:** The Platform Team manages the Auth Service.
**Key entities:** Platform Team

- **rag** [OK correct, 3.3s] - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The Auth Service is managed by the **Platform Team** (source: service-auth-service.md).
- **graph** [OK correct, 1.9s] - The agent's answer states the same fact and mentions the expected entity 'Platform Team'.
    > The team that manages the Auth Service is the Platform Team.

### `gold-002` - *one_hop*

**Question:** What programming language is the Payments Service implemented in?

**Expected:** Python.
**Key entities:** Python

- **rag** [X wrong, 2.1s] - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java** (source: team-product.md).
- **graph** [X wrong, 12.8s] - The agent's answer does not mention Python and incorrectly states the language is not specified.
    > The Payments Service is implemented in a programming language that is not explicitly mentioned in the retrieved data. However, it is associated with the service-payments-service, which leverages Kafka and employs Redis, indicating a modern architecture likely involving languages commonly used in microservices, such as Java, Python, or Node.js. Unfortunately, the specific programming language is no...

### `gold-003` - *one_hop*

**Question:** What does Istio facilitate in the ShopFlow platform?

**Expected:** Istio facilitates service-to-service communication.
**Key entities:** service-to-service communication

- **rag** [OK correct, 7.3s] - The agent's answer states the same facts and mentions the expected entity 'service-to-service communication'.
    > Istio facilitates efficient service-to-service communication in the ShopFlow platform by providing a uniform way to secure, connect, and observe microservices (source: technology-istio-service-mesh.md).
- **graph** [OK correct, 3.6s] - The agent's answer states the same facts and mentions all expected entities, with additional relevant details.
    > Istio facilitates service-to-service communication in the ShopFlow platform. Additionally, it provides security, observability, and traffic management, and supports canary releases. It is part of the microservices architecture and integrates with Kubernetes.   This information was gathered using the neighbourhood function on the entity "Istio".

### `gold-004` - *multi_hop_2*

**Question:** Which infrastructure does the service managed by the Platform Team for authentication use?

**Expected:** It uses AWS, Kubernetes EKS, and Kafka.
**Key entities:** AWS, Kubernetes EKS, Kafka

- **rag** [X wrong, 3.7s] - The agent's answer does not mention AWS, Kubernetes EKS, or Kafka, and instead discusses unrelated technologies.
    > The Auth Service managed by the Platform Team uses a scalable infrastructure built with Python. It integrates with Redis to cache session data and authentication tokens, which helps reduce database load by serving token validation requests directly from the cache (source: [service-auth-service.md]).
- **graph** [OK correct, 4.2s] - The agent's answer states the same facts and mentions all expected entities: AWS, Kubernetes EKS, and Kafka.
    > The service managed by the Platform Team for authentication, known as the Auth Service, uses the following infrastructure:  - **Kafka** - **Kubernetes EKS** - **AWS**  This information was gathered from the relationships of the Auth Service entity.

### `gold-005` - *multi_hop_2*

**Question:** Who authored the ADR about the QuickCart acquisition, and what is their role?

**Expected:** Bob Martinez, who is a Staff SRE, authored it.
**Key entities:** Bob Martinez, Staff SRE

- **rag** [X wrong, 16.3s] - The answer does not provide any information about the author or their role.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 4.4s] - The agent's answer states the same facts and mentions all expected entities accurately.
    > Bob Martinez authored the ADR about the QuickCart acquisition, and his role is Staff SRE. This information was gathered from the relationships in the graph, specifically the `AUTHOR_OF` relationship for the ADR and the `IS` relationship for his role.

### `gold-006` - *shared_neighbor*

**Question:** Which programming language is used by both the Auth Service and the PII Service?

**Expected:** Python is used by both.
**Key entities:** Python

- **rag** [OK correct, 2.8s] - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service are developed using **Python**.   - Auth Service: Built with Python (source: service-auth-service.md). - PII Service: Developed in Python (source: service-pii-service.md).
- **graph** [OK correct, 5.7s] - The agent's answer states that both services use Python, matching the expected answer and mentioning the key entity.
    > Both the Auth Service and the PII Service use Python as their programming language.   This was determined by checking the neighbourhoods of both services, where the Auth Service is built with Python and the PII Service is developed in Python.   Key Cypher patterns used: - `MATCH (s:Entity {name: 'Auth Service'})` and `MATCH (s:Entity {name: 'PII Service'})` to explore their relationships and attri...

### `gold-007` - *aggregation_count*

**Question:** How many services does the Platform Team manage?

**Expected:** The Platform Team manages 3 services (Auth Service, GraphQL Service, PII Service).
**Key entities:** 3, Auth Service, GraphQL Service, PII Service

- **rag** [X wrong, 12.9s] - The agent's answer lists incorrect services and misses expected entities like GraphQL Service and PII Service.
    > The Platform Team manages 3 services: Auth Service, Data Lineage Service, and Payments Service (from the notes in the scratchpad).
- **graph** [OK correct, 6.0s] - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages 3 services: PII Service, GraphQL Service, and Auth Service.

### `gold-008` - *negation*

**Question:** Among the services managed by the Platform Team, which ones do NOT depend on the Data Lineage Service?

**Expected:** The GraphQL Service and the PII Service do not depend on the Data Lineage Service.
**Key entities:** GraphQL Service, PII Service

- **rag** [~ partial, 12.7s] - The agent mentions the PII Service but omits the GraphQL Service, which is also expected.
    > Among the services managed by the Platform Team, the one that does NOT depend on the Data Lineage Service is the **PII Service**.   The other services, namely the **Auth Service**, **Payments Service**, and **Shopflow App**, all have dependencies on the Data Lineage Service (source: service dependencies for each service).
- **graph** [~ partial, 12.9s] - The agent correctly identifies the PII and GraphQL Services but incorrectly includes the Auth Service.
    > The Platform Team manages three services: PII Service, GraphQL Service, and Auth Service. However, none of these services depend on the Data Lineage Service, as there are no services listed that have a dependency on it.  Thus, the services managed by the Platform Team that do NOT depend on the Data Lineage Service are: - PII Service - GraphQL Service - Auth Service  This conclusion is based on the...

### `gold-009` - *multi_hop_3*

**Question:** What database does the service authored (developed) by Bob Martinez use for caching?

**Expected:** The Auth Service, developed by Bob Martinez, uses Redis for caching.
**Key entities:** Auth Service, Redis

- **rag** [X wrong, 10.1s] - The agent's answer mentions Redis but incorrectly identifies the service as the Payments Service instead of the Auth Service.
    > The service authored by Bob Martinez, known as the Payments Service, uses **Redis** for caching. This caching layer enhances transaction lookup speed and contributes to a smoother user experience by caching transaction histories and recent payment details (source: [technology-redis-cache.md](technology-redis-cache.md)).
- **graph** [X wrong, 16.9s] - The agent's answer is a refusal and does not mention any expected entities.
    > Sorry, need more steps to process this request.

### `gold-010` - *dependency_chain*

**Question:** Which services depend on the Data Lineage Service, directly or transitively?

**Expected:** The Auth Service and the Payments Service depend on the Data Lineage Service.
**Key entities:** Auth Service, Payments Service

- **rag** [~ partial, 13.3s] - The agent's answer includes the expected entities but adds extra services not mentioned in the expected answer.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service**    - **Fraud Detection Service** (depends on Payments Service) 3. **Shopflow App**    - **Recommendation Service** (depends on Shopflow App)    - **Mobile BFF Service** (depends on Shopflow App)  Thus, the complete list of services is: Auth Service, Payments Serv...
- **graph** [~ partial, 8.2s] - The answer includes the expected entities but adds unrelated services, making it overly broad.
    > The services that depend on the Data Lineage Service, directly or transitively, are:  1. Payments Service 2. Auth Service 3. ShopFlow 4. service-auth-service 5. service-payments-service 6. Fraud Detection Service 7. e-commerce operations 8. Kibana 9. Elasticsearch 10. QuickCart  This information was gathered using the Cypher pattern that explored relationships like `INTEGRATES_WITH`, `PROVIDES_TRA...
