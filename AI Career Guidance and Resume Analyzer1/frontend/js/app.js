const API = ""; // Leave this empty to use the current server

document.addEventListener("DOMContentLoaded", () => {
    // Initial check if user is logged in
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

// --- Auth Logic ---

document.getElementById("loginBtn")?.addEventListener("click", async () => {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    
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
    } catch (e) {
        alert("Server connection error");
    }
});

document.getElementById("registerBtn")?.addEventListener("click", async () => {
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    
    if(!email) return alert("Please enter an email for registration.");

    const formData = new FormData();
    formData.append("username", username);
    formData.append("email", email);
    formData.append("password", password);

    try {
        const res = await fetch(`${API}/auth/register`, { method: "POST", body: formData });
        if(res.ok) {
            alert("Registration successful! Please login.");
        } else {
            const err = await res.json();
            alert(err.detail || "Registration failed");
        }
    } catch (e) {
        alert("Server connection error");
    }
});

function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}

// --- Dashboard Logic ---

function showSection(name) {
    document.querySelectorAll(".content-section").forEach(s => s.style.display = "none");
    document.getElementById(name + "-section").style.display = "block";
    
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    event.currentTarget.classList.add("active");
}

// File input display
document.getElementById("resumeFile")?.addEventListener("change", function() {
    const fileName = this.files[0]?.name;
    if(fileName) {
        document.getElementById("fileNameDisplay").innerText = `Selected: ${fileName}`;
    }
});

async function analyzeResume() {
    const fileInput = document.getElementById("resumeFile");
    const userId = localStorage.getItem("user_id");
    
    if(!fileInput.files.length) return alert("Please select a file first!");
    
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    // Show Loader
    document.getElementById("loader").style.display = "block";
    document.getElementById("results-section").style.display = "none";

    try {
        const res = await fetch(`${API}/analysis/upload/${userId}`, { method: "POST", body: formData });
        const data = await res.json();

        // Hide Loader
        document.getElementById("loader").style.display = "none";
        
        renderResults(data);
        showSection('results');
        
        // Update Active Nav
        document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
        document.querySelectorAll(".nav-item")[2].classList.add("active"); // Index 2 is Results

    } catch (e) {
        document.getElementById("loader").style.display = "none";
        alert("Analysis failed. Make sure the server is running.");
    }
}

function renderResults(data) {
    // 1. Skills Tags
    const skillsHtml = data.skills.map(s => `<div class="skill-tag">${s}</div>`).join('');
    document.getElementById("skillsList").innerHTML = skillsHtml;

    // 2. Chart
    const ctx = document.getElementById('skillsChart').getContext('2d');
    if(window.skillChartInstance) window.skillChartInstance.destroy(); // Clear previous
    
    window.skillChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.skills,
            datasets: [{
                label: 'Proficiency (Mock Score)',
                data: data.skills.map(() => Math.floor(Math.random() * 30) + 70),
                backgroundColor: '#4f46e5',
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            scales: { x: { beginAtZero: true, max: 100 } }
        }
    });

    // 3. Career Recommendations
    // Format the text slightly for better HTML display
    document.getElementById("careerRec").innerHTML = `<pre style="font-family:inherit; white-space:pre-wrap;">${data.recommendations}</pre>`;

    // 4. Roadmap (Simple parsing if AI followed format, otherwise display text)
    // This attempts to find lines starting with "Step"
    const steps = data.recommendations.split('\n').filter(line => line.toLowerCase().includes("step"));
    let roadmapHtml = "";
    if(steps.length > 0) {
        steps.forEach(step => {
            roadmapHtml += `<div class="roadmap-step">${step}</div>`;
        });
    } else {
        roadmapHtml = `<p style="color:#666;">See full recommendation above for roadmap details.</p>`;
    }
    document.getElementById("roadmapList").innerHTML = roadmapHtml;
}

// --- Chat Logic ---

function handleEnter(e) {
    if(e.key === 'Enter') sendChat();
}

async function sendChat() {
    const input = document.getElementById("chatInput");
    const chatWindow = document.getElementById("chatWindow");
    const query = input.value;
    
    if(!query) return;
    
    chatWindow.innerHTML += `<div class="msg user">${query}</div>`;
    input.value = "";
    
    const formData = new FormData();
    formData.append("query", query);
    
    try {
        const res = await fetch(`${API}/analysis/chat`, { method: "POST", body: formData });
        const data = await res.json();
        
        chatWindow.innerHTML += `<div class="msg bot">${data.response}</div>`;
        chatWindow.scrollTop = chatWindow.scrollHeight;
    } catch (e) {
        chatWindow.innerHTML += `<div class="msg bot" style="background:#fee2e2; color:#b91c1c;">Error connecting to server.</div>`;
    }
}