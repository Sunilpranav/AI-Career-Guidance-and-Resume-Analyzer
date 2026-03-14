const API = "http://127.0.0.1:8000";
let conversationHistory = [];

document.addEventListener("DOMContentLoaded", () => {
    const userId = localStorage.getItem("user_id");
    const currentPage = window.location.pathname.split("/").pop();

    if (userId && currentPage === "index.html") {
        window.location.href = "dashboard.html";
    } else if (!userId && currentPage === "dashboard.html") {
        window.location.href = "index.html";
    } else if (userId) {
        document.getElementById("userName").innerText = localStorage.getItem("username") || "Student";
    }
});

document.getElementById("loginBtn")?.addEventListener("click", async () => {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);
    try {
        const res = await fetch(`${API}/auth/login`, { method: "POST", body: formData });
        if(res.ok) {
            const data = await res.json();
            localStorage.setItem("user_id", data.user_id);
            localStorage.setItem("username", data.username);
            window.location.href = "dashboard.html";
        } else {
            const err = await res.json();
            alert(err.detail || "Login failed");
        }
    } catch (e) { alert("Server connection error"); }
});

document.getElementById("registerBtn")?.addEventListener("click", async () => {
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    if(!email) return alert("Please enter an email.");
    const formData = new FormData();
    formData.append("username", username);
    formData.append("email", email);
    formData.append("password", password);
    try {
        const res = await fetch(`${API}/auth/register`, { method: "POST", body: formData });
        if(res.ok) { alert("Registration successful! Please login."); } 
        else { const err = await res.json(); alert(err.detail || "Registration failed"); }
    } catch (e) { alert("Server connection error"); }
});

function logout() { localStorage.clear(); window.location.href = "index.html"; }

function showSection(name) {
    document.querySelectorAll(".content-section").forEach(s => s.style.display = "none");
    document.getElementById(name + "-section").style.display = "block";
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    event.currentTarget.classList.add("active");
}

document.getElementById("resumeFile")?.addEventListener("change", function() {
    const fileName = this.files[0]?.name;
    if(fileName) { document.getElementById("fileNameDisplay").innerText = `Selected: ${fileName}`; }
});

async function analyzeResume() {
    const fileInput = document.getElementById("resumeFile");
    const userId = localStorage.getItem("user_id");
    if(!fileInput.files.length) return alert("Please select a file first!");
    
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    document.getElementById("loader").style.display = "block";
    document.getElementById("results-section").style.display = "none";

    try {
        const res = await fetch(`${API}/analysis/upload/${userId}`, { method: "POST", body: formData });
        if (!res.ok) throw new Error("Server returned error");
        
        const data = await res.json();

        document.getElementById("loader").style.display = "none";
        renderResults(data);
        showSection('results');
        
        const navItems = document.querySelectorAll(".nav-item");
        navItems.forEach(n => n.classList.remove("active"));
        if(navItems[2]) navItems[2].classList.add("active");

    } catch (e) {
        document.getElementById("loader").style.display = "none";
        console.error(e);
        alert("Analysis failed. Make sure the server is running.");
    }
}

function renderResults(data) {
    try {
        // 1. Skills
        const skillsHtml = (data.skills || []).map(s => `<div class="skill-tag">${s}</div>`).join('');
        document.getElementById("skillsList").innerHTML = skillsHtml;

        // 2. Chart
        const ctx = document.getElementById('skillsChart').getContext('2d');
        if(window.skillChartInstance) window.skillChartInstance.destroy();
        window.skillChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: (data.skills || []).slice(0, 8),
                datasets: [{
                    label: 'Relevance',
                    data: (data.skills || []).slice(0, 8).map(() => Math.floor(Math.random() * 30) + 70),
                    backgroundColor: 'rgba(79, 70, 229, 0.7)',
                }]
            },
            options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, max: 100 } } }
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

        // Find lines starting with "Step"
        lines.forEach(line => {
            if (line.trim().match(/^Step\s\d+:/)) {
                steps.push(line.trim());
            }
        });

        if(steps.length > 0) {
            roadmapHtml = `<div class="roadmap-highway">`;
            steps.forEach((step, index) => {
                let cleanStep = step.replace(/^Step\s\d+:\s*/, '');
                let techIcon = "🎯"; let techLabel = "Goal";
                let lowerStep = cleanStep.toLowerCase();
                if(lowerStep.includes("python") || lowerStep.includes("code")) { techIcon = "💻"; techLabel = "Coding"; }
                else if(lowerStep.includes("cloud")) { techIcon = "☁️"; techLabel = "Cloud"; }
                else if(lowerStep.includes("ai") || lowerStep.includes("machine learning")) { techIcon = "🤖"; techLabel = "AI"; }
                else if(lowerStep.includes("data")) { techIcon = "📊"; techLabel = "Data"; }
                else if(lowerStep.includes("learn")) { techIcon = "📚"; techLabel = "Learn"; }
                else if(lowerStep.includes("project") || lowerStep.includes("build")) { techIcon = "🛠️"; techLabel = "Build"; }

                let sideClass = index % 2 === 0 ? "left-side" : "right-side";
                roadmapHtml += `
                    <div class="roadmap-milestone ${sideClass}" style="--delay: ${index * 0.4}s">
                        <div class="milestone-icon">${techIcon}<span class="icon-label">${techLabel}</span></div>
                        <div class="milestone-content"><h4>Step ${index + 1}</h4><p>${cleanStep}</p></div>
                    </div>
                `;
            });
            roadmapHtml += `</div>`;
        } else {
            roadmapHtml = `<p style='padding:20px; text-align:center; color:#666;'>Roadmap steps not detected in text.</p>`;
        }
        if (roadmapContainer) roadmapContainer.innerHTML = roadmapHtml;

    } catch (error) {
        console.error("Rendering Error:", error);
    }
}

function handleEnter(e) { if(e.key === 'Enter') sendChat(); }

async function sendChat() {
    const input = document.getElementById("chatInput");
    const chatWindow = document.getElementById("chatWindow");
    const query = input.value;
    if(!query) return;
    
    const userHTML = `<div class="message-row user-row"><div class="avatar">👤</div><div class="message-bubble">${query}<span class="timestamp">Just now</span></div></div>`;
    chatWindow.innerHTML += userHTML;
    conversationHistory.push({ role: 'user', content: query });

    const botId = "bot-" + Date.now();
    const botHTML = `<div class="message-row bot-row" id="${botId}"><div class="avatar">🤖</div><div class="message-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div></div>`;
    chatWindow.innerHTML += botHTML;
    chatWindow.scrollTop = chatWindow.scrollHeight;
    input.value = "";

    const botBubble = document.querySelector(`#${botId} .message-bubble`);
    let fullResponse = "";
    const formData = new FormData();
    formData.append("query", query);
    formData.append("history", JSON.stringify(conversationHistory));

    try {
        const response = await fetch(`${API}/analysis/chat`, { method: "POST", body: formData });
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        botBubble.innerHTML = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            fullResponse += chunk;
            if (typeof marked !== 'undefined') botBubble.innerHTML = marked.parse(fullResponse);
            else botBubble.innerHTML = fullResponse;
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
        botBubble.innerHTML += `<span class="timestamp">CareerAI Bot</span>`;
        conversationHistory.push({ role: 'assistant', content: fullResponse });
    } catch (e) {
        botBubble.innerHTML = "<span style='color:red'>Error connecting to AI.</span>";
    }
}
