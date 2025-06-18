**ESKİ-SÜRÜM**
{% extends "base.html" %}
{% block title %}Sorgu - DATASAGE{% endblock %}
{% block content %}

<!-- Hero Section -->
<section class="query-hero">
  <div class="hero-background"></div>
  <div class="container position-relative">
    <div class="row justify-content-center">
      <div class="col-lg-10 text-center" data-aos="fade-up">
        <div class="hero-icon-wrapper mb-4">
          <i class="bi bi-search hero-icon"></i>
        </div>
        <h1 class="hero-title">Akıllı Sorgu</h1>
        <p class="hero-subtitle">Veritabanınızı yükleyin ve doğal dilde sorularınızı sorun</p>
        <div class="hero-decoration"></div>
      </div>
    </div>
  </div>
</section>

<!-- Main Content -->
<div class="container main-container">
  <div class="row justify-content-center">
    <div class="col-lg-10">
      
      {% if tokens is not none %}
      <div class="row justify-content-center">
        <div class="col-lg-8">
          <div class="alert alert-info text-center">
            Kalan sorgu hakkınız: <strong>{{ tokens }}</strong><br>

            {% if remaining_timedelta %}
              {% set total_seconds = remaining_timedelta.total_seconds()|int %}
              {% set hours = total_seconds // 3600 %}
              {% set minutes = (total_seconds % 3600) // 60 %}
              {% set seconds = total_seconds % 60 %}

              {% if tokens == 0 %}
                Yeni haklarınız <strong>{{ hours }} saat {{ minutes }} dakika {{ seconds }} saniye</strong> sonra yüklenecektir.
              {% elif tokens < 10 %}
                Token haklarınız <strong>{{ hours }} saat {{ minutes }} dakika {{ seconds }} saniye</strong> sonra yenilenecek.
              {% endif %}
            {% endif %}
          </div>
        </div>
      </div>
      {% endif %}
    
      <!-- Query Form Card -->
      <div class="query-card glass-card" data-aos="fade-up" data-aos-delay="200">
        
        <!-- Active Database Alert -->
        {% if last_db %}
        <div class="db-alert" data-aos="fade-down">
          <div class="db-alert-icon">
            <i class="bi bi-database-check"></i>
          </div>
          <div class="db-alert-content">
            <div class="db-alert-title">Aktif veritabanı</div>
            <div class="db-alert-subtitle">{{ last_db.split('_', 1)[1] if '_' in last_db else last_db }}</div>
            <small class="db-alert-note">Yeni bir veritabanı yüklersen, bu veritabanının yerine geçer.</small>
          </div>
        </div>
        {% endif %}

        <!-- Database Summary -->
        {% if db_summary %}
        <input type="hidden" id="current-db-filename" value="{{ last_db }}">
        <div class="db-summary-container">
          <div class="db-summary-header">
            <i class="bi bi-info-circle"></i>
            <span>Veritabanı Özeti</span>
          </div>
          <div class="db-summary-content">
            <div id="db-summary-text">{{ db_summary }}</div>
            <button id="toggle-summary-btn" class="summary-toggle-btn">
              <span>Daha ayrıntılı göster</span>
              <i class="bi bi-chevron-right"></i>
            </button>
          </div>
        </div>
        {% endif %}

        <!-- Query Form -->
        <form action="{{ url_for('ask') }}" method="post" enctype="multipart/form-data" class="query-form">
          
          <!-- Database Upload Section -->
          <div class="form-section">
            <div class="section-header">
              <div class="section-icon">
                <i class="bi bi-database"></i>
              </div>
              <div class="section-title">Veritabanı Dosyası</div>
            </div>
            
            <div class="upload-zone" id="uploadArea">
              <input type="file" name="database" class="upload-input" id="databaseFile" accept=".db,.sqlite,.sqlite3">
              <div class="upload-content">
                <div class="upload-icon-wrapper">
                  <i class="bi bi-cloud-upload upload-icon"></i>
                </div>
                <div class="upload-text">SQLite dosyanızı sürükleyin veya tıklayın</div>
                <div class="upload-formats">Desteklenen formatlar: .db, .sqlite, .sqlite3</div>
              </div>
            </div>
            
            <div class="file-preview" id="fileInfo">
              <div class="file-preview-icon">
                <i class="bi bi-file-earmark-check"></i>
              </div>
              <div class="file-preview-name" id="fileName"></div>
              <button type="button" class="file-remove-btn" id="removeFile">
                <i class="bi bi-x"></i>
              </button>
            </div>
          </div>

          <!-- Question Section -->
          <div class="form-section">
            <div class="section-header">
              <div class="section-icon">
                <i class="bi bi-chat-dots"></i>
              </div>
              <div class="section-title">Sorunuz</div>
            </div>
            
            <div class="question-container">
              <div class="question-input-wrapper">
                <input type="text" name="question" class="question-input" 
                       placeholder="Örn: En uzun film nedir?" required>
                <div class="input-focus-ring"></div>
              </div>
              
              <div class="suggestions-container">
                <div class="suggestions-label">Örnek sorular:</div>
                <div class="suggestions-grid">
                  <button type="button" class="suggestion-pill" onclick="setSuggestion(this)">
                    En çok satan ürün nedir?
                  </button>
                  <button type="button" class="suggestion-pill" onclick="setSuggestion(this)">
                    Toplam müşteri sayısı kaç?
                  </button>
                  <button type="button" class="suggestion-pill" onclick="setSuggestion(this)">
                    En yüksek fiyatlı ürün hangisi?
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Live Database Connection -->
          <div class="form-section">
            <div class="section-divider">
              <span>veya</span>
            </div>
            
            <div class="collapsible-section">
              <button type="button" class="collapsible-header" data-bs-toggle="collapse" 
                      data-bs-target="#liveDBCollapse" aria-expanded="false">
                <div class="collapsible-icon">
                  <i class="bi bi-plug-fill"></i>
                </div>
                <div class="collapsible-title">Canlı Veritabanı ile Bağlantı Kur</div>
                <div class="collapsible-arrow">
                  <i class="bi bi-chevron-down"></i>
                </div>
              </button>
              
              <div class="collapse" id="liveDBCollapse">
                <div class="collapsible-content">
                  <div class="db-connection-form">
                    
                    <div class="form-group">
                      <label class="form-label">Veritabanı Türü</label>
                      <select name="db_type" class="form-select custom-select">
                        <option value="">Seçiniz</option>
                        <option value="mysql">MySQL</option>
                        <option value="postgres">PostgreSQL</option>
                      </select>
                    </div>

                    <div class="form-row">
                      <div class="form-group">
                        <label class="form-label">Host</label>
                        <input type="text" name="host" class="form-control custom-input" placeholder="localhost">
                      </div>
                      <div class="form-group">
                        <label class="form-label">Port</label>
                        <input type="text" name="port" class="form-control custom-input" placeholder="3306 / 5432">
                      </div>
                    </div>

                    <div class="form-row">
                      <div class="form-group">
                        <label class="form-label">Kullanıcı Adı</label>
                        <input type="text" name="user" class="form-control custom-input" placeholder="root">
                      </div>
                      <div class="form-group">
                        <label class="form-label">Şifre</label>
                        <input type="password" name="password" class="form-control custom-input" placeholder="••••••••">
                      </div>
                    </div>

                    <div class="form-group">
                      <label class="form-label">Veritabanı Adı</label>
                      <input type="text" name="database" class="form-control custom-input" placeholder="my_database">
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="submit-section">
            <button type="submit" class="submit-btn primary-btn">
              <div class="btn-content">
                <i class="bi bi-play-circle btn-icon"></i>
                <span class="btn-text">Sorgula</span>
              </div>
              <div class="btn-loading">
                <div class="loading-spinner"></div>
                <span>İşleniyor...</span>
              </div>
            </button>
          </div>
        </form>
      </div>

      <!-- SQL Query Display -->
      {% if sql_query %}
      <div class="result-card sql-result-card" data-aos="fade-up" data-aos-delay="300">
        <div class="result-header">
          <div class="result-header-content">
            <div class="result-icon">
              <i class="bi bi-code-slash"></i>
            </div>
            <div class="result-title">Üretilen SQL Sorgusu</div>
          </div>
          <button class="copy-btn" onclick="copySql()">
            <i class="bi bi-clipboard"></i>
            <span>Kopyala</span>
          </button>
        </div>
        <div class="sql-content">
          <pre class="sql-query"><code>{{ sql_query }}</code></pre>
        </div>
      </div>
      {% endif %}

      <!-- Results Section -->
      {% if result %}
      <div class="result-card data-result-card" data-aos="fade-up" data-aos-delay="400">
        {% if result["columns"][0] == "Hata" %}
        <!-- Error Display -->
        <div class="error-display">
          <div class="error-header">
            <div class="error-icon">
              <i class="bi bi-exclamation-triangle-fill"></i>
            </div>
            <div class="error-title">Hata Oluştu</div>
          </div>
          <div class="error-content">
            <p>{{ result["rows"][0][0] }}</p>
          </div>
        </div>
        {% else %}
        <!-- Success Results -->
        <div class="result-header">
          <div class="result-header-content">
            <div class="result-icon success">
              <i class="bi bi-table"></i>
            </div>
            <div class="result-info">
              <div class="result-title">Sorgu Sonuçları</div>
              <div class="result-count">{{ result["rows"]|length }} kayıt bulundu</div>
            </div>
          </div>
          <div class="result-actions">
            <button class="action-btn csv-btn" onclick='downloadResult("csv")'>
              <i class="bi bi-download"></i>
              <span>CSV</span>
            </button>
            <button class="action-btn excel-btn" onclick='downloadResult("xlsx")'>
              <i class="bi bi-download"></i>
              <span>Excel</span>
            </button>
          </div>
        </div>
        
        <div class="table-wrapper">
          <div class="table-container">
            <table class="results-table">
              <thead>
                <tr>
                  {% for col in result["columns"] %}
                    <th>{{ col }}</th>
                  {% endfor %}
                </tr>
              </thead>
              <tbody>
                {% for row in result["rows"] %}
                  <tr>
                    {% for item in row %}
                      <td>{{ item }}</td>
                    {% endfor %}
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>

        <!-- Chart Section -->
        {% if result["columns"]|length >= 2 and result["rows"]|length > 0 %}
        <div class="chart-section">
          <div class="chart-header">
            <div class="chart-title">
              <i class="bi bi-graph-up"></i>
              <span>Grafiksel Görselleştirme</span>
            </div>
          </div>
          
          <div class="chart-controls">
            <div class="control-group">
              <label class="control-label">X Eksen</label>
              <select id="labelColumn" class="chart-select"></select>
            </div>
            <div class="control-group">
              <label class="control-label">Y Eksen</label>
              <select id="valueColumn" class="chart-select"></select>
            </div>
            <div class="control-group">
              <label class="control-label">Grafik Tipi</label>
              <select id="chartType" class="chart-select">
                <option value="bar">📊 Sütun Grafik</option>
                <option value="line">📈 Çizgi Grafik</option>
                <option value="pie">🥧 Pasta Grafik</option>
                <option value="doughnut">🍩 Halka Grafik</option>
                <option value="radar">🎯 Radar Grafik</option>
              </select>
            </div>
          </div>
          
          <div class="chart-container">
            <canvas id="chartArea"></canvas>
          </div>
        </div>
        {% endif %}

        {% endif %}
      </div>
      {% endif %}
    </div>
  </div>
</div>

<!-- Chart.js and Scripts -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
{% if result and result["columns"][0] != "Hata" %}
<script>
const rows = JSON.parse('{{ result["rows"] | tojson | safe }}');
const columns = JSON.parse('{{ result["columns"] | tojson | safe }}');
let chartInstance = null;

function generateColors(count) {
    const baseColors = [
        '#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1',
        '#20c997', '#fd7e14', '#e83e8c', '#6c757d',
        '#17a2b8', '#6610f2', '#198754', '#0dcaf0',
        '#b23cfd', '#f46262', '#ffa94d', '#63e6be'
    ];
    const colors = [];
    for (let i = 0; i < count; i++) {
        colors.push(baseColors[i % baseColors.length]);
    }
    return colors;
}

function populateColumnDropdowns() {
    const labelDropdown = document.getElementById("labelColumn");
    const valueDropdown = document.getElementById("valueColumn");
    if (!labelDropdown || !valueDropdown) return;

    labelDropdown.innerHTML = "";
    valueDropdown.innerHTML = "";
    columns.forEach((col, i) => {
        let opt1 = document.createElement("option");
        opt1.value = i;
        opt1.text = col;
        labelDropdown.appendChild(opt1);

        let opt2 = document.createElement("option");
        opt2.value = i;
        opt2.text = col;
        valueDropdown.appendChild(opt2);
    });
    labelDropdown.selectedIndex = 0;
    valueDropdown.selectedIndex = columns.length > 1 ? 1 : 0;
}

function drawChart() {
    const type = document.getElementById("chartType").value;
    const labelIdx = parseInt(document.getElementById("labelColumn").value);
    const valueIdx = parseInt(document.getElementById("valueColumn").value);

    const labels = [];
    const values = [];
    for (let i = 0; i < rows.length; i++) {
        const label = rows[i][labelIdx];
        const raw = rows[i][valueIdx];
        const value = parseFloat(String(raw).replace(/[^\d.-]/g, ""));
        if (!isNaN(value)) {
            labels.push(label);
            values.push(value);
        }
    }

    if (chartInstance) chartInstance.destroy();

    if (labels.length > 0 && values.length > 0) {
        const ctx = document.getElementById("chartArea").getContext("2d");
        chartInstance = new Chart(ctx, {
            type: type,
            data: {
                labels: labels,
                datasets: [{
                    label: columns[valueIdx],
                    data: values,
                    backgroundColor: generateColors(labels.length),
                    borderColor: generateColors(labels.length),
                    borderWidth: 2,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: "Grafiksel Görselleştirme",
                        font: { size: 16, weight: 'bold' }
                    },
                    legend: {
                        position: type === 'pie' || type === 'doughnut' ? 'right' : 'top',
                        labels: { usePointStyle: true }
                    }
                },
                ...(type === "bar" || type === "line"
                    ? {
                        scales: {
                            x: { ticks: { color: '#6c757d' }, grid: { color: '#e9ecef' } },
                            y: { ticks: { color: '#6c757d' }, grid: { color: '#e9ecef' } }
                        }
                    }
                    : {}
                )
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    populateColumnDropdowns();
    drawChart();

    document.getElementById("chartType").addEventListener("change", drawChart);
    document.getElementById("labelColumn").addEventListener("change", drawChart);
    document.getElementById("valueColumn").addEventListener("change", drawChart);
});

function downloadResult(format) {
    const btn = event.target.closest('button');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-arrow-clockwise spinner-border spinner-border-sm"></i> İndiriliyor...';
    btn.disabled = true;

    fetch("/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rows: rows, columns: columns, format: format })
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = format === "xlsx" ? "sonuc.xlsx" : "sonuc.csv";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    })
    .finally(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
}


document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("toggle-summary-btn");
  const summaryBox = document.getElementById("db-summary-text");
  const dbFilename = document.getElementById("current-db-filename")?.value || "";

  let isDetailed = false;
  let originalShort = summaryBox?.textContent; // Sayfa ilk yüklendiğindeki özet

  if (toggleBtn && summaryBox && dbFilename) {
    toggleBtn.addEventListener("click", async function () {
      toggleBtn.disabled = true;
      toggleBtn.innerHTML = `<span><span class="spinner-border spinner-border-sm me-2"></span>Yükleniyor...</span>`;

      try {
        const mode = isDetailed ? "short" : "detail";
        const response = await fetch(`/get-db-summary?filename=${encodeURIComponent(dbFilename)}&mode=${mode}`);
        const data = await response.json();

        if (data.summary) {
          summaryBox.textContent = data.summary;
        } else {
          summaryBox.textContent = "❌ Özet alınamadı.";
        }

        // Buton metnini değiştir
        if (isDetailed) {
          toggleBtn.innerHTML = '<span>Daha ayrıntılı göster</span> <i class="bi bi-chevron-right"></i>';
        } else {
          toggleBtn.innerHTML = '<span>Daha kısa göster</span> <i class="bi bi-chevron-up"></i>';
        }

        isDetailed = !isDetailed;
      } catch (e) {
        summaryBox.textContent = "❌ Özet getirilirken bir hata oluştu.";
        toggleBtn.innerHTML = '<span>Tekrar dene</span> <i class="bi bi-arrow-clockwise"></i>';
      } finally {
        toggleBtn.disabled = false;
      }
    });
  }
});




</script>
{% endif %}

{% endblock %}