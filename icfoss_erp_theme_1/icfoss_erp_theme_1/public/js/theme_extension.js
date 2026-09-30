frappe.provide('frappe.ui');

frappe.ui.ThemeSwitcher = class ThemeSwitcher extends frappe.ui.ThemeSwitcher {
    fetch_themes() {
        return [
            { name: "light", label: __("Frappe Light") },
            { name: "dark", label: __("Timeless Night") },
            { name: "automatic", label: __("Automatic") },
            { name: "icfoss", label: __("SLIS Green"), info: __("Custom Green Theme") }
        ];
    }

    display_theme_options() {
        super.display_theme_options();
        const icfoss_item = this.dialog.$wrapper.find('.theme-grid-item[data-theme="icfoss"] .theme-preview');
        if (icfoss_item.length) {
            icfoss_item.css({
                'background-color': '#1a3c2b',
                'display': 'flex',
                'align-items': 'center',
                'justify-content': 'center',
                'color': '#ffffff',
                'font-weight': '600',
                'font-size': '12px',
                'letter-spacing': '0.05em'
            }).html('SLIS');
        }
    }
};

// Apply theme as soon as the page loads based on User Settings
$(document).on('app_ready', function () {
    const root = document.documentElement;
    if (frappe.boot.user.desk_theme === 'icfoss') {
        root.setAttribute('data-theme', 'icfoss');
    }
});