// $(document).ready(function() {
//     // 1. Add a custom class for the theme
//     $('body').addClass('prodeel-theme');

//     // 2. Adjust Navbar Layout
//     const searchBar = $('.search-bar');
//     if (searchBar.length) {
//         searchBar.attr('placeholder', 'Search settings, people...');
//     }
    
//     // 3. Optional: Add user greeting in the navbar (like ProDeel)
//     if (!$('.navbar-greeting').length) {
//         const user_fullname = frappe.session.user_fullname;
//         $('.navbar .mr-auto').after(`
//             <div class="navbar-greeting" style="margin-right: 0px; font-weight: 500; font-size: 13px;">
//                 Hello, ${user_fullname.split(' ')[0]}!
//             </div>
//         `);
//     }
// });