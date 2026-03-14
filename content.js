let site = window.location.hostname;

if(site.includes("youtube") || site.includes("instagram")){

    let warning = document.createElement("div");

    warning.innerText = "Warning: This site may reduce productivity.";

    warning.style.position = "fixed";
    warning.style.top = "0";
    warning.style.left = "0";
    warning.style.width = "100%";
    warning.style.background = "red";
    warning.style.color = "white";
    warning.style.textAlign = "center";
    warning.style.zIndex = "9999";

    document.body.appendChild(warning);
}
