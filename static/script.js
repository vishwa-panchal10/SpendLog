let currentChart = null;

// Chart Color Palette matching our UI theme (Light & Distinct for Dark Mode)
const CHART_COLORS = [
    'rgba(54, 235, 255, 0.8)',  // Bright Cyan
    'rgba(255, 180, 84, 0.8)',  // Soft Orange
    'rgba(172, 115, 255, 0.8)', // Light Purple
    'rgba(255, 138, 138, 0.8)', // Soft Red
    'rgba(144, 238, 144, 0.8)', // Light Green
    'rgba(255, 243, 109, 0.8)', // Bright Yellow
    'rgba(255, 143, 203, 0.8)', // Light Pink
];


const BORDER_COLORS = CHART_COLORS.map(color => color.replace('0.8', '1'));

// Helper to get week number (basic implementation)
function getWeekNumber(d) {
    d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay()||7));
    var yearStart = new Date(Date.UTC(d.getUTCFullYear(),0,1));
    var weekNo = Math.ceil(( ( (d - yearStart) / 86400000) + 1)/7);
    return d.getUTCFullYear() + "-W" + weekNo;
}

// Fetch and visualize data
async function updateVisuals(isAdmin = false) {
    const timeframe = document.getElementById('timeframe-select').value;
    
    let url = '/api/expenses';
    if (isAdmin) {
        const userSelect = document.getElementById('user-select');
        if (userSelect) {
            url += `?user_id=${userSelect.value}`;
        }
    }

    try {
        const response = await fetch(url);
        const data = await response.json();
        
        // Hide both initially
        document.getElementById('chart-container').style.display = 'none';
        document.getElementById('table-container').style.display = 'none';

        if (data.length === 0) {
            // Optional: Handle empty state
            const ctx = document.getElementById('expenseChart').getContext('2d');
            if (currentChart) currentChart.destroy();
            document.getElementById('chart-container').style.display = 'block';
            return;
        }

        if (timeframe === 'tabular') {
            document.getElementById('table-container').style.display = 'block';
            renderTable(data);
        } else {
            document.getElementById('chart-container').style.display = 'block';
            renderChart(data, timeframe);
        }
    } catch (e) {
        console.error("Error fetching data:", e);
    }
}

function renderTable(data) {
    const tbody = document.getElementById('expense-table-body');
    tbody.innerHTML = '';
    
    // Sort descending by date
    data.sort((a,b) => new Date(b.date) - new Date(a.date));

    data.forEach(expense => {
        const tr = document.createElement('tr');
        
        const tdDate = document.createElement('td');
        tdDate.textContent = expense.date;
        
        const tdCategory = document.createElement('td');
        tdCategory.textContent = expense.category;
        
        const tdAmount = document.createElement('td');
        tdAmount.textContent = `$${expense.amount.toFixed(2)}`;
        
        tr.appendChild(tdDate);
        tr.appendChild(tdCategory);
        tr.appendChild(tdAmount);
        tbody.appendChild(tr);
    });
}

function renderChart(data, timeframe) {
    const ctx = document.getElementById('expenseChart').getContext('2d');
    
    if (currentChart) {
        currentChart.destroy();
    }

    let labels = [];
    let datasets = [];
    let configType = 'bar';
    Chart.register(ChartDataLabels);

    let chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { color: '#f8fafc', font: { family: 'Outfit' } }
            },
            datalabels: {
                display: function(context) {
                    return context.chart.config.type === 'bar';
                },
                color: '#f8fafc',
                anchor: 'end',
                align: 'top',
                formatter: function(value) {
                    if (value > 0) return '$' + value;
                    return '';
                },
                font: {
                    weight: '600',
                    family: 'Outfit',
                    size: 11
                }
            }
        },
        scales: {
            y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            x: { ticks: { color: '#94a3b8' }, grid: { display: false } }
        }
    };

    if (timeframe === 'category') {
        configType = 'pie';
        chartOptions.scales = undefined; // No scales for pie chart
        
        const catMap = {};
        data.forEach(e => {
            catMap[e.category] = (catMap[e.category] || 0) + e.amount;
        });
        
        labels = Object.keys(catMap);
        datasets = [{
            data: Object.values(catMap),
            backgroundColor: CHART_COLORS,
            borderColor: BORDER_COLORS,
            borderWidth: 2
        }];
    } else {
        // Daily, Weekly, Monthly, Yearly grouping
        const grouped = {};
        
        data.forEach(e => {
            let key;
            const d = new Date(e.date);
            if (timeframe === 'daily') key = e.date;
            else if (timeframe === 'weekly') key = getWeekNumber(d);
            else if (timeframe === 'monthly') key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
            else if (timeframe === 'yearly') key = `${d.getFullYear()}`;
            
            if (!grouped[key]) grouped[key] = {};
            grouped[key][e.category] = (grouped[key][e.category] || 0) + e.amount;
        });

        // Ensure sorted chronologically
        labels = Object.keys(grouped).sort();
        
        // Extract all unique categories
        const allCategories = new Set();
        data.forEach(e => allCategories.add(e.category));
        
        let colorIdx = 0;
        allCategories.forEach(cat => {
            const seriesData = labels.map(l => grouped[l][cat] || 0);
            datasets.push({
                label: cat,
                data: seriesData,
                backgroundColor: CHART_COLORS[colorIdx % CHART_COLORS.length],
            });
            colorIdx++;
        });
        
        // Un-stack the bars to prevent label overlap
        chartOptions.scales.x.stacked = false;
        chartOptions.scales.y.stacked = false;
        
        // Use a logarithmic scale to balance massive outliers vs small expenses
        chartOptions.scales.y.type = 'logarithmic';
        chartOptions.scales.y.ticks = {
            color: '#94a3b8',
            callback: function(value, index, values) {
                const num = Number(value);
                if (num === 1 || num === 10 || num === 100 || num === 1000 || num === 10000 || num === 100000) {
                    return '$' + num;
                }
                return null;
            }
        };
    }

    currentChart = new Chart(ctx, {
        type: configType,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: chartOptions
    });
}

// Auto-load on page start if we are on global/dashboard
document.addEventListener('DOMContentLoaded', () => {
    const el = document.getElementById('expenseChart');
    if (el) {
        // If an admin select is present, pass true
        const isAdmin = !!document.getElementById('user-select');
        updateVisuals(isAdmin);
    }
});

// --- AI Features ---

// Smart Entry
async function submitSmartExpense() {
    const inputEl = document.getElementById('smart-expense-input');
    const btnEl = document.getElementById('smart-add-btn');
    const text = inputEl.value.trim();
    
    if (!text) return;
    
    btnEl.disabled = true;
    btnEl.textContent = '...';
    
    try {
        const response = await fetch('/api/smart_add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            inputEl.value = '';
            // Refresh visuals
            updateVisuals(false);
            // Show simple alert
            alert(data.message);
        } else {
            alert(data.message || 'Error parsing expense');
        }
    } catch (e) {
        console.error("Smart add error:", e);
        alert("Failed to contact AI.");
    } finally {
        btnEl.disabled = false;
        btnEl.textContent = 'ADD';
    }
}

// Chatbot UI
function toggleChat() {
    const modal = document.getElementById('chat-modal');
    if (modal.style.display === 'none' || modal.style.display === '') {
        modal.style.display = 'flex';
        document.getElementById('chat-input').focus();
    } else {
        modal.style.display = 'none';
    }
}

function handleChatKeyPress(e) {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const inputEl = document.getElementById('chat-input');
    const msg = inputEl.value.trim();
    if (!msg) return;
    
    const messagesContainer = document.getElementById('chat-messages');
    
    // Add user message
    const userDiv = document.createElement('div');
    userDiv.style.cssText = 'background: rgba(59, 130, 246, 0.2); padding: 0.8rem; border-radius: 8px; border-right: 3px solid var(--neon-blue); align-self: flex-end; max-width: 85%;';
    userDiv.textContent = msg;
    messagesContainer.appendChild(userDiv);
    
    inputEl.value = '';
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Add loading indicator
    const loadDiv = document.createElement('div');
    loadDiv.id = 'chat-loading';
    loadDiv.style.cssText = 'padding: 0.5rem; color: var(--text-muted); font-size: 0.9rem;';
    loadDiv.textContent = 'Thinking...';
    messagesContainer.appendChild(loadDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        
        const data = await response.json();
        
        // Remove loading
        const loader = document.getElementById('chat-loading');
        if (loader) loader.remove();
        
        // Add bot message
        const botDiv = document.createElement('div');
        botDiv.style.cssText = 'background: rgba(45, 212, 191, 0.1); padding: 0.8rem; border-radius: 8px; border-left: 3px solid var(--neon-cyan); align-self: flex-start; max-width: 85%; white-space: pre-wrap; line-height: 1.4;';
        // Handle bold markdown roughly for basic nice display
        let reply = data.reply || "Sorry, I didn't get that.";
        reply = reply.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        botDiv.innerHTML = reply;
        
        messagesContainer.appendChild(botDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
    } catch (e) {
        console.error("Chat error:", e);
        const loader = document.getElementById('chat-loading');
        if (loader) loader.remove();
        
        const errDiv = document.createElement('div');
        errDiv.style.cssText = 'color: var(--error); padding: 0.5rem; font-size: 0.9rem;';
        errDiv.textContent = 'Connection error.';
        messagesContainer.appendChild(errDiv);
    }
}
