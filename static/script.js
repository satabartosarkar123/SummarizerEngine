const fileInput = document.getElementById("audioFile");
const resultContainer = document.getElementById("result");
const uploadLabel = document.querySelector(".upload-label");

function resetResult() {
  resultContainer.innerHTML = "";
}

function escapeHtml(value) {
  const str = value == null ? "" : String(value);
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderMarkdown(text) {
  if (!text) return "<p>No summary available.</p>";

  const lines = text.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let inUl = false;
  let inOl = false;
  let paragraph = [];

  const inlineFormat = (value) => {
    let formatted = escapeHtml(value);
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    formatted = formatted.replace(/\*(.+?)\*/g, "<em>$1</em>");
    formatted = formatted.replace(/`([^`]+)`/g, "<code>$1</code>");
    return formatted;
  };

  const flushParagraph = () => {
    if (!paragraph.length) return;
    html += `<p>${inlineFormat(paragraph.join(" ").trim())}</p>`;
    paragraph = [];
  };

  const closeLists = () => {
    if (inUl) {
      html += "</ul>";
      inUl = false;
    }
    if (inOl) {
      html += "</ol>";
      inOl = false;
    }
  };

  for (const line of lines) {
    const headingMatch = line.match(/^\s{0,3}(#{1,6})\s+(.*)$/);
    const unorderedMatch = line.match(/^\s{0,3}[-*+]\s+(.*)$/);
    const orderedMatch = line.match(/^\s{0,3}(\d+)\.\s+(.*)$/);
    const blockquoteMatch = line.match(/^\s{0,3}>\s?(.*)$/);
    const trimmed = line.trim();

    if (headingMatch) {
      flushParagraph();
      closeLists();
      const level = headingMatch[1].length;
      html += `<h${level}>${inlineFormat(headingMatch[2].trim())}</h${level}>`;
      continue;
    }

    if (blockquoteMatch) {
      flushParagraph();
      closeLists();
      html += `<blockquote>${inlineFormat(blockquoteMatch[1].trim())}</blockquote>`;
      continue;
    }

    if (unorderedMatch) {
      flushParagraph();
      if (inOl) {
        html += "</ol>";
        inOl = false;
      }
      if (!inUl) {
        html += "<ul>";
        inUl = true;
      }
      html += `<li>${inlineFormat(unorderedMatch[1].trim())}</li>`;
      continue;
    }

    if (orderedMatch) {
      flushParagraph();
      if (inUl) {
        html += "</ul>";
        inUl = false;
      }
      if (!inOl) {
        html += "<ol>";
        inOl = true;
      }
      html += `<li>${inlineFormat(orderedMatch[2].trim())}</li>`;
      continue;
    }

    if (trimmed === "") {
      flushParagraph();
      closeLists();
      continue;
    }

    if (inUl || inOl) {
      closeLists();
    }

    paragraph.push(trimmed);
  }

  flushParagraph();
  closeLists();

  return html || "<p>No summary available.</p>";
}

function renderError(message) {
  resultContainer.innerHTML = `
    <div>
      <h2>Something went wrong</h2>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
}

function renderResult({ summary, transcript, segments }) {
  const summaryHtml = `<div class="summary-body">${renderMarkdown(summary)}</div>`;

  const transcriptHtml = `<pre>${transcript ? escapeHtml(transcript) : "No transcript available."}</pre>`;

  let segmentsMarkup = "";
  if (Array.isArray(segments) && segments.length > 0) {
    const segmentText = segments
      .map((segment) => {
        const speaker = escapeHtml(segment.speaker ?? "Speaker");
        const start = escapeHtml(String(segment.start ?? "?"));
        const end = escapeHtml(String(segment.end ?? "?"));
        const text = escapeHtml(segment.text ?? "");
        return `[${start}s - ${end}s] ${speaker}: ${text}`;
      })
      .join("\n\n");
    segmentsMarkup = `
      <h3>Segments</h3>
      <pre>${segmentText}</pre>
    `;
  }

  resultContainer.innerHTML = `
    <div>
      <h2>Summary</h2>
      ${summaryHtml}
      <h2>Transcript</h2>
      ${transcriptHtml}
      ${segmentsMarkup}
    </div>
  `;
}

function setLoading(isLoading) {
  const button = document.querySelector(".upload-btn");
  if (!button) return;
  button.disabled = isLoading;
  button.textContent = isLoading ? "Processing..." : "Upload & Summarize";
}

async function uploadAndProcess() {
  resetResult();

  if (!fileInput.files.length) {
    renderError("Please choose an audio file before uploading.");
    return;
  }

  setLoading(true);

  try {
    const formData = new FormData();
    formData.append("audio", fileInput.files[0]);

    const response = await fetch("/api/process", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new Error(errorPayload.error || "Unable to process the audio file.");
    }

    const payload = await response.json();
    renderResult(payload);
  } catch (error) {
    renderError(error.message);
  } finally {
    setLoading(false);
  }
}

uploadLabel.addEventListener("dragover", (event) => {
  event.preventDefault();
  uploadLabel.classList.add("dragging");
});

uploadLabel.addEventListener("dragleave", () => {
  uploadLabel.classList.remove("dragging");
});

uploadLabel.addEventListener("drop", (event) => {
  event.preventDefault();
  uploadLabel.classList.remove("dragging");

  if (event.dataTransfer?.files?.length) {
    fileInput.files = event.dataTransfer.files;
  }
});

fileInput.addEventListener("change", () => {
  const fileName = fileInput.files[0]?.name;
  if (fileName) {
    uploadLabel.querySelector("span:last-child").textContent = fileName;
  }
});
