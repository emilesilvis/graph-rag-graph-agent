# Eval report - `20260422T151717Z-71aee8`

- Started: 2026-04-22T15:30:00.528005+00:00
- Questions: 30
- Agents: rag, graph
- Source: `/Users/emilesilvis/Dropbox/30 - 39 Projects/llms-on-graphs/graph-rag-graph-agent/eval_runs/20260422T151717Z-71aee8.json`

## Accuracy by category

Scores are mean judge grades (correct=1, partial=0.5, wrong=0); `n` is sample size in that cell.

| Category | rag | graph |
| --- | --- | --- |
| aggregation_count | 0.25 (n=4) | 0.75 (n=4) |
| dependency_chain | 0.75 (n=4) | 0.50 (n=4) |
| multi_hop_2 | 0.00 (n=5) | 0.80 (n=5) |
| multi_hop_3 | 0.25 (n=4) | 0.75 (n=4) |
| negation | 0.25 (n=4) | 0.25 (n=4) |
| one_hop | 0.80 (n=5) | 0.80 (n=5) |
| shared_neighbor | 0.88 (n=4) | 1.00 (n=4) |
| **overall** | **0.45** (n=30) | **0.70** (n=30) |

## Latency

| Agent | mean (s) | p95 (s) | n |
| --- | --- | --- | --- |
| rag | 11.19 | 20.25 | 30 |
| graph | 12.02 | 34.83 | 30 |

## Per-question detail

### `gold-001` - *one_hop*

**Question:** Which team manages the Auth Service?

**Expected:** The Platform Team manages the Auth Service.
**Key entities:** Platform Team

- **rag** [OK correct, 10.2s] - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The Auth Service is managed by the **Platform Team** (source: [service-auth-service.md](service-auth-service.md)).
- **graph** [OK correct, 5.3s] - The agent's answer states the same facts and mentions the expected entity 'Platform Team'.
    > The team that manages the Auth Service is the **Platform Team**. This information was retrieved from the relationship `IS_MANAGED_BY` in the graph.

### `gold-002` - *one_hop*

**Question:** What programming language is the Payments Service implemented in?

**Expected:** Python.
**Key entities:** Python

- **rag** [X wrong, 3.8s] - The agent's answer contradicts the expected answer by stating Java instead of Python.
    > The Payments Service is implemented in **Java** (source: team-product.md).
- **graph** [X wrong, 44.9s] - The agent's answer does not mention Python or provide any relevant information.
    > Sorry, need more steps to process this request.

### `gold-003` - *one_hop*

**Question:** What does Istio facilitate in the ShopFlow platform?

**Expected:** Istio facilitates service-to-service communication.
**Key entities:** service-to-service communication

- **rag** [OK correct, 3.8s] - The agent's answer states the same facts and mentions all expected entities, including service-to-service communication.
    > Istio facilitates efficient service-to-service communication within the ShopFlow platform by providing a uniform way to secure, connect, and observe microservices. This service mesh is integral to the platform's microservices architecture, allowing for smooth management of complex distributed systems. Key microservices, including the Shopflow App, operate on this robust Istio infrastructure (sourc...
- **graph** [OK correct, 5.0s] - The agent's answer states the same facts and mentions all expected entities, with additional relevant details.
    > Istio facilitates service-to-service communication in the ShopFlow platform. Additionally, it provides security, observability, and traffic management, and supports canary releases. It is part of the microservices architecture and integrates with Kubernetes.   This information was gathered from the relationships associated with the entity "Istio" in the graph.

### `gold-004` - *multi_hop_2*

**Question:** Which infrastructure does the service managed by the Platform Team for authentication use?

**Expected:** It uses AWS, Kubernetes EKS, and Kafka.
**Key entities:** AWS, Kubernetes EKS, Kafka

- **rag** [X wrong, 4.2s] - The agent's answer does not mention AWS, Kubernetes EKS, or Kafka, and instead discusses unrelated technologies like Python and Redis.
    > The Auth Service managed by the Platform Team uses scalable infrastructure built with Python. It integrates with Redis to cache session data and authentication tokens, which helps reduce database load by serving token validation requests directly from the cache (source: [service-auth-service.md]).
- **graph** [OK correct, 5.5s] - The agent's answer states the same facts and mentions all expected entities: AWS, Kubernetes EKS, and Kafka.
    > The service managed by the Platform Team for authentication, known as the Auth Service, uses the following infrastructure:  1. **Kafka** 2. **Kubernetes EKS** 3. **AWS**  These details were gathered from the relationships associated with the Auth Service, specifically the `USES_INFRASTRUCTURE` relationship.

### `gold-005` - *multi_hop_2*

**Question:** Who authored the ADR about the QuickCart acquisition, and what is their role?

**Expected:** Bob Martinez, who is a Staff SRE, authored it.
**Key entities:** Bob Martinez, Staff SRE

- **rag** [X wrong, 17.5s] - The answer does not provide any information about the author or their role.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 5.2s] - The agent's answer states the same facts and mentions all expected entities accurately.
    > Bob Martinez authored the ADR about the QuickCart acquisition, and his role is Staff SRE (Site Reliability Engineer). This information was gathered from the relationships in the knowledge graph, specifically the `AUTHOR_OF` relationship linking Bob Martinez to the ADR.

### `gold-006` - *shared_neighbor*

**Question:** Which programming language is used by both the Auth Service and the PII Service?

**Expected:** Python is used by both.
**Key entities:** Python

- **rag** [OK correct, 4.9s] - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service are developed using **Python**.   - Auth Service: Built with Python (source: service-auth-service.md). - PII Service: Developed in Python (source: service-pii-service.md).
- **graph** [OK correct, 3.1s] - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Auth Service and the PII Service use Python as their programming language.   This was determined from the outgoing relationships of both services, where the Auth Service is built with Python and the PII Service is developed in Python.

### `gold-007` - *aggregation_count*

**Question:** How many services does the Platform Team manage?

**Expected:** The Platform Team manages 3 services (Auth Service, GraphQL Service, PII Service).
**Key entities:** 3, Auth Service, GraphQL Service, PII Service

- **rag** [~ partial, 9.8s] - The answer mentions two of the three expected services but omits the GraphQL Service.
    > The Platform Team manages **two services**:  1. **Auth Service** 2. **PII Service**  These services are critical for user authentication and data protection, respectively (source: service-auth-service.md, service-pii-service.md).
- **graph** [OK correct, 7.0s] - The agent's answer states the same facts and mentions all expected entities.
    > The Platform Team manages 3 services: PII Service, GraphQL Service, and Auth Service.

### `gold-008` - *negation*

**Question:** Among the services managed by the Platform Team, which ones do NOT depend on the Data Lineage Service?

**Expected:** The GraphQL Service and the PII Service do not depend on the Data Lineage Service.
**Key entities:** GraphQL Service, PII Service

- **rag** [~ partial, 11.2s] - The agent mentions the PII Service but omits the GraphQL Service, which is expected.
    > The services managed by the Platform Team that do NOT depend on the Data Lineage Service are:  1. **PII Service**  The **Auth Service** and **Payments Service** do depend on the Data Lineage Service (from the retrieved data).
- **graph** [OK correct, 18.4s] - The agent's answer correctly identifies the GraphQL Service and PII Service as not depending on the Data Lineage Service.
    > The Platform Team manages three services: PII Service, GraphQL Service, and Auth Service. None of these services depend on the Data Lineage Service, as there are no dependencies recorded in the graph.  Key Cypher patterns used: 1. `MATCH (s:Entity {name: 'Platform Team'})-[:MANAGES]->(service:Entity) RETURN service.name AS service_name` 2. `MATCH (service:Entity)<-[:DEPENDS_ON]-(d:Entity {name: 'D...

### `gold-009` - *multi_hop_3*

**Question:** What database does the service authored (developed) by Bob Martinez use for caching?

**Expected:** The Auth Service, developed by Bob Martinez, uses Redis for caching.
**Key entities:** Auth Service, Redis

- **rag** [X wrong, 16.7s] - The answer does not provide any information about the expected entities or the database used for caching.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 6.8s] - The agent's answer states the same facts and mentions all expected entities: Auth Service and Redis.
    > The service authored by Bob Martinez, known as the Auth Service, uses **Redis** for caching.

### `gold-010` - *dependency_chain*

**Question:** Which services depend on the Data Lineage Service, directly or transitively?

**Expected:** The Auth Service and the Payments Service depend on the Data Lineage Service.
**Key entities:** Auth Service, Payments Service

- **rag** [~ partial, 13.1s] - The answer includes the expected entities but adds additional, unverified services.
    > The services that depend on the Data Lineage Service, either directly or transitively, are:  1. **Auth Service** 2. **Payments Service** 3. **Shopflow App** 4. **Recommendation Service** 5. **Fraud Detection Service** 6. **Mobile BFF Service**  These dependencies reflect both direct and indirect relationships (from the retrieved data across multiple searches).
- **graph** [~ partial, 7.5s] - The agent's answer includes the expected entities but adds an extra entity not in the expected answer.
    > The services that depend on the Data Lineage Service, either directly or transitively, are: 1. Payments Service 2. Monolithic Django App 3. Auth Service  This information was retrieved using a transitive query for the `DEPENDS_ON` relationship.

### `gold-011` - *one_hop*

**Question:** What programming language is the Data Lineage Service implemented in?

**Expected:** Python.
**Key entities:** Python

- **rag** [OK correct, 2.5s] - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in **Python** (source: [service-data-lineage-service.md :: Data Lineage Service > Overview]).
- **graph** [OK correct, 3.5s] - The agent's answer states the same fact and mentions the expected entity 'Python'.
    > The Data Lineage Service is implemented in Python. This information was retrieved from the relationship `IS_IMPLEMENTED_IN` in the graph.

### `gold-012` - *one_hop*

**Question:** Which cache does the Auth Service use for storing session data?

**Expected:** Redis.
**Key entities:** Redis

- **rag** [OK correct, 2.7s] - The agent's answer correctly states that the Auth Service uses Redis for caching session data.
    > The Auth Service uses Redis to cache session data and authentication tokens. This helps reduce the load on the primary database by serving token validation requests directly from the cache (source: technology-redis-cache.md).
- **graph** [OK correct, 5.1s] - The agent's answer states the same fact and mentions the expected entity 'Redis'.
    > The Auth Service uses **Redis** for storing session data.   This was determined by examining the relationships of the Auth Service, which indicated it "uses database" Redis, and further confirming that Redis is used for session management.

### `gold-013` - *multi_hop_2*

**Question:** Who leads the team that operates the QuickCart Orders Service?

**Expected:** Bob Martinez leads the Orders Team, which operates the QuickCart Orders Service.
**Key entities:** Bob Martinez, Orders Team

- **rag** [X wrong, 16.6s] - The answer does not mention any expected entities and states it needs more information.
    > Sorry, need more steps to process this request.
- **graph** [~ partial, 4.1s] - The answer mentions Bob Martinez but omits the 'Orders Team' entity.
    > The team that operates the QuickCart Orders Service is led by Bob Martinez.

### `gold-014` - *multi_hop_2*

**Question:** What programming language is the service developed by Bob Martinez built with?

**Expected:** Python - the Auth Service, which Bob Martinez developed, is built with Python.
**Key entities:** Auth Service, Python

- **rag** [X wrong, 7.1s] - The agent's answer contradicts the expected answer by stating JavaScript instead of Python and misses 'Auth Service'.
    > The service developed by Bob Martinez is built with JavaScript.
- **graph** [OK correct, 3.3s] - The agent's answer states the same facts and mentions all expected entities: 'Auth Service' and 'Python'.
    > The service developed by Bob Martinez, known as the Auth Service, is built with Python.

### `gold-015` - *multi_hop_2*

**Question:** Who authored the ADR about GDPR compliance, and what team do they lead?

**Expected:** Alice Chen authored the ADR and leads the SRE Team.
**Key entities:** Alice Chen, SRE Team

- **rag** [X wrong, 18.8s] - The answer does not mention any of the expected entities or provide relevant information.
    > Sorry, need more steps to process this request.
- **graph** [~ partial, 6.2s] - The agent correctly identifies Alice Chen as the author but incorrectly states the team she leads.
    > Alice Chen authored the ADR about GDPR compliance and leads the Customer Experience Team.

### `gold-016` - *multi_hop_3*

**Question:** Which programming language is used by the service that is managed by the Platform Team and depends on the Data Lineage Service?

**Expected:** Python - the Auth Service is managed by the Platform Team, depends on the Data Lineage Service, and is built with Python.
**Key entities:** Auth Service, Python

- **rag** [OK correct, 7.9s] - The agent's answer states the same facts and mentions all expected entities: Auth Service and Python.
    > The service managed by the Platform Team that depends on the Data Lineage Service is the **Auth Service**. It is implemented in **Python**.
- **graph** [X wrong, 43.1s] - The agent's answer is a refusal and does not mention any expected entities like 'Auth Service' or 'Python'.
    > Sorry, need more steps to process this request.

### `gold-017` - *multi_hop_3*

**Question:** What programming language is used by the service developed by the person who authored 'ADR: QuickCart Acquisition and Integration'?

**Expected:** Python - Bob Martinez authored the ADR and developed the Auth Service, which is built with Python.
**Key entities:** Bob Martinez, Auth Service, Python

- **rag** [X wrong, 20.2s] - The answer is a refusal and does not mention any expected entities or facts.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 8.6s] - The agent's answer includes all expected entities and states the same facts as the expected answer.
    > The service developed by Bob Martinez, who authored 'ADR: QuickCart Acquisition and Integration', is built with Python.   This information was gathered through the relationships connecting Bob Martinez to the Auth Service, which is developed using Python.

### `gold-018` - *multi_hop_3*

**Question:** What role does the person who developed the authentication service managed by the Platform Team have?

**Expected:** Staff SRE - Bob Martinez, who developed the Auth Service (managed by the Platform Team), is a Staff SRE.
**Key entities:** Bob Martinez, Staff SRE

- **rag** [X wrong, 25.2s] - The agent's answer is a refusal and does not mention any expected entities or facts.
    > Sorry, need more steps to process this request.
- **graph** [OK correct, 8.8s] - The agent's answer states the same facts and mentions all expected entities.
    > The person who developed the Authentication Service, Bob Martinez, has the role of Staff SRE (Site Reliability Engineer).   This information was gathered through the relationships connected to the "Auth Service" and "Bob Martinez" entities.

### `gold-019` - *dependency_chain*

**Question:** Which services rely on the Payments Service, directly or transitively?

**Expected:** The Fraud Detection Service relies on the Payments Service.
**Key entities:** Fraud Detection Service

- **rag** [OK correct, 18.0s] - The agent's answer includes the Fraud Detection Service, which is the expected entity.
    > The services that rely on the Payments Service, either directly or transitively, are:  1. **ShopFlow App** 2. **Data Lineage Service** 3. **Fraud Detection Service** 4. **Recommendation Service** (depends on ShopFlow App) 5. **Auth Service** (depends on Data Lineage Service)  Thus, the complete list of services is: ShopFlow App, Data Lineage Service, Fraud Detection Service, Recommendation Service...
- **graph** [X wrong, 11.3s] - The agent's answer does not mention the Fraud Detection Service, which is the key expected entity.
    > The services that rely on the Payments Service, directly or transitively, are:  1. Monolithic Django App 2. Logistics Team 3. Data Lineage Service  This information was gathered using the relationships `INTEGRATES_WITH` and `SUPPORTS` in the graph.

### `gold-020` - *dependency_chain*

**Question:** Which service, directly or transitively, depends on the ShopFlow application?

**Expected:** The Recommendation Service depends on the ShopFlow application.
**Key entities:** Recommendation Service

- **rag** [~ partial, 24.6s] - The agent's answer mentions the Recommendation Service but includes additional unrelated services.
    > The services that depend on the ShopFlow application, either directly or transitively, are:  1. **Payments Service**    - Depends on: Data Lineage Service, Fraud Detection Service 2. **Recommendation Service**  Transitive dependencies include: - **Data Lineage Service** (depends on Auth Service) - **Fraud Detection Service** (depends on Payments Service)  Thus, the complete list of services is: - ...
- **graph** [OK correct, 3.7s] - The agent's answer states the same fact and mentions the expected entity 'Recommendation Service'.
    > The service that directly or transitively depends on the ShopFlow application is the Recommendation Service.

### `gold-021` - *dependency_chain*

**Question:** Which services use Redis for caching or session storage? Consider all relationship types that express use/employ/cache.

**Expected:** The Auth Service and the Payments Service both use Redis for caching.
**Key entities:** Auth Service, Payments Service

- **rag** [OK correct, 4.4s] - The agent's answer states the same facts and mentions all expected entities: Auth Service and Payments Service.
    > The services that use Redis for caching or session storage are:  1. **Auth Service**    - Uses Redis for caching session data and user credentials.  2. **Payments Service**    - Employs Redis for caching transaction histories and managing session data.  Both services utilize Redis to enhance performance by reducing load on the primary database and improving response times (sources: [technology-red...
- **graph** [~ partial, 11.0s] - The agent's answer mentions the Auth Service but omits the Payments Service, making it incomplete.
    > The services that use Redis for caching or session storage are:  1. Auth Service  This was determined by querying the relationships that express usage of Redis, including various types of "use" and "cache" relationships.

### `gold-022` - *shared_neighbor*

**Question:** Which cache database is used by both the Auth Service and the Payments Service?

**Expected:** Redis.
**Key entities:** Redis

- **rag** [OK correct, 5.2s] - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the Auth Service and the Payments Service use **Redis** as their cache database. Redis is utilized to cache session data and authentication tokens for the Auth Service, and to cache transaction histories and recent payment details for the Payments Service (source: technology-redis-cache.md).
- **graph** [OK correct, 6.2s] - The agent's answer states the same facts and mentions the expected entity 'Redis'.
    > Both the Auth Service and the Payments Service use **Redis** as their cache database.   This was determined by checking the outgoing relationships for both services:  - The Auth Service has a relationship indicating it "USES_DATABASE" Redis. - The Payments Service has a relationship indicating it "EMPLOYS" Redis.   Thus, Redis is the common cache database used by both services.

### `gold-023` - *shared_neighbor*

**Question:** Which programming language is used by both the Fraud Detection Service and the Recommendation Service?

**Expected:** Python.
**Key entities:** Python

- **rag** [OK correct, 4.2s] - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service are implemented in **Python**.   - The Fraud Detection Service is designed to identify and prevent fraudulent activities and is implemented in Python (source: service-fraud-detection-service.md). - The Recommendation Service offers tailored recommendations and is also built using Python (source: service-recommendation-service.md).
- **graph** [OK correct, 5.3s] - The agent's answer states the same facts and mentions the expected entity 'Python'.
    > Both the Fraud Detection Service and the Recommendation Service use **Python** as their programming language.   This was determined by checking the neighbourhoods of both services:  - The Fraud Detection Service is implemented in Python. - The Recommendation Service is built using Python.   Thus, Python is the common programming language used by both services.

### `gold-024` - *shared_neighbor*

**Question:** Which services integrate with both the GraphQL Federation Layer and the Monolithic Django App?

**Expected:** The BFF Service and the Recommendation Service integrate with both.
**Key entities:** BFF Service, Recommendation Service

- **rag** [~ partial, 17.0s] - The agent's answer includes the expected entities but adds extra services not mentioned in the expected answer.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are:  1. **BFF Service** 2. **Recommendation Service** 3. **Fraud Detection Service** 4. **Quickcart Orders Service** 5. **Payments Service**  These services are mentioned as key integrations for the GraphQL Federation Layer and are also listed as integrations or dependencies for the Monolithic Django ...
- **graph** [OK correct, 22.8s] - The agent's answer states the same facts and mentions all expected entities.
    > The services that integrate with both the GraphQL Federation Layer and the Monolithic Django App are: 1. BFF Service 2. Recommendation Service  This was determined by examining the outgoing relationships for both services and identifying the common ones.

### `gold-025` - *aggregation_count*

**Question:** How many teams does the ShopFlow platform have?

**Expected:** ShopFlow has 9 teams - Catalog, Customer Experience, Data, Engineering, Logistics, Orders, Platform, Product, and the Site Reliability Engineering (SRE) Team.
**Key entities:** 9, Catalog Team, Customer Experience Team, Data Team, Engineering Team, Logistics Team, Orders Team, Platform Team, Product Team, Site Reliability Engineering (SRE) Team

- **rag** [~ partial, 11.9s] - The answer mentions some expected teams but not all and does not specify the number of teams.
    > The ShopFlow platform has approximately 1,500 dedicated professionals organized into several specialized teams, including the Data Team, Product Team, Platform Team, and Engineering Team.
- **graph** [X wrong, 22.4s] - The agent's answer lists incorrect teams and an incorrect total number of teams.
    > The ShopFlow platform has 6 teams: Platform Team, Catalog Team, Engineering Team, SRE Team, Payments Service, and Mobile Backend-for-Frontend (BFF) Service.

### `gold-026` - *aggregation_count*

**Question:** How many distinct services or components have their code implemented in Python?

**Expected:** 6 - the Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, and the Monolithic Django App.
**Key entities:** 6, Auth Service, PII Service, Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

- **rag** [X wrong, 5.2s] - The agent's answer lists 5 services and misses key entities like Data Lineage Service and Monolithic Django App.
    > There are 5 distinct services implemented in Python: Auth Service, PII Service, Fraud Detection Service, Recommendation Service, and Shopflow App.
- **graph** [OK correct, 14.1s] - The agent's answer lists all expected entities and states the same facts as the expected answer.
    > There are 6 distinct services or components implemented in Python:  1. Recommendation Service 2. Auth Service 3. PII Service 4. Fraud Detection Service 5. Data Lineage Service 6. Monolithic Django App  This information was gathered using the relationships related to Python in the graph.

### `gold-027` - *aggregation_count*

**Question:** How many entities does the Fraud Detection Service directly integrate with (via INTEGRATES_WITH edges)?

**Expected:** 3 - Elasticsearch, Kibana, and QuickCart.
**Key entities:** 3, Elasticsearch, Kibana, QuickCart

- **rag** [X wrong, 8.5s] - The answer lists incorrect entities and an incorrect number of integrations, missing Elasticsearch and Kibana.
    > The Fraud Detection Service directly integrates with 2 entities: Payments Service and QuickCart.
- **graph** [OK correct, 10.0s] - The agent's answer states the same facts and mentions all expected entities.
    > The Fraud Detection Service directly integrates with 3 entities: Kibana, Elasticsearch, and QuickCart.

### `gold-028` - *negation*

**Question:** Among the services managed by the Platform Team, which ones are NOT implemented in Python?

**Expected:** The GraphQL Service is not documented as being implemented in Python (the Auth Service and PII Service both are).
**Key entities:** GraphQL Service

- **rag** [X wrong, 17.5s] - The agent's answer contradicts the expected answer by stating all services are implemented in Python, missing the GraphQL Service entity.
    > The services managed by the Platform Team that are **NOT** implemented in Python are:  - None.   All identified services (Auth Service, PII Service, Fraud Detection Service, and Recommendation Service) are implemented in Python.   Sources:  - Auth Service (service-auth-service.md) - PII Service (service-pii-service.md) - Fraud Detection Service (service-fraud-detection-service.md) - Recommendation...
- **graph** [X wrong, 12.8s] - The agent's answer incorrectly states that none of the services are implemented in Python, contradicting the expected answer.
    > The Platform Team manages 3 services: PII Service, GraphQL Service, and Auth Service. None of these services are implemented in Python, as there are no services linked to Python in the graph.  Thus, all services managed by the Platform Team (PII Service, GraphQL Service, Auth Service) are NOT implemented in Python.

### `gold-029` - *negation*

**Question:** Among the services that depend on the Data Lineage Service, which are NOT managed by the Platform Team?

**Expected:** The Payments Service and the Monolithic Django App depend on the Data Lineage Service but are not managed by the Platform Team.
**Key entities:** Payments Service, Monolithic Django App

- **rag** [~ partial, 9.8s] - The agent correctly identifies the Payments Service but misses the Monolithic Django App and incorrectly includes the Shopflow App.
    > The services that depend on the Data Lineage Service are:  1. **Auth Service** (managed by the Platform Team) 2. **Payments Service** (managed by the Product Team) 3. **Shopflow App** (managed by the Engineering Team)  Among these, the services that are **NOT managed by the Platform Team** are:  - **Payments Service** - **Shopflow App**   Thus, the answer is: - Payments Service - Shopflow App
- **graph** [X wrong, 34.8s] - The agent's answer is a refusal and does not mention any expected entities.
    > Sorry, need more steps to process this request.

### `gold-030` - *negation*

**Question:** Among the services implemented in Python, which ones are NOT managed by the Platform Team?

**Expected:** The Data Lineage Service, the Fraud Detection Service, the Recommendation Service, and the Monolithic Django App are implemented in Python but not managed by the Platform Team.
**Key entities:** Data Lineage Service, Fraud Detection Service, Recommendation Service, Monolithic Django App

- **rag** [X wrong, 13.2s] - The agent's answer misses key entities and incorrectly states that the Fraud Detection Service is managed by the Platform Team.
    > The services implemented in Python that are **not** managed by the Platform Team are:  1. **Recommendation Service** 2. **Shopflow App**  The following services are managed by the Platform Team: - **Auth Service** - **PII Service** - **Fraud Detection Service**   Thus, the services not managed by the Platform Team are the Recommendation Service and the Shopflow App (from the findings in the servic...
- **graph** [X wrong, 14.7s] - The agent's answer contradicts the expected answer and misses all key entities.
    > The only service implemented in Python is the **PII Service**, which is managed by the Platform Team. Therefore, there are no services implemented in Python that are NOT managed by the Platform Team.   Key Cypher patterns used: - `MATCH (s:Entity) WHERE (s)-[:IS_DEVELOPED_IN]->(:Entity {name: 'Python'})` to find Python services. - Checked management relationships for the identified services.
