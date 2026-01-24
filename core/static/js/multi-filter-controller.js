class MultiFilterController {
    constructor(config) {
        this.filterListEl = config.filterListEl; // container with all selects
        this.filterToggleContainerEl = config.filterToggleContainerEl; // container where toggle should be injected
        this.filters = config.filters; // list of filters
        this.selectedOptionsMap = {}; // track selected values

        this.init();
    }

    // -------------------------------
    // Utility
    // -------------------------------
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    populateSelect(selectEl, items) {
        if (!selectEl || !Array.isArray(items)) return;
        selectEl.innerHTML = '';
        items.forEach(item => {
            if (item.key !== undefined && item.value !== undefined) {
                const option = document.createElement('option');
                option.value = item.key;
                option.text = item.value;
                selectEl.appendChild(option);
            }
        });
    }

    // -------------------------------
    // Initialize a single dropdown
    // -------------------------------
    initDropdown(selectEl, placeholderText) {
        const name = selectEl.name;
        if (!this.selectedOptionsMap[name]) this.selectedOptionsMap[name] = new Set();

        const placeholder = selectEl.options[0];
        placeholder.dataset.defaultText = placeholderText;

        selectEl.addEventListener('change', () => {
            const value = selectEl.value;
            if (!value) return;

            if (this.selectedOptionsMap[name].has(value)) this.selectedOptionsMap[name].delete(value);
            else this.selectedOptionsMap[name].add(value);

            Array.from(selectEl.options).forEach(opt => {
                if (!opt.value) return;
                if (this.selectedOptionsMap[name].has(opt.value)) {
                    opt.text = '🗹 ' + opt.text.replace(/^🗹 |^☐ /, '');
                    opt.setAttribute('checked', 'true');
                } else {
                    opt.text = opt.text.replace(/^🗹 |^☐ /, '');
                    opt.setAttribute('checked', 'false');
                }
            });

            const count = this.selectedOptionsMap[name].size;
            placeholder.text = count > 0 ? `${this.capitalize(name)} (${count})` : placeholder.dataset.defaultText;

            selectEl.selectedIndex = 0;
            this.updateFilterToggleOption(name);
            this.updateFilterTogglePlaceholder();
        });
    }

    // -------------------------------
    // Preselect from URL
    // -------------------------------
    preselectFromURL(selectEl, urlParam) {
        const params = new URLSearchParams(window.location.search);
        if (!params.has(urlParam)) return;

        const values = params.get(urlParam).split(',');
        const name = selectEl.name;
        if (!this.selectedOptionsMap[name]) this.selectedOptionsMap[name] = new Set();
        values.forEach(v => this.selectedOptionsMap[name].add(v));

        Array.from(selectEl.options).forEach(opt => {
            if (!opt.value) return;
            if (this.selectedOptionsMap[name].has(opt.value)) {
                opt.text = '🗹 ' + opt.text.replace(/^🗹 |^☐ /, '');
                opt.setAttribute('checked', 'true');
            } else {
                opt.text = opt.text.replace(/^🗹 |^☐ /, '');
                opt.setAttribute('checked', 'false');
            }
        });

        const placeholder = selectEl.options[0];
        const count = this.selectedOptionsMap[name].size;
        placeholder.text = count > 0 ? `${this.capitalize(name)} (${count})` : placeholder.dataset.defaultText;

        selectEl.classList.remove('d-none');
        this.updateFilterToggleOption(name);
        this.updateFilterTogglePlaceholder();
    }

    // -------------------------------
    // Dynamically create <select> elements for each filter
    // -------------------------------
    createSelectElements() {
        if (!this.filterListEl) return;

        this.filters.forEach(filter => {
            // Only create if it doesn't exist yet
            if (!this.filterListEl.querySelector(`select[name="${filter.name}"]`)) {
                const selectEl = document.createElement('select');
                selectEl.name = filter.name;
                selectEl.className = 'form-control form-control-sm mr-2 d-none select2bs4';
                this.filterListEl.appendChild(selectEl);
            }
        });
    }

    // -------------------------------
    // Populate dropdown from API or static data
    // -------------------------------
    populateAndPreselectDropdown(filter) {
        const selectEl = this.filterListEl.querySelector(`select[name="${filter.name}"]`);
        if (!selectEl) return;

        const placeholder = {key: '', value: this.capitalize(filter.name)};
        if (filter.data) {
            const data = [placeholder, ...filter.data];
            this.populateSelect(selectEl, data);
            this.initDropdown(selectEl, placeholder.value);
            this.preselectFromURL(selectEl, filter.urlParam);
        } else if (filter.fetchUrl) {
            fetch(filter.fetchUrl)
                .then(res => res.json())
                .then(data => {
                    data.unshift(placeholder);
                    this.populateSelect(selectEl, data);
                    this.initDropdown(selectEl, placeholder.value);
                    this.preselectFromURL(selectEl, filter.urlParam);
                });
        }
    }

    // -------------------------------
    // Create the filter toggle dropdown dynamically
    // -------------------------------
    createFilterToggle() {
        if (!this.filterToggleContainerEl) return;

        const toggle = document.createElement('select');
        toggle.className = 'form-control form-control-sm mr-2';
        toggle.id = 'filter-toggle';

        const placeholder = document.createElement('option');
        placeholder.value = '';
        placeholder.text = 'Filter';
        toggle.appendChild(placeholder);

        this.filters.forEach(f => {
            const option = document.createElement('option');
            option.value = f.name;
            option.text = `☐ ${this.capitalize(f.name)}`;
            toggle.appendChild(option);
        });

        this.filterToggleContainerEl.prepend(toggle);
        this.filterToggleEl = toggle;
    }

    // -------------------------------
    // Filter toggle logic
    // -------------------------------
    initFilterToggle() {
        this.createFilterToggle();
        const toggleEl = this.filterToggleEl;
        toggleEl.addEventListener('change', () => {
            const selected = toggleEl.value;
            if (!selected) return;

            const selectEl = this.filterListEl.querySelector(`select[name="${selected}"]`);
            if (selectEl) selectEl.classList.toggle('d-none');

            this.updateFilterToggleOption(selected);
            this.updateFilterTogglePlaceholder();
            toggleEl.selectedIndex = 0;
        });

        this.filters.forEach(f => this.updateFilterToggleOption(f.name));
        this.updateFilterTogglePlaceholder();
    }

    updateFilterToggleOption(name) {
        const toggleEl = this.filterToggleEl;
        const selectedSet = this.selectedOptionsMap[name];
        const option = Array.from(toggleEl.options).find(o => o.value === name);
        if (option) {
            const count = selectedSet ? selectedSet.size : 0;
            option.text = count > 0 ? '🗹 ' + this.capitalize(name) + ` (${count})` : '☐ ' + this.capitalize(name);
        }
    }

    updateFilterTogglePlaceholder() {
        const toggleEl = this.filterToggleEl;
        const placeholder = toggleEl.options[0];
        const totalSelected = Object.values(this.selectedOptionsMap).filter(set => set.size > 0).length;
        placeholder.text = totalSelected > 0 ? `Filter (${totalSelected})` : 'Filter';
    }

    // -------------------------------
    // Initialize all filters
    // -------------------------------
    init() {
        this.createSelectElements();
        this.initFilterToggle();
        this.filters.forEach(f => this.populateAndPreselectDropdown(f));
    }

    // -------------------------------
    // Get current filter selections
    // -------------------------------
    getSelections() {
        const filters = {};
        Object.keys(this.selectedOptionsMap).forEach(name => {
            const set = this.selectedOptionsMap[name];
            if (set && set.size > 0) filters[name] = Array.from(set);
        });
        return filters;
    }
}