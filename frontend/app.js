const elements = {
  question: document.getElementById("question"),
  askButton: document.getElementById("ask-button"),
  status: document.getElementById("status"),
  answer: document.getElementById("answer"),
  plotStatus: document.getElementById("plot-status"),
  plot: document.getElementById("plot"),
  table: document.getElementById("table"),
  sqlCode: document.getElementById("sql-code"),
  copySql: document.getElementById("copy-sql"),
};

let resizeObserver = null;

const state = {
  answer: "",
  plotConfig: null,
  sql: "",
  sqlResult: null,
};

function setStatus(message, isError = false) {
  elements.status.textContent = message || "";
  elements.status.style.color = isError ? "#b23b2a" : "";
}

function setPlotStatus(message, isError = false) {
  elements.plotStatus.textContent = message || "";
  elements.plotStatus.style.color = isError ? "#b23b2a" : "";
}

function setLoading(isLoading) {
  elements.askButton.disabled = isLoading;
  elements.askButton.textContent = isLoading ? "Running..." : "Run";
}

function renderAnswer(text) {
  elements.answer.textContent = text || "No answer available.";
}

function renderSql(sql) {
  elements.sqlCode.textContent = sql || "";
  if (window.hljs) {
    window.hljs.highlightElement(elements.sqlCode);
  }
}

function clearPlot() {
  elements.table.innerHTML = "";
  if (window.Plotly) {
    window.Plotly.purge(elements.plot);
  }
}

function rowsToObjects(columns, rows) {
  return rows.map((row) => {
    const obj = {};
    columns.forEach((col, idx) => {
      obj[col] = row[idx];
    });
    return obj;
  });
}

function getPrimaryResult(sqlResult) {
  if (!sqlResult) {
    return null;
  }
  if (Array.isArray(sqlResult.result_sets) && sqlResult.result_sets.length > 0) {
    return sqlResult.result_sets[0];
  }
  return sqlResult;
}

function renderTable(columns, rows, columnConfig) {
  const visibleColumns =
    Array.isArray(columnConfig) && columnConfig.length
      ? columnConfig.map((col) => col.value)
      : columns;
  const headerLabels =
    Array.isArray(columnConfig) && columnConfig.length
      ? columnConfig.map((col) => col.name)
      : columns;

  const table = document.createElement("table");
  table.className = "data-table";

  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  headerLabels.forEach((label) => {
    const th = document.createElement("th");
    th.textContent = label;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    visibleColumns.forEach((col) => {
      const td = document.createElement("td");
      td.textContent = row[col] !== undefined ? String(row[col]) : "";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  elements.table.innerHTML = "";
  elements.table.appendChild(table);
}

function renderPlot(plotConfig, sqlResult) {
  clearPlot();
  if (!plotConfig || !plotConfig.type) {
    setPlotStatus("No plot_config available.");
    return;
  }
  if (plotConfig.type === "none") {
    setPlotStatus(plotConfig.reason || "No chart suggested.");
    return;
  }
  if (plotConfig.type === "error") {
    setPlotStatus(plotConfig.reason || "Chart config error.", true);
    return;
  }

  const primary = getPrimaryResult(sqlResult);
  if (!primary || !Array.isArray(primary.columns) || !Array.isArray(primary.rows)) {
    setPlotStatus("No SQL data available for chart.");
    return;
  }

  const rows = rowsToObjects(primary.columns, primary.rows);
  if (!rows.length) {
    setPlotStatus("Query returned no rows.");
    return;
  }

  setPlotStatus("");

  if (plotConfig.type === "table") {
    renderTable(primary.columns, rows, plotConfig.columns);
    return;
  }

  if (!window.Plotly) {
    setPlotStatus("Plotly not available.", true);
    return;
  }

  const axis = plotConfig.axis || {};
  const xField = axis.x?.value;
  const yField = axis.y?.value;
  const seriesField = axis.series?.value;

  if (!yField || (plotConfig.type !== "pie" && !xField)) {
    setPlotStatus("Plot config missing axis fields.", true);
    return;
  }

  const traces = [];
  if (plotConfig.type === "pie") {
    if (!seriesField) {
      setPlotStatus("Plot config missing pie series field.", true);
      return;
    }
    traces.push({
      type: "pie",
      labels: rows.map((row) => row[seriesField]),
      values: rows.map((row) => row[yField]),
      textinfo: "label+percent",
      hoverinfo: "label+value",
    });
  } else {
    const groups = seriesField
      ? Array.from(new Set(rows.map((row) => row[seriesField])))
      : [null];

    groups.forEach((group) => {
      const groupRows = group === null ? rows : rows.filter((row) => row[seriesField] === group);
      const trace = {
        name: group === null ? axis.y?.name || yField : String(group),
        x: groupRows.map((row) => row[xField]),
        y: groupRows.map((row) => row[yField]),
      };
      if (plotConfig.type === "line") {
        trace.type = "scatter";
        trace.mode = "lines+markers";
      } else {
        trace.type = "bar";
        if (plotConfig.type === "bar") {
          trace.orientation = "h";
          trace.x = groupRows.map((row) => row[yField]);
          trace.y = groupRows.map((row) => row[xField]);
        }
      }
      traces.push(trace);
    });
  }

  const layout = {
    title: plotConfig.title || "",
    margin: { t: 40, l: 50, r: 20, b: 50 },
    legend: { orientation: "h" },
    autosize: true,
  };

  window.Plotly.react(elements.plot, traces, layout, { responsive: true }).then(() => {
    if (resizeObserver) {
      resizeObserver.disconnect();
    }
    resizeObserver = new ResizeObserver(() => {
      window.Plotly.Plots.resize(elements.plot);
    });
    resizeObserver.observe(elements.plot);
  });
}

async function runSql(sql) {
  if (!sql) {
    setPlotStatus("No SQL to run.");
    return null;
  }
  setPlotStatus("Running SQL for chart...");
  try {
    const response = await fetch("/run_sql", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql }),
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "run_sql failed");
    }
    return await response.json();
  } catch (error) {
    setPlotStatus(`SQL error: ${error.message}`, true);
    return null;
  }
}

async function askQuestion() {
  const question = elements.question.value.trim();
  if (!question) {
    setStatus("Enter a question to continue.", true);
    return;
  }

  setStatus("");
  setLoading(true);
  setPlotStatus("");
  renderAnswer("");
  renderSql("");
  clearPlot();

  try {
    const response = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "Ask failed");
    }
    const data = await response.json();
    state.answer = data.answer || "";
    state.plotConfig = data.plot_config || null;
    state.sql = data.sql || "";

    renderAnswer(state.answer);
    renderSql(state.sql);

    const sqlResult = await runSql(state.sql);
    state.sqlResult = sqlResult;
    renderPlot(state.plotConfig, state.sqlResult);
  } catch (error) {
    setStatus(`Error: ${error.message}`, true);
    renderAnswer("No answer available.");
  } finally {
    setLoading(false);
  }
}

elements.askButton.addEventListener("click", askQuestion);
elements.copySql.addEventListener("click", () => {
  if (!state.sql) {
    return;
  }
  navigator.clipboard.writeText(state.sql).then(() => {
    setStatus("SQL copied.");
    setTimeout(() => setStatus(""), 2000);
  });
});

elements.question.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    askQuestion();
  }
});
