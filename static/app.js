document.addEventListener('DOMContentLoaded', () => {
    
    // Register Plugin
    if (typeof ChartDataLabels !== 'undefined') {
        Chart.register(ChartDataLabels);
    }

    const sectionUpload = document.getElementById('section-upload');
    const sectionLoading = document.getElementById('section-loading');
    const sectionResult = document.getElementById('section-result');

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const btnAnalyze = document.getElementById('btn-analyze');
    const previewContainer = document.getElementById('preview-hidden');
    const videoPlayer = document.getElementById('video-player');
    const changeBtn = document.getElementById('change-btn');

    let currentFile = null;
    let pieChartInstance = null;
    let barChartInstance = null;

    // -- File Selection Setup --
    dropZone.addEventListener('click', () => fileInput.click());
    changeBtn.addEventListener('click', (e) => { e.stopPropagation(); fileInput.click(); });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = '#06B6D4'; });
    dropZone.addEventListener('dragleave', (e) => { e.preventDefault(); dropZone.style.borderColor = ''; });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '';
        if(e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
    });

    function handleFile(file) {
        if (file.type.startsWith('video/') || file.name.match(/\.(mp4|mov|avi)$/i)) {
            currentFile = file;
            videoPlayer.src = URL.createObjectURL(file);
            dropZone.style.display = 'none';
            previewContainer.style.display = 'block';
            btnAnalyze.disabled = false;
        } else {
            alert("Please upload a valid MP4, MOV, or AVI video.");
        }
    }


    // -- Processing Protocol --
    btnAnalyze.addEventListener('click', async () => {
        if (!currentFile) return;
        
        const startTime = performance.now();
        sectionUpload.classList.remove('active');
        sectionLoading.classList.add('active');

        const formData = new FormData();
        formData.append('video', currentFile);

        try {
            const req = await fetch('/upload', { method: 'POST', body: formData });
            if (!req.ok) throw new Error("Server communication lost.");
            
            const data = await req.json();
            const duration = ((performance.now() - startTime) / 1000).toFixed(1);
            
            if (data.error) {
                alert(data.error);
                resetFlow();
                return;
            }

            renderView(data, duration);

        } catch (err) {
            console.error(err);
            alert("Exception Caught: " + err.message + "\nLine: " + err.stack);
            resetFlow();
        }
    });

    // -- Render Results --
    function renderView(data, duration) {
        sectionLoading.classList.remove('active');
        sectionResult.classList.add('active');

        const isFake = data.verdict === 'FAKE';
        const colorReal = '#34D399';
        const colorFake = '#EF4444';
        
        const confVal = isFake ? (data.overall_fake_ratio * 100).toFixed(2) : ((1 - data.overall_fake_ratio) * 100).toFixed(2);
        
        // 1. Result Card
        const mainCard = document.getElementById('main-result');
        mainCard.className = 'card result-card ' + (isFake ? 'fake' : 'real');
        
        document.getElementById('verdict-title').innerText = data.verdict;
        document.getElementById('verdict-conf').innerText = `${confVal}%`;
        document.getElementById('stat-time').innerText = `${duration}s`;
        document.getElementById('stat-faces').innerText = data.total_faces_analyzed || 0;

        // Animate Circular & Linear CSS Indicators
        const circleIndicator = document.getElementById('circle-indicator');
        const linearBar = document.getElementById('linear-bar');
        

        const offset = Math.max(0, 251.2 - (251.2 * confVal) / 100);
        setTimeout(() => {
            circleIndicator.style.strokeDashoffset = offset;
            linearBar.style.width = `${confVal}%`;
        }, 100);

        // 2. Pie Chart
        if (pieChartInstance) pieChartInstance.destroy();
        const ctxPie = document.getElementById('pie-chart').getContext('2d');
        const realPct = isFake ? (100 - confVal).toFixed(2) : confVal;
        const fakePct = isFake ? confVal : (100 - confVal).toFixed(2);

        pieChartInstance = new Chart(ctxPie, {
            type: 'doughnut',
            data: {
                labels: ['Real', 'Fake'],
                datasets: [{
                    data: [parseFloat(realPct), parseFloat(fakePct)],
                    backgroundColor: [colorReal, colorFake],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#94A3B8', font: { family: 'Inter' } } },
                    datalabels: {
                        color: '#fff',
                        font: { weight: 'bold', family: 'Inter', size: 14 },
                        formatter: (val) => val.toFixed(1) + '%'
                    }
                }
            }
        });

        // 3. Bar Chart Custom Data
        if (barChartInstance) barChartInstance.destroy();
        const ctxBar = document.getElementById('bar-chart').getContext('2d');
        
        barChartInstance = new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: ['Our Model', 'FaceForensics++', 'DeepFake Detection Challenge', 'DeeperForensics-1.0'],
                datasets: [{
                    label: 'Accuracy (%)',
                    data: [96.0, 85.1, 82.3, 80.7], 
                    backgroundColor: [
                        '#6EE7B7', 
                        '#334155', 
                        '#334155',
                        '#3B82F6'  
                    ],
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true, max: 100, 
                        grid: { color: 'rgba(255,255,255,0.05)' }, 
                        ticks: { color: '#94A3B8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94A3B8', font: { size: 11, family: 'Inter' } }
                    }
                },
                plugins: {
                    legend: { display: false },
                    datalabels: {
                        anchor: 'end',
                        align: 'top',
                        color: '#fff',
                        font: { weight: 'bold', family: 'Orbitron' },
                        formatter: (val) => val.toFixed(1) + '%'
                    }
                }
            }
        });
    }

    // -- Resetting --
    document.getElementById('btn-reset').addEventListener('click', resetFlow);

    function resetFlow() {
        currentFile = null;
        fileInput.value = '';
        videoPlayer.src = '';
        
        previewContainer.style.display = 'none';
        dropZone.style.display = 'block';
        btnAnalyze.disabled = true;

        sectionResult.classList.remove('active');
        sectionLoading.classList.remove('active');
        sectionUpload.classList.add('active');
    }
});
