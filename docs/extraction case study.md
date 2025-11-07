Tentu, ini adalah ekstraksi semua teks dari dokumen PDF yang Anda berikan, diformat sebagai Markdown:

## 📄 Case Study Brief - Backend Developer

### **Case Study Brief & Objective**

Hello! [cite_start]Thank you for applying with us as a backend developer[cite: 1, 2]. [cite_start]This mini project should be completed within **5 days** after you have received this document[cite: 3]. [cite_start]Please spare your time to complete this project with the best results[cite: 4]. [cite_start]We are really pleased to answer your questions if there are unclear things[cite: 5].

[cite_start]Your mission is to build a backend service that **automates the initial screening of a job application**[cite: 7]. [cite_start]The service will receive a candidate's CV and a project report, evaluate them against a specific job description and a case study brief, and produce a structured, AI-generated evaluation report[cite: 8].

[cite_start]We want to see your ability to combine backend engineering with **AI workflows** (prompt design, LLM chaining, retrieval, resilience)[cite: 20].

---

### **Core Logic & Data Flow**

[cite_start]The system operates with a clear separation of inputs and reference documents[cite: 9]:

#### [cite_start]**Candidate-Provided Inputs (The Data to be Evaluated)** [cite: 10]
1.  [cite_start]**Candidate CV**: The candidate's resume (PDF)[cite: 11].
2.  [cite_start]**Project Report**: The candidate's project report to our take-home case study (PDF)[cite: 12].

#### [cite_start]**System-Internal Documents (The "Ground Truth" for Comparison)** [cite: 13]
1.  [cite_start]**Job Description**: A document detailing the requirements and responsibilities for the role you're currently applying[cite: 14]. [cite_start]This document will be used as ground truth for **Candidate CV**[cite: 15]. [cite_start]You might need to ingest a few job description documents to ensure the vector retrieval is accurate enough[cite: 16, 17].
2.  **Case Study Brief**: This document. [cite_start]Used as ground truth for **Project Report** (PDF)[cite: 18].
3.  [cite_start]**Scoring Rubric**: A predefined set of parameters for evaluating CV and Report, each has it's own documents (PDF)[cite: 19].

---

### **Deliverables**

#### **1. [cite_start]Backend Service (API Endpoints)** [cite: 21, 22]
[cite_start]Implement a backend service with at least the following RESTful API endpoints[cite: 23]:

| Method | Endpoint | Description | Request/Response Example |
| :--- | :--- | :--- | :--- |
| **POST** | `/upload` | [cite_start]Accepts `multipart/form-data` containing Candidate CV and Project Report (PDF)[cite: 24, 25]. [cite_start]Stores files and returns each with its own ID for later processing[cite: 26]. | (Implied: Returns document IDs) |
| **POST** | `/evaluate` | [cite_start]Triggers the **asynchronous** AI evaluation pipeline[cite: 27, 28, 29]. [cite_start]Receives input **job title (string)**, and **both document ID**[cite: 28]. [cite_start]Immediately returns a job ID to track the evaluation process[cite: 29]. | [cite_start]`{"id": "456", "status": "queued"}` [cite: 30, 31, 32, 33] |
| **GET** | `/result/{id}` | [cite_start]Retrieves the status and result of an evaluation job[cite: 34, 35]. [cite_start]Should reflect the asynchronous, multi-stage nature of the process[cite: 36]. | **While queued or processing:** `{"id": "456", "status": "queued" | [cite_start]"processing"}` [cite: 38, 39, 41, 42] |
| | | | [cite_start]**Once completed:** `{"id": "456", "status": "completed", "result": {"cv_match_rate": 0.82, "cv_feedback": "Strong in backend and cloud, limited AI integration experience...", "project_score": 4.5, "project_feedback": "Meets prompt chaining requirements, lacks error handling robustness...", "overall_summary": "Good candidate fit, would benefit from deeper RAG knowledge..."}}` [cite: 44-54] |

#### **2. [cite_start]Evaluation Pipeline** [cite: 55]
[cite_start]The AI-driven pipeline, triggered by `[POST] /evaluate`, should consist of these key components[cite: 56]:

* [cite_start]**RAG (Context Retrieval)**[cite: 57]:
    * [cite_start]Ingest all **System-Internal Documents** (Job Description, Case Study Brief, Both Scoring Rubrics) into a **vector database**[cite: 58].
    * [cite_start]Retrieve relevant sections and inject into prompts (e.g., "for CV scoring" vs "for project scoring")[cite: 59].
* [cite_start]**Prompt Design & LLM Chaining**[cite: 60, 61]:
    * [cite_start]**CV Evaluation**[cite: 62]:
        * [cite_start]Parse the candidate's CV into structured data[cite: 63].
        * [cite_start]Retrieve relevant information from both Job Description and CV Scoring Rubrics[cite: 64].
        * [cite_start]Use an LLM to get `cv_match_rate` & `cv_feedback`[cite: 65].
    * [cite_start]**Project Report Evaluation**[cite: 66]:
        * [cite_start]Parse the candidate's Project Report into structured data[cite: 67].
        * [cite_start]Retrieve relevant information from both Case Study Brief and CV Scoring Rubrics[cite: 68].
        * [cite_start]Use an LLM to get `project_score` & `project_feedback`[cite: 69].
    * [cite_start]**Final Analysis**[cite: 70]:
        * [cite_start]Use a final LLM call to synthesize the outputs into a concise `overall_summary`[cite: 71].
* [cite_start]**Long-Running Process Handling**[cite: 72]:
    * [cite_start]`POST /evaluate` should not block[cite: 73].
    * [cite_start]Store task, return job ID, allow `GET /result/{id}` to check later periodically[cite: 74].
* [cite_start]**Error Handling & Randomness Control**[cite: 75]:
    * [cite_start]Simulate any edge cases and how the service handles them[cite: 76].
    * [cite_start]Simulate failures from LLM API (timeouts, rate limit)[cite: 77].
    * [cite_start]Implement **retries/back-off**[cite: 78].
    * [cite_start]Control LLM temperature or add validation layer to keep responses stable[cite: 79].

#### **3. [cite_start]Standardized Evaluation Parameters** [cite: 80, 81]

##### [cite_start]**CV Evaluation (Match Rate)** [cite: 82]
* [cite_start]Technical Skills Match (backend, databases, APIs, cloud, AI/LLM exposure)[cite: 83].
* [cite_start]Experience Level (years, project complexity)[cite: 83].
* [cite_start]Relevant Achievements (impact, scale)[cite: 84].
* [cite_start]Cultural Fit (communication, learning attitude)[cite: 85].

##### [cite_start]**Project Deliverable Evaluation** [cite: 86]
* [cite_start]Correctness (meets requirements: prompt design, chaining, RAG, handling errors)[cite: 87].
* [cite_start]Code Quality (clean, modular, testable)[cite: 88].
* [cite_start]Resilience (handles failures, retries)[cite: 89].
* [cite_start]Documentation (clear README, explanation of trade-offs)[cite: 90].
* [cite_start]Creativity / Bonus (optional improvements like authentication, deployment, dashboards)[cite: 91].
* [cite_start]Each parameter can be scored **1-5**, then aggregated to final score[cite: 92].

---

### [cite_start]**Requirements** [cite: 93]

* [cite_start]Use any backend framework (Rails, Django, Node.js, etc.)[cite: 94].
* Use a proper LLM service (e.g., OpenAl, Gemini, or OpenRouter). [cite_start]Several free LLM API providers are available[cite: 95].
* [cite_start]Use a simple vector DB (e.g. ChromaDB, Qdrant, etc) or RAG-as-a-service (e.g. Ragie, S3 Vector, etc), any of your own choice[cite: 96].
* [cite_start]Provide **README** with run instructions + explanation of design choices[cite: 97].
* [cite_start]Provide the documents together with their **ingestion scripts** in the repository for reproducibility purposes[cite: 98].

---

### **Scoring Rubric for Case Study Evaluation**

#### [cite_start]**CV Match Evaluation (1-5 scale per parameter)** [cite: 100]

| Parameter | Description | Scoring Guide | Weight |
| :--- | :--- | :--- | :--- |
| **Technical Skills Match** | [cite_start]Alignment with job requirements (backend, databases, APIs, cloud, Al/LLM)[cite: 101]. | [cite_start]1 = Irrelevant skills, 2 = Few overlaps, 3 = Partial match, 4 = Strong match, 5 = Excellent match + Al/LLM exposure[cite: 101]. | [cite_start]40% [cite: 101] |
| **Experience Level** | [cite_start]Years of experience and project complexity[cite: 101]. | [cite_start]1 < 1 yr/trivial projects, 2 = 1-2 yrs, 3 = 2-3 yrs with mid-scale projects, 4 = 3-4 yrs solid track record, 5 = 5+ yrs / high-impact projects[cite: 101]. | [cite_start]25% [cite: 101] |
| **Relevant Achievements** | [cite_start]Impact of past work (scaling, performance, adoption)[cite: 101]. | [cite_start]1 = No clear achievements, 2 = Minimal improvements, 3 = Some measurable outcomes, 4 = Significant contributions, 5 = Major measurable impact[cite: 101]. | [cite_start]20% [cite: 101] |
| **Cultural/Collaboration Fit** | [cite_start]Communication, learning mindset, teamwork/leadership[cite: 101]. | [cite_start]1 = Not demonstrated, 2 = Minimal, 3 = Average, 4 = Good, 5 = Excellent and well-demonstrated[cite: 101]. | [cite_start]15% [cite: 101] |

#### [cite_start]**Project Deliverable Evaluation (1-5 scale per parameter)** [cite: 102]

| Parameter | Description | Scoring Guide | Weight |
| :--- | :--- | :--- | :--- |
| **Correctness (Prompt & Chaining)** | [cite_start]Implements prompt design, LLM chaining, RAG context injection[cite: 103]. | [cite_start]1 = Not implemented, 2 = Minimal attempt, 3 = Works partially, 4 = Works correctly, 5 = Fully correct + thoughtful[cite: 103]. | [cite_start]30% [cite: 103] |
| **Code Quality & Structure** | [cite_start]Clean, modular, reusable, tested[cite: 103]. | [cite_start]1 = Poor, 2 = Some structure, 3 = Decent modularity, 4 = Good structure + some tests, 5 = Excellent quality + strong tests[cite: 103]. | [cite_start]25% [cite: 103] |
| **Resilience & Error Handling** | [cite_start]Handles long jobs, retries, randomness, API failures[cite: 103]. | [cite_start]1 = Missing, 2 = Minimal, 3 = Partial handling, 4 = Solid handling, 5 = Robust, production-ready[cite: 103]. | [cite_start]20% [cite: 103] |
| **Documentation & Explanation** | [cite_start]README clarity, setup instructions, trade-off explanations[cite: 103]. | [cite_start]1 = Missing, 2 = Minimal, 3 = Adequate, 4 = Clear, 5 = Excellent + insightful[cite: 103]. | [cite_start]15% [cite: 103] |
| **Creativity / Bonus** | [cite_start]Extra features beyond requirements[cite: 103]. | [cite_start]1 = None, 2 = Very basic, 3 = Useful extras, 4 = Strong enhancements, 5 = Outstanding creativity[cite: 103, 104]. | [cite_start]10% [cite: 103] |

#### [cite_start]**Overall Candidate Evaluation** [cite: 105]
* [cite_start]**CV Match Rate**: Weighted Average (1-5) → Convert to 0-1 decimal ($\times 0.2$)[cite: 106].
* [cite_start]**Project Score**: Weighted Average (1-5)[cite: 107].
* [cite_start]**Overall Summary**: Service should return 3-5 sentences (strengths, gaps, recommendations)[cite: 108].

---

### [cite_start]**Study Case Submission Template** [cite: 109]

Please use this template to document your solution. [cite_start]Submit it as a **PDF file** along with your project repository[cite: 110].

#### **1. [cite_start]Title** [cite: 111]

#### **2. [cite_start]Candidate Information** [cite: 112]
* [cite_start]Full Name: [cite: 113]
* [cite_start]Email Address: [cite: 114]

#### **3. [cite_start]Repository Link** [cite: 115]
* [cite_start]Provide a link to your GitHub repository[cite: 116].
* **Important**: Do not use the word **Rakamin** anywhere in your repository name, commits, or documentation. [cite_start]This is to reduce plagiarism risk[cite: 117, 118].
* [cite_start]*Example*: `github.com/username/ai-cv-evaluator` [cite: 119]

#### **4. [cite_start]Approach & Design (Main Section)** [cite: 120]
Tell the story of how you approached this challenge. [cite_start]Clarity and reasoning matter more than buzzwords[cite: 121, 142]. Please include:
* [cite_start]**Initial Plan**[cite: 123]:
    * [cite_start]How you broke down the requirements[cite: 124].
    * [cite_start]Key assumptions or scope boundaries[cite: 125].
* [cite_start]**System & Database Design**[cite: 126]:
    * [cite_start]API endpoints design[cite: 127].
    * [cite_start]Database schema (diagram or explanation)[cite: 128].
    * [cite_start]Job queue / long-running task handling[cite: 129].
* [cite_start]**LLM Integration**[cite: 130]:
    * [cite_start]Why you chose a specific LLM or provider[cite: 131].
    * [cite_start]Prompt design decisions[cite: 132].
    * [cite_start]Chaining logic (if any)[cite: 133].
    * [cite_start]RAG (retrieval, embeddings, vector DB) strategy[cite: 134].
* [cite_start]**Prompting Strategy** (examples of your actual prompts)[cite: 135].
* [cite_start]**Resilience & Error Handling**[cite: 136]:
    * [cite_start]How you handled API failures, timeouts, or randomness[cite: 137].
    * [cite_start]Any retry, backoff, or fallback logic[cite: 138].
* [cite_start]**Edge Cases Considered**[cite: 139]:
    * [cite_start]What unusual inputs or scenarios you thought about[cite: 140].
    * [cite_start]How you tested them[cite: 141].

#### **5. [cite_start]Results & Reflection** [cite: 143]
* [cite_start]**Outcome**[cite: 144]:
    * [cite_start]What worked well in your implementation? [cite: 145]
    * [cite_start]What didn't work as expected? [cite: 146]
* [cite_start]**Evaluation of Results**[cite: 147]:
    * [cite_start]If the evaluation scores/outputs were bad or inconsistent, explain why[cite: 148].
    * [cite_start]If they were good, explain what made them stable[cite: 149].
* [cite_start]**Future Improvements**[cite: 150]:
    * [cite_start]What would you do differently with more time? [cite: 151]
    * [cite_start]What constraints (time, tools, API limits) affected your solution? [cite: 152]

#### **6. [cite_start]Screenshots of Real Responses** [cite: 153]
Show real JSON response from your API using your own CV + Project Report. Minimum:
* [cite_start]`/evaluate` returns `job_id + status`[cite: 155, 156].
* [cite_start]`/result/:id` returns final evaluation (scores + feedback)[cite: 157].
* [cite_start]Paste screenshots or Postman/terminal logs[cite: 158].

#### **7. (Optional) [cite_start]Bonus Work** [cite: 159]
* [cite_start]If you added extra features, describe them here[cite: 160].

---

### [cite_start]**Job Description - Product Engineer (Backend) 2025** [cite: 161]

[cite_start]Rakamin is hiring a Product Engineer (Backend)[cite: 162]. [cite_start]We're looking for dedicated engineers who write code they're proud of and who are eager to keep scaling and improving complex systems, including those powered by AI[cite: 163].

#### [cite_start]**About the Job** [cite: 164]
[cite_start]You'll be building new product features alongside a frontend engineer and product manager using our Agile methodology, as well as addressing issues to ensure our apps are robust and our codebase is clean[cite: 165]. [cite_start]You'll write clean, efficient code to enhance our product's codebase[cite: 166].

[cite_start]In addition to classic backend work, this role also touches on building **AI-powered systems**, where you'll design and orchestrate how large language models (LLMs) integrate into Rakamin's product ecosystem[cite: 167].

**Examples of Work:**
* [cite_start]Collaborating to build robust backend solutions that support highly configurable platforms and cross-platform integration[cite: 169].
* [cite_start]Developing and maintaining server-side logic for central database, ensuring high performance throughput and response time[cite: 170].
* [cite_start]Designing and fine-tuning AI prompts that align with product requirements and user contexts[cite: 171].
* [cite_start]Building **LLM chaining flows**[cite: 172].
* [cite_start]Implementing **Retrieval-Augmented Generation (RAG)** by embedding and retrieving context from vector databases, then injecting it into AI prompts[cite: 173].
* [cite_start]Handling **long-running AI processes gracefully** including job orchestration, async background workers, and retry mechanisms[cite: 174, 175].
* [cite_start]Designing safeguards for uncontrolled scenarios: managing failure cases from 3rd party APIs and mitigating the **randomness/nondeterminism of LLM outputs**[cite: 176].
* [cite_start]Leveraging AI tools and workflows to increase team productivity[cite: 177].
* [cite_start]Writing reusable, testable, and efficient code[cite: 178].
* [cite_start]Strengthening test coverage with RSpec[cite: 179].
* [cite_start]Conducting full product lifecycles[cite: 180].
* [cite_start]Providing input on technical feasibility, timelines, and potential product trade-offs[cite: 181].
* [cite_start]Actively engaging with users and stakeholders[cite: 182].

#### [cite_start]**About You** [cite: 183]
[cite_start]We're looking for candidates with a **strong track record of working on backend technologies** of web apps, ideally with exposure to **AI/LLM development** or a strong desire to learn[cite: 184].

**Required Experience and Knowledge:**
* [cite_start]Backend languages and frameworks (**Node.js, Django, Rails**)[cite: 185].
* Modern backend tooling and technologies:
    * [cite_start]Database management (MySQL, PostgreSQL, MongoDB)[cite: 186].
    * [cite_start]RESTful APIs[cite: 187].
    * [cite_start]Security compliance[cite: 188].
    * [cite_start]Cloud technologies (AWS, Google Cloud, Azure)[cite: 189].
    * [cite_start]Server-side languages (Java, Python, Ruby, or JavaScript)[cite: 190].
    * [cite_start]Understanding of frontend technologies[cite: 191].
    * [cite_start]User authentication and authorization[cite: 192].
    * [cite_start]Scalable application design principles[cite: 193].
    * [cite_start]Creating database schemas[cite: 194].
    * [cite_start]Implementing automated testing platforms and unit tests[cite: 195].
    * [cite_start]Familiarity with **LLM APIs, embeddings, vector databases** and **prompt design best practices**[cite: 196].

[cite_start]We care about what you can do and how you do it, not how you got here; a Computer Science degree or graduating from a prestigious university isn't emphasized[cite: 197, 198].

[cite_start]You'll report to a CTO directly[cite: 199]. [cite_start]Rakamin is a company where **Managers of One thrive**[cite: 199]. [cite_start]This is a **remote job**[cite: 202]. [cite_start]To ensure time zone overlap, we're only looking for people based in **Indonesia**[cite: 203].

#### [cite_start]**Benefits & Perks** [cite: 204]
1.  [cite_start]**Paid time off**: 17 days of vacation and personal days per year[cite: 206, 207].
2.  [cite_start]**Learning benefits** with total Rp29 million per year[cite: 208]:
    * [cite_start]Rp6 million per year for courses, books, or resources[cite: 209].
    * [cite_start]O'Reilly subscription worth Rp8 million per year[cite: 210].
    * [cite_start]Access to all Bootcamps and Short Courses worth Rp15 million per year[cite: 211].
3.  [cite_start]**Device ownership**: Rp7 million budget per year to purchase any device to support your productivity[cite: 212].
