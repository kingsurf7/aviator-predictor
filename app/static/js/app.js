// Configuration initiale
let mainChart, performanceChart, distributionChart;
let darkMode = localStorage.getItem('darkMode') === 'true';
let lastPredictionTime = 0;

// Initialiser l'application
document.addEventListener('DOMContentLoaded', function() {
    initCharts();
    setupEventListeners();
    applyTheme();
    startDataUpdates();
});

function initCharts() {
    // Chart principal
    const mainCtx = document.getElementById('main-chart').getContext('2d');
    mainChart = new Chart(mainCtx, {
        type: 'line',
        data: {
            datasets: [
                {
                    label: 'Multiplicateur Actuel',
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    tension: 0.1,
                    data: []
                },
                {
                    label: 'Prédiction',
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderDash: [5, 5],
                    tension: 0.1,
                    data: []
                }
            ]
        },
        options: getChartOptions('Historique et Prédictions')
    });

    // Chart de performance
    const perfCtx = document.getElementById('performance-chart').getContext('2d');
    performanceChart = new Chart(perfCtx, {
        type: 'bar',
        data: {
            labels: ['1', '2', '3', '4', '5'],
            datasets: [{
                label: 'Erreurs Récentes',
                backgroundColor: 'rgba(239, 68, 68, 0.7)',
                data: []
            }]
        },
        options: getChartOptions('Performance des Prédictions')
    });

    // Chart de distribution
    const distCtx = document.getElementById('distribution-chart').getContext('2d');
    distributionChart = new Chart(distCtx, {
        type: 'pie',
        data: {
            labels: ['Correctes', 'Erreurs'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#10b981', '#ef4444']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Précision Récente',
                    color: darkMode ? '#fff' : '#374151'
                },
                legend: {
                    labels: {
                        color: darkMode ? '#fff' : '#374151'
                    }
                }
            }
        }
    });
}

function getChartOptions(title) {
    return {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: title,
                color: darkMode ? '#fff' : '#374151'
            },
            legend: {
                labels: {
                    color: darkMode ? '#fff' : '#374151'
                }
            }
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'second',
                    displayFormats: {
                        second: 'HH:mm:ss'
                    }
                },
                ticks: {
                    color: darkMode ? '#fff' : '#374151'
                },
                grid: {
                    color: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
                }
            },
            y: {
                beginAtZero: true,
                ticks: {
                    color: darkMode ? '#fff' : '#374151'
                },
                grid: {
                    color: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
                }
            }
        }
    };
}

function setupEventListeners() {
    document.getElementById('save-settings').addEventListener('click', saveSettings);
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
    
    // Initialiser les seuils depuis le localStorage
    const savedThreshold = localStorage.getItem('alertThreshold');
    const savedConfidence = localStorage.getItem('confidenceThreshold');
    
    if (savedThreshold) {
        document.getElementById('alert-threshold').value = savedThreshold;
    }
    
    if (savedConfidence) {
        document.getElementById('confidence-threshold').value = savedConfidence;
    }
}

function applyTheme() {
    if (darkMode) {
        document.body.classList.add('dark');
        document.body.classList.remove('bg-gray-100');
        document.body.classList.add('bg-gray-900');
    } else {
        document.body.classList.remove('dark');
        document.body.classList.remove('bg-gray-900');
        document.body.classList.add('bg-gray-100');
    }
    
    // Mettre à jour les charts
    updateChartStyles();
}

function toggleTheme() {
    darkMode = !darkMode;
    localStorage.setItem('darkMode', darkMode);
    applyTheme();
}

function updateChartStyles() {
    const textColor = darkMode ? '#fff' : '#374151';
    const gridColor = darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    
    // Mettre à jour tous les charts
    [mainChart, performanceChart, distributionChart].forEach(chart => {
        if (chart) {
            chart.options.plugins.title.color = textColor;
            chart.options.scales.x.ticks.color = textColor;
            chart.options.scales.y.ticks.color = textColor;
            chart.options.scales.x.grid.color = gridColor;
            chart.options.scales.y.grid.color = gridColor;
            
            if (chart.legend) {
                chart.legend.options.labels.color = textColor;
            }
            
            chart.update();
        }
    });
}

function startDataUpdates() {
    // Démarrer les mises à jour
    setInterval(fetchData, 3000);
    fetchData();
}

async function fetchData() {
    try {
        const [predictionRes, analyticsRes] = await Promise.all([
            fetch('/api/prediction'),
            fetch('/api/analytics')
        ]);
        
        const predictionData = await predictionRes.json();
        const analyticsData = await analyticsRes.json();
        
        if (predictionData && !predictionData.error) {
            updatePredictionUI(predictionData);
        }
        
        if (analyticsData) {
            updateAnalyticsUI(analyticsData);
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function updatePredictionUI(data) {
    // Mettre à jour les valeurs principales
    document.getElementById('current-value').textContent = data.current.toFixed(2) + 'x';
    document.getElementById('prediction-value').textContent = `Prédiction: ${data.prediction.toFixed(2)}x`;
    
    // Mettre à jour la barre de confiance
    const confidencePercent = Math.round(data.confidence * 100);
    const confidenceBar = document.getElementById('confidence-bar');
    confidenceBar.style.width = `${confidencePercent}%`;
    
    // Changer la couleur en fonction du niveau de confiance
    if (confidencePercent >= 75) {
        confidenceBar.className = 'h-4 rounded-full transition-all duration-500 bg-green-500';
    } else if (confidencePercent >= 50) {
        confidenceBar.className = 'h-4 rounded-full transition-all duration-500 bg-yellow-500';
    } else {
        confidenceBar.className = 'h-4 rounded-full transition-all duration-500 bg-red-500';
    }
    
    document.getElementById('confidence-text').textContent = `Confiance: ${confidencePercent}%`;
    
    // Mettre à jour les indicateurs
    document.getElementById('volatility-indicator').textContent = data.volatility.toFixed(2);
    
    const trendElement = document.getElementById('trend-indicator');
    if (data.trend === 'up') {
        trendElement.className = 'px-2 py-1 rounded-md bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
        trendElement.textContent = 'Haussière ↑';
    } else if (data.trend === 'down') {
        trendElement.className = 'px-2 py-1 rounded-md bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
        trendElement.textContent = 'Baissière ↓';
    } else {
        trendElement.className = 'px-2 py-1 rounded-md bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
        trendElement.textContent = 'Neutre →';
    }
    
    // Mettre à jour le graphique principal
    updateMainChart(data);
    
    // Vérifier les alertes
    checkForAlerts(data);
}

function updateMainChart(data) {
    const now = new Date();
    
    // Ajouter les données actuelles
    if (mainChart.data.datasets[0].data.length >= 50) {
        mainChart.data.datasets[0].data.shift();
    }
    mainChart.data.datasets[0].data.push({
        x: now,
        y: data.current
    });
    
    // Mettre à jour la prédiction
    const predictionTime = new Date(now.getTime() + 30000); // 30s dans le futur
    mainChart.data.datasets[1].data = [
        { x: now, y: data.current },
        { x: predictionTime, y: data.prediction }
    ];
    
    mainChart.update();
}

function updateAnalyticsUI(data) {
    // Mettre à jour les indicateurs clés
    document.getElementById('avg-accuracy').textContent = `${Math.round((1 - data.avg_error) * 100)}%`;
    document.getElementById('last-error').textContent = `${Math.round(data.last_error * 100)}%`;
    document.getElementById('stability-indicator').textContent = `${Math.round(data.stability * 100)}%`;
    
    // Mettre à jour le graphique de performance
    if (performanceChart && data.error_history) {
        const errorHistory = data.error_history.slice(-5);
        performanceChart.data.datasets[0].data = errorHistory.map(e => e * 100);
        performanceChart.update();
    }
    
    // Mettre à jour le graphique de distribution
    if (distributionChart && data.success_rate) {
        distributionChart.data.datasets[0].data = [
            data.success_rate * 100,
            (1 - data.success_rate) * 100
        ];
        distributionChart.update();
    }
}

function checkForAlerts(data) {
    const threshold = parseFloat(document.getElementById('alert-threshold').value);
    const confidenceThreshold = parseFloat(document.getElementById('confidence-threshold').value) / 100;
    
    if (data.prediction > threshold && 
        data.confidence > confidenceThreshold && 
        data.trend === 'up' &&
        Date.now() - lastPredictionTime > 300000) { // 5 minutes entre les alertes
        
        showAlert(data);
        lastPredictionTime = Date.now();
    }
}

function showAlert(data) {
    // Mettre en surbrillance la carte
    const card = document.getElementById('prediction-card');
    card.classList.add('border-2', 'border-green-500', 'animate-pulse');
    setTimeout(() => {
        card.classList.remove('animate-pulse');
    }, 2000);
    
    // Notification du navigateur
    if (Notification.permission === 'granted') {
        new Notification('Bonne opportunité de pari!', {
            body: `Prédiction: ${data.prediction.toFixed(2)}x (Confiance: ${Math.round(data.confidence * 100)}%)`,
            icon: '/static/images/logo.png'
        });
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission();
    }
}

async function saveSettings() {
    const threshold = document.getElementById('alert-threshold').value;
    const confidence = document.getElementById('confidence-threshold').value;
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                alert_threshold: parseFloat(threshold),
                confidence_threshold: parseFloat(confidence) / 100
            })
        });
        
        if (response.ok) {
            localStorage.setItem('alertThreshold', threshold);
            localStorage.setItem('confidenceThreshold', confidence);
            
            // Afficher un feedback
            const btn = document.getElementById('save-settings');
            btn.textContent = '✓ Enregistré!';
            btn.classList.remove('bg-indigo-600');
            btn.classList.add('bg-green-600');
            
            setTimeout(() => {
                btn.textContent = 'Enregistrer';
                btn.classList.remove('bg-green-600');
                btn.classList.add('bg-indigo-600');
            }, 2000);
        }
    } catch (error) {
        console.error('Error saving settings:', error);
    }
}
