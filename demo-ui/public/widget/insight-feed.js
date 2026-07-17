(function () {
  var currentScript = document.currentScript;
  if (!currentScript) return;

  var src = new URL(currentScript.src);
  var widgetUrl = new URL("/widget/insight-feed", src.origin);
  var params = ["tenantId", "studentRef", "pairId"];

  params.forEach(function (name) {
    var value = currentScript.getAttribute("data-" + name.replace(/[A-Z]/g, function (letter) {
      return "-" + letter.toLowerCase();
    }));
    if (value) widgetUrl.searchParams.set(name, value);
  });

  var iframe = document.createElement("iframe");
  iframe.src = widgetUrl.toString();
  iframe.title = "Adaptive tutor memory insight feed";
  iframe.loading = "lazy";
  iframe.style.width = currentScript.getAttribute("data-width") || "360px";
  iframe.style.maxWidth = "100%";
  iframe.style.height = currentScript.getAttribute("data-height") || "420px";
  iframe.style.border = "0";
  iframe.style.display = "block";

  currentScript.parentNode.insertBefore(iframe, currentScript.nextSibling);
})();
