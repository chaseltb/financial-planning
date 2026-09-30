// Accessibility helpers that apply across every page.

// 1. Keyboard support for click-driven elements that aren't native buttons
//    (e.g. clickable table rows). Elements opt in with role="button" + tabindex="0".
document.addEventListener('keydown', function (event) {
    if (event.key !== 'Enter' && event.key !== ' ') { return; }
    var el = event.target;
    if (!el || el.getAttribute('role') !== 'button' || el.tagName === 'BUTTON') { return; }
    event.preventDefault();
    el.click();
});

// 2. Associate visible <label>s with their form controls. Dash pattern-matching
//    ids are JSON strings, which makes label[for] awkward to wire up per page, so
//    controls without a programmatic name get aria-labelledby pointing at the
//    closest preceding label (or an aria-label fallback from the placeholder).
(function () {
    var counter = 0;

    function nearestLabel(input) {
        var node = input;
        for (var depth = 0; depth < 4 && node && node.parentElement; depth++) {
            var sib = node.previousElementSibling;
            while (sib) {
                if (sib.tagName === 'LABEL') { return sib; }
                var inner = sib.querySelector && sib.querySelector('label');
                if (inner && !sib.querySelector('input, select, textarea')) { return inner; }
                sib = sib.previousElementSibling;
            }
            node = node.parentElement;
            if (node.classList && (node.classList.contains('glass-card') || node.tagName === 'MAIN')) { break; }
        }
        return null;
    }

    function labelControls(root) {
        var controls = root.querySelectorAll('input:not([type=hidden]):not([type=file]), select, textarea');
        controls.forEach(function (input) {
            if (input.getAttribute('aria-label') || input.getAttribute('aria-labelledby')) { return; }
            if (input.closest('.dash-spreadsheet-container') || input.closest('.Select')) { return; }
            if (input.id && document.querySelector('label[for="' + CSS.escape(input.id) + '"]')) { return; }
            if (input.closest('label')) { return; }
            var label = nearestLabel(input);
            if (label) {
                if (!label.id) { label.id = 'a11y-label-' + (++counter); }
                input.setAttribute('aria-labelledby', label.id);
            } else if (input.placeholder) {
                input.setAttribute('aria-label', input.placeholder);
            }
        });
    }

    var scheduled = false;
    function schedule() {
        if (scheduled) { return; }
        scheduled = true;
        // setTimeout rather than requestAnimationFrame: rAF is paused in background tabs.
        window.setTimeout(function () {
            scheduled = false;
            labelControls(document);
        }, 50);
    }

    new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
    document.addEventListener('DOMContentLoaded', schedule);
})();
