
 

# **LeadHer Career Quest**



**LeadHer Career Quest** is an interactive educational career-readiness simulation built with Python and Streamlit. It helps university students explore career paths, map their current skills, practice recruitment-style tasks, and identify areas for development in a low-pressure learning environment.



> Discover your strengths. Identify your gaps. Build your readiness.



\## **What It Does**



LeadHer Career Quest turns career preparation into a guided quest.



Instead of treating career readiness as a single test, the platform breaks the experience into practical activities covering career direction, CV readiness, analytical and problem-solving skills, business decision-making, and interview practice.



The current build is designed as an \*\*educational simulation\*\*, not a real recruitment or hiring system.



\## **Career Quest Journey**



\### 1. Career Quest



Choose a career direction and build a personalized skill map.



Users can currently explore 10 career personas:



\* Data Analyst

\* Business Analyst

\* Product Manager

\* Marketing Professional

\* Finance Professional

\* HR Professional

\* Supply Chain Professional

\* Technology / Software Professional

\* Entrepreneur

\* Other / Still Exploring



Each path has its own career-specific skill framework with a \*\*5-level proficiency scale\*\*, from "Never used it" to "Advanced".



The user can also provide a small amount of profile information:



\* First name

\* University

\* Study year

\* Optional email



This information is kept in the Streamlit session and is not stored in a database.



\### 2. CV X-Ray



Upload a PDF CV and receive a structured readiness analysis.



The CV analyzer checks areas such as:



\* Contact information

\* Education

\* Skills

\* Experience / Projects

\* Action-oriented wording

\* Measurable results

\* CV length / content signals

\* Other basic CV structure indicators



The scoring is \*\*rule-based\*\*, transparent, and intended for practice rather than professional recruitment screening.



Uploaded CV content is processed in memory rather than being saved to a database or permanent file store.



\### 3. Skill Challenge



Complete a career-path-specific assessment.



Questions are loaded from the project's structured content banks and are mapped to the selected underlying career track.



The current content system supports 8 underlying tracks:



\* Data Analytics

\* Business Analysis

\* Marketing

\* Finance

\* HR

\* Technology

\* Supply Chain

\* General



The assessment uses transparent rule-based scoring rather than an AI model.



Some assessments also include a short real-world data question with source information stored in the project's data files.



\### 4. Case Room



Work through a small business case based on the selected career track.



The Case Room presents the situation progressively, including:



\*\*Client Brief → Data Pack → Stakeholder Message → Decision Points → Recommendation\*\*



Cases are scored using transparent, rule-based logic and provide competency-level feedback.



The Phase 2 results interface also organizes performance into broader dimensions such as:



\* Problem Understanding

\* Evidence Use

\* Decision Making

\* Business Reasoning

\* Career-Specific Skill



Not every case assesses every dimension; unassessed areas are shown rather than guessed.



\### 5. Interview Room



Practice a structured mock interview consisting of five interview stages:



\* Introduction

\* Experience

\* Role Knowledge

\* Real-World Problem

\* Pressure / Situational



Some questions can generate deterministic follow-up questions based on the student's answer.



Users can answer by typing or, where available, by recording their response.



\### Local Voice Simulation



Voice responses use \*\*faster-whisper locally\*\* for English transcription.



The project is designed so that:



\* Audio is processed locally

\* Raw audio is not written to disk

\* Only the resulting transcript and selected speaking metrics are retained in session state

\* The speaking analysis is a transparent simulation, not an IELTS, CEFR, pronunciation, or accent certification

\* Users can switch back to typed answers if voice transcription is unavailable



The default model is `tiny.en`, with `base.en` also supported.



\### 6. Career Readiness Map



The final page brings together the student's completed activities.



It shows:



\* Quest progress

\* CV performance

\* Skill Challenge performance

\* Case Room performance

\* Interview performance

\* Speaking-simulation information when available

\* A self-rated skill radar

\* Identified strengths

\* Development areas

\* A personalized rule-based 7-day development plan



The final results are presented as \*\*Career Quest Performance / Career Readiness information\*\*, not as employability or hiring predictions.



\## **Progression System**



LeadHer Career Quest also includes a lightweight gamification layer.



The quest system tracks progress through XP and levels:



| Level           |  XP |

| --------------- | --: |

| Quest Starter   |   0 |

| Career Explorer | 100 |

| Skill Builder   | 250 |

| Case Strategist | 400 |

| Interview Ready | 600 |

| Quest Champion  | 800 |



The XP system measures \*\*journey completion and engagement\*\*. It is separate from the actual performance scores produced by the CV, assessment, case, and interview modules.



\## **Technology Stack**



\* \*\*Python\*\*

\* \*\*Streamlit\*\*

\* \*\*Pandas\*\*

\* \*\*Plotly\*\*

\* \*\*pypdf\*\*

\* \*\*faster-whisper\*\*

\* HTML/CSS customization for the UI

\* JSON-based structured content

\* Git / GitHub



\## **Project Structure**



```text

leadHer/

│

├── app.py

├── requirements.txt

├── README.md

├── .gitignore

│

├── .streamlit/

│   └── config.toml

│

├── data/

│   ├── careers.json

│   ├── career\_paths.py

│   ├── questions.json

│   ├── cases.json

│   ├── real\_world\_cases.json

│   ├── interview\_questions.json

│   ├── interview\_cases.json

│   └── role\_profiles.json

│

├── utils/

│   ├── case.py

│   ├── cv.py

│   ├── interview.py

│   ├── navigation.py

│   ├── profile.py

│   ├── quest.py

│   ├── theme.py

│   └── voice.py

│

└── views/

&#x20;   ├── landing.py

&#x20;   ├── career\_goal.py

&#x20;   ├── cv\_readiness.py

&#x20;   ├── assessment.py

&#x20;   ├── case\_challenge.py

&#x20;   ├── interview.py

&#x20;   └── report.py

```



\## **Running Locally**



Clone the repository:



```bash

git clone https://github.com/tasnimj274-ux/leadHer.git

```



Move into the project:



```bash

cd leadHer

```



Create a virtual environment:



```bash

python -m venv .venv

```



Activate it on Windows:



```bash

.venv\\Scripts\\activate

```



Install the dependencies:



```bash

pip install -r requirements.txt

```



Run the application:



```bash

python -m streamlit run app.py

```



Streamlit will provide a local URL such as:



```text

http://localhost:8501

```



\## **Privacy \& Data Handling**



LeadHer Career Quest is currently a session-based prototype.



The application does not use a database for user profiles or quest results. Relevant information is kept in Streamlit's session state during the active session.



The project is designed to avoid unnecessary personal-data collection.



CV files are processed in memory, and recorded interview audio is handled locally for transcription rather than being sent to a third-party API.



\## **Scoring Philosophy**



The current prototype deliberately uses \*\*transparent, explainable scoring rules\*\* rather than pretending to provide intelligent hiring judgments.



Assessment, case, CV, and interview results are intended to answer questions such as:



 What did I do well?



 Where do I need more practice?



 What should I work on next?



They are \*\*not\*\* intended to answer:



 Will I get hired?



The platform does not calculate hiring probability or claim to predict employment outcomes.



\## **Project Status**



\*\*Status: Phase 2 Prototype / MVP Development\*\*



The core end-to-end quest is implemented, including onboarding, skill calibration, CV analysis, assessment, business case, mock interview, voice-based interview support, progression tracking, and the Career Readiness Map.



The architecture is intentionally modular so additional career personas, content banks, assessment questions, cases, and interview scenarios can be added without redesigning the entire application.



\## **Future Direction**



The longer-term vision for LeadHer is to evolve this prototype into a scalable digital career-readiness platform.



Potential future development areas include:



\* More career tracks and specialized content

\* Larger question and case banks

\* Richer feedback and learning resources

\* Gamified progression

\* Personalized learning pathways

\* Portfolio and project-building support

\* Additional practice simulations

\* A broader digital product ecosystem for career development



\## **Social Impact**



LeadHer Career Quest is being developed around a simple idea:



\*\*Career readiness should be something students can practice — not something they are expected to magically have on the day they apply for a job.\*\*



The project focuses on helping students build practical confidence, understand their skill gaps, and approach career preparation more systematically.



\---



**LeadHer Career Quest**
      Discover your strengths. Identify your gaps. Build your readiness.



