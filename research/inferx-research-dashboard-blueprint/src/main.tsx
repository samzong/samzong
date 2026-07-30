import "./index.css";

const cssHref = "/recovered/assets/index-CTU77RO5.css";
const jsSrc = "/recovered/assets/index-C7QLgfVG.js";

if (!document.querySelector(`link[href="${cssHref}"]`)) {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.crossOrigin = "";
  link.href = cssHref;
  document.head.appendChild(link);
}

if (!document.querySelector(`script[src="${jsSrc}"]`)) {
  const script = document.createElement("script");
  script.type = "module";
  script.crossOrigin = "";
  script.src = jsSrc;
  document.body.appendChild(script);
}
