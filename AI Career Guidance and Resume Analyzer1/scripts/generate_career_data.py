import json
import os
import random

# Base list of 100+ career titles and their attributes
career_templates = [
    {"t": "Software Engineer", "ind": "Tech", "sk": ["Python", "Java", "SDLC", "Algorithms", "Git"], "tools": ["VS Code", "Jira", "Docker"]},
    {"t": "Data Scientist", "ind": "Tech", "sk": ["Python", "R", "Machine Learning", "Statistics", "SQL"], "tools": ["Jupyter", "Pandas", "TensorFlow"]},
    {"t": "Web Developer", "ind": "Tech", "sk": ["HTML", "CSS", "JavaScript", "React"], "tools": ["VS Code", "Chrome DevTools", "Git"]},
    {"t": "Mobile App Developer", "ind": "Tech", "sk": ["Swift", "Kotlin", "React Native", "UI Design"], "tools": ["Xcode", "Android Studio"]},
    {"t": "DevOps Engineer", "ind": "Tech", "sk": ["Linux", "AWS", "Docker", "Kubernetes", "CI/CD"], "tools": ["Jenkins", "Terraform", "Ansible"]},
    {"t": "Cloud Architect", "ind": "Tech", "sk": ["AWS", "Azure", "Networking", "Security"], "tools": ["CloudFormation", "Terraform"]},
    {"t": "Cybersecurity Analyst", "ind": "Tech", "sk": ["Network Security", "Penetration Testing", "Cryptography"], "tools": ["Kali Linux", "Wireshark", "Metasploit"]},
    {"t": "Database Administrator", "ind": "Tech", "sk": ["SQL", "NoSQL", "Data Modeling", "Backup"], "tools": ["MySQL", "MongoDB", "PostgreSQL"]},
    {"t": "AI Research Scientist", "ind": "Tech", "sk": ["Deep Learning", "NLP", "Computer Vision", "Math"], "tools": ["PyTorch", "TensorFlow", "Hugging Face"]},
    {"t": "Network Engineer", "ind": "Tech", "sk": ["Routing", "Switching", "VPN", "Firewalls"], "tools": ["Cisco IOS", "Packet Tracer"]},
    {"t": "UX Designer", "ind": "Design", "sk": ["Figma", "Prototyping", "User Research", "Wireframing"], "tools": ["Sketch", "Adobe XD"]},
    {"t": "UI Designer", "ind": "Design", "sk": ["Visual Design", "Typography", "Color Theory"], "tools": ["Figma", "Illustrator"]},
    {"t": "Graphic Designer", "ind": "Design", "sk": ["Adobe Photoshop", "Illustrator", "Branding"], "tools": ["Wacom Tablet", "Canva"]},
    {"t": "Product Manager", "ind": "Business", "sk": ["Agile", "Roadmap", "Market Research", "Stakeholder Management"], "tools": ["Jira", "Confluence", "Trello"]},
    {"t": "Project Manager", "ind": "Business", "sk": ["PMP", "Risk Management", "Budgeting", "Leadership"], "tools": ["MS Project", "Asana"]},
    {"t": "Business Analyst", "ind": "Business", "sk": ["Requirements Gathering", "SQL", "Process Modeling"], "tools": ["Visio", "Tableau"]},
    {"t": "Financial Analyst", "ind": "Finance", "sk": ["Excel", "Financial Modeling", "Forecasting"], "tools": ["Bloomberg Terminal", "QuickBooks"]},
    {"t": "Accountant", "ind": "Finance", "sk": ["Taxation", "Auditing", "GAAP"], "tools": ["SAP", "QuickBooks", "Xero"]},
    {"t": "Investment Banker", "ind": "Finance", "sk": ["Valuation", "Mergers & Acquisitions", "Modeling"], "tools": ["Capital IQ", "FactSet"]},
    {"t": "Marketing Manager", "ind": "Marketing", "sk": ["SEO", "Content Strategy", "Branding", "Digital Ads"], "tools": ["Google Analytics", "HubSpot", "Mailchimp"]},
    {"t": "SEO Specialist", "ind": "Marketing", "sk": ["Keyword Research", "Link Building", "Analytics"], "tools": ["SEMrush", "Ahrefs", "Google Search Console"]},
    {"t": "Content Writer", "ind": "Media", "sk": ["Copywriting", "Editing", "Research", "Storytelling"], "tools": ["WordPress", "Grammarly"]},
    {"t": "Journalist", "ind": "Media", "sk": ["Reporting", "Interviewing", "Ethics"], "tools": ["Recording Tools", "CMS"]},
    {"t": "Public Relations Specialist", "ind": "Media", "sk": ["Media Relations", "Crisis Mgmt", "Writing"], "tools": ["Cision", "Social Media"]},
    {"t": "Sales Manager", "ind": "Sales", "sk": ["Negotiation", "CRM", "Lead Gen", "Closing"], "tools": ["Salesforce", "LinkedIn Sales Nav"]},
    {"t": "Real Estate Agent", "ind": "Real Estate", "sk": ["Negotiation", "Property Law", "Marketing"], "tools": ["Zillow", "MLS"]},
    {"t": "Civil Engineer", "ind": "Engineering", "sk": ["AutoCAD", "Structural Analysis", "Project Mgmt"], "tools": ["Revit", "MS Project"]},
    {"t": "Mechanical Engineer", "ind": "Engineering", "sk": ["CAD", "Thermodynamics", " Mechanics"], "tools": ["SolidWorks", "ANSYS"]},
    {"t": "Electrical Engineer", "ind": "Engineering", "sk": ["Circuit Design", "MATLAB", "PLC"], "tools": ["Multisim", "Oscilloscope"]},
    {"t": "Chemical Engineer", "ind": "Engineering", "sk": ["Process Design", "Chemistry", "Safety"], "tools": ["Aspen Plus", "MATLAB"]},
    {"t": "Biomedical Engineer", "ind": "Healthcare", "sk": ["Medical Devices", "Biology", "CAD"], "tools": ["3D Printers", "Lab Equipment"]},
    {"t": "Doctor (GP)", "ind": "Healthcare", "sk": ["Diagnosis", "Patient Care", "Medicine"], "tools": ["EMR Systems", "Stethoscope"]},
    {"t": "Nurse", "ind": "Healthcare", "sk": ["Patient Care", "IV", "EMR", "Critical Thinking"], "tools": ["Medical Equipment", "Epic Systems"]},
    {"t": "Pharmacist", "ind": "Healthcare", "sk": ["Pharmacology", "Dispensing", "Patient Counseling"], "tools": ["Pharmacy Softwares"]},
    {"t": "Psychologist", "ind": "Healthcare", "sk": ["Therapy", "Assessment", "Empathy"], "tools": ["Assessment Tools"]},
    {"t": "Lawyer", "ind": "Legal", "sk": ["Legal Research", "Litigation", "Drafting"], "tools": ["Westlaw", "LexisNexis"]},
    {"t": "Paralegal", "ind": "Legal", "sk": ["Research", "Filing", "Drafting"], "tools": ["Clio", "MyCase"]},
    {"t": "Teacher (High School)", "ind": "Education", "sk": ["Curriculum Dev", "Classroom Mgmt"], "tools": ["Blackboard", "Zoom"]},
    {"t": "Professor", "ind": "Education", "sk": ["Research", "Publishing", "Teaching"], "tools": ["SPSS", "Turnitin"]},
    {"t": "Instructional Designer", "ind": "Education", "sk": ["E-learning", "Storyline", "Pedagogy"], "tools": ["Articulate 360", "Camtasia"]},
    {"t": "Chef", "ind": "Hospitality", "sk": ["Cooking Techniques", "Menu Planning", "Kitchen Mgmt"], "tools": ["Knives", "Commercial Ovens"]},
    {"t": "Hotel Manager", "ind": "Hospitality", "sk": ["Operations", "Guest Services", "Budgeting"], "tools": ["Opera PMS"]},
    {"t": "Event Planner", "ind": "Hospitality", "sk": ["Vendor Mgmt", "Budgeting", "Logistics"], "tools": ["Cvent", "Eventbrite"]},
    {"t": "Pilot", "ind": "Aviation", "sk": ["Avionics", "Navigation", "Safety"], "tools": ["Flight Simulator", "GPS"]},
    {"t": "Flight Attendant", "ind": "Aviation", "sk": ["Safety Procedures", "Customer Service"], "tools": ["Safety Equipment"]},
    {"t": "Automotive Mechanic", "ind": "Automotive", "sk": ["Engine Repair", "Diagnostics"], "tools": ["OBD Scanner", "Hydraulic Lifts"]},
    {"t": "Electrician", "ind": "Trades", "sk": ["Wiring", "Blueprint Reading", "Safety"], "tools": ["Multimeter", "Conduit Benders"]},
    {"t": "Plumber", "ind": "Trades", "sk": ["Pipe Fitting", "Blueprints", "Troubleshooting"], "tools": ["Pipe Wrench", "Video Inspection"]},
    {"t": "Carpenter", "ind": "Trades", "sk": ["Woodworking", "Measurements", "Framing"], "tools": ["Saws", "Drills", "Levels"]},
    {"t": "HVAC Technician", "ind": "Trades", "sk": ["Refrigeration", "Electrical", "Troubleshooting"], "tools": ["Manifold Gauges", "Thermometers"]},
    {"t": "Fashion Designer", "ind": "Fashion", "sk": ["Sketching", "Sewing", "Textiles"], "tools": ["Sewing Machine", "Adobe Illustrator"]},
    {"t": "Interior Designer", "ind": "Design", "sk": ["Space Planning", "CAD", "Color Theory"], "tools": ["AutoCAD", "SketchUp"]},
    {"t": "Animator", "ind": "Entertainment", "sk": ["3D Modeling", "Rigging", "Storytelling"], "tools": ["Blender", "Maya", "After Effects"]},
    {"t": "Video Editor", "ind": "Media", "sk": ["Color Grading", "Transitions", "Storytelling"], "tools": ["Premiere Pro", "DaVinci Resolve"]},
    {"t": "Data Entry Clerk", "ind": "Admin", "sk": ["Typing", "Excel", "Accuracy"], "tools": ["MS Office", "Google Sheets"]},
    {"t": "Executive Assistant", "ind": "Admin", "sk": ["Scheduling", "Communication", "Travel Arrangements"], "tools": ["Outlook", "Teams"]},
    {"t": "Customer Service Rep", "ind": "Support", "sk": ["Problem Solving", "Empathy", "CRM"], "tools": ["Zendesk", "Intercom"]},
    {"t": "HR Manager", "ind": "HR", "sk": ["Recruitment", "Employee Relations", "Payroll"], "tools": ["Workday", "BambooHR"]},
    {"t": "Recruiter", "ind": "HR", "sk": ["Sourcing", "Interviewing", "ATS"], "tools": ["LinkedIn Recruiter", "Greenhouse"]},
    {"t": "Supply Chain Manager", "ind": "Logistics", "sk": ["Logistics", "Inventory", "Procurement"], "tools": ["SAP SCM", "Oracle"]},
    {"t": "Logistics Coordinator", "ind": "Logistics", "sk": ["Shipping", "Scheduling", "Tracking"], "tools": ["SAP", "TMS"]},
    {"t": "Quality Assurance Analyst", "ind": "Tech", "sk": ["Testing", "Bug Tracking", "Automation"], "tools": ["Selenium", "JIRA"]},
    {"t": "Scrum Master", "ind": "Tech", "sk": ["Agile", "Facilitation", "JIRA"], "tools": ["Confluence", "Trello"]},
    {"t": "Technical Writer", "ind": "Tech", "sk": ["Documentation", "API Knowledge", "Markdown"], "tools": ["MadCap Flare", "GitBook"]},
    {"t": "Geologist", "ind": "Science", "sk": ["Field Work", "GIS", "Mapping"], "tools": ["Petrel", "ArcGIS"]},
    {"t": "Environmental Scientist", "ind": "Science", "sk": ["Data Collection", "Regulations", "GIS"], "tools": ["GIS", "Statistical Softwares"]},
    {"t": "Biologist", "ind": "Science", "sk": ["Lab Techniques", "Research", "DNA Sequencing"], "tools": ["Microscopes", "PCR Machines"]},
    {"t": "Physicist", "ind": "Science", "sk": ["Math", "Research", "Modeling"], "tools": ["MATLAB", "Python"]},
    {"t": "Astronomer", "ind": "Science", "sk": ["Telescopes", "Data Analysis", "Physics"], "tools": ["Python", "Telescope Control"]},
    {"t": "Economist", "ind": "Finance", "sk": ["Econometrics", "Statistics", "Forecasting"], "tools": ["Stata", "R", "Excel"]},
    {"t": "Urban Planner", "ind": "Govt", "sk": ["Zoning", "GIS", "Community Dev"], "tools": ["AutoCAD", "ArcGIS"]},
    {"t": "Social Worker", "ind": "Social", "sk": ["Counseling", "Advocacy", "Case Mgmt"], "tools": ["Case Management Software"]},
    {"t": "Translator", "ind": "Linguistics", "sk": ["Fluency", "Cultural Knowledge", "Writing"], "tools": ["CAT Tools", "MemoQ"]},
    {"t": "Interpreter", "ind": "Linguistics", "sk": ["Listening", "Speaking", "Cultural Mediation"], "tools": ["Headsets", "Booths"]},
    {"t": "Fitness Trainer", "ind": "Fitness", "sk": ["Anatomy", "Nutrition", "Exercise Tech"], "tools": ["Fitness Apps", "Equipment"]},
    {"t": "Nutritionist", "ind": "Healthcare", "sk": ["Diet Planning", "Biology", "Counseling"], "tools": ["Nutrition Software"]},
    {"t": "Architect", "ind": "Design", "sk": ["AutoCAD", "Revit", "Building Codes"], "tools": ["Rhino", "V-Ray"]},
    {"t": "Marine Biologist", "ind": "Science", "sk": ["Diving", "Research", "Data Analysis"], "tools": ["Underwater Drones", "GIS"]},
    {"t": "Veterinarian", "ind": "Healthcare", "sk": ["Surgery", "Diagnosis", "Animal Handling"], "tools": ["X-Ray", "Surgical Tools"]},
    {"t": "Dentist", "ind": "Healthcare", "sk": ["Oral Surgery", "Diagnosis", "Patient Care"], "tools": ["Dental Drill", "X-Ray"]},
    {"t": "Radiologist", "ind": "Healthcare", "sk": ["Imaging", "Diagnosis", "Anatomy"], "tools": ["MRI", "CT Scanner"]},
    {"t": "Paramedic", "ind": "Healthcare", "sk": ["Emergency Care", "ALS", "Driving"], "tools": ["Defibrillator", "Stretcher"]},
    {"t": "Forensic Scientist", "ind": "Science", "sk": ["Evidence Analysis", "Lab Techniques"], "tools": ["Microscopes", "DNA Analyzers"]},
    {"t": "Meteorologist", "ind": "Science", "sk": ["Forecasting", "Radar", "Physics"], "tools": ["WRF", "Python"]},
    {"t": "Librarian", "ind": "Education", "sk": ["Cataloging", "Research", "Organization"], "tools": ["ILS", "Dewey Decimal"]},
    {"t": "Archivist", "ind": "Culture", "sk": ["Preservation", "Digitization"], "tools": ["Archival Software"]},
    {"t": "Museum Curator", "ind": "Culture", "sk": ["Art History", "Management", "Research"], "tools": ["Collection Mgmt SW"]},
    {"t": "Art Director", "ind": "Design", "sk": ["Visual Style", "Team Lead", "Branding"], "tools": ["Photoshop", "InDesign"]},
    {"t": "Sound Engineer", "ind": "Media", "sk": ["Mixing", "Mastering", "Audio Edit"], "tools": ["Pro Tools", "Logic Pro"]},
    {"t": "Broadcast Journalist", "ind": "Media", "sk": ["Reporting", "Voice Modulation", "Research"], "tools": ["Teleprompter", "Mic"]},
    {"t": "Social Media Manager", "ind": "Marketing", "sk": ["Content Creation", "Analytics", "Engagement"], "tools": ["Hootsuite", "Buffer"]},
    {"t": "Insurance Agent", "ind": "Finance", "sk": ["Risk Assessment", "Sales", "Underwriting"], "tools": ["Agency Management SW"]},
    {"t": "Loan Officer", "ind": "Finance", "sk": ["Underwriting", "Customer Service", "Analysis"], "tools": ["Loan Origination SW"]},
    {"t": "Compliance Officer", "ind": "Finance", "sk": ["Regulations", "Audit", "Risk Mgmt"], "tools": ["Compliance Software"]},
    {"t": "Operations Manager", "ind": "Business", "sk": ["Process Improvement", "Logistics", "HR"], "tools": ["SAP", "ERP Systems"]},
    {"t": "Training Specialist", "ind": "HR", "sk": ["Curriculum Dev", "Public Speaking"], "tools": ["Zoom", "LMS"]},
    {"t": "Help Desk Technician", "ind": "Support", "sk": ["Troubleshooting", "Windows", "Linux"], "tools": ["TeamViewer", "ServiceNow"]},
    {"t": "Web Administrator", "ind": "Tech", "sk": ["CMS", "HTML", "Server Mgmt"], "tools": ["cPanel", "WordPress"]},
    {"t": "AI Ethics Officer", "ind": "Tech", "sk": ["Ethics", "Policy Making", "AI Knowledge"], "tools": ["Compliance Tools"]},
    {"t": "Blockchain Developer", "ind": "Tech", "sk": ["Solidity", "Cryptography", "Smart Contracts"], "tools": ["Remix IDE", "Ganache"]},
    {"t": "Game Designer", "ind": "Gaming", "sk": ["Level Design", "Storytelling", "Unity"], "tools": ["Unreal Engine", "Unity"]},
    {"t": "Robotics Engineer", "ind": "Engineering", "sk": ["ROS", "C++", "Electronics"], "tools": ["SolidWorks", "Gazebo"]},
]

output_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'career_data.json')
os.makedirs(os.path.dirname(output_path), exist_ok=True)

final_data = []

for i, item in enumerate(career_templates):
    salary = random.randint(50, 200) * 1000
    exp_level = random.choice(["Entry Level", "Mid Level", "Senior Level"])
    
    future = random.choice([
        "High demand expected in the next decade.",
        "Growing steadily with technological advancements.",
        "Stable career path with consistent opportunities.",
        "Rapidly evolving field with high growth potential."
    ])

    day_in_life = random.choice([
        "Meetings, planning, and executing core tasks.",
        "Research, analysis, and reporting.",
        "Hands-on work with tools and technology.",
        "Collaborating with teams and clients."
    ])

    entry = {
        "id": f"career_{i+1}",
        "title": item["t"],
        "description": f"A professional responsible for tasks related to {item['t']} in the {item['ind']} industry.",
        "required_skills": item["sk"],
        "tools": item["tools"],
        "responsibilities": f"Manage and execute key functions of {item['t']}.",
        "salary_range": f"${salary:,} per year",
        "future_scope": future,
        "day_in_life": day_in_life
    }
    final_data.append(entry)

with open(output_path, 'w') as f:
    json.dump(final_data, f, indent=4)

print(f"Successfully generated {len(final_data)} career entries.")
