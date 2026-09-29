"""Single source of truth for Freelancer portfolio items (form limits checked in make_portfolio_pack.py).

Freelancer "Create a portfolio item" form: title ≤ 36 chars, description ≤ 2000 chars,
tags, tools & software, skills, industry. No URL field → links go inside the description.
Every fact below comes from the project READMEs or your published Freelancer profile.
"""

ITEMS = [
    {
        "slug": "01-ai-receptionist",
        "title": "WhatsApp AI Receptionist & Booking",
        "card_title": "AI Receptionist",
        "card_sub": "WhatsApp · Instagram · Messenger · X — answers 24/7, books appointments, replies with voice",
        "chips": ["Azure OpenAI", "WhatsApp API", "Graph API", ".NET"],
        "description": """Problem: small businesses miss customer messages and bookings outside working hours, and staff lose time answering the same questions on four different apps.

What I built: an AI receptionist that answers customers 24/7 on WhatsApp, Messenger, Instagram and X from one system.

Key features:
• Understands natural-language questions and answers from the business's own information
• Checks real availability in Outlook / Microsoft 365 and books the appointment
• Sends a confirmation email with a calendar invite (.ics), then automatic reminders and follow-ups
• Replies with voice notes in English or Urdu (speech-to-text + neural voice)
• Web dashboard: owner sees every conversation and can take over at any time
• Channel credentials stored encrypted; CI/CD with GitHub Actions; deployed on Azure

How it works: channel webhook (Meta Graph API / Twilio) → Azure OpenAI understands the request → Microsoft Graph checks the calendar and books → MailKit sends the confirmation → dashboard logs everything.

Stack: Azure OpenAI, Azure AI Speech, Microsoft Graph, Meta Graph API, Twilio, C# / .NET, ASP.NET Core, Blazor Server, SQLite, GitHub Actions, Azure.

Good fit for: clinics, salons, agencies, shops, restaurants — any business that takes bookings over chat.

Code: github.com/dheerajkumar47/AI-receptionist""",
        "tags": ["ai receptionist", "whatsapp bot", "chatbot", "appointment booking", "voice ai", "customer support", "automation"],
        "tools": ["Azure OpenAI", "Azure AI Speech", "Microsoft Graph", "Twilio", ".NET", "Blazor", "GitHub Actions"],
        "skills": ["AI Chatbot", "WhatsApp API", "AI Agents", "Azure", "Automation", "C# Programming"],
        "industry": "Small business / Customer service",
        "flow": [
            ("Customer messages", "WhatsApp, Instagram, Messenger or X — text or voice note"),
            ("Channel webhooks", "Meta Graph API and Twilio deliver every message to one backend"),
            ("Azure OpenAI", "Understands the request and answers from the business's own info"),
            ("Microsoft Graph", "Checks Outlook free/busy and books the appointment"),
            ("Confirm & remind", "Email with .ics invite, reminders, English/Urdu voice replies"),
            ("Owner dashboard", "Blazor dashboard to monitor chats and take over anytime"),
        ],
    },
    {
        "slug": "02-cctv-tracking",
        "title": "CCTV Employee Tracking: YOLO+ArUco",
        "card_title": "Real-Time CCTV Tracking",
        "card_sub": "Live RTSP cameras · YOLO person detection · ArUco employee ID · trails & heatmaps",
        "chips": ["YOLO", "OpenCV", "CUDA", "Python"],
        "description": """Problem: a factory wanted to know where each employee is and how people move across the floor — using the CCTV cameras it already had, in real time.

What I built: a real-time computer-vision tracking system that runs on live camera feeds.

Key features:
• Threaded capture of multiple RTSP camera streams
• Person detection with YOLO, GPU-accelerated with CUDA
• Employee identification with ArUco markers (marker matched to the detected person before tracking)
• Movement trails and a separate MP4 recording per employee
• Heatmaps and map analysis to show where time is spent
• Live web dashboard with camera feeds and CPU / RAM / GPU telemetry
• JSON / CSV logs for reporting

How it works: RTSP feeds → YOLO detects people → ArUco identifies the employee → tracker builds trails and clips → heatmaps + live dashboard.

Stack: Python, YOLO, OpenCV (ArUco), CUDA, RTSP, HTML/JavaScript dashboard.

Good fit for: factories, warehouses, retail stores, offices — people counting, zone monitoring, safety and time-on-task analytics.

Code: github.com/dheerajkumar47/Gumcorp""",
        "tags": ["computer vision", "cctv", "object detection", "people tracking", "yolo", "video analytics", "real-time"],
        "tools": ["YOLO", "OpenCV", "CUDA", "Python", "RTSP"],
        "skills": ["Computer Vision", "OpenCV", "Python", "Deep Learning", "Machine Learning (ML)"],
        "industry": "Manufacturing",
        "flow": [
            ("RTSP camera feeds", "Threaded capture from multiple CCTV cameras"),
            ("YOLO detection", "Person detection on GPU (CUDA)"),
            ("ArUco identification", "Marker matched to each detected person → employee ID"),
            ("Tracking", "Movement trails + one MP4 recording per employee"),
            ("Analytics", "Heatmaps and map analysis, JSON/CSV logs"),
            ("Live dashboard", "Camera feeds with CPU / RAM / GPU telemetry"),
        ],
    },
    {
        "slug": "03-rag-langgraph",
        "title": "RAG Chatbot with LangGraph Agent",
        "card_title": "RAG Chatbot + LangGraph Router",
        "card_sub": "An agent that picks vector search or web search, then answers from real sources",
        "chips": ["LangGraph", "Pinecone", "FastAPI", "Gemini"],
        "description": """Problem: students wasted time digging through long PDF course catalogues to find prerequisites and which courses cover a topic.

What I built: an AI course advisor that answers questions like "What are the prerequisites for Software Engineering?" or "Which courses cover Python?" in seconds.

Key features:
• LangGraph agent with 4 nodes: router, course retriever, web search, answer generator
• Router classifies each question and sends it to the right tool
• Retrieval-Augmented Generation over the catalogue (Pinecone vector database + all-MiniLM-L6-v2 embeddings)
• Live web search (Tavily) for general questions outside the catalogue
• Answers generated by Google Gemini from the retrieved context — grounded, not guessed
• FastAPI REST API with typed request/response models and a web UI with query history

How it works: question → LangGraph router → Pinecone retriever or Tavily web search → Gemini writes the answer from that context → FastAPI returns it.

Stack: Python, FastAPI, LangChain, LangGraph, Pinecone, Hugging Face embeddings, Google Gemini, Tavily.

Same pattern works for: company knowledge bases, HR/policy assistants, product documentation bots, customer-support chat over your PDFs and website.

Code: github.com/dheerajkumar47/IntelliCourse""",
        "tags": ["rag", "chatbot", "langgraph", "ai agent", "vector database", "knowledge base", "llm"],
        "tools": ["LangChain", "LangGraph", "Pinecone", "FastAPI", "Google Gemini", "Tavily", "Hugging Face"],
        "skills": ["LangChain", "AI Chatbot", "Large Language Models", "FastAPI", "Python", "AI Agents"],
        "industry": "Education",
        "flow": [
            ("User question", "Asked in the web UI"),
            ("LangGraph router", "Classifies the question and picks a tool"),
            ("Course retriever", "Pinecone vector search with MiniLM embeddings"),
            ("Web search", "Tavily for general questions outside the catalogue"),
            ("Gemini generator", "Writes the answer from the retrieved context"),
            ("FastAPI response", "Typed API + query history in the UI"),
        ],
    },
    {
        "slug": "04-psx-dashboard",
        "title": "AI Stock Market Dashboard (PSX)",
        "card_title": "AI Stock Market Dashboard (PSX)",
        "card_sub": "Live Pakistan Stock Exchange data + AI daily summaries and SWOT per company",
        "chips": ["FastAPI", "React", "MongoDB", "Gemini"],
        "description": """Problem: investors in Pakistan have no single place that combines live PSX market data with clear, readable analysis of each company.

What I built: an investor-grade intelligence platform for PSX-listed companies, live on the web.

Key features:
• Live market dashboard: real-time price and volume tracking
• Sector heatmaps (Cement, Textiles, Banks and more) and USD/PKR monitoring
• "Market Pulse": daily AI-generated summaries that explain market movements in plain language
• Automated SWOT (Strengths, Weaknesses, Opportunities, Threats) report for each company
• Watchlist, smart filtering by sector or ticker, dark mode
• Secure login with OAuth + JWT

How it works: market data → async FastAPI backend + MongoDB → Google Gemini generates summaries and SWOT → React dashboard.

Stack: FastAPI (Python, async), MongoDB, Google Gemini, React, Vite, Tailwind CSS, OAuth, JWT. Frontend on Vercel, API on Render.

Good fit for: fintech dashboards, market research tools, any product that turns raw data into AI-written insight.

Live demo: pak-industry-insight.vercel.app
Code: github.com/dheerajkumar47/PAK_Industry_Insight""",
        "tags": ["stock market", "dashboard", "fintech", "ai analysis", "data visualization", "llm", "web app"],
        "tools": ["FastAPI", "React", "MongoDB", "Google Gemini", "Tailwind CSS", "Vercel", "Render"],
        "skills": ["FastAPI", "React.js", "MongoDB", "Large Language Models", "Data Visualization"],
        "industry": "Finance",
        "flow": [
            ("Market data", "Live PSX prices, volume and USD/PKR"),
            ("FastAPI backend", "Async Python API with MongoDB storage"),
            ("Google Gemini", "Daily Market Pulse summaries + SWOT per company"),
            ("React dashboard", "Heatmaps, watchlist, sector and ticker filters"),
            ("Secure & live", "OAuth + JWT · Vercel frontend · Render API"),
        ],
    },
    {
        "slug": "05-interview-agents",
        "title": "Multi-Agent AI Interview Platform",
        "card_title": "Multi-Agent Interview Platform",
        "card_sub": "4 AI agents · ATS resume scoring · coding, MCQ and behavioural rounds",
        "chips": ["Next.js", "Gemini", "Groq", "Supabase"],
        "description": """Problem: job candidates need realistic interview practice and honest feedback before they apply — generic question lists don't prepare them.

What I built: an automated mock-interview platform where several AI agents run the full hiring process.

Key features:
• 4 specialised AI agents: Resume Analyst, Technical Interviewer, Knowledge Assessor, HR Coach
• ATS scoring of the resume against a specific job description
• Mixed rounds: coding challenges, multiple-choice questions and behavioural prompts
• Detailed analytics and a final "Readiness Verdict"
• Real-time interview flow with Socket.io
• Reliability by design: Google Gemini as the main model with automatic fallback to Groq (Llama 3.3)

How it works: resume + job description → Resume Analyst scores it → technical and knowledge rounds → HR Coach behavioural round → readiness report.

Stack: Next.js 14, TypeScript, Tailwind CSS, Node.js, Express, Socket.io, Google Gemini, Groq, Supabase / PostgreSQL. Deployed on Vercel and Render.

Good fit for: HR-tech, recruitment agencies, bootcamps and universities — any multi-agent workflow where each agent has one clear job.

Code: github.com/dheerajkumar47/Interview-Pilot""",
        "tags": ["multi-agent", "ai interview", "ats", "resume screening", "hr tech", "llm", "web app"],
        "tools": ["Next.js", "Node.js", "Socket.io", "Google Gemini", "Groq", "Supabase"],
        "skills": ["AI Agents", "Large Language Models", "Next.js", "Node.js", "AI Development"],
        "industry": "Human resources / Recruitment",
        "flow": [
            ("Resume + job description", "Candidate uploads CV and target role"),
            ("Resume Analyst agent", "ATS score against the job description"),
            ("Technical + Knowledge agents", "Coding challenges and MCQ rounds"),
            ("HR Coach agent", "Behavioural questions and feedback"),
            ("Readiness verdict", "Analytics report · Gemini with Groq fallback"),
        ],
    },
    {
        "slug": "06-meeting-intelligence",
        "title": "AI Meeting Intelligence (Whisper)",
        "card_title": "AI Meeting Intelligence",
        "card_sub": "Whisper transcripts → ask questions about any past meeting, with grounded answers",
        "chips": ["Whisper", "RAG", "FastAPI", "Python"],
        "description": """Problem: important decisions and action items get lost in hours of meeting recordings that nobody has time to re-watch.

What I built: an AI meeting assistant that transcribes recordings with Whisper and lets you ask questions about every past meeting — answers come from the actual transcripts (grounded RAG), not from guesses.

Key features:
• Automatic transcription of meeting recordings (Whisper)
• Transcripts indexed so every meeting becomes searchable
• Ask in plain language: "What did we decide about pricing?", "Who owns the follow-up?"
• Grounded answers built only from the relevant parts of the transcripts

How it works: recording → Whisper transcript → transcripts indexed for retrieval → your question → most relevant passages retrieved → answer written from them.

Stack: Python, Whisper (speech-to-text), Retrieval-Augmented Generation, FastAPI.

Good fit for: teams, agencies, consultants and call centres that want searchable meetings, calls, interviews or podcasts.""",
        "tags": ["speech to text", "transcription", "rag", "meeting assistant", "llm", "search"],
        "tools": ["Whisper", "Python", "FastAPI"],
        "skills": ["Speech Recognition", "Large Language Models", "Python", "AI Development"],
        "industry": "Business services / Productivity",
        "flow": [
            ("Meeting recording", "Audio or video from any meeting"),
            ("Whisper", "Speech-to-text transcript"),
            ("Index", "Transcripts made searchable for retrieval"),
            ("Your question", "Plain-language question about any meeting"),
            ("Grounded answer", "Written only from the retrieved transcript passages"),
        ],
    },
    {
        "slug": "07-ai-qa-platform",
        "title": "AI QA Platform: Agents Write Tests",
        "card_title": "AI QA Platform",
        "card_sub": "Agents turn tickets and screenshots into test cases, run UI & API tests, report results",
        "chips": ["AI Agents", "LLM", "API Testing", "Python"],
        "description": """Problem: writing and maintaining test cases by hand is slow, so new features often ship with thin test coverage.

What I built: a multi-agent QA platform where AI agents turn tickets and screenshots into test cases, run UI and API tests, and report the results.

Key features:
• Agents read tickets and screenshots and generate structured test cases
• Automated UI and API test execution
• Clear result reports so the team sees what passed, what failed and why
• Multi-agent design: each agent has one job (understand, generate, execute, report)

How it works: ticket + screenshots → test-case generation agent → execution agent runs UI/API tests → reporting agent summarises results.

Stack: Python, LLM-based AI agents, UI and API test automation.

Good fit for: software teams and agencies that want faster QA, regression suites and better coverage without hiring more testers.""",
        "tags": ["qa automation", "test cases", "ai agents", "api testing", "software testing", "llm"],
        "tools": ["Python", "LLM APIs"],
        "skills": ["AI Agents", "Software Testing", "API Testing", "Python", "Automation"],
        "industry": "Software / IT",
        "flow": [
            ("Tickets + screenshots", "Feature tickets and UI screenshots as input"),
            ("Generation agent", "Writes structured test cases"),
            ("Execution agent", "Runs UI and API tests"),
            ("Reporting agent", "Pass / fail summary with reasons"),
        ],
    },
    {
        "slug": "08-anomaly-detection",
        "title": "Time-Series Anomaly Detection",
        "card_title": "Time-Series Anomaly Detection",
        "card_sub": "Server, finance & IoT anomalies · Prophet + Isolation Forest · FastAPI + Streamlit",
        "chips": ["Prophet", "scikit-learn", "FastAPI", "Docker"],
        "description": """Problem: spikes, drops and odd patterns in server metrics, financial transactions or IoT sensors are easy to miss until they cause damage.

What I built: an anomaly-detection system for time-series data with two complementary models and a proper evaluation setup.

Key features:
• Prophet (Meta) detects breaks in trend and seasonality
• Isolation Forest (scikit-learn) finds unsupervised outliers
• Evaluation with Precision, Recall, F1-score and AUC-ROC
• Built-in data generator for Financial, Server and Sensor scenarios
• Resource profiling (training time, memory use)
• FastAPI backend, interactive Streamlit dashboard with Plotly charts
• Dockerised with Docker Compose — production-ready template

How it works: time-series data → Prophet + Isolation Forest → anomalies scored and evaluated → FastAPI serves results → Streamlit dashboard visualises them.

Stack: Python, Prophet, scikit-learn, Pandas, NumPy, FastAPI, Streamlit, Plotly, Docker.

Good fit for: DevOps monitoring, fraud detection, IoT and sensor monitoring, forecasting.

Code: github.com/dheerajkumar47/Time-Series-Anomaly-Detection""",
        "tags": ["anomaly detection", "time series", "machine learning", "forecasting", "iot", "monitoring", "data science"],
        "tools": ["Prophet", "scikit-learn", "Pandas", "FastAPI", "Streamlit", "Plotly", "Docker"],
        "skills": ["Machine Learning (ML)", "Data Science", "Python", "FastAPI", "Statistical Analysis"],
        "industry": "IT operations / Finance / IoT",
        "flow": [
            ("Time-series data", "Server metrics, financial transactions or IoT sensors"),
            ("Prophet", "Detects trend and seasonality breaks"),
            ("Isolation Forest", "Finds unsupervised outliers"),
            ("Evaluation", "Precision, Recall, F1 and AUC-ROC"),
            ("FastAPI + Streamlit", "API plus interactive Plotly dashboard, Dockerised"),
        ],
    },
]
