async function scanInput() {
  const text = document.getElementById("inputText").value;
  const file = document.getElementById("pdfInput").files[0];
  const loader = document.getElementById("loader");
  const resultBox = document.getElementById("resultBox");

  resultBox.style.display = "none";
  loader.style.display = "block";

  let response;

  try {
    if (file) {
      const formData = new FormData();
      formData.append("file", file);

      response = await fetch("/scan", {
        method: "POST",
        body: formData
      });
    } else if (text.trim()) {
      response = await fetch("/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
      });
    } else {
      alert("Please enter text or upload a PDF.");
      loader.style.display = "none";
      return;
    }

    const data = await response.json();
    loader.style.display = "none";
    resultBox.style.display = "block";

    document.getElementById("risk").textContent = `Risk Score: ${data.risk_score}`;

    let listHTML = "";
    data.detected.forEach(d => {
      listHTML += `<li><strong>${d.type}</strong>: ${d.text} (via ${d.method})</li>`;
    });
    document.getElementById("detections").innerHTML = listHTML;

    const status = document.getElementById("status");
    if (data.blocked) {
      status.textContent = "❌ Message BLOCKED due to sensitive content.";
      status.className = "blocked";
    } else {
      status.textContent = "✅ Message is safe to send.";
      status.className = "safe";
    }
  } catch (error) {
    loader.style.display = "none";
    alert("Error during scanning.");
    console.error(error);
  }
}

function toggleTheme() {
  document.body.classList.toggle("dark-mode");
}
