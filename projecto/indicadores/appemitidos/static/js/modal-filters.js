// static/js/modal-filters.js

const locationIds = ['continents','countries','regions','provinces','cities','establishments', 'points'];

function copyModalFiltersToPageAndFetch() {
    locationIds.forEach(id => {
        const modalSel = document.getElementById('modal-' + id);
        if (!modalSel) return;
        const modalVal = modalSel.value;

        const mainSel = document.getElementById(id);
        if (mainSel) {
            mainSel.value = modalVal;
            mainSel.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
            let hid = document.getElementById(id + '-hidden');
            if (!hid) {
                hid = document.createElement('input');
                hid.type = 'hidden';
                hid.id = id + '-hidden';
                hid.name = id;
                document.body.appendChild(hid);
            }
            hid.value = modalVal;
        }
    });

    const modalYears = document.getElementById('modal-years');
    if (modalYears) {
        let hidY = document.getElementById('years-hidden');
        if (!hidY) { hidY = document.createElement('input'); hidY.type='hidden'; hidY.id='years-hidden'; hidY.name='years'; document.body.appendChild(hidY); }
        hidY.value = modalYears.value;
    }
    const modalMonths = document.getElementById('modal-months');
    if (modalMonths) {
        let hidM = document.getElementById('months-hidden');
        if (!hidM) { hidM = document.createElement('input'); hidM.type='hidden'; hidM.id='months-hidden'; hidM.name='months'; document.body.appendChild(hidM); }
        hidM.value = modalMonths.value;
    }

    const modalEl = document.getElementById('filtrosModal');
    const bsModal = bootstrap.Modal.getInstance(modalEl);
    if (bsModal) bsModal.hide();

    const fetchBtn = document.getElementById('fetchDataBtn');
    if (fetchBtn) {
        fetchBtn.click();
    }
}

document.addEventListener('click', function(e){
    if (e.target && e.target.id === 'applyFiltersBtn') {
        copyModalFiltersToPageAndFetch();
    }
});
