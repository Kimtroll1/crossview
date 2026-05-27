chrome.runtime.onInstalled.addListener(() => {
  console.log("CrossView v0.3.5 installed");
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analyze") {
    fetch(request.url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(request.data)
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        sendResponse({ success: true, data: data });
      })
      .catch((error) => {
        console.error("Fetch error in background script:", error);
        sendResponse({ success: false, error: error.message });
      });

    // Return true to indicate that we wish to send a response asynchronously
    return true;
  }
});
