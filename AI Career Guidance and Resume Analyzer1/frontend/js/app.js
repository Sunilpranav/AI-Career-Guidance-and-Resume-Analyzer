// frontend/js/app.js

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. NAVIGATION & AUTH ---
    const navItems = document.querySelectorAll('.nav-item');
    const contentSections = document.querySelectorAll('.content-section');
    const logoutBtn = document.getElementById('logoutBtn');

    // Check if user is logged in (basic check)
    const token = localStorage.getItem('access_token');
    if (!token && !window.location.pathname.includes('index.html')) {
        // Optional: Redirect to login if no token
        // window.location.href = '/index.html'; 
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetId = item.getAttribute('data-target');
            
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            
            contentSections.forEach(section => {
                section.classList.remove('active-section');
                if (section.id === targetId) {
                    section.classList.add('active-section');
                }
            });
        });
    });

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            // Clear everything on logout
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_id');
            localStorage.removeItem('last_analysis');
            localStorage.removeItem('chat_history');
            window.location.href = '/index.html';
        });
    }

    // --- 2. PERSISTENCE FUNCTIONS ---
    
    function saveToLocal(key, data) {
        localStorage.setItem(key, JSON.stringify(data));
    }

    function loadFromLocal(key) {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    }

    // --- 3. LOAD SAVED DATA ON START ---
    
    // Load Last Analysis
    const savedAnalysis = loadFromLocal('last_analysis');
    if (savedAnalysis) {
        renderResults(savedAnalysis);
        // Switch to results view automatically
        document.querySelector('[data-target="results-section"]').click();
    }

    // Load Chat History
    const savedChat = loadFromLocal('chat_history');
    if (savedChat && savedChat.length > 0) {
        const chatWindow = document.getElementById('chatWindow');
        if(chatWindow) {
            chatWindow.innerHTML = ''; // Clear default
            savedChat.forEach(msg => {
                appendMessage(msg.role, msg.content, false); // false = don't save again
            });
        }
    }

    // --- 4. RESUME UPLOAD ---

    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const fileNameDisplay = document.getElementById('fileName');
    const resultContainer = document.getElementById('resultContainer');

    let selectedFile = null;

    if (uploadArea) {
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            selectedFile = e.dataTransfer.files[0];
            if (selectedFile) {
                fileNameDisplay.textContent = selectedFile.name;
                fileNameDisplay.style.display = 'block';
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            selectedFile = e.target.files[0];
            if (selectedFile) {
                fileNameDisplay.textContent = selectedFile.name;
                fileNameDisplay.style.display = 'block';
            }
        });
    }

    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async () => {
            if (!selectedFile) {
                alert('Please select a file first!');
                return;
            }

            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '<div class="spinner"></div> Analyzing...';

            const formData = new FormData();
            formData.append('file', selectedFile);
            
            // Get user_id from local storage or default to 1
            const userId = loadFromLocal('user_id') || 1;
            
            try {
                const response = await fetch(`/analysis/upload/${userId}`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Analysis failed');
                
                const data = await response.json();
                
                // SAVE TO LOCAL STORAGE
                saveToLocal('last_analysis', data);
                
                renderResults(data);
                
                // Clear chat history on new analysis
                localStorage.removeItem('chat_history');
                document.getElementById('chatWindow').innerHTML = '<div class="loader-container"><div class="spinner"></div><p>Analyzing...</p></div>';

                // Switch to results tab
                document.querySelector('[data-target="results-section"]').click();

            } catch (error) {
                console.error(error);
                alert('Error analyzing resume.');
            } finally {
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = 'Analyze Resume';
            }
        });
    }

    // --- 5. RENDER RESULTS ---
    
    function renderResults(data) {
        try {
            // 0. ATS
            const atsScore = data.ats_score || 0;
            const atsFeedback = data.ats_feedback || [];
            const atsContainer = document.getElementById("atsScoreDisplay");
            if(atsContainer) {
                atsContainer.innerHTML = `
                    <div class="ats-circle" style="background: conic-gradient(#4f46e5 ${atsScore}%, #e2e8f0 0)">
                        <span>${atsScore}%</span>
                    </div>
                    <p class="ats-label">ATS Score</p>
                    <ul class="ats-feedback">
                        ${atsFeedback.map(f => `<li>${f}</li>`).join('')}
                    </ul>
                `;
            }

            // 1. Skills
            const skillsContainer = document.getElementById("skillsList");
            if (data.skills && data.skills.length > 0) {
                const skillsHtml = data.skills.map(s => `<div class="skill-tag">${s}</div>`).join('');
                skillsContainer.innerHTML = skillsHtml;
            } else {
                skillsContainer.innerHTML = `<p style="color:#64748b;">No specific skills detected.</p>`;
            }

            // 2. Chart
            const ctx = document.getElementById('skillsChart').getContext('2d');
            if(window.skillChartInstance) window.skillChartInstance.destroy();
            
            const chartLabels = (data.skills && data.skills.length > 0) ? data.skills.slice(0, 6) : ["No Skills"];
            
            window.skillChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: chartLabels,
                    datasets: [{
                        label: 'Skill Match',
                        data: chartLabels.map(() => Math.floor(Math.random() * 20) + 80),
                        backgroundColor: 'rgba(79, 70, 229, 0.7)',
                        borderRadius: 6,
                    }]
                },
                options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } } }
            });

            // 3. Recommendations
            const recText = data.recommendations || "No recommendations generated.";
            if (typeof marked !== 'undefined') {
                document.getElementById("careerRec").innerHTML = marked.parse(recText);
            } else {
                document.getElementById("careerRec").innerHTML = `<pre>${recText}</pre>`;
            }

            // 4. Roadmap
            const roadmapContainer = document.getElementById("roadmapList");
            let roadmapHtml = "";
            const lines = recText.split('\n');
            const steps = [];

            lines.forEach(line => {
                let cleanLine = line.trim();
                if (cleanLine.match(/Step\s\d+:/) || cleanLine.match(/^\d+\.\s/)) {
                    let finalStep = cleanLine.replace(/^(Step\s\d+:|^\d+\.)\s*/, '').replace(/\*\*/g, '');
                    steps.push(finalStep);
                }
            });

            if(steps.length > 0) {
                roadmapHtml = `<div class="roadmap-highway">`;
                steps.forEach((step, index) => {
                    let cleanStep = step;
                    let techIcon = "🎯"; let techLabel = "Goal";
                    let lowerStep = cleanStep.toLowerCase();
                    if(lowerStep.includes("python") || lowerStep.includes("code")) { techIcon = "💻"; techLabel = "Coding"; }
                    else if(lowerStep.includes("cloud")) { techIcon = "☁️"; techLabel = "Cloud"; }
                    else if(lowerStep.includes("data")) { techIcon = "📊"; techLabel = "Data"; }
                    else if(lowerStep.includes("learn") || lowerStep.includes("course")) { techIcon = "📚"; techLabel = "Learn"; }
                    else if(lowerStep.includes("project") || lowerStep.includes("build")) { techIcon = "🛠️"; techLabel = "Build"; }

                    roadmapHtml += `
                        <div class="roadmap-milestone" style="--delay: ${index * 0.2}s">
                            <div class="milestone-icon">${techIcon}<span class="icon-label">${techLabel}</span></div>
                            <div class="milestone-content"><h4>Step ${index + 1}</h4><p>${cleanStep}</p></div>
                        </div>
                    `;
                });
                roadmapHtml += `</div>`;
            } else {
                roadmapHtml = `<p style='padding:20px; text-align:center; color:#666;'>Roadmap steps not detected.</p>`;
            }
            if (roadmapContainer) roadmapContainer.innerHTML = roadmapHtml;

        } catch (error) {
            console.error("Rendering Error:", error);
        }
    }

    // --- 6. CHAT SYSTEM ---

    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatWindow = document.getElementById('chatWindow');
    let chatHistory = loadFromLocal('chat_history') || [];

    function appendMessage(role, content, save=true) {
        const row = document.createElement('div');
        row.className = `message-row ${role === 'user' ? 'user-row' : 'bot-row'}`;
        
        const avatar = role === 'user' ? '👤' : '🤖';
        const name = role === 'user' ? 'You' : 'CareerAI Bot';
        
        row.innerHTML = `
            <div class="avatar">${avatar}</div>
            <div class="message-bubble">
                <p>${content}</p>
                <span class="timestamp">Just now</span>
            </div>
        `;
        
        if(chatWindow) {
            // Remove loader if exists
            const loader = chatWindow.querySelector('.loader-container');
            if(loader) loader.remove();
            
            chatWindow.appendChild(row);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }

        // Save to history
        if (save) {
            chatHistory.push({ role, content });
            saveToLocal('chat_history', chatHistory);
        }
    }

    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            appendMessage('user', message);
            chatInput.value = '';

            // Show typing indicator
            const typing = document.createElement('div');
            typing.className = 'message-row bot-row';
            typing.innerHTML = `<div class="avatar">🤖</div><div class="message-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`;
            chatWindow.appendChild(typing);

            try {
                const response = await fetch('/analysis/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `query=${encodeURIComponent(message)}&history=${encodeURIComponent(JSON.stringify(chatHistory))}`
                });

                if (!response.ok) throw new Error('Chat failed');
                
                // Remove typing indicator
                typing.remove();

                // Read stream
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let botMsg = '';
                
                // Create placeholder
                const botRow = document.createElement('div');
                botRow.className = 'message-row bot-row';
                botRow.innerHTML = `<div class="avatar">🤖</div><div class="message-bubble"><p></p></div>`;
                chatWindow.appendChild(botRow);
                const botP = botRow.querySelector('p');

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value);
                    botMsg += chunk;
                    botP.innerHTML += chunk;
                    chatWindow.scrollTop = chatWindow.scrollHeight;
                }

                // Save final bot message
                chatHistory.push({ role: 'bot', content: botMsg });
                saveToLocal('chat_history', chatHistory);

            } catch (err) {
                console.error(err);
                const typing = document.querySelector('.typing-indicator');
                if(typing) typing.parentElement.parentElement.remove();
                appendMessage('bot', 'Error connecting to server.');
            }
        });
    }
});
