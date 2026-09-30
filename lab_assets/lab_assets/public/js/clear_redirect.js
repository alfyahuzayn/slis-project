if (window.location.pathname === '/login' || window.location.pathname === '/') {
    // 1. Remove saved route from browser local storage
    localStorage.removeItem('session_last_route');

    // 2. Remove 'redirect-to' query parameter from the URL if present
    const url = new URL(window.location.href);
    if (url.searchParams.has('redirect-to')) {
        url.searchParams.delete('redirect-to');
        window.history.replaceState({}, document.title, url.pathname + url.search);
    }
}


