async function checkHealth() {
  const statusEl = document.getElementById("status");
  try {
    const response = await fetch("/health");
    const data = await response.json();
    statusEl.textContent = `API says: ${data.status}`;
  } catch (error) {
    statusEl.textContent = "Could not reach the API.";
    console.error(error);
  }
}

checkHealth();