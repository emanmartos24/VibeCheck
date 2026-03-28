const textInput = document.getElementById("textInput");
const predictBtn = document.getElementById("predictBtn");
const clearBtn = document.getElementById("clearBtn");
const errorBox = document.getElementById("errorBox");
const resultBox = document.getElementById("resultBox");
const topEmotion = document.getElementById("topEmotion");
const emotionBars = document.getElementById("emotionBars");
const charCount = document.getElementById("charCount");
const sampleButtons = document.querySelectorAll(".chip");

function updateCharacterCount() {
  const count = textInput.value.length;
  charCount.textContent = `${count} character${count === 1 ? "" : "s"}`;
}

function renderEmotionBars(scores) {
  emotionBars.innerHTML = "";

  scores.slice(0, 4).forEach((item) => {
    const percent = Math.round((item.probability || 0) * 100);

    const row = document.createElement("div");
    row.className = "bar-row";

    const head = document.createElement("div");
    head.className = "bar-head";
    head.textContent = `${item.emotion} (${percent}%)`;

    const track = document.createElement("div");
    track.className = "bar-track";

    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = `${percent}%`;

    track.appendChild(fill);
    row.appendChild(head);
    row.appendChild(track);
    emotionBars.appendChild(row);
  });
}

async function classifyText() {
  errorBox.hidden = true;
  resultBox.hidden = true;

  const text = textInput.value.trim();
  if (!text) {
    errorBox.textContent = "Please enter text before classifying.";
    errorBox.hidden = false;
    return;
  }

  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Prediction failed.");
    }

    topEmotion.textContent = `${data.predicted_emotion} (${Math.round((data.predicted_probability || 0) * 100)}%)`;

    renderEmotionBars(data.emotion_scores || []);

    resultBox.hidden = false;
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  }
}

predictBtn.addEventListener("click", classifyText);
textInput.addEventListener("input", updateCharacterCount);

clearBtn.addEventListener("click", () => {
  textInput.value = "";
  updateCharacterCount();
  errorBox.hidden = true;
  resultBox.hidden = true;
  textInput.focus();
});

sampleButtons.forEach((button) => {
  button.addEventListener("click", () => {
    textInput.value = button.dataset.sample || "";
    updateCharacterCount();
    textInput.focus();
  });
});

updateCharacterCount();
