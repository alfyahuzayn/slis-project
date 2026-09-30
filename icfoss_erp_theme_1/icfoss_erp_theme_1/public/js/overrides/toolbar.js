$(document).ready(function() {
    let fullwidth = JSON.parse(localStorage.container_fullwidth || "true");
    localStorage.container_fullwidth = fullwidth;
    $(document.body).toggleClass("full-width", fullwidth);
});