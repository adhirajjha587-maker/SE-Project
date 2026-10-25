/**
 * TalentPulse ATS - Client-Side JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // Re-initialize Lucide Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Auto-dismiss flash banner after 5 seconds if present
    const flashBanner = document.getElementById('flash-banner');
    if (flashBanner) {
        setTimeout(function () {
            flashBanner.style.opacity = '0';
            setTimeout(function () {
                flashBanner.remove();
            }, 300);
        }, 5000);
    }
});

/**
 * Copy text helper with toast alert
 */
function copyToClipboard(text, alertMessage) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () {
            showToast(alertMessage || 'Copied to clipboard!');
        });
    } else {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            showToast(alertMessage || 'Copied to clipboard!');
        } catch (err) {
            console.error('Failed to copy', err);
        }
        document.body.removeChild(textArea);
    }
}

/**
 * Lightweight Toast Notification
 */
function showToast(message) {
    const existing = document.getElementById('app-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.className = 'fixed bottom-5 right-5 z-50 bg-slate-900 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-xl flex items-center gap-2 border border-slate-700 transition-all transform duration-200';
    toast.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400"></span><span>' + message + '</span>';

    document.body.appendChild(toast);

    setTimeout(function () {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(function () {
            toast.remove();
        }, 300);
    }, 3000);
}
